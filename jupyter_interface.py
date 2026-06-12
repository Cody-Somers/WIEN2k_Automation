# Created: 05/06/2025 (June 5, 2025)
# Rename to wien2k_jupyter_interface??
import json
import sys
from getpass import getpass # Create server connection
from fabric import Connection # To get python notebook connection to server
from patchwork.transfers import rsync
import h5py # To convert to h5
import chardet # Find Encoding
import os
from pathlib import Path
import re
import hashlib
import time # For testing purposes only
import shutil
import subprocess
import ast
import pexpect

# Necessary python installs
# pip install patchwork
# pip install fabric

# So the plan is....
# We create a list of calculations and their folder that they should be uploaded into.
# All calculations have a delete parameter. If it is, then delete folder
# If it's a different command but no delete parameter and file overlaps then ask if want to delete on cluster
# Check if folder number exists. If no, then go for it. If yes, then check defaults. This will have to be initializiation function.


###################################################################################################################
"""
Updated Jan 8, 2026
Function Interactions and their impact to server calculations

create_new_calculations()
    - Writes JupyterCommands.py holding calculation arguments
initialize_server()
    - Sets up parameters with server info. Does not connect
submit_calculation()
    - Connects to server and uploads JupyterCommands.py and initialization.py, then starts program
upload_file()
    - If user wants to manually upload a file
find_encoding()
    - Used when different servers might have different file encodings. Only if error.
download_info()
    - Connects to server and downloads all files that have changed since last iteration
    - check_file_modified()
    - md5()
    - convert_to_hdf5()
        * create_dataset()
"""
###################################################################################################################
# Main Class

# TODO: Change it so that it does all the value finding on the server, then sends a single file of parameters + the dos/xspec files.
# TODO: Create a function that can upload the entire folder with the specifics that we want to the cluster

class JupyterInterface:
    """
    An interface between a local jupyter notebook and a remote server running Wien2k.
    """

    def __init__(self, cif_file, storage_directory = None):
        with open("JupyterCommands.py", "w") as file:
            pass
        with open("logbook.txt", "a") as file:#TODO: Actually do something with logbook
            pass
        self.working_directory = None
        self.server_name = None
        self.server_connection = None
        self.cif_file = cif_file
        if storage_directory is None:
            self.storage_directory = f"{Path(self.cif_file).stem}_WIEN2k_data"
        else:
            self.storage_directory = storage_directory

        self.slurm_options_keys = ["--job-name", "--mail-user", "--mail_type", "--account", "--partition",
                              "--nodes", "--ntasks-per-node", "--mem", "--time",
                              "max-ntasks-per-node", "max-mem-per-cpu", "misc"]

    def create_new_calculation(self, **kwargs):
        """
        Takes in kwargs and creates a file (JupyterCommands.py) that contains these commands.
        These commands are to be run by initialization.py on the cluster

        Parameters
        ----------
        kwargs: String containing many different parameters

        Returns
        -------
        Creates a new file (JupyterCommands.py)
        """
        os.makedirs(self.storage_directory, exist_ok=True) # Just ensure that the storage directory exists
        identical_folder_count = 0
        identical_folders = []
        identical_folder_log_dict = {}

        for folder in Path(self.storage_directory).iterdir(): # Go through all cases in folder
            if folder.is_dir(): # Exclude any files
                output_log = folder / "output_log.txt"
                if file_exists(output_log): # Check that the log actually exists
                    with open(output_log, "r") as file:
                        log_dict = ast.literal_eval(file.readline()) # Convert string to dictionary
                    # Create duplicate and remove the unwanted categories
                    # Folder Name is unwanted since it changes based on current folder
                    # Slurm options are unwanted since they don't affect final scf outcome of wien2k
                    # WorkflowAction will change depending on if first or second time running command
                    exclude_keys = ["folder_name"] + self.slurm_options_keys + ["workflowAction"] + ["cif_file"]
                    log_dict_filtered = {key: value for key, value in log_dict.items() if key not in exclude_keys}
                    kwargs_filtered = {key: value for key, value in kwargs.items() if key not in exclude_keys}
                    if kwargs_filtered == log_dict_filtered: # If we have a match, then append the folder name into a list to access later
                        identical_folder_count += 1
                        identical_folders.append(folder)
                        identical_folder_log_dict = log_dict_filtered
                else:
                    print("No output_log file found for " + folder.name)

        if identical_folder_count > 0: # If we have a calculation that already exists somewhere
            print("Current parameters are: " + str(identical_folder_log_dict)) # output parameters from when there was a match
            print("An existing calculation already exists in folders: ")
            identical_folders = sorted(identical_folders) # Sort to get it in numerical order
            for index, folder in enumerate(identical_folders):
                print(str(index) + ") " + folder.stem) # Print out list for user to see
            if identical_folder_count > 1:
                folder_selection = input("Press select a folder to continue: ")
                folder = str(identical_folders[int(folder_selection)]) # Access folder by index
            else:
                folder = str(identical_folders[0]) # Only one folder, so choose it by default.

            print("Options are: ")
            print("1) Delete old calculation and overwrite it in the same folder")
            print("2) Create new calculation in a new folder")
            print("3) Resubmit job file without altering current parameters")
            print("4) Cancel and take no effect")
            calc_decision = input("Enter a number: ")
            match calc_decision:
                case "1": # Delete and start new calc
                    certain = input("All files in original folder " + folder + " are going to be erased. Are you sure? [y/n]:")
                    if certain not in ["y", "yes", "Y", "Yes"]:
                        print("Exiting calculation creation with nothing has been deleted or submitted to server. Please rerun the notebook cell.")
                        sys.exit(1)
                    else:
                        print("Deleting all files in folder " + folder)
                        shutil.rmtree(folder)
                        os.makedirs(folder, exist_ok=True)
                        shutil.copy(self.cif_file, folder)
                        kwargs.update({"folder_name": folder, "workflowAction": "overwrite"})
                        print("New folder created in folder " + folder)
                case "2": # Make a new folder
                    folder = make_new_working_folder(self.cif_file, self.storage_directory)
                    kwargs.update({"folder_name": folder, "workflowAction": "create"})
                    print("New folder created in folder " + folder)
                case "3": # Resubmit, add flag
                    kwargs.update({"folder_name": folder, "workflowAction": "resubmit"})
                    print("Resubmitting job file without altering current parameters in folder " + folder)
                case "4": # Cancel submission
                    print(
                        "Exiting calculation creation with nothing has been submitted to server. Please rerun the notebook cell.")
                    sys.exit(1)
                case _:
                    print("Invalid input.")
                    sys.exit(1)
        else:
            folder = make_new_working_folder(self.cif_file, self.storage_directory)
            kwargs.update({"folder_name": folder, "workflowAction": "create"})
            print("New folder created in folder " + folder)

        # This creates the file that will up uploaded to server
        kwargs.update({"cif_file": self.cif_file})
        # kwargs.update("scf status, folder name" "resubmit, overwrite") # If we want brand new calculation then folder name will be a new number
        # Issue is if they delete a folder locally but not on the cluster, we should ask if they want to delete and output the parameters from that folder too.
        with open("JupyterCommands.py", "a") as file:
            # Initialization(**kwargs).main_program()
            # file.write(f"Initialization(cif_file='{self.cif_file}',{(','.join('{0}={1!r}'.format(k, v) for k, v in kwargs.items()))}).main_program()\n")
            file.write(f"Initialization({kwargs}).main_program()\n")
        with open(folder + '/' + "output_log.txt", "w") as file:
            file.write(f"{kwargs}")
        # return self

    def initialize_server(self, working_directory, server_name, ssh_key=None, password=None):
        """
        Sets up the connection parameters for a server. Does not actually do any interacting with the server, but
        is necessary for other functions to properly connect.

        Parameters
        ----------
        password: String. Specify password to use when connecting to the server
        working_directory: String. Specify the working directory of the server
        server_name: String. Specify the name of the server. user@host.ca:port
        ssh_key: Boolean or String. Specify True if keys are handled entirely by the server, otherwise provide file
            where the ssh key is located.

        Returns
        -------
        Parameters for server connection
        """

        self.working_directory = working_directory
        self.server_name = server_name
        if ssh_key is None:
            if password is None:
                password = getpass('Enter the password for %s: ' % self.server_name)
                self.server_connection = Connection(self.server_name, connect_kwargs={"password": password})
            else:
                self.server_connection = Connection(self.server_name, connect_kwargs={"password": password})
        elif ssh_key is True:
            self.server_connection = Connection(self.server_name)
        else:
            self.server_connection = Connection(self.server_name, connect_kwargs={"key_filename": ssh_key})

    def submit_calculations(self):
        """
        Puts the list of calculations onto the server, along with python program, then runs it.

        Returns
        -------
        Two files onto server, and job submission.
        """
        if self.server_connection is not None:
            with self.server_connection as c:
                # run_terminal_command("rsync -pthrvz --rsh='ssh -p 22 ' /Users/cas003/PycharmProjects/JupyterWien2k/TiCv2_WIEN2k_data cas003@plato.usask.ca:/globalhome/cas003/HPC/TestingStuff/TeakTest")
                # rsync(c, os.getcwd() + "/" + self.storage_directory, self.working_directory,strict_host_keys=False,ssh_opts='pysshpass ssh cas003@plato.usask.ca')
                c.put(self.cif_file, self.working_directory) # Upload cif file
                c.put('initialization.py', self.working_directory) # Upload program instructions
                c.put('JupyterCommands.py', self.working_directory) # Upload calculations to run
                # TODO: Remove jupytercommands from local server after successful upload
                with c.cd(self.working_directory):
                    c.run('python initialization.py') # Ensure python on cluster
        else:
            print("No connection to server")

    def upload_file(self,filename,overwrite=False):
        """
        Allows user to upload a single file

        Parameters
        ----------
        filename: File to be uploaded
        overwrite: If file exists, do not overwrite. Currently non-functional.

        Returns
        -------
        File to server
        """
        if self.server_connection is not None:
            with self.server_connection as c: # This will open and close connection automatically
                c.put(filename, self.working_directory) # TODO: Check if file already exists
        else:
            print("No connection to server")

    def find_encoding(self):
        """
        Reads the two files generated on the server (initialization.py) and attempts to determine which encoding
        type is present. Then print out to user.

        Returns
        -------
        Outputs text to jupyter notebook
        """
        if self.server_connection is not None:
            with self.server_connection as c:
                c.get(self.working_directory + '/encoding_stdout')
                c.get(self.working_directory + '/encoding_stderr')
                with open("encoding_stdout", 'rb') as f:
                    data = f.read()  # or a chunk, f.read(1000000)
                encoding = chardet.detect(data).get("encoding")
                print("Standard Output in: " + encoding)
                with open("encoding_stderr", 'rb') as f:
                    data = f.read()  # or a chunk, f.read(1000000)
                encoding = chardet.detect(data).get("encoding")
                print("Standard Error in: " + encoding)
        else:
            print("No connection to server")

    def download_info(self,do_hash=True):
        """
        Creates a hash table to check if any change occurs since the last download.
        Will download all files that have changes and store them locally.
        For large systems (+30sec download times) it is roughly 2x faster to do hash table check then it is to download all files each time.
        It then converts them to HDF5 files.

        Parameters
        ----------
        do_hash: Controls whether to perform a hash, or to simply download all files in the DownloadFolder

        Returns
        -------
    `   A local folder containing all server folders with case name
        An hdf5 file
        """
        if self.server_connection is not None:
            with self.server_connection as c:  # This will open and close connection automatically
                print("Starting download")
                start_time = time.perf_counter()

                c.put('download_info.py', self.working_directory)  # Upload file to compile info on cluster
                with c.cd(self.working_directory):
                    c.run(f'python download_info.py {self.cif_file}')

                # Make storage folder locally
                folder_name = Path(self.cif_file).stem
                storage_folder = f"StorageFor{folder_name}"
                Path(storage_folder).mkdir(exist_ok=True)

                if do_hash:
                    # Make hash table
                    with open("hash_table.txt", "w") as hash_table:
                        for dirpath, dirnames, files in os.walk(storage_folder):
                            for file in files:
                                #s = f"{file} + md5({dirpath} + '/' + file"
                                s = file + md5(dirpath + "/" + file) # Note this is our md5 function to get contents
                                hash_value = hashlib.md5(s.encode()).hexdigest() # This uses general function to get filename in string
                                hash_table.write(hash_value)
                                # So we are hashing contents of file, then adding name to the front and hashing that string.
                                # Co_000.inm gives hash 1e56p (all identical .inm files will give the same hash however)
                                # Then we hash(Co_000.inm1e56p) and get a new hash
                                # This allows us to tell if a specific file has changed in contents or name.

                                #print("File" + file + " converted locally with hash " + hash_value)
                    c.put("hash_table.txt", self.working_directory) # Throw it onto server

                    # Go through the files in DownloadFolder and download whatever has been updated.
                    with c.cd(self.working_directory):
                        c.run(f'find ~+ -type f | grep DownloadFolder > foldernames.txt')
                        c.get(f"{self.working_directory}/foldernames.txt")

                        # On server check to see which files have been changed compared to the ones downloaded locally
                        c.put("check_file_modified.sh", self.working_directory)
                        c.run('chmod +x check_file_modified.sh')
                        c.run('./check_file_modified.sh')
                        c.get(f"{self.working_directory}/foldernames_updated.txt")

                        # Locally, sort through all the files and find the ones that we want
                        with open("foldernames_updated.txt", 'r') as f:
                            for file_location_server in f:
                                c.get(file_location_server.strip())
                                shutil.move(Path(file_location_server.strip()).name, os.path.join(storage_folder,Path(file_location_server.strip()).name))
                else: # This will just download all files, without worrying about hash table. In case md5 doesn't exist on cluster
                    with c.cd(self.working_directory):
                        c.run(f'find ~+ -type f | grep DownloadFolder > foldernames.txt') # Get path of files in DownloadFolder
                        c.get(f"{self.working_directory}/foldernames.txt")
                        # Locally, sort through all the files and find the ones that we want
                        with open("foldernames.txt", 'r') as f:
                            for file_location_server in f:
                                c.get(file_location_server.strip())
                                shutil.move(Path(file_location_server.strip()).name,os.path.join(storage_folder, Path(file_location_server.strip()).name)) # Move into storage folder

                self.convert_to_hdf5(storage_folder)

                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                print(f"Execution time: {elapsed_time:.4f} seconds")
                print("Download Complete")
        else:
            print("No connection to server")
        return

    def convert_to_hdf5(self, storage_folder):
        """
        Converts desired parameters from text into an hdf5 file.

        Parameters
        ----------
        storage_folder: Path to the folder containing the downloaded files from the cluster.

        Returns
        -------
        An hdf5 file
        """
        # Just go through the parameters and create the dataset based on the name of each of the keys in the dictionary
        with open(storage_folder+"/parameter_info.json", 'r') as f:
            data_list = json.load(f)
            for i in range(len(data_list)):
                # print(data_list[i])
                case_name = data_list[i]["case_name"]
                for key, value in data_list[i].items():
                    self.create_dataset(f"{case_name}/parameters/{key}", data = value)

    def print_h5_structure(self):
        """
        Prints the entire h5 structure to terminal
        """
        try:
            with h5py.File(Path(self.cif_file).stem + ".hdf5", 'r') as file:
                # for name in file:
                #    print(name)
                def printname(name):
                    print(name)
                file.visit(printname)
        except FileNotFoundError:
            with h5py.File(Path(self.cif_file).stem + ".h5", 'r') as file:
                # for name in file:
                #    print(name)
                def printname(name):
                    print(name)
                file.visit(printname)

    def create_dataset(self, dataset_name, **kwargs):
        """
        Creates a dataset in the hdf5 file. Will overwrite existing dataset.

        Parameters
        ----------
        dataset_name: Name of dataset to be created
        kwargs: Information to be stored in dataset

        Returns
        -------
        New dataset in hdf5 file
        """
        # Only creates a dataset of the information that is actually downloaded from the server. Needs to do that to convert to hdf5
        with h5py.File(Path(self.cif_file).stem + ".hdf5", 'a') as h5_file: # Main file to store all info
            if dataset_name in h5_file.keys():
                del h5_file[dataset_name]
                h5_file.create_dataset(dataset_name, **kwargs)
            else:
                h5_file.create_dataset(dataset_name, **kwargs)

###################################################################################################################
### Helper Functions

def string_matching(s1, s2):
    return sorted(s1) == sorted(s2)

def file_exists(file_name):
    """
    Search if file exists in current directory

    Parameters
    ----------
    file_name: string

    Returns
    -------
    True if the file exists, False otherwise
    """
    if os.path.exists(file_name): # Check if path exists
        return os.path.isfile(file_name) # Check that path is a file and not a directory
    else:
        return False


def configure_xspec(start, end, edge):
    """
    Helper function to configure xspec parameters. Will be automated later.

    Parameters
    ----------
    start: First atom in the unit cell of a specific edge.
    end: Final atom in the unit cell of a specific edge.
    edge: The desired edge. ["1s","2s","2p","3s","3p","3d","4s","4p","4d","4f"]

    Returns
    -------
    Prints to terminal the xspec configuration.
    """
    # array
    array = ["1s","2s","2p","3s","3p","3d","4s","4p","4d","4f"]
    n_arr = [1,2,2,3,3,3,4,4,4,4]
    l_arr = [0,0,1,0,1,2,0,1,2,3]
    inside = ""
    for i in range(start,end+1):
        inside += str(i)+',"'+edge+'",'
    print("[" + inside + "]")


def md5(fname):
    """
    Function to help calculate the md5 hash of a file.
    """
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def run_terminal_command(args, silent=False):
    """
    Will run a command in terminal and return its output. Has built in error handling.

    Parameters
    ----------
    args: command line arguments to be run
    silent: boolean to determine if command should be printed to terminal.

    Returns
    -------
    stdout: return output from command
    exit(1): If error occurred, exit with error code
    """
    print(args)  # Print input commands for user to see in jupyter notebook
    # Some clusters have different encoding types and may need to be specified manually.
    # Common encoding includes UTF-8/16/32, ASCII
    command = subprocess.run(args, shell=True, capture_output=False, check=False, text=False)
    if not silent:
        print(command.stdout)  # Print output results for user
    return command.stdout

def make_new_working_folder(cif_file, storage_directory):
    """
    Creates a new folder, with a naming scheme of case_000 to case_999, incrementing based on previously existing files.

    Parameters
    ----------
    cif_file: name of the file to be created/appended to.
    storage_directory: name of the folder to be created/appended to.

    Returns
    -------
    A new folder properly named
    """
    cif_file_no_extension = Path(cif_file).stem # Remove the extension
    # Make the new folder with numerical name
    for i in range(0, 1000):
        if os.path.exists(f'./{storage_directory}/{cif_file_no_extension}_00{i}'):
            pass
        elif os.path.exists(f'./{storage_directory}/{cif_file_no_extension}_0{i}'):
            pass
        elif os.path.exists(f'./{storage_directory}/{cif_file_no_extension}_{i}'):
            pass
        else:
            if i < 10:
                folder_name = cif_file_no_extension + '_00' + str(i)
            elif i < 100:
                folder_name = cif_file_no_extension + '_0' + str(i)
            else:
                folder_name = cif_file_no_extension + '_' + str(i)
            os.makedirs(storage_directory + '/' + folder_name, exist_ok=True)
            shutil.copy(cif_file, storage_directory + '/' + folder_name) # Can also likely be a struct file?
            return storage_directory + '/' + folder_name
    print("Have reached maximum number of files (1000 max). Make a new folder with original cif and start again.")
    sys.exit(1)

# H5 Data Storage Rough Structure
"""
Have a file with the name of the cif
f = h5py.File('Cif Name', 'a')

In the file we store the individual calculations as groups
grp = f.create_group('Cif_001')

# Make a dataset for each of the things that we care about
dset = grp.create_dataset('Binding Energy', data='f')

grp = f.create_group('Cif_002')
"""



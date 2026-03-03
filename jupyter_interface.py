# Created: 05/06/2025 (June 5, 2025)
# Rename to wien2k_jupyter_interface??

from getpass import getpass # Create server connection
from fabric import Connection # To get python notebook connection to server
import h5py # To convert to h5
import chardet # Find Encoding
import os
from pathlib import Path
import re
import hashlib
import time # For testing purposes only

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

class JupyterInterface:
    """
    List of parameters that you can customize and their default values
    rkmax = None,           nn = None,
    functional = None,      cutoff_energy = None,
    kgen = None,            e_range = (-10.0, 4),
    cif_file = None,        encoding_type = None,
    errors = None,          sbatch = None,
    scf_type = "Basic",     xspec = "True",
    resubmit = "False",     scratch = "$SCRATCH",
    xspec_config = None,    email_address = None,
    account = None,         cpu_limit = 32,
    node_limit = 3,         timelimit = "01:00:00"
    """

    def __init__(self, cif_file):
        with open("JupyterCommands.py", "w") as file:
            pass
        with open("logbook.txt", "a") as file:
            pass
        self.working_directory = None
        self.server_name = None
        self.server_connection = None
        self.cif_file = cif_file

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
        with open("JupyterCommands.py", "a") as file:
            # Initialization(**kwargs).main_program()
            file.write(f"Initialization(cif_file='{self.cif_file}',{(','.join('{0}={1!r}'.format(k, v) for k, v in kwargs.items()))}).main_program()\n")

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
                c.put(self.cif_file, self.working_directory) # Upload cif file
                c.put('initialization.py', self.working_directory) # Upload program instructions
                c.put('JupyterCommands.py', self.working_directory) # Upload calculations to run
                # TODO: Remove jupytercommands from local server after successful upload
                with c.cd(self.working_directory):
                    c.run('python initialization.py') # Gotta have python on cluster
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

    def download_info(self, overwrite = False, download_all = False):
        """
        Creates a hash table to check if any change occurs since the last download.
        Will download all files that have changes and store them locally.
        It's roughly 2-3x faster to do hash table check then it is to download all files each time.
        It then converts them to HDF5 files.

        Parameters
        ----------
        overwrite: Not working, want an option that any existing files (even if changed) will not be overwritten.
        download_all: This forces the program to download all files, even if no change.

        Returns
        -------
    `   A local folder containing all server folders with case name
        An hdf5 file
        """
        if self.server_connection is not None:
            with self.server_connection as c:  # This will open and close connection automatically
                print("Starting download")
                start_time = time.perf_counter()

                # Make storage folder
                folder_name = Path(self.cif_file).stem
                current_folder = os.getcwd()
                storage_folder = f"StorageFor{folder_name}"
                Path(storage_folder).mkdir(exist_ok=True)

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

                # Test if we find the value we want. Remove
                with open("hash_table.txt", "r") as hash_table:
                    if "5be6ce84" in hash_table.read():
                        print("We found it")


                # Generate string to only find the files that we want directly from the server
                files_we_want = ['.in1', 'in1c', '.in2', 'in2c', '.klist', '.outputd', '.scf2', '.scfc', '.txspec','.dos']
                bash_command_middle = ""
                for index, extension in enumerate(files_we_want):
                    if index != len(files_we_want)-1: # Go until last index
                        bash_command_middle += f"-name '*{extension}' -o "
                    else:
                        bash_command_middle += f"-name '*{extension}'"
                bash_command = "find ~+ -type f " + bash_command_middle + f" | grep {folder_name}_ > foldernames.txt"

                # If we need the \( then add back, but this seems to work
                # bash_command = "find ~+ -type f \(" + bash_command_middle + f" \) | grep {folder_name}_ > foldernames.txt"

                # On server find all files
                with c.cd(self.working_directory):
                    # Find all files in the directory
                    if download_all: #TODO: Implement this so that it actually pulls all cases
                        c.run(f'find ~+ -type f | grep {folder_name}_ > foldernames.txt')
                        c.get(f"{self.working_directory}/foldernames.txt")
                    else:
                        c.run(bash_command)

                # On server check to see which files have been changed compared to the ones downloaded locally
                self.check_file_modified()
                c.get(f"{self.working_directory}/foldernames_updated.txt")

                # Locally, sort through all the files and find the ones that we want
                with open("foldernames_updated.txt", 'r') as f:
                    for file_location_server in f:
                        # TODO: Might break in windows with the different slash directions
                        # TODO: Figure out how to check if it changed from previous versions. So, using md5sum likely.

                        # The location of the file on the local computer and where we want to put it.
                        # NOTE: We use strip to remove the \n character at the end of the line in the txt file
                        file_location_local = current_folder + '/' + storage_folder + '/' + Path(file_location_server.strip()).parent.name + '/' + Path(file_location_server.strip()).name
                        Path(storage_folder + '/' + Path(file_location_server.strip()).parent.name).mkdir(exist_ok=True)
                        c.get(file_location_server.strip(), file_location_local)
                        self.convert_to_hdf5(file_location_local)
                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                print(f"Execution time: {elapsed_time:.4f} seconds")
                print("Download complete")
                # TODO: Add server name to download, so if you have identical calculations on different servers then you know which came where.
        else:
            print("No connection to server")
        return

    def convert_to_hdf5(self, file_name, overwrite = False):
        """
        Converts desired parameters from text into an hdf5 file.

        Parameters
        ----------
        file_name: name of file to be converted
        overwrite: not working. Want option to not overwrite existing files

        Returns
        -------
        An hdf5 file
        """
        # This parses through the files and gets the info we care about
        case_name = Path(file_name.strip()).stem
        if Path(file_name.strip()).suffix == '.in1' or Path(file_name.strip()).suffix == '.in1c':  # This is for RKMax, Emin/Emax
            with open(file_name, 'r') as in1:
                in1_lines = in1.readlines()
                rkmax = float(in1_lines[1].split()[0])  # Get the second line, first value, which is rkmax
                emin = float(in1_lines[-1].split()[3])  # Last line, second value
                emax = float(in1_lines[-1].split()[4])  # Last line, third value
            self.create_dataset(f"{case_name}/parameters/rkmax", data=rkmax)
            self.create_dataset(f"{case_name}/parameters/inputEnergyRange", data = [emin,emax])#data=(float(emin),float(emax))) #data=[emin, emax])
        elif Path(file_name.strip()).suffix == '.scf2':  # This is for :GAP, :FER, high/low energy sep
            with open(file_name, 'r') as scf2:
                scf2_lines = scf2.readlines()
                for i in scf2_lines:
                    if re.search(":GAP \(global\)", i):  # TODO: Spin polarized has GAP (this spin)
                        gap_ry = float(i.split()[3])
                        gap_ev = float(i.split()[6])
                        self.create_dataset(f"{case_name}/parameters/bandgap", data=[gap_ry, gap_ev])
                    elif re.search(":FER", i):
                        fermi = i.split()[9]
                        self.create_dataset(f"{case_name}/parameters/fermi", data=fermi)
                    elif re.search("Energy to separate low and high energystates", i):
                        low_high_sep = i.split()[7]
                        self.create_dataset(f"{case_name}/parameters/energystatesSeparation", data=low_high_sep)


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

    def check_file_modified(self):
        """
        Puts shell script onto server and checks if file is modified by using hash table.
        It's faster to run md5sum on directly on server than to send each command individually.

        Returns
        -------
        Runs shell script on server
        """
        if self.server_connection is not None:
            with self.server_connection as c:  # This will open and close connection automatically
                c.put("check_file_modified.sh", self.working_directory)
                with c.cd(self.working_directory):
                    c.run('chmod +x check_file_modified.sh')
                    c.run('./check_file_modified.sh')
        else:
            print("No connection to server")



###################################################################################################################
### Helper Functions

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



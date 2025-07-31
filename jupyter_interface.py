# Created: 05/06/2025 (June 5, 2025)
# Last Edit: 24/06/2025
# Rename to wien2k_jupyter_interface??

# TODO: Make these import statements local to the functions. This allows us to not force user to make imports if they don't
    # want to user the server functionality

from getpass import getpass # Create server connection

import h5py
import numpy as np
from fabric import Connection
import chardet # Find Encoding
import os
from pathlib import Path
import subprocess
import re
import time # For testing purposes only

def configure_xspec(start, end, edge):
    # Helper function to print out the xspec_config parameter
    # array
    array = ["1s","2s","2p","3s","3p","3d","4s","4p","4d","4f"]
    n_arr = [1,2,2,3,3,3,4,4,4,4]
    l_arr = [0,0,1,0,1,2,0,1,2,3]
    inside = ""
    for i in range(start,end+1):
        inside += str(i)+',"'+edge+'",'
    print("[" + inside + "]")

class JupyterInterface:
    """
    Hela
    """
    def __init__(self, cif_file):
        with open("JupyterCommands.py", "w") as file:
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
        if self.server_connection is not None:
            with self.server_connection as c:
                c.put(self.cif_file, self.working_directory) # Upload cif file
                c.put('initialization.py', self.working_directory) # Upload program instructions
                c.put('JupyterCommands.py', self.working_directory) # Upload calculations to run
                # TODO: Remove jupytercommands from local server after successful upload
                with c.cd(self.working_directory):
                    c.run('python initialization.py')
        else:
            print("No connection to server")

    def upload_file(self,filename,overwrite=False):
        if self.server_connection is not None:
            with self.server_connection as c: # This will open and close connection automatically
                c.put(filename, self.working_directory) # TODO: Check if file already exists
        else:
            print("No connection to server")

    def find_encoding(self):
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

    def download_info_old(self, overwrite = False):
        # TODO: Only download data if we know that it has converged. (Can be based on the xspec folder perhaps)
        # TODO: Could this be implemented by using a bash script that does it all at once. Create a local hash that sees whether it needs to download new folders. No need to check local versions.
        # TODO: Issue if people want to manually download their data and then convert to h5...
        #rsync -vaP somersc0@cedar.alliancecan.ca:/home/somersc0/projects/def-moewes/somersc0/CoFeMnPlusU/PlusUOnlyCo/xspec_export /Users/cas003/Downloads/scratch
        #subprocess.run(f'scp -r somersc0@cedar.alliancecan.ca:/home/somersc0/projects/def-moewes/somersc0/Test/TeakTest/TiCv2_006 ./', shell=True)


        if self.server_connection is not None:
            with self.server_connection as c: # This will open and close connection automatically
                print("Starting download")
                start_time = time.perf_counter()

                with c.cd(self.working_directory):
                    folder_name = Path(self.cif_file).stem
                    #folders = c.run(f'ls | grep {folder_name}_')
                    #c.run(f'find -type d | grep {folder_name} > foldernames.txt')
                    c.run(f'find ~+ -type f | grep {folder_name}_ > foldernames.txt')
                    c.get(f"{self.working_directory}/foldernames.txt")
                    try:
                        c.get(f"{self.working_directory}/checksums.txt")
                    except:
                        pass
                    current_folder = os.getcwd()
                    storage_folder = f"StorageFor{folder_name}"
                    Path(storage_folder).mkdir(exist_ok=True)

                if overwrite: # This will cause issues until we solve only importing
                    h5_flag = 'w'
                else:
                    h5_flag = 'a'
                with open("foldernames.txt", 'r') as f:
                    with h5py.File(Path(self.cif_file).stem + ".hdf5", 'w') as file:  # Main file to store all info #TODO: Change to h5_flag
                        for line in f:
                            # TODO: Might break in windows with the different slash directions
                            # TODO: Figure out how to check if it changed from previous versions. So, using md5sum likely.
                            # TODO: Create the datastructure at the same time that we download info
                                # We generate the md5sum on our local computer, and upload that
                                # Or see if we can md5sum the entire directory
                                # Likely better to make it as a tar and get a single file. Then easy to compare md5sum likely

                            # The location of the file on the local computer and where we want to put it.
                            file_location = current_folder + '/' + storage_folder + '/' + Path(line.strip()).parent.name + '/' + Path(line.strip()).name
                            """ if overwrite:
                                Path(storage_folder + '/' + Path(line.strip()).parent.name).mkdir(exist_ok=True)
                                c.get(line.strip(), file_location)
                            else:
                                if not os.path.exists(file_location):
                                    Path(storage_folder + '/' + Path(line.strip()).parent.name).mkdir(exist_ok=True)
                                    c.get(line.strip(),file_location)
                                else:
                                    #print("File already exists")
                                    pass
"""
                            # TODO: Create something that uses grep to find the parameters and stores in a file before we h5 it???
                            # Check if group exists, if it does then we can delete it and overwrite it with new data???
                            if Path(line.strip()).suffix == '.in1':  # This is for RKMax, Emin/Emax
                                Path(storage_folder + '/' + Path(line.strip()).parent.name).mkdir(exist_ok=True)
                                c.get(line.strip(), file_location)
                                with open(file_location, 'r') as in1:
                                    in1_lines = in1.readlines()
                                    rkmax = in1_lines[1].split()[0] # Get the second line, first value, which is rkmax
                                    emin = in1_lines[-1].split()[3] # Last line, second value
                                    emax = in1_lines[-1].split()[4] # Last line, third value
                                file.create_dataset(f"{Path(line.strip()).stem}/parameters/rkmax",data=rkmax)
                                file.create_dataset(f"{Path(line.strip()).stem}/parameters/inputEnergyRange", data=[emin, emax])
                            if Path(line.strip()).suffix == '.in2':  # GMAX
                                Path(storage_folder + '/' + Path(line.strip()).parent.name).mkdir(exist_ok=True)
                                c.get(line.strip(), file_location)
                                print(line)
                            if Path(line.strip()).suffix == '.klist':  # Get the number of k points, as well as k grid
                                Path(storage_folder + '/' + Path(line.strip()).parent.name).mkdir(exist_ok=True)
                                c.get(line.strip(), file_location)
                                print(line)
                            if Path(line.strip()).suffix == '.outputd':  # Has everything. gmin, gmax, lattice constants, atoms in unit cell, rkmax
                                Path(storage_folder + '/' + Path(line.strip()).parent.name).mkdir(exist_ok=True)
                                c.get(line.strip(), file_location)
                                print(line)
                            if Path(line.strip()).suffix == '.scf2':  # This is for :GAP, :FER, high/low energy sep
                                Path(storage_folder + '/' + Path(line.strip()).parent.name).mkdir(exist_ok=True)
                                c.get(line.strip(), file_location)
                                with open(file_location, 'r') as scf2:
                                    scf2_lines = scf2.readlines()
                                    for i in scf2_lines:
                                        if re.search(":GAP \(global\)",i): # TODO: Spin polarized has GAP (this spin)
                                            gap_ry = i.split()[3]
                                            gap_ev = i.split()[6]
                                            file.create_dataset(f"{Path(line.strip()).stem}/parameters/bandgap",data=[gap_ry, gap_ev])
                                        elif re.search(":FER",i):
                                            fermi = i.split()[9]
                                            file.create_dataset(f"{Path(line.strip()).stem}/parameters/fermi",data=fermi)
                                        elif re.search("Energy to separate low and high energystates",i):
                                            low_high_sep = i.split()[7]
                                            file.create_dataset(f"{Path(line.strip()).stem}/parameters/energystatesSeparation", data=low_high_sep)

                            if Path(line.strip()).suffix == '.scfc':  # Has the energy of the core states, 1S, 2S, 2P etc.
                                Path(storage_folder + '/' + Path(line.strip()).parent.name).mkdir(exist_ok=True)
                                c.get(line.strip(), file_location)
                                print(line)

                with h5py.File(Path(self.cif_file).stem + ".hdf5", 'r') as file:
                    #for name in file:
                    #    print(name)
                    def printname(name):
                        print(name)
                    file.visit(printname)


                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                print(f"Execution time: {elapsed_time:.4f} seconds")
                print("Download complete")
        else:
            print("No connection to server")

    def convert_to_hdf5_old(self):
        with h5py.File(Path(self.cif_file).stem + ".hdf5", 'w') as file: # Main file to store all info
            # Iterate over all folders in the storage
            case = file.create_group("ToCv2_006")

            # Parameters to read from files
            parameters = case.create_group("parameters")
            parameters.create_dataset("fermi_energy", shape=1, dtype='f') # Make these attributes?
            parameters.create_dataset("Emin/Emax",shape=(2,1), dtype='f')

            # If they exist, collect the xspec_export folder
            xspec = case.create_group("xspec")

            # If they exist, collect the dos
            dos = case.create_group("dos")
            print("Converting to HDF5")

    def download_info(self, overwrite = False):
        if self.server_connection is not None:
            with self.server_connection as c:  # This will open and close connection automatically
                print("Starting download")
                start_time = time.perf_counter()

                with c.cd(self.working_directory):
                    folder_name = Path(self.cif_file).stem
                    c.run(f'find ~+ -type f | grep {folder_name}_ > foldernames.txt')
                    c.get(f"{self.working_directory}/foldernames.txt")

                current_folder = os.getcwd()
                storage_folder = f"StorageFor{folder_name}"
                Path(storage_folder).mkdir(exist_ok=True)

                with open("foldernames.txt", 'r') as f:
                    for line in f:
                        # TODO: Might break in windows with the different slash directions
                        # TODO: Figure out how to check if it changed from previous versions. So, using md5sum likely.

                        # The location of the file on the local computer and where we want to put it.
                        # NOTE: We use strip to remove the \n character at the end of the line in the txt file
                        file_location = current_folder + '/' + storage_folder + '/' + Path(line.strip()).parent.name + '/' + Path(line.strip()).name
                        files_we_want = ['.in1','.in2','.klist','.outputd','.scf2','.scfc','.txspec']
                        if Path(line.strip()).suffix in files_we_want:  # This is for RKMax, Emin/Emax
                            Path(storage_folder + '/' + Path(line.strip()).parent.name).mkdir(exist_ok=True)
                            c.get(line.strip(), file_location)
                            self.convert_to_hdf5(file_location)
                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                print(f"Execution time: {elapsed_time:.4f} seconds")
                print("Download complete")
        else:
            print("No connection to server")
        return

    def convert_to_hdf5(self, file_name, overwrite = False):
        # This parses through the files and gets the info we care about
        case_name = Path(file_name.strip()).stem
        if Path(file_name.strip()).suffix == '.in1':  # This is for RKMax, Emin/Emax
            with open(file_name, 'r') as in1:
                in1_lines = in1.readlines()
                rkmax = in1_lines[1].split()[0]  # Get the second line, first value, which is rkmax
                emin = in1_lines[-1].split()[3]  # Last line, second value
                emax = in1_lines[-1].split()[4]  # Last line, third value
            self.create_dataset(f"{case_name}/parameters/rkmax", data=rkmax)
            self.create_dataset(f"{case_name}/parameters/inputEnergyRange", data=[emin, emax])
        elif Path(file_name.strip()).suffix == '.scf2':  # This is for :GAP, :FER, high/low energy sep
            with open(file_name, 'r') as scf2:
                scf2_lines = scf2.readlines()
                for i in scf2_lines:
                    if re.search(":GAP \(global\)", i):  # TODO: Spin polarized has GAP (this spin)
                        gap_ry = i.split()[3]
                        gap_ev = i.split()[6]
                        self.create_dataset(f"{case_name}/parameters/bandgap", data=[gap_ry, gap_ev])
                    elif re.search(":FER", i):
                        fermi = i.split()[9]
                        self.create_dataset(f"{case_name}/parameters/fermi", data=fermi)
                    elif re.search("Energy to separate low and high energystates", i):
                        low_high_sep = i.split()[7]
                        self.create_dataset(f"{case_name}/parameters/energystatesSeparation", data=low_high_sep)


    def print_h5_structure(self):
        with h5py.File(Path(self.cif_file).stem + ".hdf5", 'r') as file:
            # for name in file:
            #    print(name)
            def printname(name):
                print(name)
            file.visit(printname)

    def create_dataset(self, dataset_name, **kwargs):
        with h5py.File(Path(self.cif_file).stem + ".hdf5", 'a') as h5_file: # Main file to store all info
            if dataset_name in h5_file.keys():
                del h5_file[dataset_name]
                h5_file.create_dataset(dataset_name, **kwargs)
            else:
                h5_file.create_dataset(dataset_name, **kwargs)

# H5 Data Storage
"""
Have a file with the name of the cif
f = h5py.File('Cif Name', 'a')

In the file we store the individual calculations as groups
grp = f.create_group('Cif_001')

# Make a dataset for each of the things that we care about
dset = grp.create_dataset('Binding Energy', data='f')

grp = f.create_group('Cif_002')
"""



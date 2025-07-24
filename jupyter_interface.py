# Created: 05/06/2025 (June 5, 2025)
# Last Edit: 24/06/2025
# Rename to wien2k_jupyter_interface??

# TODO: Make these import statements local to the functions. This allows us to not force user to make imports if they don't
    # want to user the server functionality

from getpass import getpass # Create server connection
from fabric import Connection
import chardet # Find Encoding
import os
from pathlib import Path
import subprocess

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

    def download_info(self, overwrite = False): #TODO: Create an overwrite feature
        # TODO: Only download data if we know that it has converged. (Can be based on the xspec folder perhaps)
        #subprocess.run(f'scp -r somersc0@cedar.alliancecan.ca:/home/somersc0/projects/def-moewes/somersc0/Test/TeakTest/TiCv2_006 ./', shell=True)


        if self.server_connection is not None:
            with self.server_connection as c: # This will open and close connection automatically
                with c.cd(self.working_directory):
                    folder_name = Path(self.cif_file).stem
                    #folders = c.run(f'ls | grep {folder_name}_')
                    #c.run(f'find -type d | grep {folder_name} > foldernames.txt')
                    c.run(f'find ~+ -type f | grep {folder_name}_ > foldernames.txt')
                    c.get(f"{self.working_directory}/foldernames.txt")
                    current_folder = os.getcwd()
                    storage_folder = f"StorageFor{folder_name}"
                    Path(storage_folder).mkdir(exist_ok=True)
                with open("foldernames.txt", 'r') as f:
                    for line in f:
                        # TODO: Might break in windows with the different slash directions
                        Path(storage_folder + '/' + Path(line.strip()).parent.name).mkdir(exist_ok=True)
                        c.get(line.strip(),current_folder + '/' + storage_folder + '/' + Path(line.strip()).parent.name + '/' + Path(line.strip()).name)

                print("Download complete")


                # Get the folder name
                # Check if file exists
                # Get the file name
                # Copy to

                #print(self.working_directory + '/' + Path(self.cif_file).stem + "_006")
                #c.get(self.working_directory + '/' + Path(self.cif_file).stem + "_006",'./')
                #folder_name = Path(self.cif_file).stem + '_006'
                #Path(folder_name).mkdir(exist_ok=True)
                #c.get('/home/somersc0/projects/def-moewes/somersc0/Test/TeakTest/TiCv2_006/nn.def','/Users/cas003/PycharmProjects/JupyterWien2k/TiCv2_006/nn.def')
                #c.get('/home/somersc0/projects/def-moewes/somersc0/Test/TeakTest/TiCv2_006/')
                # So error in putting it because the local directory is a directory?{?? Bruv

                # Things we want to get
        else:
            print("No connection to server")


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



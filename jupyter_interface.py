# Created: 05/06/2025 (June 5, 2025)
# Last Edit: 24/06/2025
# Rename to wien2k_jupyter_interface??

# TODO: Make these import statements local to the functions. This allows us to not force user to make imports if they don't
    # want to user the server functionality

from getpass import getpass # Create server connection
from fabric import Connection
import chardet # Find Encoding
import os

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
    def __init__(self, name="JupyterCommands"):
        self.name = name
        with open(self.name + ".py", "w") as file:
            pass
        self.working_directory = None
        self.server_name = None
        self.server_connection = None
        self.password = None

    def create_new_calculation(self, **kwargs):
        with open(self.name + ".py", "a") as file:
            # Initialization(**kwargs).main_program()
            file.write(f"Initialization({(','.join('{0}={1!r}'.format(k, v) for k, v in kwargs.items()))}).main_program()\n")

    def initialize_server(self, working_directory, server_name, ssh_key=False):
        self.working_directory = working_directory
        self.server_name = server_name
        if not ssh_key:
            self.password = getpass('Enter the password for %s: ' % self.server_name)
            self.server_connection = Connection(self.server_name, connect_kwargs={"password": self.password})
        else:
            self.server_connection = Connection(self.server_name)

    def upload_cif_structure(self,filename,overwrite=False):
        if self.server_connection is not None:
            with self.server_connection as c: # This will open and close connection automatically
                c.put(filename, self.working_directory) # TODO: Check if cif file already exists
        else:
            print("No connection to server")

    def submit_calculation(self):
        if self.server_connection is not None:
            with self.server_connection as c:
                c.put('initialization.py', self.working_directory)
                c.put('JupyterCommands.py', self.working_directory)
                # TODO: Remove jupytercommands from local server after successful upload
                with c.cd(self.working_directory):
                    c.run('python initialization.py')
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
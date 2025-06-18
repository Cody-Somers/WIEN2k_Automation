# Created: 05/06/2025 (June 5, 2025)
# Last Edit: 17/06/2025

# Rename to wien2k_jupyter_interface??

from fabric import Connection
import os

def create_job_file(slurm_job="run.job", scf_type="Basic", xspec="False", resubmit="False"):
    # This will hold the info for a job file. So in jupyter notebook they can create the auto_run, but they can also create
    # a job file. They will have to upload then

    return

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

    def create_new_calculation(self, **kwargs):
        with open(self.name + ".py", "a") as file:
            # Initialization(**kwargs).main_program()
            file.write(f"Initialization({(','.join('{0}={1!r}'.format(k, v) for k, v in kwargs.items()))}).main_program()\n")

    def initialize_server(self, working_directory, server_name):
        self.working_directory = working_directory
        self.server_name = server_name
        if self.server_connection is None:
            self.server_connection = Connection(self.server_name)
        else: # If server connection already exists, we close it before making new
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

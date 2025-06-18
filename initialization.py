# Created: 02/06/2025 (June 2, 2025)
# Last Edit: 17/06/2025

import os
import shutil
import subprocess
from tempfile import mkstemp

# TODO: Create a function that uses the .struct instead of the .cif if it exists
# TODO: Create a function that uses the built in init to see what Wien2k recommends for input parameters
# TODO: Create a function that checks for warnings and outputs them to the user
# TODO: Figure how to replace gmax
# TODO: Create a logbook that keeps track of what commands were sent, and which file name they were sent to.
    # With logbook we should write to the file "CASE #: Failed", then overwrite it afterwards if it succeeded

# Helper Functions
def get_current_folder_name():
    """
    Gets the current working directory name.

    Returns
    -------
    String containing the current folder name
    """
    current_path = os.getcwd() # Get full path
    folder_name = os.path.basename(current_path) # Cut only the last folder
    return folder_name


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

def run_terminal_command(args):
    """
    Will run a command in terminal and return its output. Has built in error handling.

    Parameters
    ----------
    args: command line arguments to be run

    Returns
    -------
    stdout: return output from command
    exit(1): If error occurred, exit with error code
    """
    print(args) # Print input commands
    command = subprocess.run(args, shell=True, capture_output=True, check=True, text=True)
    print(command.stdout) # Print output results

    # Error handling
    check_error_files() # Check if case.error files exist
    for line in command.stdout.splitlines(): # Reads stdout and check if any errors occurred
        if ("ERROR IN OPENING UNIT" or "error: command") in line: # Update this line as more error combinations occur
            exit(1)
    return command.stdout

def check_error_files():
    """
    Checks the case.error files from WIEN2k, and if any exists then it will end the process.

    Returns
    -------
    exit(1): If error occurred, exit with error code
    """
    for file_name in os.listdir('.'): # For all files in current directory
        if file_name.endswith('.error'): # Find case.error
            if len(open(file_name).readlines()) > 0: # If file length is not 0 then error occurred
                print("Error in file: " + file_name)
                for line in open(file_name).readlines(): # Print out error for user
                    print(line)
                exit(1)


def replace(source_file_path, pattern, substring):
    """

    Parameters
    ----------
    source_file_path
    pattern
    substring

    Returns
    -------

    """
    fh, target_file_path = mkstemp()
    with open(target_file_path, 'w') as target_file, open(source_file_path, 'r') as source_file:
        for line in source_file:
            target_file.write(line.replace(pattern, substring))
    run_terminal_command(f'rm {source_file_path}')
    run_terminal_command(f'mv {target_file_path} {source_file_path}')


def make_new_working_folder():
    # Make the new folder with numerical name
    for i in range(0, 1000):
        if os.path.exists(f'./{i}'):
            pass
        else:
            os.mkdir(f'./{i}')
            # Copy the cif file into this new folder
            for file_name in os.listdir('.'):
                if file_name.endswith('.cif'):
                    shutil.copy(file_name, f'./{i}')
                    return f'./{i}'
            print("No Cif file found")
            exit(1)
    print("Have reached maximum number of files (1000 max). Make a new folder with original cif and start again.")
    exit(1)

def auto_run(file_name="JupyterCommands.py"):
    with open(file_name, "r") as file: # Read in Initialization().main_program() commands
        lines = file.readlines()

    while len(lines) > 0:
        exec(lines[0]) # Run each command
        lines.pop(0) # If command was successful then remove from list. (Assumes will crash if unsuccessful)
        with open(file_name, "w") as file: # Update file with reduced list
            file.writelines(lines)

    if len(lines) == 0: # All commands ran successfully
        run_terminal_command(f'rm {file_name}')


class Initialization:

    def __init__(self, rkmax = 7.00, nn = 3, functional = "PBE", cutoff_energy = -6, k_points = 1000, e_range = (-9.0, 3.5), slurm_job = "run.job"):
        self.case = get_current_folder_name()
        self.rkmax = rkmax
        self.functional = functional
        self.nn = nn
        self.cutoff_energy = cutoff_energy
        self.k_points = k_points
        self.complex_calc = False
        self.e_range = e_range
        self.slurm_job = slurm_job

    # Functions interacting with WIEN2k
    def convert_cif_to_struct(self):
        for file_name in os.listdir('.'):
            if file_name.endswith('.cif'): # Will convert the first cif file it finds. User can only have 1 cif in a folder for accurate parsing
                if file_name == self.case+".cif":
                    break
                else:
                    shutil.move(file_name, self.case+".cif") # Change this to copy to preserve the system
                    break
        if file_exists(self.case+".cif"):
            run_terminal_command('x cif2struct')
            run_terminal_command('setrmt')
            run_terminal_command(f'cp {self.case}.struct_setrmt {self.case}.struct')
        else:
            print("No cif structure found")
            exit(1)

    def change_directory(self, directory):
        os.chdir(directory)
        self.case = get_current_folder_name()

    def initialize_structure(self):
        # Calculate the x nearest neighbours and accept the recommendations of the program
        run_terminal_command(f'echo {self.nn} | x nn')
        while len(open(self.case+".struct_nn").readlines()) > 1:
            run_terminal_command(f'cp {self.case}.struct_nn {self.case}.struct')
            run_terminal_command(f'echo {self.nn} | x nn')

        run_terminal_command('x sgroup')
        # TODO: Check output for warning, then prompt user to accept the space group
        symmetry_found = run_terminal_command('x symmetry')
        for line in symmetry_found.splitlines():
            if "SPACE GROUP DOES NOT CONTAIN INVERSION" in line: # Is this the best check for complex calcs?
                print("Calculation is complex")
                self.complex_calc = True
                break
        run_terminal_command(f'cp {self.case}.struct_st {self.case}.struct') # Uses found symmetry group

        run_terminal_command('echo "y" | instgen_lapw -up') # TODO: Make option to not default to spin up

        run_terminal_command(f'{{ echo {self.functional}; echo {self.cutoff_energy}; }} | x lstart')

        # Update case.in1_st to change rkmax
        default_rkmax = "7.00     10   4   ELPA" # TODO: Check if better way to change rkmax, or if the other params change
        replace_rkmax = f"{self.rkmax}     10   4   ELPA"
        replace(self.case+".in1_st", default_rkmax, replace_rkmax)

        # Update case.in1_st to increase energy range
        default_energy = "4   -9.0       1.5"
        replace_energy =  f"4   {self.e_range[0]}       {self.e_range[1]}"
        replace(self.case+".in1_st", default_energy, replace_energy)

        # Prepare input file
        run_terminal_command(f'cp {self.case}.in0_st {self.case}.in0')
        if self.complex_calc:
            run_terminal_command(f'cp {self.case}.in1_st {self.case}.in1c')
            run_terminal_command(f'cat {self.case}.in2_ls > {self.case}.in2c')
            run_terminal_command(f'cat {self.case}.in2_sy >> {self.case}.in2c')
        else:
            run_terminal_command(f'cp {self.case}.in1_st {self.case}.in1')
            run_terminal_command(f'cat {self.case}.in2_ls > {self.case}.in2')
            run_terminal_command(f'cat {self.case}.in2_sy >> {self.case}.in2')

        run_terminal_command(f'cp {self.case}.inc_st {self.case}.inc')
        run_terminal_command(f'cp {self.case}.inm_st {self.case}.inm')
        run_terminal_command(f'cp {self.case}.inq_st {self.case}.inq')

        # Generate the k-mesh
        run_terminal_command(f'{{ echo {self.k_points}; echo 0; }} | x kgen')
        run_terminal_command('x dstart')
        run_terminal_command(f'cp {self.case}.in0_std {self.case}.in0')
        print("END OF INITIALIZATION FOR CASE " + self.case)

    def initialize_spin_polarized(self):
        self.initialize_structure()
        run_terminal_command('x dstart -up')
        run_terminal_command('x dstart -dn')

    def print_info(self):
        # RKmax, Energy k-vector range stored in .in1 or .in1c
        # Gmax stored in .in2 or .in2c
        # k-mesh and # of k-points found in .klist
        return

    def main_program(self):
        self.change_directory(make_new_working_folder())
        self.convert_cif_to_struct()
        self.initialize_structure()
        self.change_directory("../")
        # Change back out of directory???

    def submit_slurm_job(self):
        #os.system('chmod +x run.job')
        #pass_arg = ["./run.job", "CoFeMn", "7"]

        #subprocess.check_call(pass_arg)
        return


#Initialization(rkmax=6.5, k_points=500).main_program()

# This will execute when the file is run.
if file_exists('JupyterCommands.py'):
    auto_run()
else:
    print("No JupyterCommands.py found")
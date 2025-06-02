# Created: 02/06/2025 (June 2, 2025)
# Last Edit: 02/06/2025

import os
import shutil
import subprocess
from tempfile import mkstemp

# TODO: Create a function that uses the .struct instead of the .cif if it exists
# TODO: Create a function that uses the built in init to see what Wien2k recommends for input parameters
# TODO: Create a function that checks for warnings and outputs them to the user
# TODO: Figure how to replace RKmax, gmax

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
    print(args) # Might not be necessary
    command = subprocess.run(args, shell=True, capture_output=True, check=True, text=True)
    print(command.stdout)

    # Error handling
    check_error_files()
    for line in command.stdout.splitlines():
        if ("ERROR IN OPENING UNIT" or "error: command") in line: # Update this line as more error combinations occur
            exit(1)
    return command.stdout

def check_error_files():
    for file_name in os.listdir('.'):
        if file_name.endswith('.error'):
            if len(open(file_name).readlines()) > 0:
                print("Error in file: " + file_name)
                for line in open(file_name).readlines():
                    print(line)
                # Should we remove the error so that it can run again next iteration? Or let user do that manually?
                exit(1)

def replace(source_file_path, pattern, substring):
    fh, target_file_path = mkstemp()
    with open(target_file_path, 'w') as target_file, open(source_file_path, 'r') as source_file:
        for line in source_file:
            target_file.write(line.replace(pattern, substring))
    run_terminal_command(f'rm {source_file_path}')
    run_terminal_command(f'mv {target_file_path} {source_file_path}')

# Functions interacting with WIEN2k
def convert_cif_to_struct():
    case = get_current_folder_name()
    for file_name in os.listdir('.'):
        if file_name.endswith('.cif'): # Will convert the first cif file it finds. User can only have 1 cif in a folder for accurate parsing
            if file_name == case+".cif":
                break
            else:
                shutil.copy(file_name, case+".cif")
                break
    if file_exists(case+".cif"):
        run_terminal_command('x cif2struct')
        run_terminal_command('setrmt')
        run_terminal_command(f'cp {case}.struct_setrmt {case}.struct')
    else:
        print("No cif structure found")
        exit(1)

def initialize_structure(nn = 3, functional = "PBE", cutoff_energy = -6, k_points = 1000, spin_polar = False, plus_u = False):
    case = get_current_folder_name()
    # Calculate the x nearest neighbours and accept the recommendations of the program
    run_terminal_command(f'echo {nn} | x nn')
    while len(open(case+".struct_nn").readlines()) > 1:
        run_terminal_command(f'cp {case}.struct_nn {case}.struct')
        run_terminal_command(f'echo {nn} | x nn')

    run_terminal_command('x sgroup')
    # TODO: Check output for warning, then prompt user to accept the space group
    symmetry_found = run_terminal_command('x symmetry')
    complex_calc = False
    for line in symmetry_found.splitlines():
        if "SPACE GROUP DOES NOT CONTAIN INVERSION" in line: # Is this the best check for complex calcs?
            print("Calculation is complex")
            complex_calc = True
            break
    run_terminal_command(f'cp {case}.struct_st {case}.struct') # Uses found symmetry group

    run_terminal_command('echo "y" | instgen_lapw -up') # TODO: Make option to not default to spin up

    run_terminal_command(f'{{ echo {functional}; echo {cutoff_energy}; }} | x lstart')

    # Update case.in1_st to increase energy range
    original_energy = "4   -9.0       1.5"
    replace_energy =  "4   -9.0       3.5"
    replace(case+".in1_st", original_energy, replace_energy)

    # Prepare input file
    run_terminal_command(f'cp {case}.in0_st {case}.in0')
    if complex_calc:
        run_terminal_command(f'cp {case}.in1_st {case}.in1c')
        run_terminal_command(f'cat {case}.in2_ls > {case}.in2c')
        run_terminal_command(f'cat {case}.in2_sy >> {case}.in2c')
    else:
        run_terminal_command(f'cp {case}.in1_st {case}.in1')
        run_terminal_command(f'cat {case}.in2_ls > {case}.in2')
        run_terminal_command(f'cat {case}.in2_sy >> {case}.in2')

    run_terminal_command(f'cp {case}.inc_st {case}.inc')
    run_terminal_command(f'cp {case}.inm_st {case}.inm')
    run_terminal_command(f'cp {case}.inq_st {case}.inq')

    # Generate the k-mesh
    run_terminal_command(f'{{ echo {k_points}; echo 0; }} | x kgen')
    run_terminal_command('x dstart')
    run_terminal_command(f'cp {case}.inc_st {case}.inc')

def get_info():
    # RKmax, Energy k-vector range stored in .in1 or .in1c
    # Gmax stored in .in2 or .in2c
    # k-mesh and # of k-points found in .klist
    case = get_current_folder_name()

def main_program():
    convert_cif_to_struct()
    initialize_structure()

main_program()
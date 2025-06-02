# Created: June 2, 2025
# Last Edit: 02/06/2025

import os
import shutil


# Check if a .struct file exists. If yes, then use it
# If no, then convert from the cif file.

# The cif file must have the same name as the folder that it is put into.
#
# x cif2struct
# setrmt
# cp case.struct_setrmt case.struct

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

def convert_cif_to_struct():
    case = get_current_folder_name()
    for file_name in os.listdir('.'):
        if file_name.endswith('.cif'): # Will convert the first cif file it finds. User can only have 1 cif in a folder for accurate parsing
            if file_name == case+".cif":
                break
            else:
                shutil.copy(file_name, case+".cif")
                break
    if file_exists(case+".cif"): # Need the case to search if a .struct file exsits still
        os.system('x cif2struct')
        os.system('setrmt')
        os.system(f'cp {case}.struct_setrmt {case}.struct')
    else:
        print("No cif structure found")

convert_cif_to_struct()
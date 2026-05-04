# Created: 28/04/2026 (Apr 28, 2025)

import re
from pathlib import Path
import shutil
import json

# The purpose of this file is to download and compile all folders within a folder with a given initial start
# cif file name. Then put all the info into a single file that can be downloaded locally.

# Need DOS, XSPEC,
required_info = {"case_name":None, "rkmax":None, "num_kpoints":None, "emin":None, "emax":None, "energy_state_seperation":None,
                 "fermi":None,"bandgap":None, "gmin":None,"gmax":None,
                 "lattice_constants":None, "num_atom_unitcell":None,
                 "fermi_convergence":[],"energy_convergence":[],"gap_convergence":[],"dist_convergence":[],"converged":False}
# Get the convergence using the analyis function in wien2k.

def gather_info(cif_file):
    Path("DownloadFolder").mkdir(parents=True, exist_ok=True)
    download_folder = Path("DownloadFolder")
    file_storage = []
    foldername = Path(cif_file).stem
    for folder in Path("./").glob(f"{foldername}*"): # This goes through all files that have the cif_file initial in the name
        if folder.is_dir(): # Just ensures not trying to enter a file
            parameters = {"case_name": str(folder)} # Create a dictionary entry for every new folder. Put in list later
            for file in Path(folder).iterdir(): # Goes through all files in the folder. This is the main calculation folder with in1 etc.
                if file.is_file():
                    match file.suffix:
                        case ".in1" | ".in1c":
                            with open(file, 'r') as f:
                                f_lines = f.readlines()
                                parameters["rkmax"] = float(f_lines[1].split()[0])  # Get the second line, first value, which is rkmax
                                parameters["emin"] = float(f_lines[-1].split()[3])  # Last line, second value
                                parameters["emax"] = float(f_lines[-1].split()[4])  # Last line, third value

                            print(file)
                        case ".scf1":
                            print(file)
                        case ".scf2":
                            with open(file, 'r') as f:
                                f_lines = f.readlines()
                                for line in f_lines:
                                    if re.search(":GAP \(global\)", line):  # TODO: Spin polarized has GAP (this spin)
                                        parameters["gap_ry"] = float(line.split()[3])
                                        parameters["gap_ev"] = float(line.split()[6])
                                    elif re.search(":FER", line):
                                        parameters["fermi"] = line.split()[9]
                                    elif re.search("Energy to separate low and high energystates", line):
                                        parameters["low_high_sep"] = line.split()[7]
                            print(file)
                        case ".dayfile":
                            with open(file, 'r') as f:
                                f_lines = f.readlines()
                                for line in f_lines:
                                    if re.search("ec cc fc and str_conv 1 1 1 1",line):
                                        parameters["converged"] = True
                            print(file)
                elif file.is_dir(): # If there is a folder inside the main directory it is the dos_export or xspec_export
                    for subfile in Path(file).iterdir(): # Go through all files in this subdirectory
                        if subfile.is_file():
                            match subfile.suffix:
                                case ".txspec":
                                    shutil.copy2(subfile, download_folder)
                                    print(subfile)
                                case ".dos":
                                    shutil.copy2(subfile, download_folder)
                                    print(subfile)
            file_storage.append(parameters)
    file_storage.sort(key=lambda x: x["case_name"]) # Sort the list of dictionaries based on the case_name
    print(file_storage)
    with open(f"{download_folder}/parameter_info.json", "w") as f:
        json.dump(file_storage, f, indent=4)
    # row name is the tag, and colmun name is the case_name. then fill in the rest.
cif = "TiCv2.struct"
gather_info(cif)

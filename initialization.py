# Created: 02/06/2025 (June 2, 2025)

import os
import shutil
import subprocess
from pathlib import Path
from tempfile import mkstemp

# TODO: Create a function that uses the built in init to see what WIEN2k recommends for input parameters
# TODO: Create a function that checks for warnings and outputs them to the user
# TODO: Figure how to replace gmax
# TODO: Create a logbook that keeps track of what commands were sent, and which file name they were sent to.
    # With logbook we should write to the file "CASE #: Failed", then overwrite it afterwards if it succeeded
# TODO: Make a try and catch case where we try a bunch of different encodings then specify that explicitly.
    # Right now we have commented out two aspects of the code that read the stdout to determine (such as complex)
# TODO: Give the user the option to upload their own job file instead of our own.
# TODO: Finish tasks
# TODO: Make the job submission SBATCH stuff automatic
# TODO: Create function that finds relationship based on number of cpus and the memory required based on in-eq sites
    # On top of that, automatically find the ntasks-required for a job script.
# TODO: Make a new job submission with only a single core that does the DOS and the Xtetra
# TODO: Make error handling better, so that user can actually see error messages from the terminal.
# TODO: Think about cluster configuration. bash type shell, planc defaults to...
# TODO: MAke sure k-point convergence test uses a specific precision level

###################################################################################################################
"""
Updated Jan 7, 2026
Function interactions to show which main functions make use of which sub-functions

main_program()
    - change_directory()
        * get_current_folder_name()
    - convert_cif_to_struct()
        * run_terminal_command()
            $ check_error_files()
        * file_exists()
        * find_encoding()   # Only used if error
    - initialize_structure_auto()
        * run_terminal_command()
            $ check_error_files()
        * replace()
    - create_job_file()
        * job_file_script_no_header()
        * factors()
    - create_xspec_file()
        * xspec_file_script_no_header()
    - create_dos_file()
        * get_atomic_species()
            $ run_terminal_command()
                & check_error_files()
        * run_terminal_command()
            $ check_error_files()
    - submit_slurm_job()
        * run_terminal_command()
            $ check_error_files()
"""
###################################################################################################################
# Main Function

class Initialization:
    PeriodicTable = ['H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne', 'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar', 'K', 'Ca',
         'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y',
         'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La',
         'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'W', 'Re',
         'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th', 'Pa', 'U', 'Np',
         'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm', 'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds', 'Rg',
         'Cn', 'Nh', 'Fl', 'Mc', 'Lv', 'Ts', 'Og']
    #edge_arr = ("1s" "2s" "2p" "3s" "3p" "3d" "4s" "4p" "4d" "4f")
    #n_arr = (1 2 2 3 3 3 4 4 4 4)
    #l_arr = (0 0 1 0 1 2 0 1 2 3)

    def __init__(self, user_input): # User input should be a dictionary with keys matching some or all of those provided below.

        # Flags will be True/False booleans, Options will be None/Value/True/False arguments

        # -h = help, -m = manual steps, -b = batch, -sp = spin polarized, -nodstart = new input for converged calcs,
        # -nokshift = unshifted kmesh, -nometal = reduce k-mesh, -hdlo = set HDLOs in lstart, -nohdlo = do not set HDLOs in lstart
        self.init_lapw_flags = {"-h":False, "-m":False, "-b":True, "-sp":False, "-nodstart":False, "-nokshift":False,
                                "-nometal":False, "-hdlo":False, "-nohdlo":False}

        # -f = filehead, -prec = precision, -red = reduced RMT by %, -vxc = functional (PBE), -fftfac = Enhancement factor of fft
        # -fft = sets grid to XYZ grid, -autofft = sets grid to -1 -1 -1, -ecut = energy separation (-6Ry), -rkmax = RKMAX
        # -lmax = LMAX (10), -lvns = LVNS_max, -gmax = GMAX, -fermit = use TEMP with smearing, fermits = use TEMPS with smearing
        # -numk = number of k-points in full BZ, -s = start with program in manual, -e = exit after program in manual
        self.init_lapw_options = {"-f":None, "-prec":2, "-red":None, "-vxc":None, "-fftfac":None, "-fft":None, "-autofft":False,
                                  "-ecut":None, "-rkmax":None, "-lmax":None, "-lvns":None, "-gmax":None, "-fermit":None,
                                  "-fermits":None, "-numk":None, "-s":None, "-e":None}

        # See slurm website for more info on these parameters
        # https://slurm.schedmd.com/sbatch.html
        self.slurm_options = {"--job-name":None, "--mail-user":None, "--mail_type":None, "--account":None, "--partition":None,
                              "--nodes":None, "--ntasks-per-node":None, "--mem":None, "--time":None,
                              "max-ntasks-per-node":32, "max-mem-per-cpu":3.9, "misc":[]}

        self.WIEN2k_inputs = {"cif_file":"", "supercell": [], "corehole_elements": [], "e_range": (-10.0, 4), "xspec_elements": {}}


        # Update the default arguments with the incoming user set values
        print(user_input)
        self.init_lapw_flags.update((i, user_input[i]) for i in self.init_lapw_flags.keys() & user_input.keys())
        self.init_lapw_options.update((i, user_input[i]) for i in self.init_lapw_options.keys() & user_input.keys())
        self.slurm_options.update((i, user_input[i]) for i in self.slurm_options.keys() & user_input.keys())
        self.WIEN2k_inputs.update((i, user_input[i]) for i in self.WIEN2k_inputs.keys() & user_input.keys())

        # TODO: Convert these parameters below into a dictionary and safely remove their references from program.
        # For initialization
        encoding_type = None
        errors = None
        # For initialization
        sbatch = None
        scf_type = "Basic"
        # Will need to check is -sp flag is set. Add a function for mbj, spin polarized, plus U, and corehole
        xspec = "True"
        resubmit = "False"
        scratch = "$SCRATCH"
        xspec_config = None

        self.number_of_atoms = None
        self.k_points = None
        if xspec_config is None:
            xspec_config = []
        self.case = get_current_folder_name()
        self.complex_calc = False
        self.encoding_type = encoding_type
        self.errors = errors
        self.sbatch = sbatch
        self.scf_type = scf_type
        self.xspec = xspec # TODO: Make this a check if parameter exists, default to False then
        self.resubmit = resubmit
        self.scratch = scratch
        self.xspec_config = xspec_config
        self.gmax = None

        # TODO: Add more info about what each value is, and how it can be changed
        # TODO: Put all of the final self parameters into a text file to output to user.

    # Function that organizes the flow of the program
    def main_program(self):
        """
        This organizes the flow of the program and is the only thing that is actually run.
        Called from JupyterCommands.py, which will delete itself after running through all calculations.

        Returns
        -------
        Will initialize the structure and run through init_lapw, etc.
        Outputs xspec_export.sh, run.job, dos_export.sh.
        """
        self.change_directory(make_new_working_folder(self.WIEN2k_inputs["cif_file"])) # Change into working directory (Case_000)
        self.convert_cif_to_struct()        # Uses WIEN2k to convert input cif file to a .struct
        self.initialize_structure_auto()    # Uses the batch command with WIEN2k v23 to auto generate inputs
        if self.WIEN2k_inputs["corehole_elements"] != [] and self.WIEN2k_inputs["supercell"] != []:
            self.initialize_structure_auto()
        self.create_job_file()              # Creates a job file that is later run by the program to submit to slurm
        self.create_xspec_file()            # Creates xspec file that is used by run.job to calculate XAS/XES
        self.create_dos_file()              # Crease a dos calculation file that is used by run.job to calculate Density of States
        self.submit_slurm_job()            # This will submit run.job to slurm scheduler TODO: Turn this back on
        self.change_directory("../")        # Return out of working directory. (Maybe unnecessary based on how classes work)

    # Functions interacting with WIEN2k
    def convert_cif_to_struct(self):
        """
        This checks if user gave a .struct or .cif in initialization.
        If .struct then nothing needs to be done.
        If .cif then uses WIEN2k built in command to convert .cif to .struct

        Returns
        -------
        Outputs a .struct file for later use in the program
        """
        # If the user decides to upload a .struct. Assume they have done setrmt, or chosen accurate rmt values
        if self.WIEN2k_inputs["cif_file"].endswith('.struct'):
            shutil.move(self.WIEN2k_inputs["cif_file"], self.case + ".struct") # Update name of provided cif file to Case_000.struct
            return

        # If the user decides to upload a .cif file.
        for file_name in os.listdir('.'): # Goes through all files in the directory
            if file_name.endswith('.cif'): # Will convert the first cif file it finds. User can only have 1 cif in a folder for accurate parsing
                if file_name == self.case+".cif": # If properly named cif file is found, break
                    break
                else:
                    shutil.move(file_name, self.case+".cif") # Update name of provided cif file to Case_000.cif
                    break

        # Now that cif file is in a properly named scheme
        if file_exists(self.case+".cif"):
            # Since this is first command in main_program() it should always run first.
            # Thus, it will be here that we discover any encoding issues, or issues with WIEN2k installation
            try: # TODO: Make this a better check of encoding??
                self.run_terminal_command('x cif2struct')
            except:
                print("Error converting cif: Either WIEN2k command could not be found, or encoding error.")
                print("If encoding error please run find_encoding() in the jupyter notebook.")
                find_encoding('x cif2struct') # Writes bytes to a file that can be accessed in notebook and encoding found
                # exit(1)
            self.run_terminal_command('setrmt') # This sets the rmt values before saving as new struct. Might be irrelevant with init_lapw
            self.run_terminal_command(f'cp {self.case}.struct_setrmt {self.case}.struct') # Copy rmt values into .struct
        else:
            print("No cif structure found")
            exit(1)

    def initialize_structure_auto(self):
        """
        Performs init_lapw to generate the structure inputs to be ready for job submission.
        Makes use of the build in command to automatically generate rkmax, kpoints, etc. unless these are specifically specified.

        Returns
        -------
        Generates list of files for WIEN2k
        """
        # TODO: -h and -m break the thing. idk why.
        initialization_command = 'init_lapw'
        # Check if they requested the help flag
        if self.init_lapw_flags["-h"] is True:
            initialization_command += ' -h'
            initialization = self.run_terminal_command(f'{initialization_command}')
            exit()
        # Check if they opted to do it manually
        elif self.init_lapw_flags["-m"] is True:
            initialization_command += ' -m'
            initialization = self.run_terminal_command(f'{initialization_command}')
        # Go through the batch submission with all selected options
        else:
            # Add the flags (spin polarized etc.)
            for key, value in self.init_lapw_flags.items():
                if value is True:
                    initialization_command += ' ' + key
            # Add the options and the values (rkmax etc.)
            for key, value in self.init_lapw_options.items():
                if value not in (None, False):
                    if key == '-autofft':
                        initialization_command += ' ' + key
                    elif key == '-fft':
                        initialization_command += ' ' + key + ' ' + str(value[0]) + ' ' + str(value[1]) + ' ' + str(value[2])
                    else:
                        initialization_command += ' ' + key + ' ' + str(value)
            initialization = self.run_terminal_command(f'{initialization_command}')
        self.get_parameters(initialization)
        return initialization

    def initialize_structure_core_hole(self):


        return

    def prepare_input_files(self):
        # This is the prepare input files button from Wien2k
        shutil.copy(self.case+".in0_st", self.case+".in0") # Copy .in0 file
        in2_files = [self.case+".in2_ls", self.case+".in2_sy"]
        if self.complex_calc: # files end with a c to denote complex
            shutil.copy(self.case + ".in1_st", self.case + ".in1c")
            # Concatinate the two in2 files
            with open(self.case + ".in2c", 'wb') as dst:
                for file in in2_files:
                    with open(file, 'rb') as src:
                        shutil.copyfileobj(src, dst)

        else: # These files do not have the c in the name
            shutil.copy(self.case + ".in1_st", self.case + ".in1")
            # Concatinate the two in2 files
            with open(self.case + ".in2", 'wb') as dst:
                for file in in2_files:
                    with open(file, 'rb') as src:
                        shutil.copyfileobj(src, dst)

        shutil.copy(self.case + ".inc_st", self.case + ".inc")
        shutil.copy(self.case + ".inm_st", self.case + ".inm")
        shutil.copy(self.case + ".inq_st", self.case + ".inq")

    def change_energy(self):
        # TODO: Run dstart after changing this file?
        # Update case.in1_st to increase energy range
        # TODO: Monitor if this has a significant impact on computation time
            # If yes then do it after convergence and rerun scf cycle again with increased energy range. lapw1 and lapw2 -qtl
        default_energy = "4   -9.0       1.5"
        replace_energy = f"4   {self.WIEN2k_inputs['e_range'][0]}       {self.WIEN2k_inputs['e_range'][1]}"
        try:
            replace(self.case + ".in1", default_energy, replace_energy)
        except:
            replace(self.case + ".in1c", default_energy, replace_energy)

    def get_parameters(self, initialization):
        # These parameters should only be used for the initialization and creating of structure. These are not saved afterwards
        # New final parameters are collected by the download info to ensure that there is no external change errors
        # Get input parameters provided from the terminal output of the init_lapw command
        # TODO: Check if stopping print to notebook will impact this search
        # TODO: Turn this into a dictionary
        for line in initialization.splitlines():
            if "SPACE GROUP DOES NOT CONTAIN INVERSION" in line: # Is this the best check for complex calcs?
                self.complex_calc = True
            elif "set RKmax" in line:
                self.rkmax = line.split()[-1]
            elif "set GMAX" in line:
                self.gmax = line.split()[-1]
            elif "k-points generated" in line:
                self.k_points = line.split()[0] # This is k-mesh generated lattice
            elif "Atoms found:" in line:
                self.number_of_atoms = line.split()[0]

    ###################################################################################################################
    # Creating Shell Script Files

    def get_atomic_species(self):
        """
        Gets all atomic elements and puts them in a dictionary. {'Element':[Site1, Site2, etc.]}

        Returns
        -------
        A dictionary containing all the atomic species and their position in WIEN2k
        """
        # Search through terminal output and get the first two characters from lines with 'NPT=' and store in file
        self.run_terminal_command(f'grep "NPT=" {self.case}.struct | cut -c 1-2 > {self.case}.atomic_species')
        # Create empty dictionary and counter so we know which WIEN2k site in the list we are on
        atomic_species = {}
        counter = 1
        with open(self.case + ".atomic_species", "r") as file:
            for line in file:
                # For each site, if element doesn't exist then make new list in dictionary, otherwise append current site position
                atomic_species.setdefault(line.split()[0],[]).append(counter)
                counter += 1
        return atomic_species

    def create_dos_file(self):
        """
        Creates a .sh script that will be run to generate the density of states after job submission completes successfully.

        Returns
        -------
        A dos_export.sh file
        """
        #TODO: Turn off broadening on the dos
        atomic_species = self.get_atomic_species()
        print("GENERATING DOS INPUTS")
        print(atomic_species)
        dos_orbitals = "tot,s,p,d,f"
        dos_file_name = "DOS_export"
        self.run_terminal_command(f'mkdir -p {dos_file_name}')
        dos_inputs = f"configure_int_lapw -b total end\nx tetra\nmv {self.case}.dos1 {dos_file_name}/Total.dos\n"
        for key, value in atomic_species.items():
            print(f"Key: {key}, Value: {value}")
            for i in range(len(value)):
                dos_inputs += f"configure_int_lapw -b {value[i]} {dos_orbitals} end\nx tetra\nmv {self.case}.dos1 {dos_file_name}/{self.case}_Atom{value[i]}.dos\n"
        with open("dos_export.sh", 'w') as f:
            f.write("#!/bin/bash\nset -e\n")
            f.write(dos_inputs)
            os.system('chmod +x dos_export.sh')

            #TODO: Make sure the Emin and Emax are a specified value in the nDOS calc .int file.
            # -20 to 20

    def create_job_file(self):
        """
        Creates a job file that will be submitted to slurm. Needs user parameters to run properly.
        Contains options to perform auto-resubmission, as well as different scf types.
        Runs both the dos.sh and xspec.sh scripts after job is successful.

        Returns
        -------
        A run.job file containing slurm information.
        """
        # TODO: Find way to let them use entire job file if they so desire
        # TODO: Have argument that lets user use SBATCH only their commands

        # First we need to determine the allocation requirements
        if self.slurm_options["--ntasks-per-node"] and self.slurm_options["--nodes"] is not None:
            pass
        else:
            # Equation to roughly determine how many tasks a program should have TODO: Update equation as necessary
            # Based on the number of atoms and the rkmax value of the system.
            #ntasks_goal = int(1.2 ** float(self.rkmax) * int(self.number_of_atoms) ** 0.45 - 1.5)
            ntasks_goal = int((1.2 ** float(self.rkmax)) * (int(self.number_of_atoms) ** 0.35) * (int(self.k_points) ** 0.20) - 15)
            ntasks = 1
            self.slurm_options["--nodes"] = 1
            print("original ntasks to calculate: " + str(ntasks_goal))
            # Figure out how many nodes are required to get the goal below the threshold of max cpu per node
            # Divides and then rounds up the goal until it is lower than max-ntasks-per-node
            ntasks_goal_per_node = int(-(-ntasks_goal // self.slurm_options["--nodes"]))
            while ntasks_goal_per_node >= int(self.slurm_options["max-ntasks-per-node"]):
                self.slurm_options["--nodes"] += 1
                ntasks_goal_per_node = int(-(-ntasks_goal // self.slurm_options["--nodes"]))
                #print(-(-ntasks_goal // self.slurm_options["--nodes"]))

            print("We want roughly this many nodes " + str(self.slurm_options["--nodes"]))
            print("And our goal per node is " + str(ntasks_goal_per_node))
            factored_k_points = sorted(factors(int(self.k_points)))
            print("factors of k-points: " + str(factored_k_points))

            # Find the number of requested nodes that is closest to a divisible number of k-points
            node_temp = 1
            for i in range(len(factored_k_points) - 1):
                if factored_k_points[i] <= self.slurm_options["--nodes"]:
                    if abs(factored_k_points[i] - self.slurm_options["--nodes"]) < abs(factored_k_points[i + 1] - self.slurm_options["--nodes"]):
                        node_temp = factored_k_points[i]
                    else:
                        node_temp = factored_k_points[i + 1]
            self.slurm_options["--nodes"] = node_temp
            print("So we should have this many nodes " + str(self.slurm_options["--nodes"]))

            # Update our goal of ntasks-per-node based oun our newly found nodes
            ntasks_goal_per_node = int(-(-ntasks_goal // self.slurm_options["--nodes"]))
            print("And our updated goal per node is " + str(ntasks_goal_per_node))

            # Find the new number of k-points per node and the factors
            if int(self.k_points) % int(self.slurm_options["--nodes"]) != 0:
                print("The selection algorithm messed up and the number of tasks is not perfect.")
            factored_k_points = sorted(factors(int(self.k_points) // int(self.slurm_options["--nodes"])))
            print("New factors of k-points: " + str(factored_k_points))

            # Find the number of tasks that matches closest with our goal, but still a factor of k-points
            for i in range(len(factored_k_points) - 1):
                if factored_k_points[i] <= ntasks_goal_per_node and factored_k_points[i + 1] <= int(self.slurm_options["max-ntasks-per-node"]):
                    if abs(factored_k_points[i] - ntasks_goal_per_node) < abs(factored_k_points[i + 1] - ntasks_goal_per_node):
                        ntasks = factored_k_points[i]
                    else:
                        ntasks = factored_k_points[i + 1]
            self.slurm_options["--ntasks-per-node"] = ntasks
            print("And should have this many ntasks per node " + str(self.slurm_options["--ntasks-per-node"]))

            # Check if we are requesting more nodes that tasks-per-node. Means we have it backwards. (edge cases of limited k-point factors)
            if int(self.slurm_options["--ntasks-per-node"]) < int(self.slurm_options["--nodes"]) <= int(self.slurm_options["max-ntasks-per-node"]):
                self.slurm_options["--ntasks-per-node"], self.slurm_options["--nodes"] = self.slurm_options["--nodes"], self.slurm_options["--ntasks-per-node"]

            print("Our final values are " + str(self.slurm_options["--nodes"]) + " nodes and " + str(self.slurm_options["--ntasks-per-node"]) + " tasks")


        # Now to set the memory and the time components
        if self.slurm_options["--mem"] is None:
            self.slurm_options["--mem"] = str(round(float(self.slurm_options["max-mem-per-cpu"]) * int(self.slurm_options["--ntasks-per-node"]))) + "G"

        if self.slurm_options["--time"] is None:
            self.slurm_options["--time"] = "24:00:00"

        if self.slurm_options["--job-name"] is None:
            self.slurm_options["--job-name"] = self.case

        # Write the parameters to the run.job program
        with open("run.job", 'w') as job:
            job.write(f"#!/bin/bash\n") # Header
            job.write(f'#SBATCH --get-user-env\n')
            for key, value in self.slurm_options.items():
                if value is not None: # User input a value here
                    if key == "misc":
                        if isinstance(value, list):
                            for i in range(len(value)):
                                job.write(f"#SBATCH {value[i]}\n")
                        else:
                            print("WARNING: misc parameter is formatted incorrectly. Ensure it is a list")
                    elif key == "max-ntasks-per-node" or key == "max-mem-per-cpu":
                        pass
                    else:
                        job.write(f"#SBATCH {key}={value}\n")
                else: # value is none, so we need to choose it ourselves
                    print("No value given for " + key)

            #TODO: Update the WIEN2k commands
            job.write(f'scf_type="{self.scf_type}"\n')
            job.write(f'xspec="{self.xspec}"\n')
            job.write(f'resubmit="{self.resubmit}"\n')
            job.write(f'export SCRATCH {self.scratch}\n')
            job.write(job_file_script_no_header())

        with open("run.job", "r") as job:
            for i in range(20):
                print(job.readline())

    def create_xspec_file(self):
        """
        Creates a .sh script that will be run to generate the x-ray spectra after job submission completes successfully.

        Returns
        -------
        An xspec_export.sh file.
        """
        # TODO: Add some more checks for valid inputs
        # TODO: Make this automated? Make lookup table and calculate the orbitals based on what we want.
        with open("xspec_export.sh", 'w') as f:
            f.write(f"#!/bin/bash\n")  # Header
            f.write(f"set -e\n")
            f.write(f'case_name="{self.case}"\n')
            # Start creating the atom and orbitals required
            # Issue is that it is impossible to ask for two orbitals of same element at same time
            #{"O":"1s","O":"2p"} will default the value to 2p instead of two instances
            atoms = "("
            orbitals = "("
            atomic_species = self.get_atomic_species()
            for key, value in self.WIEN2k_inputs["xspec_elements"].items():
                if key not in atomic_species:
                    print(f"WARNING: {key} not in {atomic_species}")
                    pass
                else:
                    for i in range(len(atomic_species[key])):
                        atoms += str(atomic_species[key][i]) + " "
                        orbitals += '"' + str(self.WIEN2k_inputs["xspec_elements"][key]) + '"' + " "
            atoms += ")"
            orbitals += ")"
            f.write(f'atom_list={atoms}\n')
            f.write(f'orbital_list={orbitals}\n')
            if self.scf_type == "PlusU" or self.scf_type == "SpinPolar":
                f.write(f'spin_polarized="True"\n')
            else:
                f.write(f'spin_polarized="False"\n')
            f.write(f'ABS_FILE_TEMPLATE="{self.case}_ATOM!atom!_ABS"\n')
            f.write(f'EMIS_FILE_TEMPLATE="{self.case}_ATOM!atom!_EMIS"\n')
            f.write(f'fermi_file="{self.case}_fermi_energy"')
            f.write(xspec_file_script_no_header())
        os.system('chmod +x xspec_export.sh')
        return

    ###################################################################################################################
    # Helper Functions
    def change_directory(self, directory):
        """
        Changes current working directory to given directory.

        Parameters
        ----------
        directory: string of directory that we want to go to

        Returns
        -------
        Changes self.case to the current folder name
        """
        os.chdir(directory)
        self.case = get_current_folder_name()

    def submit_slurm_job(self):
        """
        Just a command that submits run.job to slurm.
        """
        #self.run_terminal_command(f'sbatch {self.case}.job')
        self.run_terminal_command(f'sbatch run.job')
        return

    def run_terminal_command(self, args, silent=False):
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
        if self.encoding_type is not None:
            # shell = True allows to pass commands as single string and run it similar to a regular terminal command. Can cause security issues
            # capture_output lets us use stdout and stderr and give it to user in jupyter notebook
            # check is an error handling, and raises CalledProcessError on fail
            # text allows us to read the output in strings rather than bytes
            # encoding lets us specify the encoding type rather than it choosing one for us.
            # errors is here for encoding??? not entirely sure to be honest
            command = subprocess.run(args, shell=True, capture_output=True, check=True, text=True, encoding=self.encoding_type, errors=self.errors)
        else:
            command = subprocess.run(args, shell=True, capture_output=True, check=True, text=True, errors=self.errors)
        if not silent:
            print(command.stdout)  # Print output results for user

        # Error handling
        check_error_files()  # Check if case.error files exist, and if they do then exit(1)
        for line in command.stdout.splitlines(): # Reads stdout and check if any errors occurred
            if ("ERROR IN OPENING UNIT" or "error: command") in line: # Update this line as more error combinations occur
                print(command.stderr)
                print(command.stdout)
                exit(1)
        return command.stdout


###################################################################################################################
# Global Helper Functions

# Source - https://stackoverflow.com/questions/6800193/what-is-the-most-efficient-way-of-finding-all-the-factors-of-a-number-in-python
# Posted by Julian
def factors(n):
    """
    Code stolen from stackoverflow. Efficient way to find a set of all factors of an integer

    Parameters
    ----------
    n: integer value that we want factors of

    Returns
    -------
    A set of integers containing the factors of n
    """
    return set(factor for i in range(1, int(n**0.5) + 1) if n % i == 0 for factor in (i, n//i))

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

def make_new_working_folder(cif_file=None):
    """
    Creates a new folder, with a naming scheme of case_000 to case_999, incrementing based on previously existing files.

    Parameters
    ----------
    cif_file: name of the file to be created/appended to.

    Returns
    -------
    A new folder properly named
    """
    # If user does not specify name, then it will pick the first cif file that it can find.
    if cif_file is None:
        for file_name in os.listdir('.'):
            if file_name.endswith('.cif'):
                cif_file = file_name
                print("Warning: Using found cif file: " + cif_file)
                break
        if cif_file is None:
            print("No Cif file found")
            exit(1)

    cif_file_no_extension = Path(cif_file).stem # Remove the extension

    # Make the new folder with numerical name
    for i in range(0, 1000):
        if os.path.exists(f'./{cif_file_no_extension}_00{i}'):
            pass
        elif os.path.exists(f'./{cif_file_no_extension}_0{i}'):
            pass
        elif os.path.exists(f'./{cif_file_no_extension}_{i}'):
            pass
        else:
            if i < 10:
                folder_name = cif_file_no_extension + '_00' + str(i)
            elif i < 100:
                folder_name = cif_file_no_extension + '_0' + str(i)
            else:
                folder_name = cif_file_no_extension + '_' + str(i)
            os.mkdir(folder_name)
            shutil.copy(cif_file, folder_name) # Can also likely be a struct file?
            return folder_name
    print("Have reached maximum number of files (1000 max). Make a new folder with original cif and start again.")
    exit(1)

def replace(source_file_path, pattern, substring):
    """
    Searches through a file and replaces the pattern with the desired substring.

    Parameters
    ----------
    source_file_path: File to be searched through
    pattern: Original pattern to be replaced
    substring: New string that will be used to replace pattern

    Returns
    -------
    Changes a pattern of text and overwrites original file
    """
    fh, target_file_path = mkstemp()
    with open(target_file_path, 'w') as target_file, open(source_file_path, 'r') as source_file:
        for line in source_file:
            target_file.write(line.replace(pattern, substring))
    os.remove(source_file_path)
    shutil.move(target_file_path, source_file_path) # Check that this still functions properly. Else target/source switch

def find_encoding(args):
    """
    Used to find the encoding of the output to terminal from a WIEN2k command.
    This only generates a text file that can be read locally to determine the encoding. (jupyter_interface)
    If encoding is not specified, sometimes causes issues with viewing on jupyter notebook, so needs to be explicitly
    specified on occassion.

    Parameters
    ----------
    args: Command line arguments to be run

    Returns
    -------
    Outputs two files that contain a single byte of data. These will be read locally later.
    """
    command = subprocess.run(args, shell=True, capture_output=True, check=True, text=False)
    with open('../encoding_stdout', "wb") as f:
        f.write(command.stdout)
    with open('../encoding_stderr', "wb") as f:
        f.write(command.stderr)
    return


###################################################################################################################
# Storage for shell scripts


def job_file_script_no_header():
    # Holds the information of the job script. Reduces number of files that need to be sent to server.
    # Last updated Jan 6, 2026
    # TODO: Give ability to change the convergence criteria
    job = """
# Gets the hosts and puts it into the .machines file.
srun hostname -s  >slurm.hosts
rm -f .machines
proclist=$(< slurm.hosts sort)
echo -e "$proclist" > tempproclist
while IFS= read -r line; do
  echo "1:$line" >>.machines
done < tempproclist
{ echo "granularity:1"; echo "extrafine:1"; echo ' '; }  >>.machines

##Create .processes (idk why this is here tbh)
x lapw1 -p -d >&/dev/null
#lapw1para_lapw lapw1.def


# Bash Functions
check_convergence () {
  converged=$(grep "ec cc fc" ./*.dayfile | tail -n 1)
  if [[ "$converged" == "ec cc fc and str_conv 1 1 1 1" ]]; then # This might change if you change the run_lapw??
    converged="True"
  else
    converged="False"
  fi
}

dos_calculation () {
  chmod +x dos_export.sh
  ./dos_export.sh
}

basic_xspec () {
  # Necessary to do x xspec
  # x lapw1 -p
  x lapw2 -p -qtl
  # Calculate xspec files
  chmod +x xspec_export.sh
  ./xspec_export.sh
  # Could also be bash xspec_export.sh
}

spinpolar_xspec () {
  # Necessary to do xspec (lapw1 can be added if you change kmesh or energy range)
  # x lapw1 -p -up
  x lapw2 -p -qtl -up

  # x lapw1 -p -dn
  x lapw2 -p -qtl -dn

  # Calculate the xspec files.
  chmod +x xspec_export.sh
  ./xspec_export.sh
}

basic_SCF () {
  run_lapw  -NI -p -ec 0.00001 -cc 0.01 -i 200
}

plusU_SCF () {
  runsp_lapw -orb -NI -p -ec 0.00001 -cc 0.01 -i 200
}

spinpolar_SCF() {
  runsp_lapw -NI -p -ec 0.00001 -cc 0.01 -i 200
}

forceMinimization_SCF() {
  # run_lapw -NI -p -fc 1 -i 600
  run_lapw -min -NI -p -fc 0.5 -ec 0.0001 -cc 0.01 -i 600
}

choose_SCF_type() {
  if [[ "$scf_type" == "Basic" ]]; then
    basic_SCF
  elif [[ "$scf_type" == "PlusU" ]]; then
    plusU_SCF
  elif [[ "$scf_type" == "SpinPolar" ]]; then
    spinpolar_SCF
  elif [[ "$scf_type" == "ForceMin" ]]; then
    forceMinimization_SCF
  fi
}

choose_xspec_type() {
  if [[ "$scf_type" == "Basic" ]]; then
    basic_xspec
  elif [[ "$scf_type" == "PlusU" ]]; then
    spinpolar_xspec
  elif [[ "$scf_type" == "SpinPolar" ]]; then
    spinpolar_xspec
  elif [[ "$scf_type" == "ForceMin" ]]; then
    basic_xspec # Does this actually work? Or do we have to redo an SCF cycle again.
  fi
}

run_SCF() {
  choose_SCF_type # Run an SCF cycle until it crashes
  for i in $(seq 1 2); do # If it is not converged then attempt to run it again
    check_convergence
    if [[ "$converged" == "True" ]]; then
      break
    else
      choose_SCF_type
    fi
  done

  # Checks if it has reached convergence, then calculates the xspec files (see other script)
  check_convergence
  if [[ "$converged" == "True" && "$xspec" == "True" ]]; then
    choose_xspec_type
    dos_calculation
  fi

  if [[ "$converged" != "True" && "$resubmit" == "True" ]]; then
    sbatch run.job # If it has still not converged, then resubmit the job
  fi
}

###############################
## Wien2k commands go here

run_SCF
    """
    return job


def xspec_file_script_no_header():
    # Holds the information of the xspec script. Reduces number of files that need to be sent to server.
    # Last updated Jun 28, 2025
    xspec = r"""
##########
# END of user parameters
edge_arr=("1s" "2s" "2p" "3s" "3p" "3d" "4s" "4p" "4d" "4f")
n_arr=(1 2 2 3 3 3 4 4 4 4)
l_arr=(0 0 1 0 1 2 0 1 2 3)

export_dir="xspec_export"

# create export directory if not already existing
mkdir -p $export_dir

# Find and separate all of the binding energies for the system
#BINDING_FILE="binding_energies"
# 1.ATOM # TODO: Fix the format to get binding energies for different edges. Maybe leave for python h5
# :1S, 2P, 2PP, 3D, 3DD
#: > "${export_dir}/${BINDING_FILE}.txt"
#awk "/:$ORBITAL/ {print}" "$case_name".scfc | tr "-" "\n" | tr "Ry" "\n" | awk "NR%2==0" | awk "NR%2!=0" >> "${export_dir}/${BINDING_FILE}.txt"


if [[ "${spin_polarized}" == "True" ]]; then
  : > "${export_dir}/${fermi_file}up.txt"
  awk '/:FER/ {print}' "$case_name".scf2up | tr "=" "\n" | awk "NR%2==0" >> "${export_dir}/${fermi_file}up.txt"
  : > "${export_dir}/${fermi_file}dn.txt"
  awk '/:FER/ {print}' "$case_name".scf2dn | tr "=" "\n" | awk "NR%2==0" >> "${export_dir}/${fermi_file}dn.txt"
else
  : > "${export_dir}/${fermi_file}.txt"
  awk '/:FER/ {print}' "$case_name".scf2 | tr "=" "\n" | awk "NR%2==0" >> "${export_dir}/${fermi_file}.txt"
fi

for atom_index in "${!atom_list[@]}"; do
  # Get the edge that we care about
  edge_index=999 # value that means it was not assigned properly
  for i in "${!edge_arr[@]}"; do # The ! is to get the key, without that it just returns the value instead
    # echo "For each i value: Index: $i, value: ${edge_arr[i]}"
    if [[ "${edge_arr[i]}" == "${orbital_list[${atom_index}]}" ]]; then
      # echo "Index: $i, value: ${edge_arr[i]}"
      edge_index=$i
      break
    fi
  done
  if [[ "$edge_index" == 999 ]]; then
    echo "Error in edge assignment"
    exit 1
  fi
  echo "Atom: ${atom_list[atom_index]} and Edge: ${orbital_list[${atom_index}]}"

  #export EMIS spectrum
  cat > "${case_name}.inxs" <<- EOM
Title:
${atom_list[atom_index]}         (atom)
${n_arr[edge_index]}               (n core)
${l_arr[edge_index]}               (l core)
0,0.5,0.5	(split, Int1, Int2)
-50,0.02,10	 (EMIN,DE,EMAX in eV)
EMIS            (type of spectrum)
0.50            (S)
0.5             (gamma0)
1.00            (W only for EMIS)
AUTO            (AUTO or MANually select Energy ranges for broadening)
        -19.8600000000000
        -19.9200000000000
        -20.0000000000000
EOM
  if [[ "${spin_polarized}" == "True" ]]; then
    x xspec -up
    cp "${case_name}.xspecup" "${export_dir}/${EMIS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.xspecup"
    cp "${case_name}.txspecup" "${export_dir}/${EMIS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.txspecup"

    x xspec -dn
    cp "${case_name}.xspecdn" "${export_dir}/${EMIS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.xspecdn"
    cp "${case_name}.txspecdn" "${export_dir}/${EMIS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.txspecdn"
  else
    x xspec
    cp "${case_name}.xspec" "${export_dir}/${EMIS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.xspec"
    cp "${case_name}.txspec" "${export_dir}/${EMIS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.txspec"
  fi

  #export ABS spectrum
  cat > "${case_name}.inxs" <<- EOM
Title:
${atom_list[atom_index]}         (atom)
${n_arr[edge_index]}              (n core)
${l_arr[edge_index]}               (l core)
0,0.5,0.5	(split, Int1, Int2)
-10,0.02,50	 (EMIN,DE,EMAX in eV)
ABS             (type of spectrum)
0.50            (S)
0.5             (gamma0)
1.00            (W only for EMIS)
AUTO            (AUTO or MANually select Energy ranges for broadening)
        -19.8600000000000
        -19.9200000000000
        -20.0000000000000
EOM
  if [[ "${spin_polarized}" == "True" ]]; then
    x xspec -up
    cp "${case_name}.xspecup" "${export_dir}/${ABS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.xspecup"
    cp "${case_name}.txspecup" "${export_dir}/${ABS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.txspecup"

   	x xspec -dn
    cp "${case_name}.xspecdn" "${export_dir}/${ABS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.xspecdn"
    cp "${case_name}.txspecdn" "${export_dir}/${ABS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.txspecdn"
  else
    x xspec
    cp "${case_name}.xspec" "${export_dir}/${ABS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.xspec"
    cp "${case_name}.txspec" "${export_dir}/${ABS_FILE_TEMPLATE/!atom!/${atom_list[atom_index]}}.txspec"
  fi
done

exit 0
"""
    return xspec

###################################################################################################################
# Function that actually starts the program

def auto_run(file_name="JupyterCommands.py"):
    """
    This is called when the program is run. Reads in list of instructions uploaded to server.
    If it successfully submits to slurm then removes from text file and continues down list.

    Parameters
    ----------
    file_name: name of file to search through for commands

    Returns
    -------
    Slurm submissions of job
    """
    # Example of input to the system in 'JupyterCommands.py'
    # Initialization(rkmax=6.5, kgen=500).main_program()
    with open(file_name, "r") as file:  # Read in Initialization().main_program() commands
        lines = file.readlines()
    while len(lines) > 0:
        exec(lines[0])  # Run each command
        lines.pop(0)  # If command was successful then remove from list. (Assumes will crash if unsuccessful)
        with open(file_name, "w") as file:  # Update file with reduced list
            file.writelines(lines)

    if len(lines) == 0:  # All commands ran successfully
        os.remove(file_name)


# This will execute when the file is run.
if file_exists('JupyterCommands.py'):
    auto_run()
else:
    print("No JupyterCommands.py found")
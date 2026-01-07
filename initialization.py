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
# TODO: Get site names and labels. So atom key in order, Fe1(47) So first iron, in (47'th position)
# TODO: Make a new job submission with only a single core that does the DOS and the Xtetra
# TODO: Make error handling better, so that user can actually see error messages from the terminal.
# TODO: Make a bash script that does the DOS
    # Will have to be specified to run in the run.job command, then it will receive how many files it has, only calculate
    # less than 21 cases each time, then save them in a specific naming scheme, and repeat until finished
    # On top of this, we want the run.job to be run2.job which only deals with the tasks. Runs on a single core,
    # This allows the user to rerun the tasks separately from the main job if they want to.
# TODO: THink about cluster configuration. bash type shell, planc defaults to...


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

    def __init__(self, rkmax = None, nn = None, functional = None, cutoff_energy = None, kgen = None, e_range = (-10.0, 4), # For initialization
                 cif_file = None, encoding_type = None, errors = None, # For initialization
                 sbatch = None, scf_type = "Basic", xspec = "True", resubmit = "False", scratch = "$SCRATCH", # run.job file
                 xspec_config = None, email_address = None, account = None, cpu_limit = 32, node_limit = 3, timelimit = "01:00:00"): # xspec_export.sh file

        self.number_of_atoms = None
        self.k_points = None
        if xspec_config is None:
            xspec_config = []

        self.case = get_current_folder_name()
        self.rkmax = rkmax
        self.functional = functional
        self.nn = nn
        self.cutoff_energy = cutoff_energy
        self.kgen = kgen
        self.complex_calc = False
        self.e_range = e_range
        self.encoding_type = encoding_type
        self.errors = errors
        self.cif_file = cif_file
        self.sbatch = sbatch
        self.scf_type = scf_type
        self.xspec = xspec # TODO: Make this a check if parameter exists, default to False then
        self.resubmit = resubmit
        self.scratch = scratch
        self.xspec_config = xspec_config
        self.email_address = email_address
        self.account = account
        self.cpu_limit = cpu_limit
        self.lvns = None
        self.gmax = None
        self.ifftfac = None
        self.node_limit = node_limit
        self.timelimit = timelimit

        # TODO: Convert to dection per clusterr

        # TODO: Put all of the final self parameters into a text file to output to user.

    # Function that organizes the flow of the program
    def main_program(self):
        """
        This organizes the flow of the program and is the only thing that is actually run.
        Called from JupyterCommands.py, which will delete itself after running through all calculations.

        Returns
        -------
        Will initialize the structure and run through nn, init_lapw, etc.
        Outputs xspec_export.sh, run.job.
        """
        self.change_directory(make_new_working_folder(self.cif_file)) # Change into working directory (Case_000)
        self.convert_cif_to_struct()        # Uses WIEN2k to convert input cif file to a .struct
        # self.initialize_structure()       # This is old module of initialize that did it manually. (Leave off for now)
        self.initialize_structure_auto()    # Uses the batch command with WIEN2k v23 to auto generate inputs
        self.create_job_file()              # Creates a job file that is later run by the program to submit to slurm
        self.create_xspec_file()            # Creates xspec file that is used by run.job to calculate XAS/XES
        self.create_dos_file()              # Crease a dos calculation file that is used by run.job to calculate Density of States
        #self.submit_slurm_job()            # This will submit run.job to slurm scheduler TODO: Turn this back on
        self.change_directory("../")        # Return out of working directory. (Maybe unnecessary based on how classes work)

    # Helper Functions
    def run_terminal_command(self, args):
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
        # TODO: Make a silent mode option, as this might be faster than printing out everything to terminal.
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
        print(command.stdout)  # Print output results for user

        # Error handling
        check_error_files()  # Check if case.error files exist, and if they do then exit(1)
        for line in command.stdout.splitlines(): # Reads stdout and check if any errors occurred
            if ("ERROR IN OPENING UNIT" or "error: command") in line: # Update this line as more error combinations occur
                print(command.stderr)
                print(command.stdout)
                exit(1)
        return command.stdout

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
        if self.cif_file.endswith('.struct'):
            shutil.move(self.cif_file, self.case + ".struct") # Update name of provided cif file to Case_000.struct
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

    def initialize_structure(self):
        # TODO: This is depreceated right now. Since all the parameters are set to None only the auto works.
            # This could work if you specify all of the parameters in first line of class.
        # Calculate the x nearest neighbours and accept the recommendations of the program
        self.run_terminal_command(f'echo {self.nn} | x nn')
        while len(open(self.case+".struct_nn").readlines()) > 1:
            self.run_terminal_command(f'cp {self.case}.struct_nn {self.case}.struct')
            self.run_terminal_command(f'echo {self.nn} | x nn')

        self.run_terminal_command('x sgroup')
        # TODO: Check output for warning, then prompt user to accept the space group
        symmetry_found = self.run_terminal_command('x symmetry')
        for line in symmetry_found.splitlines():
            if "SPACE GROUP DOES NOT CONTAIN INVERSION" in line: # Is this the best check for complex calcs?
                print("Calculation is complex")
                self.complex_calc = True
                break
        self.run_terminal_command(f'cp {self.case}.struct_st {self.case}.struct') # Uses found symmetry group

        self.run_terminal_command('echo "y" | instgen_lapw -up') # TODO: Make option to not default to spin up

        self.run_terminal_command(f'{{ echo {self.functional}; echo {self.cutoff_energy}; }} | x lstart')

        # Update case.in1_st to change rkmax
        default_rkmax = "7.00     10   4   ELPA" # TODO: Check if better way to change rkmax, or if the other params change
        replace_rkmax = f"{self.rkmax}     10   4   ELPA"
        replace(self.case+".in1_st", default_rkmax, replace_rkmax)

        # Update case.in1_st to increase energy range
        default_energy = "4   -9.0       1.5"
        replace_energy =  f"4   {self.e_range[0]}       {self.e_range[1]}"
        replace(self.case+".in1_st", default_energy, replace_energy)

        # Prepare input file
        self.run_terminal_command(f'cp {self.case}.in0_st {self.case}.in0')
        if self.complex_calc:
            self.run_terminal_command(f'cp {self.case}.in1_st {self.case}.in1c')
            self.run_terminal_command(f'cat {self.case}.in2_ls > {self.case}.in2c')
            self.run_terminal_command(f'cat {self.case}.in2_sy >> {self.case}.in2c')
        else:
            self.run_terminal_command(f'cp {self.case}.in1_st {self.case}.in1')
            self.run_terminal_command(f'cat {self.case}.in2_ls > {self.case}.in2')
            self.run_terminal_command(f'cat {self.case}.in2_sy >> {self.case}.in2')

        self.run_terminal_command(f'cp {self.case}.inc_st {self.case}.inc')
        self.run_terminal_command(f'cp {self.case}.inm_st {self.case}.inm')
        self.run_terminal_command(f'cp {self.case}.inq_st {self.case}.inq')

        # Generate the k-mesh
        self.run_terminal_command(f'{{ echo {self.kgen}; echo 0; }} | x kgen')
        self.run_terminal_command('x dstart')
        self.run_terminal_command(f'cp {self.case}.in0_std {self.case}.in0')
        print("END OF INITIALIZATION FOR CASE " + self.case)

    def initialize_structure_auto(self):
        initialization_command = 'init_lapw -b'
        if self.rkmax is not None:
            initialization_command += f' -rkmax {self.rkmax}'
        if self.kgen is not None:
            initialization_command += f' -numk {self.kgen}'
        if self.cutoff_energy is not None:
            initialization_command += f' -ecut {self.cutoff_energy}'
        if self.functional is not None:
            initialization_command += f' -vxc {self.functional}'
        initialization = self.run_terminal_command(f'{initialization_command}')

        # Update case.in1_st to increase energy range
        # TODO: Monitor if this has a significant impact on computation time
            # If yes then do it after convergence and rerun scf cycle again with increased energy range. lapw1 and lapw2 -qtl
        default_energy = "4   -9.0       1.5"
        replace_energy = f"4   {self.e_range[0]}       {self.e_range[1]}"
        try:
            replace(self.case + ".in1", default_energy, replace_energy)
        except:
            replace(self.case + ".in1c", default_energy, replace_energy)

        # Get input parameters provided from the terminal output of the init_lapw command
        # TODO: Check if stopping print to notebook will impact this search
        for line in initialization.splitlines():
            if "SPACE GROUP DOES NOT CONTAIN INVERSION" in line: # Is this the best check for complex calcs?
                self.complex_calc = True
            elif "set RKmax" in line:
                self.rkmax = line.split()[-1]
            elif "set LVNS" in line:
                self.lvns = line.split()[-1]
            elif "set GMAX" in line:
                self.gmax = line.split()[-1]
            elif "set IFFTfac" in line:
                self.ifftfac = line.split()[-1]
            elif "NUMK" in line:
                self.kgen = line.split()[-1] # These are input k-points
            elif "k-points generated" in line:
                self.k_points = line.split()[0] # This is k-mesh generated lattice
            elif "Atoms found:" in line:
                self.number_of_atoms = line.split()[0]

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

    def initialize_spin_polarized(self):
        # TODO: This worked with old initialization, not with the new version. Remove and update new
        self.initialize_structure()
        self.run_terminal_command('x dstart -up')
        self.run_terminal_command('x dstart -dn')

    def create_dos_file(self):
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
        # TODO: Find way to let them use entire job file if they so desire
        valid_scf_types = ["Basic", "PlusU", "SpinPolar", "ForceMin"]
        valid_boolean = ["True", "False"] # TODO: Make this an actual boolean??
        if self.scf_type not in valid_scf_types:
            print("Invalid scf type")
            exit(1)
        if self.xspec not in valid_boolean or self.resubmit not in valid_boolean:
            print("Invalid xspec or resubmit type")
            exit(1)
        if self.sbatch is not None:
            # This uses their own sbatch commands
            with open("run.job", 'w') as job:
                job.write(f"#!/bin/bash\n") # Header
                # If they want their own full sbatch commands
                job.write(self.sbatch + '\n') # SBATCH arguments

        else:
            # This makes use of an automation script to determine ntasks etc.
            with open("run.job", 'w') as job:
                job.write(f"#!/bin/bash\n") # Header
                job.write(f'#SBATCH -J {self.case}\n')
                if self.email_address is not None:
                    job.write(f'#SBATCH --mail-user={self.email_address}\n')
                    job.write(f'#SBATCH --mail-type=END\n')
                # Here we need the nodes, ntasks, mem
                # TODO: Found error where when you limit cpu, and increase node limit, gets more than desired
                ntasks = int(1.2 ** float(self.rkmax) * int(self.number_of_atoms) ** 0.45 - 1.5)
                # TODO: gmin and k mesh look at instead of rkmax atoms, and number of bands, because thats the k points at each.
                print("original ntasks: " + str(ntasks))
                requested_nodes = 1
                requested_nodes_interm = 1
                k_points_interm = self.k_points
                ntasks_interm = ntasks

                while ntasks > self.cpu_limit and requested_nodes_interm < self.node_limit:
                    requested_nodes_interm += 1
                    # Need to check if we can actually divide the number of k-points by the number of nodes that we want.
                    if int(self.k_points) % int(requested_nodes_interm) == 0:
                        requested_nodes = requested_nodes_interm
                        ntasks_interm = int(ntasks) / int(requested_nodes)
                        k_points_interm = int(self.k_points) / int(requested_nodes)
                        print("Updated ntasks" + str(ntasks_interm))
                # Finds the closest value in factor list to our originally calculated ntasks value
                factored_kpoints = sorted(factors(int(k_points_interm)))
                factored_kpoints[:] = [x for x in factored_kpoints if x <= self.cpu_limit] # restricts possible nodes to below cpu limit
                ntasks = min(factored_kpoints, key=lambda i: abs(ntasks_interm - i))
                print("ntasks before cropping" + str(ntasks))
                if ntasks < 1:
                    ntasks = 1
                print("factored_kpoints" + str(factored_kpoints))
                print("ntasks" + str(ntasks))
                print("requested_nodes" + str(requested_nodes))

                job.write(f'#SBATCH --nodes={requested_nodes}\n')
                job.write(f'#SBATCH --ntasks-per-node={ntasks}\n')
                # TODO: Find memory and time based on number of atoms and precision level
                job.write(f'#SBATCH --mem={int(3.9*ntasks*requested_nodes)}G\n') # This gives 4GB per cpu. Let user change
                job.write(f'#SBATCH --time={self.timelimit}\n')

                job.write(f'#SBATCH --get-user-env\n')
                job.write(f'#SBATCH --account={self.account}\n')
                job.write(f'scf_type="{self.scf_type}"\n')
                job.write(f'xspec="{self.xspec}"\n')
                job.write(f'resubmit="{self.resubmit}"\n')
                job.write(f'setenv SCRATCH {self.scratch}\n')
                job.write(job_file_script_no_header())

    def create_xspec_file(self):
        # TODO: Add some more checks for valid inputs
        # TODO: Make this automated? Make lookup table and calculate the orbitals based on what we want.
        with open("xspec_export.sh", 'w') as f:
            f.write(f"#!/bin/bash\n")  # Header
            f.write(f"set -e\n")
            f.write(f'case_name="{self.case}"\n')
            atoms = "("
            orbitals = "("
            for i in range(0,len(self.xspec_config),2):
                atoms += str(self.xspec_config[i]) + " "
                orbitals += '"' + str(self.xspec_config[i+1]) + '" '
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

    def submit_slurm_job(self):
        #self.run_terminal_command(f'sbatch {self.case}.job')
        self.run_terminal_command(f'sbatch run.job')
        return



###################################################################################################################
# Helper Functions

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

def auto_run(file_name="JupyterCommands.py"):
    with open(file_name, "r") as file:  # Read in Initialization().main_program() commands
        lines = file.readlines()
    while len(lines) > 0:
        exec(lines[0])  # Run each command
        lines.pop(0)  # If command was successful then remove from list. (Assumes will crash if unsuccessful)
        with open(file_name, "w") as file:  # Update file with reduced list
            file.writelines(lines)

    if len(lines) == 0:  # All commands ran successfully
        os.remove(file_name)

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
    os.remove(source_file_path)
    shutil.move(target_file_path, source_file_path) # Check that this still functions properly. Else target/source switch

def find_encoding(args):
    command = subprocess.run(args, shell=True, capture_output=True, check=True, text=False)
    with open('../encoding_stdout', "wb") as f:
        f.write(command.stdout)
    with open('../encoding_stderr', "wb") as f:
        f.write(command.stderr)
    return



###################################################################################################################
# Storage for shell scripts


def job_file_script_no_header():
    # Last updated Jan 6, 2026
    # TODO: Give ability to change the convergence criteria
    job = """
# Gets the hosts and puts it into the .machines file.
srun hostname -s  >slurm.hosts
rm .machines
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

#Initialization(rkmax=6.5, kgen=500).main_program()

# This will execute when the file is run.
if file_exists('JupyterCommands.py'):
    auto_run()
else:
    print("No JupyterCommands.py found")
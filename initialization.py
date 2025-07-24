# Created: 02/06/2025 (June 2, 2025)
# Last Edit: 24/06/2025

import os
import shutil
import subprocess
from pathlib import Path
from tempfile import mkstemp

# TODO: Create a function that uses the built in init to see what Wien2k recommends for input parameters
# TODO: Create a function that checks for warnings and outputs them to the user
# TODO: Figure how to replace gmax
# TODO: Create a logbook that keeps track of what commands were sent, and which file name they were sent to.
    # With logbook we should write to the file "CASE #: Failed", then overwrite it afterwards if it succeeded
# TODO: Make a try and catch case where we try a bunch of different encodings then specify that explicitly.
    # Right now we have commented out two aspects of the code that read the stdout to determine (such as complex)
# TODO: Give the user the option to upload their own job file instead of our own.
# TODO: Create a logbook that shows the outcome of files. As in, this calculation converged after x cycles, took x time


###################################################################################################################
# Main Function


class Initialization:

    def __init__(self, rkmax = 7.00, nn = 3, functional = "PBE", cutoff_energy = -6, k_points = 1000, e_range = (-9.0, 3.5), # For initialization
                 cif_file = None, encoding_type = None, errors=None, # For initialization
                 sbatch = None, scf_type = "Basic", xspec = "True", resubmit = "False", scratch = None, # run.job file
                 xspec_config=None): # xspec_export.sh file

        if xspec_config is None:
            xspec_config = []

        self.case = get_current_folder_name()
        self.rkmax = rkmax
        self.functional = functional
        self.nn = nn
        self.cutoff_energy = cutoff_energy
        self.k_points = k_points
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
        print(args)  # Print input commands
        if self.encoding_type is not None:
            command = subprocess.run(args, shell=True, capture_output=True, check=True, text=True, encoding=self.encoding_type, errors=self.errors)
        else:
            command = subprocess.run(args, shell=True, capture_output=True, check=True, text=True, errors=self.errors)
        print(command.stdout)  # Print output results

        # Error handling
        check_error_files()  # Check if case.error files exist
        for line in command.stdout.splitlines(): # Reads stdout and check if any errors occurred
            if ("ERROR IN OPENING UNIT" or "error: command") in line: # Update this line as more error combinations occur
                exit(1)
        return command.stdout

    # Functions interacting with WIEN2k
    def convert_cif_to_struct(self):
        # If the user decides to upload a .struct. Assume they have done setrmt, or chosen accurate rmt values
        if self.cif_file.endswith('.struct'):
            shutil.move(self.cif_file, self.case + ".struct")  # Change this to copy to preserve the system
            return


        for file_name in os.listdir('.'):
            if file_name.endswith('.cif'): # Will convert the first cif file it finds. User can only have 1 cif in a folder for accurate parsing
                if file_name == self.case+".cif":
                    break
                else:
                    shutil.move(file_name, self.case+".cif") # Change this to copy to preserve the system
                    break
        if file_exists(self.case+".cif"):
            try: # TODO: Make this a better check of encoding??
                self.run_terminal_command('x cif2struct')
            except:
                print("Error converting cif: Either WIEN2k command could not be found, or encoding error.")
                print("If encoding error please run find_encoding() in the jupyter notebook.")
                find_encoding('x cif2struct')
                # exit(1)
            self.run_terminal_command('setrmt')
            self.run_terminal_command(f'cp {self.case}.struct_setrmt {self.case}.struct')
        else:
            print("No cif structure found")
            exit(1)

    def change_directory(self, directory):
        os.chdir(directory)
        self.case = get_current_folder_name()

    def initialize_structure(self):
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
        self.run_terminal_command(f'{{ echo {self.k_points}; echo 0; }} | x kgen')
        self.run_terminal_command('x dstart')
        self.run_terminal_command(f'cp {self.case}.in0_std {self.case}.in0')
        print("END OF INITIALIZATION FOR CASE " + self.case)

    def initialize_spin_polarized(self):
        self.initialize_structure()
        self.run_terminal_command('x dstart -up')
        self.run_terminal_command('x dstart -dn')

    def print_info(self):
        # RKmax, Energy k-vector range stored in .in1 or .in1c
        # Gmax stored in .in2 or .in2c
        # k-mesh and # of k-points found in .klist
        return

    def main_program(self):
        self.change_directory(make_new_working_folder(self.cif_file))
        self.convert_cif_to_struct()
        self.initialize_structure()
        self.create_job_file()
        self.create_xspec_file()
        #self.submit_slurm_job() # TODO: Turn this back on
        self.change_directory("../")
        # Change back out of directory???

    def create_job_file(self):
        valid_scf_types = ["Basic", "PlusU", "SpinPolar"]
        valid_boolean = ["True", "False"] # TODO: Make this an actual boolean??
        if self.scf_type not in valid_scf_types:
            print("Invalid scf type")
            exit(1)
        if self.xspec not in valid_boolean or self.resubmit not in valid_boolean:
            print("Invalid xspec or resubmit type")
            exit(1)
        if self.sbatch is not None:
            #with open(self.case+".job", 'w') as job:
            with open("run.job", 'w') as job:
                job.write(f"#!/bin/bash\n") # Header
                job.write(self.sbatch + '\n') # SBATCH arguments #TODO: Auto create the name of the job that submits
                job.write(f'scf_type="{self.scf_type}"\n')
                job.write(f'xspec="{self.xspec}"\n')
                job.write(f'resubmit="{self.resubmit}"\n')
                job.write(f'setenv SCRATCH {self.scratch}\n')
                job.write(job_file_script_no_header())
        else:
            print("No sbatch arguments found to create job file. Manually run sbatch with your own job file.")
            exit(1)


    def create_xspec_file(self):
        # TODO: Add some more checks for valid inputs
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
            f.write(xspec_file_script_no_header())
        os.system('chmod +x xspec_export.sh')
        return

    def submit_slurm_job(self):
        #self.run_terminal_command(f'sbatch {self.case}.job')
        self.run_terminal_command(f'sbatch run.job')
        return



###################################################################################################################
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
    # Last updated Jun 24, 2025
    # TODO: Give ability to change the convergence criteria
    # TODO: Remove the section of spin polarized xspec. They have been merged into one file (or else have different naming schemes?
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
  chmod +x xspec_export_spin_polarized.sh
  ./xspec_export_spin_polarized.sh
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

choose_SCF_type() {
  if [[ "$scf_type" == "Basic" ]]; then
    basic_SCF
  elif [[ "$scf_type" == "PlusU" ]]; then
    plusU_SCF
  elif [[ "$scf_type" == "SpinPolar" ]]; then
    spinpolar_SCF
  fi
}

choose_xspec_type() {
  if [[ "$scf_type" == "Basic" ]]; then
    basic_xspec
  elif [[ "$scf_type" == "PlusU" ]]; then
    spinpolar_xspec
  elif [[ "$scf_type" == "SpinPolar" ]]; then
    spinpolar_xspec
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
# Not user parameters
edge_arr=("1s" "2s" "2p" "3s" "3p" "3d" "4s" "4p" "4d" "4f")
n_arr=(1 2 2 3 3 3 4 4 4 4)
l_arr=(0 0 1 0 1 2 0 1 2 3)

export_dir="xspec_export"

# create export directory if not already existing
mkdir -p $export_dir

# Find and separate all of the binding energies for the system
#BINDING_FILE="binding_energies"
fermi_file="fermi_energy"
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
-30,0.02,10	 (EMIN,DE,EMAX in eV)
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
-10,0.02,30	 (EMIN,DE,EMAX in eV)
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

#Initialization(rkmax=6.5, k_points=500).main_program()

# This will execute when the file is run.
if file_exists('JupyterCommands.py'):
    auto_run()
else:
    print("No JupyterCommands.py found")
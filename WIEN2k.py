# Created: May 14
# Last Updated: May 22
# Cody Somers

import os
import subprocess
import h5py
import numpy as np

def get_info(caseName):
    print(caseName)

def write_hdf5():

    return 0

def test_shell(case='CoFeMn',rkmax='7'):
    os.system('chmod +x test.sh')
    pass_arg = ["./test.sh", case, rkmax]

    subprocess.check_call(pass_arg)
    print("We are waiting for 1 second")



# Data Structure
#   CASENAME (Chose by User) (Group)
#       CASENAME_RKmax_kpoints_VXC (Autopicked based on input files?) (Dataset)
#   CASENAME_corehole_RKmax_kpoints_VXC (Can we do corehole in series instead of parallel?)
#       CASENAME_atom1
#   CoFeMnV2 (Group)
#       CoFeMnV2_rkm7_150k_PBE (Dataset)
#       CoFeMnV2_rkm7_300k_PBE
#       CoFeMnV2_rkm8_800k_PBE
#   CoFeMn_corehole_rkm7_600k_PBE (Think more on this)
#       CoFeMn_O1
#       CoFeMn_O2
#       CoFeMn_Fe3

# MAke a local log file that keeps track of the input parameters, then when you convert to hdf5 we need to combine
# all of those log files together. This way we know that those folders have been converted properly.

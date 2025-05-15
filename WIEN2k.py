# Created: May 14
# Last Updated: May 15
# Cody Somers

import os
import subprocess
import h5py
import numpy as np

def get_info(caseName):
    print(caseName)


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
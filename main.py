# Created: May 14
# Last Updated: May 15
# Cody Somers

import os
import subprocess
import h5py
import numpy as np

os.system('chmod +x test.sh')
pass_arg= ["./test.sh", "CoFeMn", "7"]

subprocess.check_call(pass_arg)
print("We are waiting for 1 second")

arr = np.random.random(100)
# Create a group that has the individual calcualtions in them
# Create a dataset that has the information about them
with h5py.File('test.h5', 'w') as f:
    g = f.create_group('CoFeMn')
    d = g.create_dataset('CoFeMn_150k_7RK_PBE', data=arr)

with h5py.File('test.h5', 'r') as f:
    d = f['CoFeMn/CoFeMn_150k_7RK_PBE']
    print(d[1])
    for k in f.keys():
        print(k)
    for k in f['CoFeMn'].keys():
        print(k)

# Things that we want to save into the containers
# Initial setup
# K-points
# RK-max
# VXC option (PBE etc.)
# energy seperation
# RMT reduction

# System SCF Convergence
# Fermi energy (one for each system)
# Binding energy (one for each atom)
#   Organize the files into binding energy for 1s, 2p, etc. and put in different folders
# Number of cycles
# See what save_lapw does, and do the same?
#   Do save lapw, and name it according to the parameters.
#   If it exists, then don't save it again, but ask if you want to override it.

# Task Data
# Xspec data for each atom
#   Do it automatically for each atom. Make an array based on the
#   species, and the edge you desire. [Mn 2p*, O 1s]
# DOS
# Bandstructure

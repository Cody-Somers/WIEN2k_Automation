import WIEN2k
from WIEN2k import *

###### One calculation

caseName="Case"
rkMax="RKMax"
# Create a new group based on the case name.
# Initialize calculation
# Get input parameters
# Run the SCF Cycle
# Check convergence
# Calculate DOS and Xspec (need to specify parameters before sbatch then)
# Save the calculations (Create a new dataset with naming based on the parameters)
# Rerun with new parameters
# Check convergence
# Save the calculation

# If you want to redo the calculations with a saved calculation then have to restore_lapw
# Have a case where if they do CASE as the specification for which task then no restore,
# and don't save it the h5 until they press the save button.



get_info(caseName)


###### Two Calculation

caseName="Case2"


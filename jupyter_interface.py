# Created: 05/06/2025 (June 5, 2025)
# Last Edit: 05/06/2025

# Users only need to run this once to get something. Will be the same everytime
def create_auto_run():
    auto_run = """import sys
from initialization import Initialization

with open(sys.argv[1], "r") as file:
    lines = file.readlines()

while len(lines) > 0:
    exec(lines[0])
    lines.pop(0)
    with open(sys.argv[1], "w") as file:
        file.writelines(lines)
"""
    with open("auto_run.py", "w") as file:
        file.write(auto_run)



def create_job_file(slurm_job="run.job", scf_type="Basic", xspec="False", resubmit="False"):
    # This will hold the info for a job file. So in jupyter notebook they can create the auto_run, but they can also create
    # a job file. They will have to upload then

    return

class JupyterInterface:
    """
    Hela
    """
    def __init__(self, name="JupyterCommands"):
        self.name = name
        with open(self.name + ".py", "w") as file:
            pass

    def create_new_calculation(self, **kwargs):
        with open(self.name + ".py", "a") as file:
            # Initialization(**kwargs).main_program()
            file.write(f"Initialization({(','.join('{0}={1!r}'.format(k, v) for k, v in kwargs.items()))}).main_program()\n")

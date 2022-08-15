import os

EXCLUDED_MODULES = ["__init__.py", "imt.py", "imc.py"]
BASE = os.path.dirname(os.path.abspath(__file__))


def gather_pgms():
    imt_directory = os.path.join(BASE, "imt")
    imc_directory = imt_directory.replace("imt", "imc")
    # Create list
    imt_classes = []
    imc_classes = []
    for imt_file in os.listdir(imt_directory):
        if imt_file.endswith(".py") and imt_file not in EXCLUDED_MODULES:
            imt_file = imt_file[0:-3]
            imt_classes += [imt_file]
    for imc_file in os.listdir(imc_directory):
        if imc_file.endswith(".py") and imc_file not in EXCLUDED_MODULES:
            imc_file = imc_file[0:-3]
            imc_classes += [imc_file]
    return imt_classes, imc_classes

from pathlib import Path

EXCLUDED_MODULES = ["__init__.py", "imt.py", "imc.py"]
BASE = Path(__file__).parent


def gather_pgms():
    imt_directory = BASE / "imt"
    imc_directory = BASE / "imc"
    # Create list
    imt_classes = []
    imc_classes = []
    for imt_file in imt_directory.iterdir():
        if imt_file.suffix == ".py" and imt_file.name not in EXCLUDED_MODULES:
            imt_file = imt_file.stem
            imt_classes += [imt_file]
    for imc_file in imc_directory.iterdir():
        if imc_file.suffix == ".py" and imc_file.name not in EXCLUDED_MODULES:
            imc_file = imc_file.stem
            imc_classes += [imc_file]
    return imt_classes, imc_classes

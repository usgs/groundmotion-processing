$VENV="gmprocess"
$py_ver="3.7"
$CC_PKG="c-compiler"

conda deactivate
conda remove -y -n $VENV --all

$package_list=
    "python=$py_ver",
    "pip",
    "$CC_PKG",
    "cython",
    "impactutils",
    "ipython",
    "jupyter",
    "libcomcat",
    "lxml",
    "mapio",
    "matplotlib",
    "numpy",
    "obspy>=1.2.1",
    "openpyxl",
    "openquake.engine>=3.10.1",
    "pandas",
    "ps2ff",
    "pyasdf",
    "pytest",
    "pytest-cov",
    "pyyaml",
    "requests",
    "vcrpy"

conda create -y -n $VENV -c conda-forge --channel-priority $package_list
conda activate $VENV
pip install -e . --no-deps --ignore-installed --no-cache-dir -vv

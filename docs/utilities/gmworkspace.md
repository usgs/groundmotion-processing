# Examining the workspace using gmworkspace



## The gmworkspace command

```
usage: gmworkspace [-h] --filename=WORKSPACE [--describe] [--compute-storage]

required arguments:
  --filename FILENAME  Name of workspace file.

optional arguments:
  -h, --help           Show this help message and exit
  --describe           Print a summary of workspace contents to stdout. Similar to h5dump.
  --compute-storage    Print a summary of the workspace storage to stdout.
```

## Show workspace contents

The `--describe` command line argument prints the names of the groups
and datasets in the workspace HDF5 file to stdout. For each dataset
the information also includes the dimensions and type. Strings are
stored as bytes (the type is `uint8`).

Show the contents of the `workspace.hdf` file:
```[bash]
gmworkspace --filename=workspace.hdf --describe
```

## Show workspace storage

The `--compute-storage` command line argument prints a summary of the
storage using by the various groups in the workspace HDF5 file to
stdout. The storage is shown in megabytes (MB, 2**20 bytes).

Show the storage used in the `workspace.hdf` file:
```[bash]
gmworkspace --filename=workspace.hdf --compute-storage
```

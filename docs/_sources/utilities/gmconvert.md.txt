# Converting data using gmconvert

There may be consumers of strong motion data who want to analyze these
waveforms in other packages (SAC, Matlab, etc.)  The `gmconvert`
command can be used to convert files from one of the various formats
into any one of the [formats supported by
ObsPy](https://docs.obspy.org/packages/autogen/obspy.core.stream.Stream.write.html#obspy.core.stream.Stream.write).

## The gmconvert command

```
gmconvert [-h] [-i INDIR] [-o OUTDIR]
          [-f {AH,GSE2,MSEED,PICKLE,Q,SAC,SACXY,SEGY,SH_ASC,SLIST,SU,TSPAIR,WAV}]
          [-d | -q]
          [files [files ...]]

positional arguments:
  files                 List of files to convert (default: None).

optional arguments:
  -h, --help            Show this help message and exit
  --indir INDIR         Directory containing input files to convert (default: None).
  --outdir OUTDIR       Output directory. (default: current working directory)
   --format {AH,GSE2,MSEED,PICKLE,Q,SAC,SACXY,SEGY,SH_ASC,SLIST,SU,TSPAIR,WAV}
                        Output strong motion data format (default: MSEED).
  -d, --debug           Print all informational messages (default: False).
  -q, --quiet           Print only errors (default: False).
```

The format of the input file is detected automatically, so only the
format of the output file needs to be specified.  The inventory
information will be written as an accompanying file in station XML
format.

## Convert a single file from the NIED KNET format to MiniSEED

```bash
gmconvert AOM0011801241951.EW
```

The following files will be written to the current directory:
    * `BO.AOM001.--.HN2.mseed`
    * `BO.AOM001.--.HN2.xml`

## Convert the the channels of BO.AOM001 station data into one MiniSEED file

```bash
gmconvert AOM0011801241951.*
```

The following files will be written to the current directory:
    * `BO.AOM001.HN.mseed`
    * `BO.AOM001.HN.xml`

## Convert a directory of files to SAC format 

The input files are in the `indatadir` directory and the output files
are in the `outdatadir`. The data files in the `indatadir` can be
distributed through subdirectories and gmconvert will find them.

```bash
gmconvert -i datadir -o outdatadir -f SAC
```


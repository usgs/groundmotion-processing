# Converting Data

There may be consumers of strong motion data who want to 
analyze these waveforms in other packages (SAC, Matlab, etc.) 
For those users a `gmconvert` command is provided which can be
used to convert files from one of the various formats into
any one of the formats supported by ObsPy.

https://docs.obspy.org/packages/autogen/obspy.core.stream.Stream.write.html#obspy.core.stream.Stream.write

## The gmconvert command

```
usage: gmconvert [-h] [-i INDIR] [-o OUTDIR]
                 [-f {AH,GSE2,MSEED,PICKLE,Q,SAC,SACXY,SEGY,SH_ASC,SLIST,SU,TSPAIR,WAV}]
                 [-d | -q]
                 [files [files ...]]

Convert a directory of strong motion data files into any ObsPy
    supported format.

https://docs.obspy.org/packages/autogen/obspy.core.stream.Stream.write.html#supported-formats

    The inventory information will be written as an 
    accompanying file in station XML format.

    To convert a single file in the NIED KNET format to MiniSEED:

    gmconvert AOM0011801241951.EW 

    The following files will be written to the current directory:
        - BO.AOM001.--.HN2.mseed
        - BO.AOM001.--.HN2.xml

    To convert the three files that make up the BO.AOM001 station data into one MiniSEED file:

    gmconvert AOM0011801241951.*

    The following files will be written to the current directory:
        - BO.AOM001.HN.mseed
        - BO.AOM001.HN.xml

    To convert a directory "indatadir" full of files to SAC format, and write
    to a directory called "outdatadir":

    gmconvert -i datadir -o outdatadir -f SAC

    Note: The data files in "indatadir" can be distributed through
    subdirectories and gmconvert will find them.

    

positional arguments:
  files                 List of files to convert. (default: None)

optional arguments:
  -h, --help            show this help message and exit
  -i INDIR, --indir INDIR
                        Directory containing input files to convert. (default:
                        None)
  -o OUTDIR, --outdir OUTDIR
                        Output directory. (default:
                        /Users/mhearne/src/python/groundmotion-processing/bin)
  -f {AH,GSE2,MSEED,PICKLE,Q,SAC,SACXY,SEGY,SH_ASC,SLIST,SU,TSPAIR,WAV}, --format {AH,GSE2,MSEED,PICKLE,Q,SAC,SACXY,SEGY,SH_ASC,SLIST,SU,TSPAIR,WAV}
                        Output strong motion data format. (default: MSEED)
  -d, --debug           Print all informational messages. (default: False)
  -q, --quiet           Print only errors. (default: False)
  ```
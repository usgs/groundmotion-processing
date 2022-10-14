#!/usr/bin/env python

# stdlib imports
import sys
from pathlib import Path
import argparse
import logging

from gmprocess.subcommands.lazy_loader import LazyLoader

# local imports
log = LazyLoader("log", globals(), "gmprocess.utils.logging")
argmod = LazyLoader("argmod", globals(), "gmprocess.utils.args")
streamcollection = LazyLoader(
    "streamcollection", globals(), "gmprocess.core.streamcollection"
)
readmod = LazyLoader("readmod", globals(), "gmprocess.io.read")
read_directory = LazyLoader("read_directory", globals(), "gmprocess.io.read_directory")


class CustomFormatter(
    argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter
):
    pass


FORMATS = [
    "AH",
    "GSE2",
    "MSEED",
    "PICKLE",
    "Q",
    "SAC",
    "SACXY",
    "SEGY",
    "SH_ASC",
    "SLIST",
    "SU",
    "TSPAIR",
    "WAV",
]


def main():
    desc = """Convert a directory of strong motion data files into any ObsPy
    supported format.

https://docs.obspy.org/packages/autogen/obspy.core.stream.Stream.write.html#supported-formats

    The inventory information will be written as an
    accompanying file in station XML format.

    To convert a single file in the NIED KNET format to MiniSEED:

    gmconvert AOM0011801241951.EW

    The following files will be written to the current directory:
        - BO.AOM001.--.HN2.mseed
        - BO.AOM001.--.HN2.xml

    To convert the three files that make up the BO.AOM001 station data into
    one MiniSEED file:

    gmconvert AOM0011801241951.*

    The following files will be written to the current directory:
        - BO.AOM001.HN.mseed
        - BO.AOM001.HN.xml

    To convert a directory "indatadir" full of files to SAC format, and write
    to a directory called "outdatadir":

    gmconvert -i datadir -o outdatadir -f SAC

    Note: The data files in "indatadir" can be distributed through
    subdirectories and gmconvert will find them.

    """
    parser = argparse.ArgumentParser(description=desc, formatter_class=CustomFormatter)
    parser.add_argument(
        "files", help="List of files to convert.", nargs="*", default=None
    )
    parser.add_argument(
        "-i", "--indir", help="Directory containing input files to convert."
    )
    labelhelp = (
        "Only used when converting from ASDF to specify the stream label to use."
    )
    parser.add_argument("-l", "--label", help=labelhelp, default="default")
    parser.add_argument("-o", "--outdir", help="Output directory.", default=Path.cwd())
    parser.add_argument(
        "-f",
        "--format",
        help="Output strong motion data format.",
        choices=FORMATS,
        default="MSEED",
    )

    # Shared arguments
    parser = argmod.add_shared_args(parser)
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()

    log.setup_logger(args)
    logging.info("Running gmconvert.")

    # gather arguments
    indir = Path(args.indir)
    outdir = Path(args.outdir)
    oformat = args.format

    has_files = args.files is not None and len(args.files)

    if has_files and args.indir is not None:
        print("Specify input files or an input directory, not both.")
        sys.exit(1)

    if args.files is None and args.indir is None:
        print("You must specify input files or an input directory.")
        sys.exit(1)

    outdir.mkdir(exist_ok=True)

    if args.files:
        # read all the data files, gather up a list of obspy Stream objects
        allstreams = []
        error_dict = {}
        for dfile in args.files:
            logging.info(f"Parsing {dfile}...")
            try:
                streams = readmod.read_data(dfile, label=args.label)
            except BaseException as e:
                error_dict[dfile] = str(e)
                continue
            allstreams += streams
    else:
        # grab all the files in the input directory
        allstreams, unprocessed, errors = read_directory.directory_to_streams(indir)
        error_dict = dict(zip(unprocessed, errors))

    sc = streamcollection.StreamCollection(allstreams)
    for stream in sc:
        for tr in stream:
            tag = tr.stats.tag
            if tag:
                label = tag.split("_")[1]
                trace_id = f"{tr.get_id()}_{label}"
            else:
                trace_id = tr.get_id()
            outfile = outdir / f"{trace_id}.{oformat.lower()}"
            logging.info(f"Writing data file {outfile}...")
            tr.write(str(outfile), format=oformat)

        streamid = stream.get_id()
        if len(stream) == 1:
            streamid = stream[0].get_id()
        invfile = outdir / f"{streamid}.xml"
        inv_format = "STATIONXML"
        inv = stream.getInventory()
        logging.info(f"Writing inventory file {invfile}...")
        inv.write(str(invfile), format=inv_format)

    print("Wrote %i streams to %s" % (len(sc), outdir))
    if len(error_dict):
        print("\nThe following files could not be read:")
        for fname, error in error_dict.items():
            print(f'\t{fname} - "{error}"')


if __name__ == "__main__":
    main()

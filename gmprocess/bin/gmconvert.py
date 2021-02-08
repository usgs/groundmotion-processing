#!/usr/bin/env python

# stdlib imports
import sys
import os.path
import argparse
import logging

# local imports
from gmprocess.utils.logging import setup_logger
from gmprocess.utils.args import add_shared_args
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.io.read import read_data
from gmprocess.io.read_directory import directory_to_streams


class CustomFormatter(
        argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):
    pass


FORMATS = [
    'AH',
    'GSE2',
    'MSEED',
    'PICKLE',
    'Q',
    'SAC',
    'SACXY',
    'SEGY',
    'SH_ASC',
    'SLIST',
    'SU',
    'TSPAIR',
    'WAV']


def main():
    desc = '''Convert a directory of strong motion data files into any ObsPy
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

    '''
    parser = argparse.ArgumentParser(
        description=desc,
        formatter_class=CustomFormatter)
    parser.add_argument('files', help='List of files to convert.',
                        nargs='*', default=None)
    parser.add_argument('-i', '--indir',
                        help='Directory containing input files to convert.')
    parser.add_argument('-o', '--outdir',
                        help='Output directory.', default=os.getcwd())
    parser.add_argument('-f', '--format',
                        help='Output strong motion data format.',
                        choices=FORMATS, default='MSEED')

    # Shared arguments
    parser = add_shared_args(parser)

    args = parser.parse_args()

    setup_logger(args)
    logging.info("Running gmconvert.")

    # gather arguments
    indir = args.indir
    outdir = args.outdir
    oformat = args.format

    has_files = args.files is not None and len(args.files)

    if has_files and args.indir is not None:
        print('Specify input files or an input directory, not both.')
        sys.exit(1)

    if args.files is None and args.indir is None:
        print('You must specify input files or an input directory.')
        sys.exit(1)

    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    if args.files:
        # read all the data files, gather up a list of obspy Stream objects
        allstreams = []
        error_dict = {}
        for dfile in args.files:
            logging.info('Parsing %s...' % dfile)
            try:
                streams = read_data(dfile)
            except BaseException as e:
                error_dict[dfile] = str(e)
                continue
            allstreams += streams
    else:
        # grab all the files in the input directory
        allstreams, unprocessed, errors = directory_to_streams(indir)
        error_dict = dict(zip(unprocessed, errors))

    sc = StreamCollection(allstreams)

    for stream in sc:
        streamid = stream.get_id()
        if len(stream) == 1:
            streamid = stream[0].get_id()
        outfile = os.path.join(outdir, '%s.%s' % (streamid, oformat.lower()))
        invfile = os.path.join(outdir, '%s.xml' % (streamid))
        inv_format = 'STATIONXML'
        inv = stream.getInventory()
        logging.info('Writing data file %s...' % outfile)
        stream.write(outfile, format=oformat)
        logging.info('Writing inventory file %s...' % invfile)
        inv.write(invfile, format=inv_format)

    print('Wrote %i streams to %s' % (len(sc), outdir))
    if len(error_dict):
        print('\nThe following files could not be read:')
        for fname, error in error_dict.items():
            print('\t%s - "%s"' % (fname, error))


if __name__ == '__main__':
    main()

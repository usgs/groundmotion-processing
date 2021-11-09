#!/usr/bin/env python

# stdlib imports
import os.path
import argparse
from collections import OrderedDict
import sys
import warnings
import textwrap
import logging

# third party imports
import pandas as pd

# local imports
from gmprocess.io.read import _get_format, read_data
from gmprocess.utils.args import add_shared_args
from gmprocess.core.stationtrace import REV_PROCESS_LEVELS
from gmprocess.utils.config import get_config

COLUMNS = ['Filename', 'Format', 'Process Level',
           'Start Time', 'End Time',
           'Duration (s)', 'Network', 'Station', 'Channel',
           'Sampling Rate (Hz)', 'Latitude', 'Longitude']

ERROR_COLUMNS = ['Filename', 'Error']


def get_dataframe(filename, stream):
    df = pd.DataFrame(columns=COLUMNS, index=None)
    row = pd.Series(index=COLUMNS)
    fpath, fname = os.path.split(filename)
    for trace in stream:
        row['Filename'] = filename
        row['Format'] = trace.stats['standard']['source_format']
        plevel = trace.stats['standard']['process_level']
        row['Process Level'] = REV_PROCESS_LEVELS[plevel]
        row['Start Time'] = trace.stats.starttime
        row['End Time'] = trace.stats.endtime
        dt = trace.stats.endtime - trace.stats.starttime
        row['Duration (s)'] = dt
        row['Network'] = trace.stats.network
        row['Station'] = trace.stats.station
        row['Channel'] = trace.stats.channel
        row['Sampling Rate (Hz)'] = trace.stats.sampling_rate
        row['Latitude'] = trace.stats.coordinates['latitude']
        row['Longitude'] = trace.stats.coordinates['longitude']
        df = df.append(row, ignore_index=True)

    return df


def render_concise(files, save=False):
    errors = pd.DataFrame(columns=ERROR_COLUMNS)
    df = pd.DataFrame(columns=COLUMNS, index=None)
    folders = []
    for filename in files:
        fpath, fname = os.path.split(filename)
        if fpath not in folders:
            sys.stderr.write('Parsing files from subfolder %s...\n' % fpath)
            folders.append(fpath)
        try:
            streams = read_data(filename)
            for stream in streams:
                tdf = get_dataframe(filename, stream)
                df = pd.concat([df, tdf], axis=0)
        except BaseException as e:
            row = pd.Series(index=ERROR_COLUMNS)
            row['Filename'] = os.path.abspath(filename)
            row['Error'] = str(e)
            errors = errors.append(row, ignore_index=True)
            continue

    # organize dataframe by network, station, and channel
    df = df.sort_values(['Network', 'Station', 'Channel'])
    if not save:
        print(df.to_string(index=False))

    return (df, errors)


def render_dir(rootdir, concise=True, save=False):
    datafiles = []
    for root, dirs, files in os.walk(rootdir):
        for tfile in files:
            ffile = os.path.join(root, tfile)
            datafiles.append(ffile)

    if concise:
        df, errors = render_concise(datafiles, save=save)
    else:
        errors = render_verbose(datafiles)
        df = None

    return (df, errors)


def render_verbose(files):
    config = get_config()
    errors = pd.DataFrame(columns=ERROR_COLUMNS)
    for fname in files:
        try:
            fmt = _get_format(fname, config)
            stream = read_data(fname, config)[0]
            stats = stream[0].stats
            tpl = (stats['coordinates']['latitude'],
                   stats['coordinates']['longitude'],
                   stats['coordinates']['elevation'])
            locstr = 'Lat: %.4f Lon: %.4f Elev: %.1f' % tpl
            mydict = OrderedDict(
                [('Filename', fname),
                 ('Format', fmt),
                 ('Station', stats['station']),
                 ('Network', stats['network']),
                 ('Source', stats['standard']['source']),
                 ('Location', stats['location']),
                 ('Coordinates', locstr),
                 ])
            print()

            print(pd.Series(mydict).to_string())
            for trace in stream:
                channel = OrderedDict()
                stats = trace.stats
                channel['Channel'] = stats['channel']
                channel['Start Time'] = stats['starttime']
                channel['End Time'] = stats['endtime']
                channel['Number of Points'] = stats['npts']
                channel['Units'] = stats['standard']['units']
                channel['Peak Value'] = trace.max()
                print()
                chstr = pd.Series(channel).to_string()
                parts = ['\t' + line for line in chstr.split('\n')]
                chstr = '\n'.join(parts)
                print(chstr)
        except BaseException as e:
            row = pd.Series(index=ERROR_COLUMNS)
            row['Filename'] = os.path.abspath(fname)
            row['Error'] = str(e)
            errors = errors.append(row, ignore_index=True)
            continue
    return errors


def main():
    description = '''Display summary information about a file, multiple files,
    or directories of files containing strong motion data in the supported
    formats.
    Use the -p option to print errors for files that could not be read.
    Use the -s option to save summary data AND errors to Excel/CSV format.
    .'''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('files_or_dir', nargs='+',
                        help='Files or directory to inspect.',
                        type=str)
    chelp = '''Print out results in concise CSV form. Columns are:
    Filename
    Format
    Process Level
    Start Time
    End Time
    # of Traces
    Duration
    Network
    Station
    Channels
    Sampling rate
    Latitude
    Longitude
    '''
    parser.add_argument('-c', '--concise', action='store_true',
                        help=chelp)
    shelp = '''Save concise results to CSV/Excel file
    (format determined by extension (.xlsx for Excel, anything else for CSV.))
    '''
    parser.add_argument('-s', '--save', metavar='OUTFILE',
                        help=shelp)
    phelp = 'Print error log containing files that could not be parsed.'
    parser.add_argument('--quiet-errors', action='store_true',
                        help=phelp)
    # Shared arguments
    parser = add_shared_args(parser)
    args = parser.parse_args()

    if not args.concise and args.save:
        msg = '''
        ****************************************************************
        Saving verbose output is not supported. Use -c and -s
        options together to save tabular summary/error information about
        the data.
        ****************************************************************
        '''
        print(textwrap.dedent(msg))
        parser.print_help()
        sys.exit(1)

    logger = logging.getLogger()
    logger.setLevel(logging.CRITICAL)
    warnings.filterwarnings("ignore")
    pd.set_option('display.max_columns', 10000)
    pd.set_option("display.max_colwidth", 10000)
    pd.set_option("display.expand_frame_repr", False)

    files = args.files_or_dir
    do_save = args.save is not None
    if len(files) == 1:
        # is this a file or a directory?
        if os.path.isdir(files[0]):
            df, errors = render_dir(files[0],
                                    concise=args.concise,
                                    save=do_save)
            if args.save is not None and args.concise:
                fbase, fext = os.path.splitext(args.save)
                errfile = fbase + '_errors' + fext
                print('Catalog written to %s.' % args.save)
                print('Errors written to %s.' % errfile)
                if fext == '.xlsx':
                    df.to_excel(args.save, index=False)
                    errors.to_excel(errfile, index=False)
                else:
                    df.to_csv(args.save, index=False)
                    errors.to_csv(errfile, index=False)
            if not args.save and not args.quiet_errors:
                print(errors.to_string(index=False))
            sys.exit(0)
    if args.concise:
        df, errors = render_concise(files, save=do_save)
        if args.save is not None:
            fbase, fext = os.path.splitext(args.save)
            if fext == '.xlsx':
                df.to_excel(args.save, index=False)
            else:
                df.to_csv(args.save, index=False)

    else:
        errors = render_verbose(files)
    if not args.quiet_errors and not args.save and len(errors):
        print(errors.to_string(index=False))


if __name__ == '__main__':
    main()

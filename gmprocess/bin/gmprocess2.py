#!/usr/bin/env python

# stdlib imports
import argparse
import logging
import os.path
import sys
import textwrap
from datetime import datetime
import warnings
from collections import namedtuple
import glob

# third party imports
import pandas as pd
from h5py.h5py_warnings import H5pyDeprecationWarning
from dask.distributed import Client, as_completed

# local imports
from gmprocess.utils.args import add_shared_args
from gmprocess.io.fetch_utils import (get_events, update_config,
                                      save_shakemap_amps, download,
                                      draw_stations_map)
from gmprocess.utils.logging import setup_logger
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.waveform_processing.processing import process_streams
from gmprocess.io.report import build_report_latex
from gmprocess.utils.plot import summary_plots, plot_regression, plot_moveout
from gmprocess.utils.config import get_config
from gmprocess.utils.tables import set_precisions
from gmprocess.utils.constants import \
    DEFAULT_FLOAT_FORMAT, DEFAULT_NA_REP, TAG_FMT, NON_IMT_COLS, WORKSPACE_NAME


class MyFormatter(argparse.RawTextHelpFormatter,
                  argparse.ArgumentDefaultsHelpFormatter):
    pass


def format_helptext(text):
    '''Format help text, including wrapping.
    '''
    return '\n'.join(textwrap.wrap(text))


def append_file(files_created, tag, filename):
    if tag in files_created:
        files_created[tag].append(filename)
    else:
        files_created[tag] = [filename]


def process_event(event, outdir, pcommands,
                  config, input_directory,
                  process_tag, files_created, output_format,
                  status, recompute_metrics, export_dir=None):

    # setup logging to write to the input logfile
    argthing = namedtuple('args', ['debug', 'quiet'])
    args = argthing(debug=True, quiet=False)
    setup_logger(args)

    logger = logging.getLogger()
    stream_handler = logger.handlers[0]
    logfile = os.path.join(outdir, '%s.log' % event.id)
    fhandler = logging.FileHandler(logfile)
    logger.removeHandler(stream_handler)
    logger.addHandler(fhandler)

    event_dir = os.path.join(outdir, event.id)
    if not os.path.exists(event_dir):
        os.makedirs(event_dir)

    workname = os.path.join(event_dir, WORKSPACE_NAME)
    workspace_exists = os.path.isfile(workname)
    workspace_has_processed = False
    workspace = None
    processing_done = False

    if workspace_exists:
        workspace = StreamWorkspace.open(workname)
        labels = workspace.getLabels()
        if len(labels):
            labels.remove('unprocessed')
        elif 'assemble' not in pcommands:
            print('No data in workspace. Please run assemble.')
            sys.exit(1)

        if len(labels) == 1:
            process_tag = labels[0]
            workspace_has_processed = True
        else:
            if 'process' not in pcommands:
                fmt = '\nThere are %i sets of processed data in %s.'
                tpl = (len(labels), workname)
                print(fmt % tpl)
                print(('This software can only handle one set of '
                       'processed data. Exiting.\n'))
                sys.exit(1)

    download_done = False

    # Need to initialize rstreams/pstreams
    rstreams = []
    pstreams = []

    rupture_file = None
    if 'assemble' in pcommands:
        logging.info('Downloading/loading raw streams...')
        workspace, workspace_file, rstreams, rupture_file = download(
            event, event_dir, config, input_directory)

        download_done = True
        append_file(files_created, 'Workspace', workname)

    else:
        if not workspace_exists:
            print('\nYou opted not to download or process from input.')
            print('No previous HDF workspace file could be found.')
            print('Try re-running with the assemble command with or ')
            print('without the --directory option.\n')
            sys.exit(1)
        if 'process' in pcommands:
            logging.info('Getting raw streams from workspace...')
            with warnings.catch_warnings():
                warnings.simplefilter("ignore",
                                      category=H5pyDeprecationWarning)
                rstreams = workspace.getStreams(
                    event.id, labels=['unprocessed'])
            download_done = True
        else:
            need_processed = set(['report', 'shakemap'])
            need_pstreams = len(need_processed.intersection(pcommands))
            if workspace_has_processed:
                if need_pstreams:
                    logging.info(
                        'Getting processed streams from workspace...')
                    with warnings.catch_warnings():
                        warnings.simplefilter(
                            "ignore", category=H5pyDeprecationWarning)
                        pstreams = workspace.getStreams(
                            event.id, labels=[process_tag])
                download_done = True
                processing_done = True

    if ('process' in pcommands
            and download_done
            and not processing_done
            and len(rstreams)):
        logging.info('Processing raw streams for event %s...' % event.id)
        pstreams = process_streams(rstreams, event, config=config)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore",
                                  category=H5pyDeprecationWarning)
            workspace.addStreams(event, pstreams, label=process_tag)
            workspace.calcMetrics(
                event.id, labels=[process_tag], config=config,
                streams=pstreams, stream_label=process_tag,
                rupture_file=rupture_file)
        processing_done = True

    if 'export' in pcommands:
        if export_dir is not None:
            if not os.path.isdir(export_dir):
                os.makedirs(export_dir)
            outdir = export_dir

        labels = workspace.getLabels()
        if 'unprocessed' not in labels:
            fmt = ('Workspace file "%s" appears to have no unprocessed '
                   'data. Skipping.')
            logging.info(fmt % workspace_file)
        else:
            labels.remove('unprocessed')
            if not labels:
                fmt = ('Workspace file "%s" appears to have no processed '
                       'data. Skipping.')
                logging.info(fmt % workspace_file)
            else:
                logging.info('Creating tables for event %s...', event.id)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore",
                                          category=H5pyDeprecationWarning)
                    if recompute_metrics:
                        del workspace.dataset.auxiliary_data.WaveFormMetrics
                        del workspace.dataset.auxiliary_data.StationMetrics
                        workspace.calcMetrics(
                            event.id, labels=labels, config=config,
                            rupture_file=rupture_file)
                    event_table, imc_tables, readmes = workspace.getTables(
                        labels[0], streams=pstreams, stream_label=process_tag)
                    ev_fit_spec, fit_readme = workspace.getFitSpectraTable(
                        event.id, labels[0], pstreams)

                # Set the precisions for the imc tables, event table, and
                # fit_spectra table before writing
                imc_tables_formatted = {}
                for imc, imc_table in imc_tables.items():
                    imc_tables_formatted[imc] = set_precisions(imc_table)
                event_table_formatted = set_precisions(event_table)
                df_fit_spectra_formatted = set_precisions(ev_fit_spec)

                if not os.path.isdir(outdir):
                    os.makedirs(outdir)

                filenames = ['events'] + \
                    [imc.lower() for imc in imc_tables_formatted.keys()] + \
                    [imc.lower() + '_README' for imc in readmes.keys()] + \
                    ['fit_spectra_parameters', 'fit_spectra_parameters_README']

                files = [event_table_formatted] + list(
                    imc_tables_formatted.values()) + list(
                    readmes.values()) + [df_fit_spectra_formatted, fit_readme]

                if output_format != 'csv':
                    output_format = 'xlsx'

                for filename, df in dict(zip(filenames, files)).items():
                    filepath = os.path.join(
                        outdir, filename + '.%s' % output_format)
                    if os.path.exists(filepath):
                        if 'README' in filename:
                            continue
                        else:
                            mode = 'a'
                            header = False
                    else:
                        mode = 'w'
                        header = True
                        append_file(files_created, 'Tables', filepath)
                    if output_format == 'csv':
                        df.to_csv(filepath, index=False,
                                  float_format=DEFAULT_FLOAT_FORMAT,
                                  na_rep=DEFAULT_NA_REP,
                                  mode=mode, header=header)
                    else:
                        df.to_excel(filepath, index=False,
                                    float_format=DEFAULT_FLOAT_FORMAT,
                                    na_rep=DEFAULT_NA_REP,
                                    mode=mode, header=header)

    if ('report' in pcommands
            and processing_done
            and len(pstreams)):
        logging.info(
            'Creating diagnostic plots for event %s...' % event.id)
        plot_dir = os.path.join(event_dir, 'plots')
        if not os.path.isdir(plot_dir):
            os.makedirs(plot_dir)
        for stream in pstreams:
            summary_plots(stream, plot_dir, event)

        mapfile = draw_stations_map(pstreams, event, event_dir)
        plot_moveout(pstreams, event.latitude, event.longitude,
                     file=os.path.join(event_dir, 'moveout_plot.png'))

        append_file(files_created, 'Station map', mapfile)
        append_file(files_created, 'Moveout plot', 'moveout_plot.png')

        logging.info(
            'Creating diagnostic report for event %s...' % event.id)
        # Build the summary report?
        build_conf = config['build_report']
        report_format = build_conf['format']
        if report_format == 'latex':
            report_file, success = build_report_latex(
                pstreams,
                event_dir,
                event,
                config=config
            )
        else:
            report_file = ''
            success = False
        if os.path.isfile(report_file) and success:
            append_file(files_created, 'Summary report', report_file)

    if 'provenance' in pcommands and processing_done and len(pstreams):
        logging.info(
            'Creating provenance table for event %s...' % event.id)
        with warnings.catch_warnings():
            warnings.simplefilter(
                "ignore", category=H5pyDeprecationWarning)
            provdata = workspace.getProvenance(
                event.id, labels=[process_tag])
        if output_format == 'csv':
            csvfile = os.path.join(event_dir, 'provenance.csv')
            append_file(files_created, 'Provenance', csvfile)
            provdata.to_csv(csvfile)
        else:
            excelfile = os.path.join(event_dir, 'provenance.xlsx')
            append_file(files_created, 'Provenance', excelfile)
            provdata.to_excel(excelfile, index=False)

    if 'shakemap' in pcommands and processing_done and len(pstreams):
        logging.info(
            'Creating shakemap table for event %s...' % event.id)
        shakemap_file, jsonfile = save_shakemap_amps(
            pstreams, event, event_dir)
        append_file(files_created, 'shakemap', shakemap_file)
        append_file(files_created, 'shakemap', jsonfile)

    if status and processing_done and len(pstreams):
        if status == 'short':
            index = 'Failure reason'
            col = ['Number of records']
        elif status == 'long':
            index = 'Station ID'
            col = ['Failure reason']
        elif status == 'net':
            index = 'Network'
            col = ['Number of passed records', 'Number of failed records']

        status_info = pstreams.get_status(status)
        status_info.to_csv(os.path.join(event_dir, 'status.csv'), header=col,
                           index_label=index)

    # since we don't know how many events users will be processing,
    # let's guard against memory issues by clearing out the big data
    # structures
    workspace.close()

    logging.info('Finishing event %s' % event.id)

    return workname


def find_workspace_files(outdir):
    workspace_files = []
    for root, dirs, files in os.walk(outdir):
        for tfile in files:
            if tfile.endswith('.hdf'):
                fullfile = os.path.join(root, tfile)
                workspace_files.append(fullfile)
    return workspace_files


def main():
    logging.warning("gmprocess2 (formerly gmprocess) is deprecated "
                    "and will be removed soon.")
    logging.warning("Please use gmrecords instead.")
    description = '''
    Download, process, and extract metrics from raw ground motion data.

This program will allow the user to:
   - download raw data from a number of sources, including:
   - Any FDSN provider which serves waveform data
   - Japan's KNET/KikNet repository (requires login info)
   - ...
'''
    parser = argparse.ArgumentParser(
        description=description, formatter_class=MyFormatter)

    # ***** Required arguments
    parser.add_argument('-o', '--output-directory', help='Output directory',
                        metavar="DIRECTORY", action='store', type=str,
                        required=True, dest='outdir')

    # ***** Command arguments
    help_assemble = format_helptext(
        'Download data from all available online sources, or load raw data '
        'from files if --directory is selected.'
    )
    parser.add_argument('--assemble', help=help_assemble,
                        action='store_true', dest='assemble')

    help_process = format_helptext(
        'Process data using steps defined in configuration file.'
    )
    parser.add_argument('--process', help=help_process,
                        action='store_true', dest='process')

    help_report = format_helptext(
        'Create a summary report for each event specified.'
    )
    parser.add_argument('--report', help=help_report, action='store_true',
                        dest='report')

    help_provenance = format_helptext(
        'Generate provenance table in --format format.'
    )
    parser.add_argument('--provenance', help=help_provenance,
                        action='store_true', dest='provenance')

    help_export = format_helptext(
        'Generate metrics tables (NGA-style "flat" files) for all events '
        'and IMCs.'
    )
    parser.add_argument('--export', help=help_export, action='store_true',
                        dest='export')

    help_export_dir = format_helptext('Specify an alternate directory for the '
                                      'export files, which defaults to the '
                                      'directory above event directory.')
    parser.add_argument('--export-dir', help=help_export_dir)

    help_shakemap = format_helptext(
        'Generate ShakeMap-friendly peak ground motions table.'
    )
    parser.add_argument('--shakemap', help=help_shakemap,
                        action='store_true', dest='shakemap')

    # # ***** Optional arguments
    group = parser.add_mutually_exclusive_group(required=False)
    help_eventids = format_helptext(
        'ComCat Event IDs'
    )
    group.add_argument('--eventids', help=help_eventids, nargs='+')

    help_textfile = format_helptext(
        'Text file containing lines of ComCat Event IDs or event '
        'information (ID TIME LAT LON DEPTH MAG)'
    )
    group.add_argument(
        '--textfile', help=help_textfile, action='store',
        dest='textfile'
    )

    help_event = format_helptext(
        'Single event information as ID TIME(YYYY-MM-DDTHH:MM:SS) '
        'LAT LON DEP MAG'
    )
    group.add_argument(
        '--eventinfo', help=help_event, type=str, nargs=7,
        metavar=('ID', 'TIME', 'LAT', 'LON', 'DEPTH', 'MAG', 'MAG_TYPE')
    )

    help_dir = format_helptext(
        'Sidestep online data retrieval and get from local directory instead. '
        'This is the path where data already exists. Must organized in a '
        '\'raw\' directory, within directories with names as the event IDs. '
        'For example, if `--directory` is \'proj_dir\' and you have data for '
        'event id \'abc123\' then the raw data to be read in should be '
        'located in `proj_dir/abc123/raw/`.'
    )
    parser.add_argument(
        '--directory', help=help_dir, action='store',
        dest='directory'
    )

    help_format = format_helptext(
        'Output format for tabular information'
    )
    parser.add_argument(
        '--format', help=help_format,
        choices=['excel', 'csv'], default='csv', dest='format'
    )

    help_tag = format_helptext(
        'Processing label (single word, no spaces) to attach to processed '
        'files. Defaults to the current time in YYYYMMDDHHMMSS format.'
    )
    parser.add_argument(
        '--process-tag', help=help_tag, action='store',
        type=str, dest='process_tag'
    )

    help_config = format_helptext(
        'Supply custom configuration file'
    )
    parser.add_argument(
        '--config', help=help_config, action='store',
        type=str, dest='config'
    )

    help_recompute = format_helptext(
        'Recompute metrics (i.e. from new config)'
    )
    parser.add_argument(
        '--recompute-metrics', help=help_recompute,
        action='store_true', dest='recompute_metrics'
    )

    help_logfile = format_helptext(
        'Supply file name to store processing log info.'
    )
    parser.add_argument(
        '--log-file', help=help_logfile, action='store',
        dest='log_file'
    )

    nhelpstr = 'Number of parallel processes to run over events.'
    parser.add_argument(
        '-n', '--num-processes', default=0,
        type=int, help=nhelpstr
    )

    help_status = format_helptext(
        'Output failure information, either in short form ("short"), '
        'long form ("long"), or network form ("net"). '
        'short: Two column table, where the columns are "failure reason" and '
        '"number of records". net: Three column table where the columns are '
        '"network", "number passed", and "number failed". long: Two column '
        'table, where columns are "station ID" and "failure reason".')
    parser.add_argument(
        '--status', choices=['short', 'long', 'net'], dest='status',
        help=help_status
    )

    # ***** Shared arguments
    parser = add_shared_args(parser)
    args = parser.parse_args()

    tstart = datetime.now()
    # get the process tag from the user or define by current datetime
    process_tag = args.process_tag or datetime.utcnow().strftime(TAG_FMT)

    # config handling
    configfile = args.config
    if configfile is not None:
        config = update_config(configfile)
        if config is None:
            print('\nCustom config file %s is invalid. Exiting.' % configfile)
            sys.exit(1)

    else:
        config = get_config()

    outdir = args.outdir
    eventids = args.eventids
    textfile = args.textfile
    eventinfo = args.eventinfo
    input_directory = args.directory

    # get a list of ScalarEvent objects from one of the inputs
    events = get_events(
        eventids, textfile, eventinfo, input_directory, outdir
    )
    if not events:
        print('No event information was found. Exiting.')
        sys.exit(1)

    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    workspace_files = []
    files_created = {}

    logbase = 'gmprocess_batch_log_'
    logfmt = logbase + '%i.txt'

    # compare list of all commands with list of actual commands
    process_commands = set([
        'assemble', 'process', 'report', 'shakemap', 'provenance', 'export'
    ])
    pcommands = []
    if args.assemble:
        pcommands.append('assemble')
    if args.process:
        pcommands.append('process')
    if args.provenance:
        pcommands.append('provenance')
    if args.report:
        pcommands.append('report')
    if args.shakemap:
        pcommands.append('shakemap')
    if args.export:
        pcommands.append('export')

    if len(process_commands.intersection(set(pcommands))) > 0:
        if args.num_processes:
            # parallelize processing on events using forked processes
            try:
                client = Client(n_workers=args.num_processes)
            except OSError:
                sys.stderr.write("Could not create a dask client.\n")
                sys.exit(1)

            # Need a dict holding all args that do not change across calls
            _argdict_ = {
                'outdir': outdir,
                'pcommands': pcommands,
                'config': config,
                'input_directory': input_directory,
                'process_tag': process_tag,
                'files_created': files_created,
                'output_format': args.format,
                'status': args.status,
                'recompute_metrics': args.recompute_metrics,
                'export_dir': args.export_dir
            }

            def dask_process_event(event):
                """
                Wrapper function for multiprocessing of process_event method.
                """
                workname = process_event(event, **_argdict_)
                return event, workname

            futures = client.map(dask_process_event, events)

            for _, result in as_completed(futures, with_results=True):
                print(
                    'Completed event: %s, %s' %
                    (result[0].id, str(result[1]))
                )

        else:
            logfile = os.path.join(outdir, logfmt % os.getpid())
            for event in events:
                workname = process_event(
                    event, outdir, pcommands,
                    config, input_directory, process_tag,
                    files_created, args.format, args.status,
                    args.recompute_metrics,
                    export_dir=args.export_dir)
                workspace_files.append(workname)
                print(
                    'Completed event: %s, %s' %
                    (event.id, str(workname))
                )

    # logging
    logger = None
    setup_logger(args)
    if args.log_file:
        logger = logging.getLogger()
        stream_handler = logger.handlers[0]
        fhandler = logging.FileHandler(args.log_file)
        logger.removeHandler(stream_handler)
        logger.addHandler(fhandler)

    # transfer the logfile contents into our global logger
    # first get the handler
    if logger is None:
        logger = logging.getLogger()
    handler = logger.handlers[0]
    # then get the current formatter
    old_format = handler.formatter
    handler.setFormatter(logging.Formatter('%(message)s'))
    logfiles = glob.glob(os.path.join(outdir, logbase + '*'))
    for logfile in logfiles:
        with open(logfile, 'rt', encoding='utf-8') as logobj:
            for line in logobj.readlines():
                logging.info(line.strip())
        os.remove(logfile)

    # reset handler back to original formatter
    handler.setFormatter(old_format)

    logging.info('%i workspace files created' % len(workspace_files))

    if 'export' in pcommands:

        imc_table_names = [file.replace('_README', '')
                           for file in os.listdir(outdir) if 'README' in file]
        imc_tables = {}
        for file in imc_table_names:
            imc_tables[file.replace('.%s' % args.format, '')] = pd.read_csv(
                os.path.join(outdir, file))
            if 'fit_spectra_parameters' in imc_tables:
                del imc_tables['fit_spectra_parameters']

        # TODO - where is this being written? Is it a requirement?
        event_file = os.path.join(outdir, 'events.csv')
        if os.path.isfile(event_file):
            event_table = pd.read_csv(event_file)
        else:
            data = [{'id': event.id, 'magnitude': event.magnitude}]
            event_table = pd.DataFrame(data=data)

        # make a regression plot of the most common imc/imt combination we
        # can find
        if not len(imc_tables):
            msg = '''No IMC tables found. It is likely that no streams
            passed checks. If you created reports for the events you
            have been processing, check those to see if this is the case,
            then adjust your configuration as necessary to process the data.
            '''
            logging.warning(msg)
        else:
            pref_imcs = ['rotd50.0',
                         'greater_of_two_horizontals',
                         'h1', 'h2', ]
            pref_imts = ['PGA', 'PGV', 'SA(1.0)']
            found_imc = None
            found_imt = None
            for imc in pref_imcs:
                if imc in imc_tables:
                    for imt in pref_imts:
                        if imt in imc_tables[imc].columns:
                            found_imt = imt
                            found_imc = imc
                            break
                    if found_imc:
                        break
            # now look for whatever IMC/IMTcombination we can find
            if imc_tables and not found_imc:
                found_imc = list(imc_tables.keys())[0]
                table_cols = set(imc_tables[found_imc].columns)
                imtlist = list(table_cols - NON_IMT_COLS)
                found_imt = imtlist[0]

            if found_imc and found_imt:
                pngfile = '%s_%s.png' % (found_imc, found_imt)
                regression_file = os.path.join(outdir, pngfile)
                plot_regression(event_table, found_imc,
                                imc_tables[found_imc],
                                found_imt,
                                regression_file,
                                distance_metric='EpicentralDistance',
                                colormap='viridis_r')
                append_file(files_created,
                            'Multi-event regression plot', regression_file)

    if args.status:
        if args.status == 'short':
            index_col = 'Failure reason'
        elif args.status == 'long':
            index_col = 'Station ID'
        elif args.status == 'net':
            index_col = 'Network'
        statuses = []
        for event in events:
            status_path = os.path.join(outdir, event.id, 'status.csv')
            if os.path.exists(status_path):
                status = pd.read_csv(status_path, index_col=index_col)
                if args.status == 'long':
                    status['Event ID'] = event.id
                statuses.append(status)
        if statuses:
            comp_status_path = os.path.join(outdir, 'complete_status.csv')
            if args.status == 'long':
                for idx, status in enumerate(statuses):
                    if idx == 0:
                        status.to_csv(comp_status_path, mode='w')
                    else:
                        status.to_csv(comp_status_path, mode='a', header=False)
            else:
                df_status = pd.concat(statuses)
                df_status = df_status.groupby(df_status.index).sum()
                df_status.to_csv(comp_status_path)
            append_file(files_created, 'Complete status', comp_status_path)

    print('\nThe following files have been created:')
    for file_type, file_list in files_created.items():
        print('File type: %s' % file_type)
        for fname in file_list:
            print('\t%s' % fname)

    tend = datetime.now()
    dt = (tend - tstart).total_seconds()
    minutes = dt // 60
    seconds = dt % 60
    fmt = '\nElapsed processing time: %i minutes, %i seconds.'
    print(fmt % (minutes, seconds))

    print('\nProcessing is complete.\n')


if __name__ == '__main__':
    main()

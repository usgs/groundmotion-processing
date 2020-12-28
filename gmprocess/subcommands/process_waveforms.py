import os
import logging
from datetime import datetime

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.io.fetch_utils import get_events
from gmprocess.waveform_processing.processing import process_streams
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.utils.constants import TAG_FMT


class ProcessWaveformsModule(SubcommandModule):
    """Process waveform data.
    """
    command_name = 'process_waveforms'
    aliases = ('process', )

    arguments = [
        {
            'short_flag': '-e',
            'long_flag': '--eventid',
            'help': ('Comcat event ID. If None (default) all events in '
                     'project data directory will be used.'),
            'type': str,
            'default': None,
            'nargs': '+'
        }, {
            'short_flag': '-l',
            'long_flag': '--label',
            'help': ('Processing label (single word, no spaces) to attach to '
                     'processed files. Defaults to the current time in '
                     'YYYYMMDDHHMMSS format.'),
            'type': str,
            'default': None,
        }, {
            'short_flag': '-n',
            'long_flag': '--num-processes',
            'help': 'Number of parallel processes to run over events.',
            'type': int,
            'default': 0,
        }
    ]

    def main(self, gmp):
        """Process data using steps defined in configuration file.

        Args:
            gmp: GmpApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)

        events = get_events(
            eventids=gmp.args.eventid,
            textfile=None,
            eventinfo=None,
            directory=gmp.data_path,
            outdir=None
        )

        # get the process tag from the user or define by current datetime
        process_tag = gmp.args.label or datetime.utcnow().strftime(TAG_FMT)
        logging.info('Processing tag: %s' % process_tag)

        for event in events:
            event_dir = os.path.join(gmp.data_path, event.id)
            workname = os.path.join(event_dir, 'workspace.hdf')
            if not os.path.isfile(workname):
                logging.info(
                    'No workspace file found for event %s. Please run '
                    'subcommand \'assemble\' to generate workspace file.')
                logging.info('Continuing to next event.')
                continue
            workspace = StreamWorkspace.open(workname)

            rstreams = workspace.getStreams(
                event.id, labels=['unprocessed'])

            logging.info('Processing \'%s\' streams for event %s...'
                         % ('unprocessed', event.id))
            pstreams = process_streams(rstreams, event, config=gmp.conf)
            workspace.addStreams(event, pstreams, label=process_tag)
            workspace.close()

        logging.info('Added processed waveforms to event workspace files '
                     'with tag \'%s\'.' % process_tag)
        logging.info('No new files created.')

import os
import logging

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.io.fetch_utils import download
from gmprocess.io.fetch_utils import get_events


class AssembleModule(SubcommandModule):
    """
    Assemble raw data and organize it into an ASDF file.
    """
    command_name = 'assemble'

    arguments = [
        {
            'short_flag': '-e',
            'long_flag': '--eventid',
            'help': 'Comcat event ID.',
            'type': str,
            'default': None,
            'nargs': '+'
        }, {
            'short_flag': '-t',
            'long_flag': '--textfile',
            'help': (
                'Text file containing lines of ComCat Event IDs or event '
                'information (ID TIME LAT LON DEPTH MAG).'),
            'type': str,
            'default': None,
            'nargs': 1
        }, {
            'long_flag': '--info',
            'help': (
                'Single event information as ID TIME(YYYY-MM-DDTHH:MM:SS) '
                'LAT LON DEP MAG.'),
            'type': str,
            'default': None,
            'nargs': 7,
            'metavar': ('ID', 'TIME', 'LAT', 'LON', 'DEPTH', 'MAG', 'MAG_TYPE')
        }, {
            'short_flag': '-o',
            'long_flag': '--overwrite',
            'help': (
                'Overwrite any existing workspace files. Previous results '
                'will be lost.'),
            'default': False,
            'action': 'store_true'
        }
    ]

    def main(self, gmp):
        """
        Assemble data and organize it into an ASDF file.

        Args:
            gmp: GmpApp instance.
        """
        logging.info('Running %s.' % self.command_name)
        input_directory = gmp.data_dir
        outdir = input_directory
        events = get_events(
            eventids=gmp.args.eventid,
            textfile=gmp.args.textfile,
            eventinfo=gmp.args.info,
            directory=input_directory,
            outdir=outdir
        )
        logging.info('Number of events to assemble: %s' % len(events))
        for event in events:
            logging.info('Starting event: %s' % event.id)
            event_dir = os.path.join(input_directory, event.id)
            if not os.path.exists(event_dir):
                os.makedirs(event_dir)
            workname = os.path.join(event_dir, 'workspace.hdf')
            workspace_exists = os.path.isfile(workname)
            if workspace_exists:
                logging.info("ASDF exists: %s" % workname)
                if not gmp.args.overwrite:
                    logging.info("The overwrite argument not selected.")
                    logging.info("No action taken for %s." % event.id)
                    continue
                else:
                    logging.info(
                        "Removing existing ASDF file: %s" % workname
                    )
                    os.remove(workname)
            workspace, workspace_file, rstreams, rupture_file = download(
                event, event_dir, gmp.conf, input_directory)

        # download_done = True
        # append_file(files_created, 'Workspace', workname)

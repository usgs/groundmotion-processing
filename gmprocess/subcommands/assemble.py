import os
import logging

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.io.fetch_utils import download
from gmprocess.io.fetch_utils import get_events


class AssembleModule(SubcommandModule):
    """Assemble raw data and organize it into an ASDF file.
    """
    command_name = 'assemble'

    arguments = [
        ARG_DICTS['eventid'], {
            'short_flag': '-t',
            'long_flag': '--textfile',
            'help': (
                'Text file containing lines of ComCat Event IDs or event '
                'information (ID TIME LAT LON DEPTH MAG).'),
            'type': str,
            'default': None
        }, {
            'long_flag': '--info',
            'help': (
                'Single event information as ID TIME(YYYY-MM-DDTHH:MM:SS) '
                'LAT LON DEP MAG.'),
            'type': str,
            'default': None,
            'nargs': 7,
            'metavar': ('ID', 'TIME', 'LAT', 'LON', 'DEPTH', 'MAG', 'MAG_TYPE')
        },
        ARG_DICTS['overwrite'], {
            'short_flag': '-d',
            'long_flag': '--data-source',
            'help': (
                'Where to look for data. If None (default), assemble raw data '
                'already present in the project directory; If "download", '
                'use online data fetches; Or provide a path to a directory '
                'containing data'),
            'type': str,
            'default': None
        }
    ]

    def main(self, gmp):
        """
        Assemble data and organize it into an ASDF file.

        Args:
            gmp: GmpApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)

        if gmp.args.data_source is None:
            # Use project directory from config
            temp_dir = gmp.data_path
            if not os.path.isdir(temp_dir):
                raise OSError('No such directory: %s' % temp_dir)
        elif gmp.args.data_source == 'download':
            temp_dir = None
        else:
            temp_dir = gmp.args.data_source
            if not os.path.isdir(temp_dir):
                raise OSError('No such directory: %s' % temp_dir)

        # NOTE: as currently written, `get_events` will do the following,
        #  **stopping** at the first condition that is met:
        #     1) Use event ids if event id is not None
        #     2) Use textfile if it is not None
        #     3) Use event info if it is not None
        #     4) Use directory if it is not None
        #     5) Use outdir if it is not None
        # So in order to ever make use of the 'outdir' argument, we need to
        # set 'directory' to None, but otherwise set it to proj_data_path.
        #
        # This whole thing is really hacky and should be refactored!!
        events = get_events(
            eventids=gmp.args.eventid,
            textfile=gmp.args.textfile,
            eventinfo=gmp.args.info,
            directory=temp_dir,
            outdir=gmp.data_path
        )
        logging.info('Number of events to assemble: %s' % len(events))
        for event in events:
            logging.info('Starting event: %s' % event.id)
            event_dir = os.path.join(gmp.data_path, event.id)
            if not os.path.exists(event_dir):
                os.makedirs(event_dir)
            workname = os.path.join(event_dir, 'workspace.hdf')
            workspace_exists = os.path.isfile(workname)
            if workspace_exists:
                logging.info("ASDF exists: %s" % workname)
                if not gmp.args.overwrite:
                    logging.info("The --overwrite argument not selected.")
                    logging.info("No action taken for %s." % event.id)
                    continue
                else:
                    logging.info(
                        "Removing existing ASDF file: %s" % workname
                    )
                    os.remove(workname)

            # Todo: probably want to break up `download` into finer steps to
            # call here. Also, there are files created besides workspace
            # that are not getting tracked (e.g., raw data plots, event.json)
            workspace, _, _, _ = download(
                event=event,
                event_dir=event_dir,
                config=gmp.conf,
                directory=temp_dir
            )
            workspace.close()
            self.append_file('Workspace', workname)
        self._summarize_files_created()

import os
import logging

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.io.fetch_utils import get_events, save_shakemap_amps
from gmprocess.io.asdf.stream_workspace import StreamWorkspace


class ExportShakeMapModule(SubcommandModule):
    """Export files for ShakeMap input.
    """
    command_name = 'export_shakemap'
    aliases = ('shakemap', )

    arguments = [
        ARG_DICTS['eventid'],
        ARG_DICTS['label']
    ]

    def main(self, gmp):
        """Export files for ShakeMap input.

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

        self.label = gmp.args.label

        for event in events:
            self.eventid = event.id
            logging.info(
                'Creating shakemap files for event %s...' % self.eventid)

            event_dir = os.path.join(gmp.data_path, event.id)
            workname = os.path.join(event_dir, 'workspace.hdf')
            if not os.path.isfile(workname):
                logging.info(
                    'No workspace file found for event %s. Please run '
                    'subcommand \'assemble\' to generate workspace file.'
                    % event.id)
                logging.info('Continuing to next event.')
                continue

            self.workspace = StreamWorkspace.open(workname)
            self._get_pstreams()
            self.workspace.close()

            shakemap_file, jsonfile = save_shakemap_amps(
                self.pstreams, event, event_dir)
            self.append_file('shakemap', shakemap_file)
            self.append_file('shakemap', jsonfile)

        self._summarize_files_created()

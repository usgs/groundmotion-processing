#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.io.fetch_utils import download
from gmprocess.utils.constants import WORKSPACE_NAME


class DownloadModule(SubcommandModule):
    """Download data and organize it in the project data directory.
    """
    command_name = 'download'

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
        }
    ]

    def main(self, gmrecords):
        """
        Download data and organize it in the project data directory.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)
        self.gmrecords = gmrecords
        self._check_arguments()

        self._get_events()

        logging.info('Number of events to download: %s' % len(self.events))
        for event in self.events:
            logging.info('Starting event: %s' % event.id)
            event_dir = os.path.join(gmrecords.data_path, event.id)
            if not os.path.exists(event_dir):
                os.makedirs(event_dir)

            _ = download(
                event=event,
                event_dir=event_dir,
                config=gmrecords.conf,
                directory=None,
                create_workspace=False,
                stream_collection=False
            )

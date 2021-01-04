#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from abc import ABC, abstractmethod
import logging

from gmprocess.io.fetch_utils import get_events


class SubcommandModule(ABC):
    """gmprocess base module.
    """

    @property
    @abstractmethod
    def command_name(self):
        """
        Name of subcommand: string, all lowercase.
        """
        raise NotImplementedError

    """Tuple class variable of subcommand aliases.
    """
    aliases = ()

    def __init__(self):
        """Dictionary instance variable to track files created by module.
        """
        self.files_created = {}

    @property
    @abstractmethod
    def arguments(self):
        """A list of dicts for each argument of the subcommands. Each dict
        should have the following keys: short_flag, long_flag, help, action,
        default.
        """
        raise NotImplementedError

    @abstractmethod
    def main(self, gmp):
        """
        All main methods should take one gmp object (a GmpApp instance).
        """
        raise NotImplementedError

    def append_file(self, tag, filename):
        """Convenience method to add file via tag to self.files_created.
        """
        if tag in self.files_created:
            self.files_created[tag].append(filename)
        else:
            self.files_created[tag] = [filename]

    def _summarize_files_created(self):
        if len(self.files_created):
            print('\nThe following files have been created:')
            for file_type, file_list in self.files_created.items():
                print('File type: %s' % file_type)
                for fname in file_list:
                    print('\t%s' % fname)
        else:
            print('No new files created.')

    def _get_pstreams(self):
        """Convenience method for recycled code.
        """
        labels = self.workspace.getLabels()
        if len(labels):
            labels.remove('unprocessed')
        else:
            logging.info('No processed waveform data in workspace. Please '
                         'run assemble.')
            sys.exit(1)

        # If there are more than 1 processed labels, prompt user to select
        # one.
        if (len(labels) > 1) and (self.gmp.args.label is None):
            print('\nWhich label do you want to use?')
            for lab in labels:
                print('\t%s' % lab)
            tmplab = input('> ')
            if tmplab not in labels:
                print('%s not a valid label. Exiting.' % tmplab)
                sys.exit(1)
            else:
                self.gmp.args.label = tmplab
        elif self.gmp.args.label is None:
            self.gmp.args.label = labels[0]

        self.pstreams = self.workspace.getStreams(
            self.eventid, labels=[self.gmp.args.label])

    def _get_events(self):
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
        # This whole thing is really hacky and should probably be completely
        # rewritten.
        if hasattr(self.gmp.args, 'data_source'):
            if self.gmp.args.data_source is None:
                # Use project directory from config
                temp_dir = self.gmp.data_path
                if not os.path.isdir(temp_dir):
                    raise OSError('No such directory: %s' % temp_dir)
            elif self.gmp.args.data_source == 'download':
                temp_dir = None
            else:
                temp_dir = self.gmp.args.data_source
                if not os.path.isdir(temp_dir):
                    raise OSError('No such directory: %s' % temp_dir)
            self.download_dir = temp_dir
        else:
            self.download_dir = None

        info = self.gmp.args.info if hasattr(self.gmp.args, 'info') else None
        tfile = self.gmp.args.textfile if \
            hasattr(self.gmp.args, 'textfile') else None
        self.events = get_events(
            eventids=self.gmp.args.eventid,
            textfile=tfile,
            eventinfo=info,
            directory=self.download_dir,
            outdir=self.gmp.data_path
        )

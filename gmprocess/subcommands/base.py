import sys
from abc import ABC, abstractmethod
import logging


from gmprocess.utils.logging import setup_logger


class SubcommandModule(ABC):
    """
    gmprocess base module.
    """

    @property
    @abstractmethod
    def command_name(self):
        """
        Name of subcommand: string, all lowercase.
        """
        raise NotImplementedError

    """
    Tuple class variable of subcommand aliases.
    """
    aliases = ()

    def __init__(self):
        """
        Dictionary instance variable to track files created by module.
        """
        self.files_created = {}

    @property
    @abstractmethod
    def arguments(self):
        """
        A list of dicts for each argument of the subcommands. Each dict should
        have the following keys: short_flag, long_flag, help, action, default.
        """
        raise NotImplementedError

    @abstractmethod
    def main(self, gmp):
        """
        All main methods should take one gmp object, that is a GmpApp instance.
        """
        raise NotImplementedError

    def append_file(self, tag, filename):
        """
        Convenience method to add file via tag to self.files_created
        """
        if tag in self.files_created:
            self.files_created[tag].append(filename)
        else:
            self.files_created[tag] = [filename]

    def _summarize_files_created(self):
        print('\nThe following files have been created:')
        for file_type, file_list in self.files_created.items():
            print('File type: %s' % file_type)
            for fname in file_list:
                print('\t%s' % fname)

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
        if (len(labels) > 1) and (self.label is None):
            print('\nWhich label do you want to use?')
            for lab in labels:
                print('\t%s' % lab)
            tmplab = input('> ')
            if tmplab not in labels:
                print('%s not a valid label. Exiting.' % tmplab)
                sys.exit(1)
            else:
                self.label = tmplab
        else:
            self.label = labels[0]

        self.pstreams = self.workspace.getStreams(
            self.eventid, labels=[self.label])

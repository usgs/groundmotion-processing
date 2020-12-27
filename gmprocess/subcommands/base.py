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

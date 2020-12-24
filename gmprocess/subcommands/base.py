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
        Name of subcommand. Should be a string, all lowercase.
        """
        raise NotImplementedError

    """
    Tuple of subcommand aliases.
    """
    aliases = ()

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

#!/usr/bin/env python
"""
Python script used to query information about the ASDF workspace stored as
an HDF5 file.
"""


# stdlib imports
import argparse
import textwrap
import sys

# third party imports
import h5py

# local imports
from gmprocess.io.asdf.utils import TallyStorage

INDENT = " " * 4


def format_helptext(text):
    """Format help text, including wrapping."""
    return "\n".join(textwrap.wrap(text))


class WorkspaceApp(object):
    """Application for simple queries of the workspace."""

    def __init__(self):
        """Constructor"""
        self.h5 = None
        return

    def main(self, **kwargs):
        """Application driver.

        Keyword arguments:
            filename (str):
                Name of workspace file.

            describe (bool):
                Show summary of workspace contents.

            compute_storage (bool):
                Show storage used by workspace.
        """
        args = argparse.Namespace(**kwargs) if kwargs else self._parse_command_line()
        self.h5 = h5py.File(args.filename, "r")

        if args.describe:
            self.describe()

        if args.compute_storage:
            self.compute_storage()

        self.h5.close()
        return

    def describe(self):
        """Show a summary of the workspace contents.

        For groups the entire path is show. For datasets the name,
        dimensions, and type are shown.
        """

        def _print_dataset(name, dataset, level):
            """Print dataset information to stdout.

            Args:
                name (str):
                    Name of the dataset.

                dataset (h5py.Dataset):
                    HDF5 dataset
            """
            shape = ",".join([str(d) for d in dataset.shape])
            indent = INDENT * min(level, 1)
            print(f"{indent}{name} dims=({shape}) type={dataset.dtype.name}")
            return

        def _print_group(items, level):
            """Print group information to stdout.

            Args:
                items (iterable):
                   Iterable object of items in a group.
            """
            for name, item in items:
                if isinstance(item, h5py.Group):
                    print(item.name)
                    _print_group(item.items(), level + 1)
                elif isinstance(item, h5py.Dataset):
                    _print_dataset(name, item, level)
                else:
                    raise ValueError(
                        "HDF5 item '{}' is of type '{}', expected "
                        "'h5.Dataset' or 'h5.Group'".format(name, type(item))
                    )
            return

        _print_group(self.h5.items(), level=0)
        return

    def compute_storage(self):
        """Compute the storage of items in a workspace."""
        GROUP_DETAIL = [
            "AuxiliaryData",
        ]

        def _print_subtotal(name, group, level=0):
            """Print the subtotal for a group to stdout.

            Args:
                name (str):
                    Name of group.

                group (h5py.Group):
                   HDF5 group.

                level (int):
                   Level of group in HDF5 hierarchy (root level is 0).
            """
            mb = group["total_bytes"] / float(2 ** 20)
            print(f"{INDENT * level}{name}: {mb:.3f} MB")
            for subgroup in group["groups"]:
                _print_subtotal(subgroup, group["groups"][subgroup], level + 1)
            return

        storage = TallyStorage(GROUP_DETAIL)
        (total_bytes, groups) = storage.compute_storage(
            self.h5.items(), store_subtotals=True
        )
        total = {
            "total_bytes": total_bytes,
            "groups": groups,
        }
        _print_subtotal("Total", total)
        return

    @staticmethod
    def _parse_command_line():
        """Parse command line arguments.

        Returns:
            argsparse.Namespace:
                Namespace with parsed arguments.
        """
        parser = argparse.ArgumentParser()

        help_filename = format_helptext("Name of workspace file.")
        parser.add_argument(
            "--filename",
            action="store",
            dest="filename",
            type=str,
            required=True,
            help=help_filename,
        )

        help_describe = format_helptext(
            "Print a summary of workspace contents to stdout. Similar to h5dump."
        )
        parser.add_argument(
            "--describe", action="store_true", dest="describe", help=help_describe
        )

        help_storage = format_helptext(
            "Print a summary of the workspace storage to stdout."
        )
        parser.add_argument(
            "--compute-storage",
            action="store_true",
            dest="compute_storage",
            help=help_storage,
        )
        if len(sys.argv) == 1:
            parser.print_help(sys.stderr)
            sys.exit(1)
        return parser.parse_args()


def main():
    WorkspaceApp().main()


if __name__ == "__main__":
    main()

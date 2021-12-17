"""Utilities for simple operations on an ASDF workspace.
"""

# third party imports
import h5py


class TallyStorage(object):
    """Tally storage used within each group."""

    def __init__(self, group_detail=None):
        """Constructor.

        Args:
            group_detail (list):
                List of group names for which to tally subgroups and
                datasets. By default only the storage is only reported
                for the top-level groups.
        """
        self.group_detail = group_detail if group_detail else []
        return

    @staticmethod
    def compute_dataset_storage(dataset):
        """Compute the storage used by a dataset.

        Args:
            dataset (h5py.Dataset):
                HDF5 dataset for which storage is computed.

        Returns:
            int:
                Storage of dataset in bytes.
        """
        assert isinstance(dataset, h5py.Dataset)
        return dataset.size * dataset.dtype.itemsize

    def compute_storage(self, items, store_subtotals=False):
        """Compute the storage for a group of items. By default only the total
        storage is stored.

        Args:
            items (iterable):
                Iterable object of items to compute total storage.

            store_subtotals (bool):
                Store storage for each item in items.

        Returns:
            int:
                Total storage of items, in bytes.

            dict:
                Dictionary of storage for items.
        """
        subtotal_bytes = 0
        storage = {}
        for name, item in items:
            if isinstance(item, h5py.Group):
                (item_bytes, item_groups) = self.compute_storage(
                    item.items(), store_subtotals=name in self.group_detail
                )
                if store_subtotals:
                    storage[name] = {
                        "total_bytes": item_bytes,
                        "groups": item_groups,
                    }
            elif isinstance(item, h5py.Dataset):
                item_bytes = self.compute_dataset_storage(item)
                if store_subtotals:
                    storage[name] = {"total_bytes": item_bytes, "groups": {}}
            else:
                raise ValueError(
                    "Group item '{}' is of type '{}', expected "
                    "'h5.Dataset' or 'h5.Group'".format(name, type(item))
                )
            subtotal_bytes += item_bytes
        return (subtotal_bytes, storage)

import os
import pkg_resources

from gmprocess.core.streamcollection import StreamCollection


def test_colocated():
    datapath = os.path.join('data', 'testdata', 'colocated_instruments')
    datadir = pkg_resources.resource_filename('gmprocess', datapath)
    sc = StreamCollection.from_directory(datadir)

    sc.select_colocated()
    assert sc.n_passed == 7
    assert sc.n_failed == 4

    # What if no preference is matched?
    sc = StreamCollection.from_directory(datadir)
    sc.select_colocated(preference=["XX"])
    assert sc.n_passed == 3
    assert sc.n_failed == 8


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_colocated()

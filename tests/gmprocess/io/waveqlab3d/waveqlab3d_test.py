#!/usr/bin/env python
"""Test waveqlab3d reader.
"""

# stdlib imports
import os

# third party imports
import numpy
import pkg_resources

from gmprocess.io.waveqlab3d.core import is_waveqlab3d, read_surface_waveqlab3d
from gmprocess.data.testdata.waveqlab3d.generate import (CartesianNativeEndian,
                                                         UTMBigEndian)


def l2_diff(dataE, data):
    """Compute L2 norm of difference between expected data (dataE) and test
    data (data).

    Args:
        dataE (numpy.array):
            Expected data.
        data (numpy.array):
            Test data.
    """
    return numpy.sum((dataE - data)**2)**0.5


def check_dims(dataE, data):
    """Verify dimensions match using assert.

    Args:
        dataE (numpy.array):
            Expected data.
        data (numpy.array):
            Test data.
    """
    assert len(dataE.shape) == len(data.shape)
    for dimE, dim in zip(dataE.shape, data.shape):
        assert dimE == dim


def check_parameters(metadata, stream):
    """Verify stream parameters.

    Args:
        metadata (dict):
            Metadata with expected parameters.
        stream (SurfaceStream):
            Surface stream to check.
    """
    start_time = stream.getStreamParam("starttime")
    assert metadata["start_time"] == start_time

    sampling_rate = stream.getStreamParam("sampling_rate")
    assert metadata["time_step"] == sampling_rate

    crs = stream.getStreamParam("crs")
    assert metadata["crs"] == crs


def check_stream(generator, stream):
    """Verify stream data matches expected data from generator.

    Args:
        generator (TestDataApp):
            Generator for test data.
        stream (SurfaceStream):
            Surface stream created by waveqlab3d reader.
    """
    TOLERANCE = 1.0e-6

    check_dims(generator.data, stream.data)
    assert l2_diff(generator.data, stream.data) < TOLERANCE

    check_dims(generator.geometry, stream.geometry)
    assert l2_diff(generator.geometry, stream.geometry) < TOLERANCE

    check_dims(generator.topology, stream.topology)
    assert l2_diff(generator.topology, stream.topology) < TOLERANCE

    check_parameters(generator.metadata, stream)


def test_cartesian():
    """Test function for data in Cartesian coordinate system.
    """
    data_path = os.path.join('data', 'testdata', 'waveqlab3d',
                             'fake_cartesian')
    data_fullpath = pkg_resources.resource_filename('gmprocess', data_path)

    generator = CartesianNativeEndian()
    filename = os.path.join(data_fullpath, generator.meta_filename)
    assert is_waveqlab3d(filename)

    stream = read_surface_waveqlab3d(filename, data_path=data_fullpath)
    check_stream(generator, stream)


def test_utm():
    """Test function for data in UTM coordinate system.
    """
    data_path = os.path.join('data', 'testdata', 'waveqlab3d', 'fake_utm')
    data_fullpath = pkg_resources.resource_filename('gmprocess', data_path)

    generator = UTMBigEndian()
    filename = os.path.join(data_fullpath, generator.meta_filename)
    assert is_waveqlab3d(filename)

    stream = read_surface_waveqlab3d(filename, data_path=data_fullpath)
    check_stream(generator, stream)


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_cartesian()
    test_utm()

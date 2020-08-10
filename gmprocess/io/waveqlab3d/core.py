"""Reader for surface waveforms produced by waveqlab3d ground-motion simulation
 software.

Waveqlab3d generates data files without any metadata, so we require a
YAML file with the missing metadata.

Example YAML file:

waveqlab3d:
  # Coordinate reference system as Proj parameters, WKT, or EPSG code.
  # Example is Cartersian coordinate system (East, North, Up).
  crs: >
    CS[Cartesian,3], AXIS["(X)",east],AXIS["(Y)",north],AXIS["(Z)",up],
    LENGTHUNIT["meter",1.0]

  # Origin of grid in CRS coordinate system
  origin_x: 0.0
  origin_y: 0.0

  # Endian type of floating point values in data files
  # ('little', 'big', 'native')
  endian_type: native

  # Template for forming filenames {component}=x,y,z
  filenames: drv4c50.Hslice1seis{component}dec

  # Number of grid points in the x and y directions.
  num_x: 10
  num_y: 15

  # Horizontal resolution in meters.
  horizontal_resolution: 100.0

  # Number of time steps and time step size (in seconds).
  num_timesteps: 101
  time_step: 0.05

  # Start time of data as UTC date/time (or None)
  start_time: None
"""


# stdlib imports
import os
import logging

# third party
import yaml
import numpy

# local imports
from gmprocess.surfacestream import SurfaceStream


def is_waveqlab3d(filename):
    """Check to see if file is a waveqlab3d file.

    Args:
        filename (str): Path to possible waveqlab3d metadata file.
    Returns:
        bool: True if waveqlab3d, False otherwise.
    """
    logging.debug("Checking if format is waveqlab3d.")
    try:
        with open(filename, 'rt') as f:
            metadata = yaml.load(f, Loader=yaml.FullLoader)
            if "waveqlab3d" in metadata:
                return True
        return False
    except:
        return False


def read_surface_waveqlab3d(filename, **kwargs):
    """Read surface waveforms waveqlab3d metadata file.

    Args:
        filename (str): Path to waveqlab3d file for surface waveforms.
        kwargs (ref):
            Other arguments will be ignored.
    Returns:
        SurfaceStream: Stream with surface waveform data.
    """
    ENDIAN_DTYPE = {
        "little": "<",
        "big": ">",
        "native": "="
    }
    COMPONENTS = ["x", "y", "z"]

    logging.debug("Starting read_surface_waveqlab3d.")
    data_path = kwargs.get('data_path', '.')

    if not is_waveqlab3d(filename):
        raise IOError('{} is not a valid waveqlab3d metadata file'.format(
            filename))

    with open(filename, 'rt') as f:
        metadata = yaml.load(f, Loader=yaml.FullLoader)["waveqlab3d"]

    endian_type = metadata["endian_type"] or "native"
    if endian_type not in ENDIAN_DTYPE:
        raise ValueError("Unrecognized endian type ({}) in {}. Expected "
                         "'little', 'big', or 'native'".format(
                             endian_type, filename))
    dtype = ENDIAN_DTYPE[endian_type]
    num_x = metadata["num_x"]
    num_y = metadata["num_y"]
    num_time = metadata["num_timesteps"]
    component_size = num_x * num_y * num_time
    num_components = len(COMPONENTS)

    data = numpy.zeros((num_time, num_x * num_y, num_components),
                       dtype=numpy.float64)
    for i, component in enumerate(COMPONENTS):
        filename = os.path.join(data_path, metadata["filenames"].format(
            component=component))
        data_c = _read_waveqlab3d_raw(filename, dtype)
        if len(data_c) != component_size:
            msg = "Data for component {component} has {total} values. "\
                "Expected: {total_expected} values (num_x: {num_x}, num_y: "\
                "{num_y}, num_timesteps: {num_time}".format(
                    component=component, total=len(data_c),
                    total_expected=component_size,
                    num_x=num_x, num_y=num_y, num_time=num_time)
            raise ValueError(msg)
        data[:, :, i] = data_c.reshape(num_time, num_x * num_y)

    # Convert m/s to cm/s
    data *= 100.0

    geometry = _create_geometry(metadata)
    topology = _create_topology(metadata)
    stream = SurfaceStream(data=data, geometry=geometry, topology=topology)
    stream.setStreamParam("starttime", metadata["start_time"])
    stream.setStreamParam("sampling_rate", metadata["time_step"])
    stream.setStreamParam("crs", metadata["crs"])
    return stream


def _read_waveqlab3d_raw(filename, endian_dtype):
    """Read raw waveqlab3d binary file.

    Args:
        filename (str):
            Filename of waveqlab3d file.
        endian_type (str):
            Endian type as numpy.dtype string. ("<" for little endian,
            ">" for big endian, "=" for native endian).
    """
    data = numpy.fromfile(filename, dtype="{}d".format(endian_dtype))
    return data


def _create_geometry(metadata):
    """Create surface geometry (coordinates of points in finite-difference
    grid).

    Args:
        metadata (dict):
            Metadata for waveqlab3d file.
    """
    origin_x = metadata["origin_x"]
    origin_y = metadata["origin_y"]
    horiz_res = metadata["horizontal_resolution"]
    num_x = metadata["num_x"]
    num_y = metadata["num_y"]

    x1 = origin_x + numpy.linspace(0, (num_x - 1) * horiz_res, num_x)
    y1 = origin_y + numpy.linspace(0, (num_y - 1) * horiz_res, num_y)
    x, y = numpy.meshgrid(x1, y1, indexing="xy")
    vertices = numpy.zeros((num_x * num_y, 3), dtype=numpy.float32)
    vertices[:, 0] = x.ravel()
    vertices[:, 1] = y.ravel()
    return vertices


def _create_topology(metadata):
    """Create surface topology (quadrilaterals connecting vertices of
    finite-difference grid).

    Args:
        metadata (dict):
            Metadata for waveqlab3d file.
    """
    num_x = metadata["num_x"]
    num_y = metadata["num_y"]
    cells = numpy.zeros(((num_x - 1) * (num_y - 1), 4), dtype=numpy.int64)
    i0 = numpy.linspace(0, num_x - 2, num_x - 1)
    i1 = i0 + 1
    i2 = num_x + i1
    i3 = num_x + i0
    for j in range(num_y - 1):
        c_start = (num_x - 1) * j
        c_end = c_start + num_x - 1
        cells[c_start:c_end, 0] = num_x * j + i0
        cells[c_start:c_end, 1] = num_x * j + i1
        cells[c_start:c_end, 2] = num_x * j + i2
        cells[c_start:c_end, 3] = num_x * j + i3
    return cells

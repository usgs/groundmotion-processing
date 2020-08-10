#!/usr/bin/env python3
"""Python script to generate fake waveqlab3d files for testing.
"""

# stdlib imports
import os

# third party imports
import yaml
import numpy


class TestDataApp(object):
    """Base class for generating fake waveqlab3d data files for testing.
    """
    COMPONENTS = ["x", "y", "z"]

    def __init__(self, meta_yaml, data_dir, meta_filename):
        """Constructor.

        Args:
            meta_yaml (str):
                Metadata in YAML format.
            data_dir (str):
                Path to directory where data is written.
            meta_filename (str):
                Filename for metadata.
        """
        self.meta_yaml = meta_yaml
        self.data_dir = data_dir
        self.meta_filename = meta_filename
        self.initialize()

    def initialize(self):
        """Initialize application.
        """
        self.metadata = yaml.load(self.meta_yaml,
                                  Loader=yaml.FullLoader)["waveqlab3d"]
        return

    def run(self):
        """Run application to generate data files.
        """
        self.initialize()
        self.write_metadata()
        for component in self.COMPONENTS:
            data = self.generate_data(component)
            self.write_data(component, data)

    def write_metadata(self):
        """Write YAML metadata file.
        """
        os.makedirs(self.data_dir, exist_ok=True)
        filename = os.path.join(self.data_dir, self.meta_filename)
        with open(filename, "w") as fout:
            fout.write(self.meta_yaml)

    def write_data(self, component, data):
        """Write raw waveqlab3d data file.

        Args:
            component (str):
                Name of component to write.
            data (numpy.array):
                Data for component.
        """
        filename = os.path.join(self.data_dir,
                                self.metadata["filenames"].format(
                                    component=component))
        data.tofile(filename)

    def generate_data(self, component):
        """Generate data on grid for given component.

        Args:
            component (str):
                Name of data component to generate.
        """
        SCALE = {
            "x": 1.0,
            "y": 2.0,
            "z": 3.0,
        }
        origin_x = self.metadata["origin_x"]
        origin_y = self.metadata["origin_y"]
        num_x = self.metadata["num_x"]
        num_y = self.metadata["num_y"]
        num_time = self.metadata["num_timesteps"]
        dx = self.metadata["horizontal_resolution"]
        dt = self.metadata["time_step"]
        x1 = origin_x + numpy.linspace(0, (num_x - 1) * dx, num_x)
        y1 = origin_y + numpy.linspace(0, (num_y - 1) * dx, num_y)
        x, y = numpy.meshgrid(x1, y1, indexing="xy")
        t = numpy.linspace(0, (num_time - 1) * dt, num_time)
        data = numpy.zeros((num_time, num_x * num_y), dtype=numpy.float64)
        for index, tstamp in enumerate(t):
            tdata = SCALE[component] * (2.0 * x - 0.5 * y) \
                * numpy.sin(0.25 * numpy.pi * tstamp)
            data[index, :] = tdata.ravel()
        return data

    @property
    def data(self):
        """Get data.

        Returns:
            numpy.array: Data as numpy array [num_time, num_points, 3].
        """
        num_x = self.metadata["num_x"]
        num_y = self.metadata["num_y"]
        num_time = self.metadata["num_timesteps"]
        data = numpy.zeros((num_time, num_x * num_y, 3))
        for ic, component in enumerate(self.COMPONENTS):
            data[:, :, ic] = self.generate_data(component)
        data *= 100.0  # Convert m/s to cm/s
        return data

    @property
    def geometry(self):
        """Get surface geometry.

        The surface geometry is defined by the coordinates of the vertices on
        the surface.

        Returns:
            numpy.array: Numpy array of the coordinates of the vertices.

        This just duplicates what is done in
        waveqlab3d.core._create_geometry(). The only significant
        difference is that we know the metadata is correct rather than
        reading it from a file.
        """
        origin_x = self.metadata["origin_x"]
        origin_y = self.metadata["origin_y"]
        horiz_res = self.metadata["horizontal_resolution"]
        num_x = self.metadata["num_x"]
        num_y = self.metadata["num_y"]

        x1 = origin_x + numpy.linspace(0, (num_x - 1) * horiz_res, num_x)
        y1 = origin_y + numpy.linspace(0, (num_y - 1) * horiz_res, num_y)
        x, y = numpy.meshgrid(x1, y1, indexing="xy")
        vertices = numpy.zeros((num_x * num_y, 3), dtype=numpy.float32)
        vertices[:, 0] = x.ravel()
        vertices[:, 1] = y.ravel()
        return vertices

    @property
    def topology(self):
        """Get surface topology.

        The surface topology is defined by the cells connecting the vertices.
        For finite-difference grids, the topology is quadrilaterals connecting
        the vertices. For a triangulated surface, it is triangles connecting
        the vertices.

        Returns:
            numpy.array: Numpy array of the cells connecting the vertices.

        This just duplicates what is done in
        waveqlab3d.core._create_topology(). The only significant
        difference is that we know the metadata is correct rather than
        reading it from a file.
        """
        num_x = self.metadata["num_x"]
        num_y = self.metadata["num_y"]
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


class CartesianNativeEndian(TestDataApp):
    """Generate test data on Cartesian coordinate system with floating
    point values in the native endian.
    """

    META_YAML = """
waveqlab3d:
  # Coordinate reference system as Proj parameters, WKT, or EPSG code
  crs: >
    CS[Cartesian,3], AXIS["(X)",east],AXIS["(Y)",north],AXIS["(Z)",up],
    LENGTHUNIT["meter",1.0]

  # Origin of grid in CRS coordinate system
  origin_x: 0.0
  origin_y: 0.0

  # Endian type of floating point values in data files
  # ('little', 'big', 'native')
  endian_type: native

  # Template for forming filenames {component}=x,y
  filenames: event_cartesian.slice{component}

  # Number of grid points in the x and y directions.
  num_x: 5
  num_y: 6

  # Horizontal resolution in meters.
  horizontal_resolution: 100.0

  # Number of time steps and time step size (in seconds).
  num_timesteps: 20
  time_step: 0.05

  # Start time
  start_time: None
"""

    def __init__(self):
        """Constructor.
        """
        super().__init__(self.META_YAML, "fake_cartesian",
                         "event_cartesian.yml")


class UTMBigEndian(TestDataApp):
    """Generate test data on UTM zone 10 coordinate system with floating
    point values in big endian.
    """

    META_YAML = """
waveqlab3d:
  # Coordinate reference system as Proj parameters, WKT, or EPSG code
  crs: EPSG:26910

  # Origin of grid in CRS coordinate system
  origin_x: 500000.0
  origin_y: 4000000.0

  # Endian type of floating point values in data files
  # ('little', 'big', 'native')
  endian_type: big

  # Template for forming filenames {component}=x,y
  filenames: event_utm.slice{component}

  # Number of grid points in the x and y directions.
  num_x: 5
  num_y: 7

  # Horizontal resolution in meters.
  horizontal_resolution: 100.0

  # Number of time steps and time step size (in seconds).
  num_timesteps: 18
  time_step: 0.05

  # Start time
  start_time: 2020-01-01T08:00:00
"""

    def __init__(self):
        """Constructor.
        """
        super().__init__(self.META_YAML, "fake_utm", "event_utm.yml")

    def generate_data(self, component):
        """Generate data as big endian floating point values (>d) on grid for
         given component.

        Args:
            component (str):
                Name of data component to generate.
        """
        data = super().generate_data(component)
        return data.astype(">d")


if __name__ == "__main__":
    CartesianNativeEndian().run()
    UTMBigEndian().run()

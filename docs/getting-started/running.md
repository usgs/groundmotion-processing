# Running the code

There are two main ways to run the code:

* Use the provided `gmprocess` Python command line program, or
* Use the provided API in your own Python scripts.

The `gmprocess` script targets typical use cases and users who
are not interested in writing their own Python scripts. For
additional details on how this program works, see the
"Using gmprocess" section below.

The same functionality is also available through as a library for use
in your own Python scripts. Writing your own Python scripts permits
selection of just the functionality you need as well as integration
into your own set of tools. This software provides a high-level API,
but the user also has access to the lower-level APIs upon which this
software is built, such as [ObsPy](https://www.obspy.org/),
[OpenQuake Engine](https://github.com/gem/oq-engine/#openquake-engine),
[PyASDF](https://seismicdata.github.io/pyasdf/),
[h5py](https://www.h5py.org/),
[numpy](https://www.numpy.org/), and
[scipy](https://www.scipy.org/).


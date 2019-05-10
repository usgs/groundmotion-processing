# Running the code

There are two main ways to run the code:

* Use the provided `gmprocess` Python script, or
* Use the provided API in your own Python scripts.

The `gmprocess` script targets typical use cases and users who are not interested in writing their own Python scripts. It performs all of the selected steps in a single run:

* Ingest data from the local file system (see [Reading Data](reading.md) for supported formats) or fetch data from data centers (see [Fetching Data](fetching.md) for supported data centers);

* Process the data;

  * Window the data to the earthquake recording;

  * Perform initial quality control on the record (e.g., signal to noise ratio);

  * Remove the instrument response;

  * Perform baseline correction (see [Baseline Correction](processing-baselinecorrection.md) for a list of available algorithms);

  * Generate a report of the processing steps, including plots of the processed records;

  * Compute intensity metrics from waveforms, such as peak amplitude, response spectra, and Fourier spectra, using user-specified components, such as single components, geometric mean, vector maximum, and RotD50;

  * Compute station metrics (scheduled for v1.1); and

  * Pick phases (see [Phase Pickers](processing-phasepickers.md) for a list of available algorithms);

* Save the data in an HDF5 file using an extension of the [Adaptable Seismic Data Format](http://seismic-data.org/); and

* Export the data.

All of this functionality is also available through the API for use in your own Python scripts. Writing your own Python scripts permits selection of just the functionality you need as well as integration into your own set of tools. This software provides a high-level API, but the user also has access to the lower-level APIs upon which this software is built, such as [ObsPy](https://www.obspy.org/), [OpenQuake Engine](https://github.com/gem/oq-engine/#openquake-engine), [PyASDF](https://seismicdata.github.io/pyasdf/), [h5py](https://www.h5py.org/), [numpy](https://www.numpy.org/), and [scipy](https://www.scipy.org/).

The examples section includes examples for [using gmprocess](gmprocess.md) and [writing your own Python scripts](scripting.md).

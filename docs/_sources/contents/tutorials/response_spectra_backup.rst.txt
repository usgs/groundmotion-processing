Response Spectra Calculation and Comparison
===========================================

In this tutorial we will read in an example record, compute the response 
spectra, and compare it to a ground motion prediction equation.

There are a lot of imports to take care of first


.. code-block:: python

    import os
    import pkg_resources

    import matplotlib.pyplot as plt
    from matplotlib import _cm as cm
    import numpy as np

    # OpenQuake imports for GMPEs
    from openquake.hazardlib.gsim import base
    import openquake.hazardlib.imt as imt
    from openquake.hazardlib.const import StdDev
    from openquake.hazardlib.gsim.boore_2014 import BooreEtAl2014

    from gmprocess.core.streamcollection import StreamCollection
    from gmprocess.utils.config import get_config
    from gmprocess.waveform_processing.processing import process_streams
    from gmprocess.utils.event import get_event_object
    from gmprocess.metrics.station_summary import StationSummary

Now we will read in some records from we keep in the repository for testing
purposes, get the config file that controls many of the processing steps,
and the event object for this earthquake


.. code-block:: python

    # Path to example data
    datapath = os.path.join('data', 'testdata', 'demo', 'ci38457511', 'raw')
    datadir = pkg_resources.resource_filename('gmprocess', datapath)
    sc = StreamCollection.from_directory(datadir)

    # Includes 3 StationStreams, each with 3 StationTraces
    sc.describe()

    # Get the default config file
    conf = get_config()

    # Get event object
    event = get_event_object('ci38457511')

The next step is to processing the streams and then compute a 
"StationSummary" instance, which holds the station and waveform
metrics, including the response spectra

.. code-block:: python

    # Process the straems
    psc = process_streams(sc, event, conf)
    psc.describe()

    # Compute response spectra for one of the processed streams
    summary = StationSummary.from_config(psc[0], event=event, config=conf)
    summary.available_imcs

At this point, the response spectra is computed, but accessing it in the
``StationSummary`` object is a little cumbersome. So we have a few 
functions that outputs the information in a more convenient format

.. code-block:: python

    # Get the full rotd50 dictionary, including distances, event id, etc.
    rotd_dict = summary.get_imc_dict('ROTD(50.0)')

    # That is not very convenient for plotting though, so get SA arrays:
    sa_arrays = summary.get_sa_arrays('ROTD(50.0)')
    period = sa_arrays['ROTD(50.0)']['period']
    sa = sa_arrays['ROTD(50.0)']['sa']

    # Note on units: OQ uses natural log of g, gmprocess uses %g
    sa_g = sa / 100.0

Now we are ready to compute the response spectra from a GMPE

.. code-block:: python

    # Prepare inputs for OQ GMPE
    gmpe = BooreEtAl2014()
    stddev_types = [StdDev.TOTAL]

    # Define rupture information
    rx = base.RuptureContext()
    rx.mag = rotd_dict['ROTD(50.0)']['EarthquakeMagnitude']
    rx.rake = 90.0
    rx.hypo_depth = rotd_dict['ROTD(50.0)']['EarthquakeDepth']
    rx.ztor = 0.0

    # Distance context (ignoring finite dimensions of rupture for this tutorial)
    dx = base.DistancesContext()
    dx.rjb = np.array([5.0])

    # Sites context
    sx = base.SitesContext()
    sx.vs30 = np.array([760.0])

    # Evaluate (must loop over periods since OQ takes in IMT as scalar)
    BSSA14 = {
        'lmean': np.array([]),
        'lsd': np.array([])
    }
    for per in period:
        lmean, lsd = gmpe.get_mean_and_stddevs(
            sx, rx, dx, imt.SA(per), stddev_types)
        BSSA14['lmean'] = np.append(BSSA14['lmean'], lmean[0])
        BSSA14['lsd'] = np.append(BSSA14['lsd'], lsd[0][0])

Lastly, we construct the plot

.. code-block:: python

    gmpe_mean = np.exp(BSSA14['lmean'])
    gmpe_upper = np.exp(BSSA14['lmean'] + BSSA14['lsd'])
    gmpe_lower = np.exp(BSSA14['lmean'] - BSSA14['lsd'])
    fig = plt.figure()
    ax = fig.add_axes([0.125, 0.125, 0.825, 0.825])
    ax.fill_between(period, gmpe_lower, gmpe_upper, fc='k', alpha=0.25)
    ax.loglog(period, gmpe_mean, color='k', lw=2, label='BSSA14')
    ax.loglog(period, sa_g, color=(0.0, 0.4, 0.8), lw=2, marker='o',
            label=psc[0].id)
    ax.legend()
    ax.set_xlabel('Period (sec)')
    ax.set_ylabel('Spectral Acceleration (g)')


.. figure:: ../../_static/gmpe_compare_CI.CLC.HN.png

   This is the figure constructed for this tutorial.

.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`

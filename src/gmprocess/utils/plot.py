#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import copy
import datetime
import logging
from collections import Counter

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from obspy.geodetics.base import gps2dist_azimuth
from obspy.core.utcdatetime import UTCDateTime
from esi_utils_colors.cpalette import ColorPalette
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.dates import num2date

from gmprocess.metrics.reduction.arias import Arias
from gmprocess.waveform_processing import spectrum
from gmprocess.metrics.oscillators import get_spectral
from gmprocess.utils.constants import UNIT_CONVERSIONS
from gmprocess.utils.config import get_config

MIN_MAG = 4.0
MAX_MAG = 7.0
DELTA_MAG = 0.5

BOTTOM = 0.1
AX1_LEFT = 0.1
AX1_WIDTH = 0.8
AX1_HEIGHT = 0.8
AX2_WIDTH = 0.1
AX2_HEIGHT = 1.0

# avoid this issue: https://github.com/matplotlib/matplotlib/issues/5907
plt.rcParams["agg.path.chunksize"] = 10000


def plot_regression(
    event_table,
    imc,
    imc_table,
    imt,
    filename,
    distance_metric="EpicentralDistance",
    colormap="viridis",
):
    """Make summary "regression" plot.

    TODO:
      * Add GMPE curve and compute mean/sd for all the observations
        and then also report the standardized residuals.
      * Better definitions of column names and units.

    """
    fig = plt.figure(figsize=(10, 5))
    ax = fig.add_axes([BOTTOM, AX1_LEFT, AX1_WIDTH, AX1_HEIGHT])

    if distance_metric not in imc_table.columns:
        raise KeyError(f'Distance metric "{distance_metric}" not found in table')
    imt = imt.upper()

    # Stupid hack to get units for now. Need a better, more systematic
    # approach
    if imt.startswith("SA") | (imt == "PGA"):
        units = "%g"
    elif imt.startswith("FAS") or imt in ["ARIAS", "PGV"]:
        units = "cm/s"
    else:
        units = f"Unknown units for IMT {imt}"

    if imt not in imc_table.columns:
        raise KeyError(f'IMT "{imt}" not found in table')
    # get the event information
    # group imt data by event id
    # plot imts by event using colors banded by magnitude
    eventids = event_table["id"]
    # set up the color bands
    minmag = event_table["magnitude"].min()
    min_mag = min(np.floor(minmag / DELTA_MAG) * DELTA_MAG, MIN_MAG)
    maxmag = event_table["magnitude"].max()
    max_mag = max(np.ceil(maxmag / DELTA_MAG) * DELTA_MAG, MAX_MAG)
    z0 = np.arange(min_mag, max_mag, 0.5)
    z1 = np.arange(min_mag + DELTA_MAG, max_mag + DELTA_MAG, DELTA_MAG)
    cmap = plt.get_cmap(colormap)
    palette = ColorPalette.fromColorMap("mag", z0, z1, cmap)

    colors = []
    for zval in np.arange(min_mag, max_mag + 0.5, 0.5):
        tcolor = palette.getDataColor(zval, "hex")
        colors.append(tcolor)
    cmap2 = mpl.colors.ListedColormap(colors)

    for eventid in eventids:
        emag = event_table[event_table["id"] == eventid].magnitude.to_numpy()[0]
        norm_mag = (emag - min_mag) / (max_mag - min_mag)
        color = cmap2(norm_mag)
        erows = imc_table[imc_table["EarthquakeId"] == eventid]
        distance = erows[distance_metric]
        imtdata = erows[imt]
        ax.loglog(distance, imtdata, mfc=color, mec="k", marker="o", linestyle="None")

    ax.set_xlabel(f"{distance_metric} (km)")
    ax.set_ylabel(f"{imt} ({units})")

    bounds = np.arange(min_mag, max_mag + 1.0, 0.5)
    norm = mpl.colors.BoundaryNorm(bounds, cmap2.N)

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.05)

    mpl.colorbar.ColorbarBase(
        cax,
        cmap=cmap2,
        norm=norm,
        ticks=bounds,  # optional
        spacing="proportional",
        orientation="vertical",
    )

    plt.sca(ax)
    plt.suptitle("%s vs %s (#eqks=%i)" % (distance_metric, imt, len(eventids)))
    plt.title(f"for component {imc}")

    plt.savefig(filename)


def get_time_from_percent(NIa, p, dt):
    """
    Find the closest value to the desired percent of Arias intensity and
    calculate the duration time associated with the percent.

    Args:
        NIa (array):
            Array of normalized Arias intensity values with respect to time.
        p (float):
            Percent (0 to 1) of Arias Intensity.
        dt (float):
            Time in between each record in s.

    Returns:
        time (float): Duration time to reach specified percent of Arias
        intensity.
    """

    npts = len(NIa)
    t = np.linspace(0, (npts - 1) * dt, num=npts)

    time = t[np.argmin(np.abs(p - NIa))]
    return time


def plot_arias(
    stream,
    axes=None,
    axis_index=None,
    figsize=None,
    file=None,
    minfontsize=14,
    show=False,
    show_maximum=True,
    title=None,
    xlabel=None,
    ylabel=None,
):
    """
    Create plots of arias intensity.

    Args:
        stream (obspy.core.stream.Stream):
            Set of acceleration data with units of gal (cm/s/s).
        axes (ndarray):
            Array of subplots. Default is None.
        axis_index (int):
            First index of axes array to plot the traces. Default is None.
            Required if axes is not None.
        figsize (tuple):
            Tuple of height and width. Default is None.
        file (str):
            File where the image will be saved. Default is None.
        minfontsize (int):
            Minimum font size. Default is 14.
        show (bool):
            Plot the figure. Default is False.
        show_maximum (bool):
            Show the maximum value.
        title (str):
            Title for plot. Default is None.
        xlabel (str):
            Label for x axis. Default is None.
        ylabel (str):
            Label for y axis. Default is None.

    Returns:
        numpy.ndarray: Array of matplotlib.axes._subplots.AxesSubplot.
    """
    if len(stream) < 1:
        raise Exception("No traces contained within the provided stream.")

    arias = Arias(stream)
    Ia = arias.arias_stream

    starttime = stream[0].stats.starttime
    if title is None:
        title = (
            "Event on "
            + str(starttime.month)
            + "/"
            + str(starttime.day)
            + "/"
            + str(starttime.year)
        )
    if xlabel is None:
        xlabel = "Time (s)"
    if ylabel is None:
        ylabel = "Ia (m/s)"

    if figsize is None:
        figsize = (6.5, 7.5)
    if axes is None:
        fig, axs = plt.subplots(len(Ia), 1, figsize=figsize)
        axis_numbers = np.linspace(0, len(Ia) - 1, len(Ia))
    elif axis_index is not None:
        axs = axes
        axis_numbers = np.linspace(axis_index, axis_index + len(Ia) - 1, len(Ia))
    for idx, trace in zip(axis_numbers.astype(int), Ia):
        ax = axs[idx]
        dt = trace.stats["delta"]
        npts = len(trace.data)
        t = np.linspace(0, (npts - 1) * dt, num=npts)
        network = trace.stats["network"]
        station = trace.stats["station"]
        channel = trace.stats["channel"]
        trace_label = network + "." + station + "." + channel
        ax.set_title(trace_label, fontsize=minfontsize)
        ax.plot(t, trace.data)
        if show_maximum:
            abs_arr = np.abs(trace.data.copy())
            idx = np.argmax(abs_arr)
            max_value = abs_arr[idx]
            ax.plot([t[idx]], [trace.data[idx]], marker="o", color="red")
            ax.annotate(
                f"{max_value:.2E}",
                (t[idx], trace.data[idx]),
                xycoords="data",
                xytext=(0.85, 0.25),
                textcoords="axes fraction",
                arrowprops=dict(facecolor="black", shrink=0.05, width=1, headwidth=4),
                horizontalalignment="right",
                verticalalignment="top",
            )
        ax.set_xlabel(xlabel, fontsize=minfontsize)
        ax.set_ylabel(ylabel, fontsize=minfontsize)
        ax.xaxis.set_tick_params(labelsize=minfontsize - 2)
        ax.yaxis.set_tick_params(labelsize=minfontsize - 2)
    plt.suptitle(title, y=1.01, fontsize=minfontsize + 4)
    plt.tight_layout()
    if show and axes is None:
        plt.show()
    if file is not None and axes is None:
        fig.savefig(file, format="png")
    return axs


def plot_durations(
    stream,
    durations,
    axes=None,
    axis_index=None,
    figsize=None,
    file=None,
    minfontsize=14,
    show=False,
    title=None,
    xlabel=None,
    ylabel=None,
):
    """
    Create plots of durations.

    Args:
        stream (obspy.core.stream.Stream):
            Set of acceleration data with units of gal (cm/s/s).
        durations (list):
            List of percentage minimum and maximums (tuple).
        axes (ndarray):
            Array of subplots. Default is None.
        axis_index (int):
            First index of axes array to plot the traces. Default is None.
            Required if axes is not None.
        figsize (tuple):
            Tuple of height and width. Default is None.
        file (str):
            File where the image will be saved. Default is None.
        show (bool):
            Plot the figure. Default is False.
        title (str):
            Title for plot. Default is None.
        xlabel (str):
            Label for x axis. Default is None.
        ylabel (str):
            Label for y axis. Default is None.

    Returns:
        numpy.ndarray: Array of matplotlib.axes._subplots.AxesSubplot.
    """
    if len(stream) < 1:
        raise Exception("No traces contained within the provided stream.")

    arias = Arias(stream)
    Ia = arias.arias_stream
    NIa = Ia.normalize(False)

    starttime = stream[0].stats.starttime
    if title is None:
        title = (
            "Event on "
            + str(starttime.month)
            + "/"
            + str(starttime.day)
            + "/"
            + str(starttime.year)
        )
    if xlabel is None:
        xlabel = "Time (s)"
    if ylabel is None:
        ylabel = "NIa (m/s)"

    if figsize is None:
        figsize = (6.5, 7.5)
    if axes is None:
        fig, axs = plt.subplots(len(NIa), 1, figsize=figsize)
        axis_numbers = np.linspace(0, len(NIa) - 1, len(NIa))
    elif axis_index is not None:
        axs = axes
        axis_numbers = np.linspace(axis_index, axis_index + len(NIa) - 1, len(NIa))
    for idx, trace in zip(axis_numbers.astype(int), NIa):
        ax = axs[idx]
        dt = trace.stats["delta"]
        npts = len(trace.data)
        t = np.linspace(0, (npts - 1) * dt, num=npts)
        network = trace.stats["network"]
        station = trace.stats["station"]
        channel = trace.stats["channel"]
        trace_label = network + "." + station + "." + channel
        ax.set_title(trace_label, fontsize=minfontsize)
        ax.plot(t, trace.data)
        if xlabel:
            ax.set_xlabel(xlabel)
        if xlabel:
            ax.set_ylabel(ylabel)
        for i, duration in enumerate(durations):
            first_percentile = duration[0]
            second_percentile = duration[1]
            t1 = get_time_from_percent(trace.data, first_percentile, dt)
            t2 = get_time_from_percent(trace.data, second_percentile, dt)
            height = (1 / (len(durations) + 1) * i) + 1 / (len(durations) + 1)
            ax.plot(t1, first_percentile, "ok")
            ax.plot(t2, second_percentile, "ok")
            ax.annotate(
                "",
                xy=(t1, height),
                xytext=(t2, height),
                arrowprops=dict(arrowstyle="<->"),
            )
            label = "$D_{%i{-}%i}$" % (100 * duration[0], 100 * duration[1])
            ax.text(
                t2,
                height,
                label,
                style="italic",
                horizontalalignment="left",
                verticalalignment="center",
            )
            ax.set_xlabel(xlabel, fontsize=minfontsize)
            ax.set_ylabel(ylabel, fontsize=minfontsize)
            ax.xaxis.set_tick_params(labelsize=minfontsize - 2)
            ax.yaxis.set_tick_params(labelsize=minfontsize - 2)
    plt.suptitle(title, y=1.01, fontsize=minfontsize + 4)
    plt.tight_layout()
    if show and axes is None:
        plt.show()
    if file is not None and axes is None:
        if not file.endswith(".png"):
            file += ".png"
        fig.savefig(file)
    return axs


def plot_moveout(
    streams,
    epilat,
    epilon,
    orientation=None,
    max_dist=None,
    figsize=(10, 15),
    file=None,
    minfontsize=14,
    normalize=True,
    factor=0.2,
    alpha=0.25,
):
    """
    Create moveout plot.

    Args:
        streams (StreamCollection):
            StreamCollection of acceleration data with units of gal (cm/s/s).
        epilat (float):
            Epicenter latitude.
        epilon (float):
            Epicenter longitude.
        orientation (str):
            Orientation code (str) of each stream to view. Default is None.
            If None, then the orientation code with the highest number of
            traces will be used.
        max_dist (float):
            Maximum distance (in km) to plot. Default is 200 km.
        figsize (tuple):
            Tuple of height and width. Default is (10, 15).
        file (str):
            File where the image will be saved. Default is None.
        minfontsize (int):
            Minimum font size. Default is 14.
        normalize (bool):
            Normalize the data. Default is True.
        factor (int, float):
            Factor for scaling the trace. Default is 0.2, meaning that the
            trace with the greatest amplitude variation will occupy 20% of the
            vertical space in the plot.
        alpha (float):
            Alpha value for plotting the traces.

    Returns:
        tuple: (Figure, matplotlib.axes._subplots.AxesSubplot)
    """
    if len(streams) < 1:
        raise Exception("No streams provided.")

    fig, ax = plt.subplots(figsize=figsize)

    # If no channel is given, then find the orientation code with the greatest
    # number of traces
    if orientation is None:
        orientation_codes = []
        for st in streams:
            if st.passed:
                for tr in st:
                    orientation_codes.append(tr.stats.channel[-1])
        for i, code in enumerate(orientation_codes):
            if code == "1":
                orientation_codes[i] = "N"
            if code == "2":
                orientation_codes[i] = "E"
            if code == "3":
                orientation_codes[i] = "Z"
        channel_counter = Counter(orientation_codes)
        if channel_counter:
            orientation = max(channel_counter, key=channel_counter.get)
        else:
            return (fig, ax)

    valid_channels = []
    if orientation in ["N", "1"]:
        valid_channels = ["N", "1"]
    elif orientation in ["E", "2"]:
        valid_channels = ["E", "2"]
    elif orientation in ["Z", "3"]:
        valid_channels = ["Z", "3"]

    # Create a copy of the streams to avoid modifying the data when normalizing
    streams_copy = copy.deepcopy(streams)

    # Determine the distance and amplitude variation for scaling
    distances = []
    max_amp_variation = 0
    for st in streams:
        if st.passed:
            dist = (
                gps2dist_azimuth(
                    st[0].stats.coordinates["latitude"],
                    st[0].stats.coordinates["longitude"],
                    epilat,
                    epilon,
                )[0]
                / 1000.0
            )
            max_amp_var_st = 0
            for tr in st:
                amp_var_tr = abs(max(tr.data) - min(tr.data))
                if normalize:
                    amp_var_tr *= dist
                if amp_var_tr > max_amp_var_st:
                    max_amp_var_st = amp_var_tr
            if max_dist is not None:
                if dist < max_dist:
                    distances.append(dist)
                    if max_amp_var_st > max_amp_variation:
                        max_amp_variation = max_amp_var_st
            else:
                distances.append(dist)
                if max_amp_var_st > max_amp_variation:
                    max_amp_variation = max_amp_var_st

    if distances:
        scale = max(distances) * factor / max_amp_variation
    else:
        return (fig, ax)

    nplot = 0
    for idx, stream in enumerate(streams_copy):
        if not stream.passed:
            continue
        for trace in stream:
            if trace.stats.channel[-1] not in valid_channels:
                continue
            lat = trace.stats.coordinates["latitude"]
            lon = trace.stats.coordinates["longitude"]
            distance = gps2dist_azimuth(lat, lon, epilat, epilon)[0] / 1000.0

            # Don't plot if past the maximum distance
            if max_dist is not None and distance > max_dist:
                continue

            # Multiply by distance to normalize
            if normalize:
                trace.data = trace.data.astype(float) * distance
            trace.data *= scale

            times = []
            start = trace.stats.starttime
            for time in trace.times():
                starttime = start
                td = datetime.timedelta(seconds=time)
                ti = starttime + td
                times += [ti.datetime]
            ax.plot(times, trace.data + distance, c="k", alpha=alpha)
            nplot += 1
    ax.invert_yaxis()
    ax.set_title(f"Orientation code: {orientation}", fontsize=minfontsize + 4)
    ax.set_ylabel("Epicentral distance (km)", fontsize=minfontsize)
    ax.yaxis.set_tick_params(labelsize=minfontsize - 2)
    plt.xticks([])

    # Get the x-coordinate for the time bar
    if nplot > 0:
        xmin, xmax = ax.get_xlim()
        xbar = num2date(xmin + 0.9 * (xmax - xmin))
        xlabel = num2date(xmin + 0.83 * (xmax - xmin))

        # Get the y-coordinates for the time bar and label
        ymax, ymin = ax.get_ylim()
        ybar = 0
        ylabel = 0.05 * (ymax - ymin)

        # Plot the time-scale bar
        plt.errorbar(
            xbar, ybar, xerr=datetime.timedelta(seconds=15), color="k", capsize=5
        )
        plt.text(xlabel, ylabel, "30 seconds", fontsize=minfontsize)

    if file is not None:
        fig.savefig(file, format="png")
    # plt.show()
    return (fig, ax)


def summary_plots(st, directory, origin, config=None):
    """Stream summary plot.

    Args:
        st (gmprocess.core.stationtrace.StationStream):
            Stream of data.
        directory (str):
            Directory for saving plots.
        origin (ScalarEvent):
            Flattened subclass of Obspy Event.
        config (dict):
            Configuration dictionary (or None). See get_config().

    """
    mpl.rcParams["font.size"] = 8

    if config is None:
        config = get_config()

    # Check if directory exists, and if not, create it.
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Setup figure for stream
    nrows = 5
    ntrace = min(len(st), 3)
    fig = plt.figure(figsize=(3.9 * ntrace, 10))
    gs = fig.add_gridspec(nrows, ntrace, height_ratios=[1, 1, 1, 2, 2])
    ax = [plt.subplot(g) for g in gs]

    stream_id = st.get_id()
    logging.debug(f"stream_id: {stream_id}")
    logging.debug(f"passed: {st.passed}")
    if st.passed:
        plt.suptitle(
            f"M{origin.magnitude} {origin.id} | {stream_id} (passed)",
            x=0.5,
            y=1.02,
        )
    else:
        plt.suptitle(
            f"M{origin.magnitude} {origin.id} | {stream_id} (failed)",
            color="red",
            x=0.5,
            y=1.02,
        )

    # Compute velocity
    st_vel = st.copy()
    for tr in st_vel:
        tr = tr.integrate(config=config)

    # Compute displacement
    st_dis = st.copy()
    for tr in st_dis:
        tr = tr.integrate(config=config).integrate(config=config)

    # process channels in preferred sort order (i.e., HN1, HN2, HNZ)
    channels = [tr.stats.channel for tr in st]
    if len(channels) < 3:
        channelidx = np.argsort(channels).tolist()
    else:
        channelidx = range(3)

    for j in channelidx:
        tr = st[channelidx.index(j)]

        # Break if j>3 becasue we can't on a page.
        if j > 2:
            logging.warning("Only plotting first 3 traces in stream.")
            break

        # ---------------------------------------------------------------------
        # Get trace info
        if tr.hasCached("snr"):
            snr_dict = tr.getCached("snr")
        else:
            snr_dict = None

        if tr.hasCached("signal_spectrum"):
            signal_dict = tr.getCached("signal_spectrum")
        else:
            signal_dict = None

        if tr.hasCached("noise_spectrum"):
            noise_dict = tr.getCached("noise_spectrum")
        else:
            noise_dict = None

        if tr.hasCached("smooth_signal_spectrum"):
            smooth_signal_dict = tr.getCached("smooth_signal_spectrum")
        else:
            smooth_signal_dict = None

        if tr.hasCached("smooth_noise_spectrum"):
            smooth_noise_dict = tr.getCached("smooth_noise_spectrum")
        else:
            smooth_noise_dict = None

        if tr.hasParameter("snr_conf"):
            snr_conf = tr.getParameter("snr_conf")
        else:
            snr_conf = None

        if tr.hasParameter("tail_conf"):
            tail_conf = tr.getParameter("tail_conf")
        else:
            tail_conf = None

        trace_failed = tr.hasParameter("failure")

        # Note that the theoretical spectra will only be available for
        # horizontal channels
        if tr.hasParameter("fit_spectra"):
            fit_spectra_dict = tr.getParameter("fit_spectra")
        else:
            fit_spectra_dict = None

        # ---------------------------------------------------------------------
        # Compute model spectra
        if fit_spectra_dict is not None:
            model_spec = spectrum.model(
                (fit_spectra_dict["moment"], fit_spectra_dict["stress_drop"]),
                freq=np.array(smooth_signal_dict["freq"]),
                dist=fit_spectra_dict["epi_dist"],
                kappa=fit_spectra_dict["kappa"],
            )

        # ---------------------------------------------------------------------
        # Acceleration time series plot
        pga = np.max(np.abs(st[j].data)) / UNIT_CONVERSIONS["g"]
        if trace_failed:
            trace_status = " (failed)"
            trace_title = tr.get_id() + trace_status
            ax[j].set_title(trace_title, color="red")
        else:
            trace_status = " (passed)"
        trace_title = tr.get_id() + trace_status
        ax[j].set_title(trace_title)
        dtimes = np.linspace(0, tr.stats.endtime - tr.stats.starttime, tr.stats.npts)
        ax[j].plot(dtimes, tr.data, "k", linewidth=0.5)
        ax[j].tick_params(axis="both", which="major", labelsize=5)
        ax[j].text(
            0.95,
            0.95,
            f"PGA: {pga:.3g} g",
            transform=ax[j].transAxes,
            va="top",
            ha="right",
            color="0.5",
        )

        # Show signal split as vertical dashed line
        if tr.hasParameter("signal_split"):
            split_dict = tr.getParameter("signal_split")
            sptime = UTCDateTime(split_dict["split_time"])
            dsec = sptime - tr.stats.starttime
            ax[j].axvline(dsec, color="red", linestyle="dashed")

        if j == 0:
            ax[j].set_ylabel("Acceleration (cm/s/s)")

        # ---------------------------------------------------------------------
        # Velocity time series plot
        pgv = np.max(np.abs(st_vel[j].data))
        tr_vel = st_vel[j]
        dtimes = np.linspace(
            0, tr_vel.stats.endtime - tr_vel.stats.starttime, tr_vel.stats.npts
        )
        ax[j + ntrace].plot(dtimes, tr_vel.data, "k", linewidth=0.5)
        ax[j + ntrace].tick_params(axis="both", which="major", labelsize=5)
        ax[j + ntrace].text(
            0.95,
            0.95,
            f"PGV: {pgv:.3g} cm/s",
            transform=ax[j + ntrace].transAxes,
            va="top",
            ha="right",
            color="0.5",
        )
        # Show signal split as vertical dashed line
        if tr.hasParameter("signal_split"):
            split_dict = tr.getParameter("signal_split")
            sptime = UTCDateTime(split_dict["split_time"])
            dsec = sptime - tr.stats.starttime
            ax[j + ntrace].axvline(dsec, color="red", linestyle="dashed")

        if j == 0:
            ax[j + ntrace].set_ylabel("Velocity (cm/s)")

        if tail_conf is not None:
            utc_start = UTCDateTime(tail_conf["start_time"])
            tail_start = utc_start - tr.stats.starttime
            tail_end = tr.stats.endtime - tr.stats.starttime
            abs_max_vel = np.max(np.abs(tr_vel.data))
            vel_ratio = tail_conf["max_vel_ratio"]
            vel_threshold = abs_max_vel * vel_ratio
            rect = patches.Rectangle(
                (tail_start, -vel_threshold),
                tail_end - tail_start,
                2 * vel_threshold,
                linewidth=0,
                edgecolor="none",
                facecolor="#3cfa8b",
            )

            ax[j + ntrace].add_patch(rect)

        # ---------------------------------------------------------------------
        # Displacement time series plot
        pgd = np.max(np.abs(st_dis[j].data))
        tr_dis = st_dis[j]
        dtimes = np.linspace(
            0, tr_dis.stats.endtime - tr_dis.stats.starttime, tr_dis.stats.npts
        )
        ax[j + 2 * ntrace].plot(dtimes, tr_dis.data, "k", linewidth=0.5)
        ax[j + 2 * ntrace].tick_params(axis="both", which="major", labelsize=5)
        ax[j + 2 * ntrace].text(
            0.95,
            0.95,
            f"PGD: {pgd:.3g} cm",
            transform=ax[j + 2 * ntrace].transAxes,
            va="top",
            ha="right",
            color="0.5",
        )

        # Show signal split as vertical dashed line
        if tr.hasParameter("signal_split"):
            split_dict = tr.getParameter("signal_split")
            sptime = UTCDateTime(split_dict["split_time"])
            dsec = sptime - tr.stats.starttime
            ax[j + 2 * ntrace].axvline(dsec, color="red", linestyle="dashed")

        ax[j + 2 * ntrace].set_xlabel("Time (s)")
        if j == 0:
            ax[j + 2 * ntrace].set_ylabel("Displacement (cm)")

        if tail_conf is not None:
            utc_start = UTCDateTime(tail_conf["start_time"])
            tail_start = utc_start - tr.stats.starttime
            tail_end = tr.stats.endtime - tr.stats.starttime
            abs_max_dis = np.max(np.abs(tr_dis.data))
            dis_ratio = tail_conf["max_dis_ratio"]
            dis_threshold = abs_max_dis * dis_ratio
            rect = patches.Rectangle(
                (tail_start, -dis_threshold),
                tail_end - tail_start,
                2 * dis_threshold,
                linewidth=0,
                edgecolor="none",
                facecolor="#3cfa8b",
            )

            ax[j + 2 * ntrace].add_patch(rect)

        # ---------------------------------------------------------------------
        # Spectral plot

        # Raw signal spec
        if (signal_dict is not None) and np.any(signal_dict["spec"] > 0):
            ax[j + 3 * ntrace].loglog(
                signal_dict["freq"], signal_dict["spec"], color="lightblue"
            )

        # Smoothed signal spec
        if (smooth_signal_dict is not None) and np.any(smooth_signal_dict["spec"] > 0):
            ax[j + 3 * ntrace].loglog(
                smooth_signal_dict["freq"],
                smooth_signal_dict["spec"],
                color="blue",
                label="Signal",
            )

        # Raw noise spec
        if (noise_dict is not None) and np.any(noise_dict["spec"] > 0):
            ax[j + 3 * ntrace].loglog(
                noise_dict["freq"], noise_dict["spec"], color="salmon"
            )

        # Smoothed noise spec
        if (smooth_noise_dict is not None) and np.any(smooth_noise_dict["spec"] > 0):
            ax[j + 3 * ntrace].loglog(
                smooth_noise_dict["freq"],
                smooth_noise_dict["spec"],
                color="red",
                label="Noise",
            )

        if fit_spectra_dict is not None:
            # Model spec
            ax[j + 3 * ntrace].loglog(
                smooth_signal_dict["freq"],
                model_spec,
                color="black",
                linestyle="dashed",
            )

            # Corner frequency
            ax[j + 3 * ntrace].axvline(
                fit_spectra_dict["f0"], color="black", linestyle="dashed"
            )

        ax[j + 3 * ntrace].set_xlabel("Frequency (Hz)")
        if j == 0:
            ax[j + 3 * ntrace].set_ylabel("Amplitude (cm/s)")

        # ---------------------------------------------------------------------
        # Signal-to-noise ratio plot

        if "corner_frequencies" in tr.getParameterKeys():
            hp = tr.getParameter("corner_frequencies")["highpass"]
            lp = tr.getParameter("corner_frequencies")["lowpass"]
            ax[j + 4 * ntrace].axvline(
                hp, color="black", linestyle="--", label="Highpass"
            )
            ax[j + 4 * ntrace].axvline(
                lp, color="black", linestyle="--", label="Lowpass"
            )

        if snr_conf is not None:
            ax[j + 4 * ntrace].axhline(
                snr_conf["threshold"], color="0.75", linestyle="-", linewidth=2
            )
            ax[j + 4 * ntrace].axvline(
                snr_conf["max_freq"], color="0.75", linewidth=2, linestyle="-"
            )
            ax[j + 4 * ntrace].axvline(
                snr_conf["min_freq"], color="0.75", linewidth=2, linestyle="-"
            )

        if snr_dict is not None:
            ax[j + 4 * ntrace].loglog(snr_dict["freq"], snr_dict["snr"], label="SNR")

        if j == 0:
            ax[j + 4 * ntrace].set_ylabel("SNR")
        ax[j + 4 * ntrace].set_xlabel("Frequency (Hz)")

    stream_id = st.get_id()

    # Do not save files if running tests
    file_name = None
    if "CALLED_FROM_PYTEST" not in os.environ:
        plt.subplots_adjust(left=0.08, right=0.97, hspace=0.3, wspace=0.25, top=0.97)
        file_name = os.path.join(directory, origin.id + "_" + stream_id + ".png")
        plt.savefig(fname=file_name)
        plt.close("all")

    return file_name


def plot_oscillators(st, periods=[0.1, 2, 5, 10], file=None, show=False):
    """
    Produces a figure of the oscillator responses for a StationStream. The
    figure will plot the acceleration traces in the first row, and then an
    additional row for each oscillator period. The number of columns is the
    number of channels in the stream.

    Args:
        st (gmprocess.core.stationstream.StationStream):
            StaionStream of data.
        periods (list):
            A list of periods (floats, in seconds).
        file (str):
            File where the image will be saved. Default is None.
        show (bool):
            Show the figure. Default is False.
    """

    fig, axes = plt.subplots(
        nrows=len(periods) + 1, ncols=len(st), figsize=(4 * len(st), 2 * len(periods))
    )
    if len(st) == 1:
        # Ensure that axes is a 2D numpy array
        axes = axes.reshape(-1, 1)

    for i in range(axes.shape[0]):
        if i == 0:
            plot_st = st
            ylabel = "Acceleration (cm/s$^2$)"
            textstr = "T: %s s \nPGA: %.2g cm/s$^2$"
        else:
            prd = periods[i - 1]
            plot_st = get_spectral(prd, st)
            ylabel = "SA %s s (%%g)" % prd
            textstr = "T: %s s \nSA: %.2g %%g"

        for j, tr in enumerate(plot_st):
            ax = axes[i, j]
            dtimes = np.linspace(
                0, tr.stats.endtime - tr.stats.starttime, tr.stats.npts
            )
            ax.plot(dtimes, tr.data, "k", linewidth=0.5)

            # Get time and amplitude of max SA (using absolute value)
            tmax = dtimes[np.argmax(abs(tr.data))]
            sa_max = max(tr.data, key=abs)

            ax.axvline(tmax, c="r", ls="--")
            ax.scatter([tmax], [sa_max], c="r", edgecolors="k", zorder=10)
            ax.text(
                0.01, 0.98, textstr % (tmax, sa_max), transform=ax.transAxes, va="top"
            )

            if i == 0:
                ax.set_title(tr.id)
            if i == len(periods):
                ax.set_xlabel("Time (s)")
            ax.set_ylabel(ylabel)

    plt.tight_layout()

    if file is not None:
        plt.savefig(file)
    if show:
        plt.show()

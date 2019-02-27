# stdlib imports
import datetime
import warnings

# third party imports
from matplotlib.pyplot import cm
import matplotlib.pyplot as plt
import numpy as np
from obspy.geodetics.base import gps2dist_azimuth

# Local imports
from gmprocess.metrics.imt.arias import calculate_arias
from gmprocess.metrics.oscillators import get_acceleration


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
    t = np.linspace(0, (npts-1)*dt, num=npts)

    time = t[np.argmin(np.abs(p-NIa))]
    return time


def plot_arias(stream, axes=None, axis_index=None,
               figsize=None, file=None, minfontsize=14, show=False,
               show_maximum=True, title=None, xlabel=None, ylabel=None):
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
        raise Exception('No traces contained within the provided stream.')

    stream = get_acceleration(stream, units='m/s/s')
    Ia = calculate_arias(stream, ['channels'], True)[0]

    starttime = stream[0].stats.starttime
    if title is None:
        title = ('Event on ' + str(starttime.month) + '/' +
                 str(starttime.day) + '/' + str(starttime.year))
    if xlabel is None:
        xlabel = 'Time (s)'
    if ylabel is None:
        ylabel = 'Ia (m/s)'

    if figsize is None:
        figsize = (6.5, 7.5)
    if axes is None:
        fig, axs = plt.subplots(len(Ia), 1, figsize=figsize)
        axis_numbers = np.linspace(0, len(Ia) - 1, len(Ia))
    elif axis_index is not None:
        axs = axes
        axis_numbers = np.linspace(
            axis_index, axis_index + len(Ia) - 1, len(Ia))
    for idx, trace in zip(axis_numbers.astype(int), Ia):
        ax = axs[idx]
        dt = trace.stats['delta']
        npts = len(trace.data)
        t = np.linspace(0, (npts-1)*dt, num=npts)
        network = trace.stats['network']
        station = trace.stats['station']
        channel = trace.stats['channel']
        trace_label = network + '.' + station + '.' + channel
        ax.set_title(trace_label, fontsize=minfontsize)
        ax.plot(t, trace.data)
        if show_maximum:
            abs_arr = np.abs(trace.data.copy())
            idx = np.argmax(abs_arr)
            max_value = abs_arr[idx]
            ax.plot([t[idx]], [trace.data[idx]], marker='o', color="red")
            ax.annotate('%.2E' % max_value, (t[idx], trace.data[idx]),
                        xycoords='data', xytext=(.85, 0.25),
                        textcoords='axes fraction',
                        arrowprops=dict(facecolor='black',
                                        shrink=0.05, width=1, headwidth=4),
                        horizontalalignment='right', verticalalignment='top')
        ax.set_xlabel(xlabel, fontsize=minfontsize)
        ax.set_ylabel(ylabel, fontsize=minfontsize)
        ax.xaxis.set_tick_params(labelsize=minfontsize - 2)
        ax.yaxis.set_tick_params(labelsize=minfontsize - 2)
    plt.suptitle(title, y=1.01, fontsize=minfontsize + 4)
    plt.tight_layout()
    if show and axes is None:
        plt.show()
    if file is not None and axes is None:
        fig.savefig(file, format='png')
    return axs


def plot_durations(stream, durations, axes=None, axis_index=None,
                   figsize=None, file=None, minfontsize=14, show=False,
                   title=None, xlabel=None, ylabel=None):
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
        raise Exception('No traces contained within the provided stream.')

    stream = get_acceleration(stream, units='m/s/s')
    NIa = calculate_arias(stream, ['channels'], True)[1]

    starttime = stream[0].stats.starttime
    if title is None:
        title = ('Event on ' + str(starttime.month) + '/' +
                 str(starttime.day) + '/' + str(starttime.year))
    if xlabel is None:
        xlabel = 'Time (s)'
    if ylabel is None:
        ylabel = 'NIa (m/s)'

    if figsize is None:
        figsize = (6.5, 7.5)
    if axes is None:
        fig, axs = plt.subplots(len(NIa), 1, figsize=figsize)
        axis_numbers = np.linspace(0, len(NIa) - 1, len(NIa))
    elif axis_index is not None:
        axs = axes
        axis_numbers = np.linspace(
            axis_index, axis_index + len(NIa) - 1, len(NIa))
    for idx, trace in zip(axis_numbers.astype(int), NIa):
        ax = axs[idx]
        dt = trace.stats['delta']
        npts = len(trace.data)
        t = np.linspace(0, (npts-1)*dt, num=npts)
        network = trace.stats['network']
        station = trace.stats['station']
        channel = trace.stats['channel']
        trace_label = network + '.' + station + '.' + channel
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
            height = (1/(len(durations)+1) * i) + 1/(len(durations)+1)
            ax.plot(t1, first_percentile, 'ok')
            ax.plot(t2, second_percentile, 'ok')
            ax.annotate('', xy=(t1, height), xytext=(t2, height),
                        arrowprops=dict(arrowstyle='<->'))
            label = '$D_{%i{-}%i}$' % (100 * duration[0],
                                       100 * duration[1])
            ax.text(t2, height, label, style='italic',
                    horizontalalignment='left',
                    verticalalignment='center')
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


def plot_moveout(streams, epilat, epilon, channel, cmap='viridis',
                 figsize=None, file=None, minfontsize=14, normalize=False,
                 scale=1, title=None, xlabel=None, ylabel=None):
    """
    Create moveout plots.

    Args:
        stream (obspy.core.stream.Stream):
            Set of acceleration data with units of gal (cm/s/s).
        epilat (float):
            Epicenter latitude.
        epilon (float):
            Epicenter longitude.
        channel (list):
            List of channels (str) of each stream to view.
        cmap (str):
            Colormap name.
        figsize (tuple):
            Tuple of height and width. Default is None.
        file (str):
            File where the image will be saved. Default is None.
        minfontsize (int):
            Minimum font size. Default is 14.
        normalize (bool):
            Normalize the data. Default is faulse.
        scale (int, float):
            Value to scale the trace by. Default is 1.
        title (str):
            Title for plot. Default is None.
        xlabel (str):
            Label for x axis. Default is None.
        ylabel (str):
            Label for y axis. Default is None.

    Returns:
        tuple: (Figure, matplotlib.axes._subplots.AxesSubplot)
    """
    if len(streams) < 1:
        raise Exception('No streams provided.')

    colors = cm.get_cmap(cmap)
    color_array = colors(np.linspace(0, 1, len(streams)))
    if figsize is None:
        figsize = (10, len(streams))
    fig, ax = plt.subplots(figsize=figsize)
    for idx, stream in enumerate(streams):
        traces = stream.select(channel=channel)
        if len(traces) > 0:
            trace = traces[0]
            if normalize or scale != 1:
                warnings.filterwarnings("ignore", category=FutureWarning)
                trace.normalize()
            trace.data *= scale
            lat = trace.stats.coordinates['latitude']
            lon = trace.stats.coordinates['longitude']
            distance = gps2dist_azimuth(lat, lon, epilat, epilon)[0] / 1000
            times = []
            start = trace.stats.starttime
            for time in trace.times():
                starttime = start
                td = datetime.timedelta(seconds=time)
                ti = starttime + td
                times += [ti.datetime]
            label = trace.stats.network + '.' + \
                trace.stats.station + '.' + trace.stats.channel
            ax.plot(times, trace.data + distance, label=label,
                    color=color_array[idx])
    ax.invert_yaxis()
    ax.legend(bbox_to_anchor=(1, 1), fontsize=minfontsize)
    if title is None:
        title = ('Event on ' + str(starttime.month) + '/' +
                 str(starttime.day) + '/' + str(starttime.year))
        if scale != 1:
            title += ' scaled by ' + str(scale)
    if xlabel is None:
        xlabel = 'Time (H:M:S)'
    if ylabel is None:
        ylabel = 'Distance (km)'
    ax.set_title(title, fontsize=minfontsize + 4)
    ax.set_xlabel(xlabel, fontsize=minfontsize)
    ax.set_ylabel(ylabel, fontsize=minfontsize)
    ax.xaxis.set_tick_params(labelsize=minfontsize - 2)
    ax.yaxis.set_tick_params(labelsize=minfontsize - 2)
    if file is not None:
        fig.savefig(file, format='png')
    plt.show()
    return (fig, ax)

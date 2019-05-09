import os
import datetime
import warnings
import logging

from matplotlib.pyplot import cm
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from obspy.geodetics.base import gps2dist_azimuth

from gmprocess.metrics.reduction.arias import Arias
from gmprocess import spectrum
from gmprocess.metrics.oscillators import get_velocity


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

    arias = Arias(stream)
    Ia = arias.arias_stream

    starttime = stream[0].stats.starttime
    if title is None:
        title = ('Event on ' + str(starttime.month) + '/'
                 + str(starttime.day) + '/' + str(starttime.year))
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
        t = np.linspace(0, (npts - 1) * dt, num=npts)
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

    arias = Arias(stream)
    Ia = arias.arias_stream
    NIa = Ia.normalize(False)

    starttime = stream[0].stats.starttime
    if title is None:
        title = ('Event on ' + str(starttime.month) + '/'
                 + str(starttime.day) + '/' + str(starttime.year))
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
        t = np.linspace(0, (npts - 1) * dt, num=npts)
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
            height = (1 / (len(durations) + 1) * i) + 1 / (len(durations) + 1)
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
        title = ('Event on ' + str(starttime.month) + '/'
                 + str(starttime.day) + '/' + str(starttime.year))
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


def summary_plots(st, directory, origin):
    """Stream summary plot.

    Args:
        st (gmprocess.stationtrace.StationStream):
            Stream of data.
        directory (str):
            Directory for saving plots.
        origin (ScalarEvent):
            Flattened subclass of Obspy Event.
    """
    mpl.rcParams['font.size'] = 8

    # Check if directory exists, and if not, create it.
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Setup figure for stream
    nrows = 4
    ntrace = min(len(st), 3)
    fig = plt.figure(figsize=(3.8 * ntrace, 10))
    gs = fig.add_gridspec(nrows, ntrace, height_ratios=[1, 1, 2, 2])
    ax = [plt.subplot(g) for g in gs]

    stream_id = st.get_id()
    logging.debug('stream_id: %s' % stream_id)
    logging.debug('passed: %s' % st.passed)
    if st.passed:
        plt.suptitle("M%s %s | %s (passed)" %
                     (origin.magnitude, origin.id, stream_id),
                     x=0.5, y=1.02)
    else:
        plt.suptitle("M%s %s | %s (failed)"
                     % (origin.magnitude, origin.id, stream_id),
                     color='red', x=0.5, y=1.02)

    # Compute velocity
    st_vel = get_velocity(st)

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
            logging.warning('Only plotting first 3 traces in stream.')
            break

        # ---------------------------------------------------------------------
        # Get trace info
        if tr.hasParameter('snr'):
            snr_dict = tr.getParameter('snr')
        else:
            snr_dict = None

        if tr.hasParameter('signal_spectrum'):
            signal_dict = tr.getParameter('signal_spectrum')
        else:
            signal_dict = None

        if tr.hasParameter('noise_spectrum'):
            noise_dict = tr.getParameter('noise_spectrum')
        else:
            noise_dict = None

        if tr.hasParameter('smooth_signal_spectrum'):
            smooth_signal_dict = tr.getParameter('smooth_signal_spectrum')
        else:
            smooth_signal_dict = None

        if tr.hasParameter('smooth_noise_spectrum'):
            smooth_noise_dict = tr.getParameter('smooth_noise_spectrum')
        else:
            smooth_noise_dict = None

        if tr.hasParameter('snr_conf'):
            snr_conf = tr.getParameter('snr_conf')
        else:
            snr_conf = None

        trace_failed = tr.hasParameter('failure')
        if trace_failed:
            failure_reason = tr.getParameter('failure')['reason']
        else:
            failure_reason = ''

        # Note that the theoretical spectra will only be available for
        # horizontal channels
        if tr.hasParameter('fit_spectra'):
            fit_spectra_dict = tr.getParameter('fit_spectra')
        else:
            fit_spectra_dict = None

        # ---------------------------------------------------------------------
        # Compute model spectra
        if fit_spectra_dict is not None:
            model_spec = spectrum.model(
                freq=np.array(smooth_signal_dict['freq']),
                dist=fit_spectra_dict['epi_dist'],
                kappa=fit_spectra_dict['kappa'],
                magnitude=fit_spectra_dict['magnitude'],
                stress_drop=fit_spectra_dict['stress_drop']
            )

        # ---------------------------------------------------------------------
        # Acceleration time series plot
        if trace_failed:
            trace_status = " (failed)"
            trace_title = tr.get_id() + trace_status
            ax[j].set_title(trace_title, color="red")
        else:
            trace_status = " (passed)"
        trace_title = tr.get_id() + trace_status
        ax[j].set_title(trace_title)
        dtimes = tr.times('utcdatetime') - tr.times('utcdatetime')[0]
        ax[j].plot(dtimes, tr.data, 'k', linewidth=0.5)

        # Show signal split as vertical dashed line
        if tr.hasParameter('signal_split'):
            split_dict = tr.getParameter('signal_split')
            dsec = split_dict['split_time'] - tr.times('utcdatetime')[0]
            ax[j].axvline(dsec,
                          color='red', linestyle='dashed')

        ax[j].set_xlabel('Time (s)')
        ax[j].set_ylabel('Acceleration (cm/s/s)')

        # ---------------------------------------------------------------------
        # Velocity time series plot
        tr_vel = st_vel[j]
        dtimes = tr_vel.times('utcdatetime') - tr_vel.times('utcdatetime')[0]
        ax[j + ntrace].plot(dtimes, tr_vel.data, 'k', linewidth=0.5)

        # Show signal split as vertical dashed line
        if tr.hasParameter('signal_split'):
            split_dict = tr.getParameter('signal_split')
            dsec = split_dict['split_time'] - tr.times('utcdatetime')[0]
            ax[j + ntrace].axvline(dsec, color='red', linestyle='dashed')

        ax[j + ntrace].set_xlabel('Time (s)')
        ax[j + ntrace].set_ylabel('Velocity (cm/s)')

        # ---------------------------------------------------------------------
        # Spectral plot

        # Raw signal spec
        if signal_dict is not None:
            ax[j + 2 * ntrace].loglog(signal_dict['freq'],
                                      signal_dict['spec'],
                                      color='lightblue')

        # Smoothed signal spec
        if smooth_signal_dict is not None:
            ax[j + 2 * ntrace].loglog(smooth_signal_dict['freq'],
                                      smooth_signal_dict['spec'],
                                      color='blue',
                                      label='Signal')

        # Raw noise spec
        if noise_dict is not None:
            ax[j + 2 * ntrace].loglog(noise_dict['freq'],
                                      noise_dict['spec'],
                                      color='salmon')

        # Smoothed noise spec
        if smooth_noise_dict is not None:
            ax[j + 2 * ntrace].loglog(smooth_noise_dict['freq'],
                                      smooth_noise_dict['spec'],
                                      color='red',
                                      label='Noise')

        if fit_spectra_dict is not None:
            # Model spec
            ax[j + 2 * ntrace].loglog(smooth_signal_dict['freq'],
                                      model_spec,
                                      color='black',
                                      linestyle='dashed')

            # Corner frequency
            ax[j + 2 * ntrace].axvline(fit_spectra_dict['f0'],
                                       color='black',
                                       linestyle='dashed')

        ax[j + 2 * ntrace].set_xlabel('Frequency (Hz)')
        ax[j + 2 * ntrace].set_ylabel('Amplitude (cm/s)')

        # ---------------------------------------------------------------------
        # Signal-to-noise ratio plot

        if 'corner_frequencies' in tr.getParameterKeys():
            hp = tr.getParameter('corner_frequencies')['highpass']
            lp = tr.getParameter('corner_frequencies')['lowpass']
            ax[j + 3 * ntrace].axvline(hp,
                                       color='black',
                                       linestyle='--',
                                       label='Highpass')
            ax[j + 3 * ntrace].axvline(lp,
                                       color='black',
                                       linestyle='--',
                                       label='Lowpass')

        if snr_conf is not None:
            ax[j + 3 * ntrace].axhline(snr_conf['threshold'],
                                       color='0.75',
                                       linestyle='-',
                                       linewidth=2)
            ax[j + 3 * ntrace].axvline(snr_conf['max_freq'],
                                       color='0.75',
                                       linewidth=2,
                                       linestyle='-')
            ax[j + 3 * ntrace].axvline(snr_conf['min_freq'],
                                       color='0.75',
                                       linewidth=2,
                                       linestyle='-')

        if snr_dict is not None:
            ax[j + 3 * ntrace].loglog(snr_dict['freq'],
                                      snr_dict['snr'],
                                      label='SNR')

        ax[j + 3 * ntrace].set_ylabel('SNR')
        ax[j + 3 * ntrace].set_xlabel('Frequency (Hz)')

    stream_id = st.get_id()

    # Do not save files if running tests
    if 'CALLED_FROM_PYTEST' not in os.environ:
        plt.subplots_adjust(hspace=0.35, wspace=0.35, top=0.97)
        file_name = os.path.join(
            directory,
            origin.id + '_' + stream_id + '.png')
        plt.savefig(fname=file_name, bbox_inches='tight')
        plt.close('all')

    return st

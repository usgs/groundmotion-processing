# stdlib imports
import os.path

# third party imports
from obspy.geodetics.base import locations2degrees
from obspy.taup import TauPyModel
import matplotlib.pyplot as plt


def plot_raw(rawdir, tcollection, event):
    model = TauPyModel(model="iasp91")
    source_depth = event.depth_km
    eqlat = event.latitude
    eqlon = event.longitude
    for stream in tcollection:
        stlat = stream[0].stats.coordinates['latitude']
        stlon = stream[0].stats.coordinates['longitude']
        dist = locations2degrees(eqlat, eqlon, stlat, stlon)
        arrivals = model.get_travel_times(source_depth_in_km=source_depth,
                                          distance_in_degree=dist, phase_list=['P', 'p', 'Pn'])
        arrival = arrivals[0]
        arrival_time = arrival.time
        ptime = arrival_time + (event.time - stream[0].stats.starttime)
        outfile = os.path.join(rawdir, '%s.png' % stream.get_id())

        fig, axeslist = plt.subplots(nrows=3, ncols=1, figsize=(12, 6))
        for ax, trace in zip(axeslist, stream):
            ax.plot(trace.times(), trace.data, color='k')
            ax.set_xlabel('seconds since start of trace')
            ax.set_title('')
            ax.axvline(ptime, color='r')
            ax.set_xlim(left=0, right=trace.times()[-1])
            legstr = '%s.%s.%s.%s' % (trace.stats.network,
                                      trace.stats.station,
                                      trace.stats.location,
                                      trace.stats.channel)
            ax.legend(labels=[legstr], frameon=True, loc='upper left')
            tbefore = event.time + arrival_time < trace.stats.starttime + 1.0
            tafter = event.time + arrival_time > trace.stats.endtime - 1.0
            if tbefore or tafter:
                legstr = 'P arrival time %.1f seconds' % ptime
                left, right = ax.get_xlim()
                xloc = left + (right - left) / 20
                bottom, top = ax.get_ylim()
                yloc = bottom + (top - bottom) / 10
                ax.text(xloc, yloc, legstr, color='r')
        plt.savefig(outfile, bbox_inches='tight')
        print(outfile)
        x = 1

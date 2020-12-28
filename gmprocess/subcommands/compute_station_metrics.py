import os
import sys
import logging

from mapio.gmt import GMTGrid

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.io.fetch_utils import get_events, get_rupture_file
from gmprocess.io.asdf.stream_workspace import \
    StreamWorkspace, format_netsta, format_nslit
from gmprocess.utils.constants import TAG_FMT
from gmprocess.metrics.station_summary import StationSummary, XML_UNITS


class ComputeStationMetricsModule(SubcommandModule):
    """Compute station metrics.
    """
    command_name = 'compute_station_metrics'
    aliases = ('sm', )

    arguments = [
        {
            'short_flag': '-e',
            'long_flag': '--eventid',
            'help': ('Comcat event ID. If None (default) all events in '
                     'project data directory will be used.'),
            'type': str,
            'default': None,
            'nargs': '+'
        }
    ]

    def main(self, gmp):
        """Compute station metrics.

        Args:
            gmp: GmpApp instance.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)

        events = get_events(
            eventids=gmp.args.eventid,
            textfile=None,
            eventinfo=None,
            directory=gmp.data_path,
            outdir=None
        )

        vs30_grids = None
        if gmp.conf is not None:
            if 'vs30' in gmp.conf['metrics']:
                vs30_grids = gmp.conf['metrics']['vs30']
                for vs30_name in vs30_grids:
                    vs30_grids[vs30_name]['grid_object'] = GMTGrid.load(
                        vs30_grids[vs30_name]['file'])

        label = None

        for event in events:
            event_dir = os.path.join(gmp.data_path, event.id)
            workname = os.path.join(event_dir, 'workspace.hdf')
            if not os.path.isfile(workname):
                logging.info(
                    'No workspace file found for event %s. Please run '
                    'subcommand \'assemble\' to generate workspace file.'
                    % event.id)
                logging.info('No waveforms to process.')
                logging.info('Continuing to next event.')
                continue
            workspace = StreamWorkspace.open(workname)
            labels = workspace.getLabels()
            if len(labels):
                labels.remove('unprocessed')
            else:
                logging.info('No processed waveform data in workspace. Please '
                             'run assemble.')
                sys.exit(1)

            # If there are more than 1 processed labels, prompt user to select
            # one.
            if len(labels) > 1 and label is not None:
                print('Which label do you want to use?')
                for labs in labels:
                    print('\tlab')
                tmplab = input()
                if tmplab not in labels:
                    raise ValueError('%s not a valid label. Exiting.' % tmplab)
                else:
                    label = tmplab
            else:
                label = labels[0]

            pstreams = workspace.getStreams(
                event.id, labels=[label])

            rupture_file = get_rupture_file(event_dir)
            # workspace.calcMetrics(
            #     event.id, labels=[process_tag], config=gmp.conf,
            #     streams=pstreams, stream_label=label,
            #     rupture_file=rupture_file)

            for stream in pstreams:
                summary = StationSummary.from_config(
                    stream, event=event, config=gmp.conf,
                    calc_waveform_metrics=False,
                    calc_station_metrics=True,
                    rupture=rupture_file, vs30_grids=vs30_grids)
                xmlstr = summary.get_metric_xml()
                xmlstr = summary.get_station_xml()
                metricpath = '/'.join([
                    format_netsta(stream[0].stats),
                    format_nslit(stream[0].stats, stream.get_inst(), event.id)
                ])
                workspace.insert_aux(xmlstr, 'StationMetrics', metricpath)

            workspace.close()
            logging.info('Computed station metrics for event %s...' % event.id)

        logging.info('Added station metrics to workspace files '
                     'with tag \'%s\'.' % label)
        logging.info('No new files created.')

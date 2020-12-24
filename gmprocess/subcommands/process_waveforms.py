
import logging
import warnings

from h5py.h5py_warnings import H5pyDeprecationWarning

from gmprocess.subcommands.base import SubcommandModule
from gmprocess.waveform_processing.processing import process_streams


class ProcessWaveformsModule(SubcommandModule):
    """
    Process data using steps defined in configuration file.
    """
    command_name = 'process_waveforms'
    aliases = ('process', )

    arguments = [
        {
            'short_flag': '-l',
            'long_flag': '--label',
            'help': ('Processing label (single word, no spaces) to attach to '
                     'processed files. Defaults to the current time in '
                     'YYYYMMDDHHMMSS format.'),
            'type': str,
            'default': None,
            'nargs': 1
        }, {
            'short_flag': '-n',
            'long_flag': '--num-processes',
            'help': 'Number of parallel processes to run over events.',
            'type': int,
            'default': 0,
            'nargs': 1
        }
    ]

    def main(self, gmp):
        """

        Args:
            gmp: GmpApp instance.
        """
        logging.info('Running %s.' % self.command_name)
        with warnings.catch_warnings():
            warnings.simplefilter(
                "ignore", category=H5pyDeprecationWarning)
            rstreams = workspace.getStreams(
                event.id, labels=['unprocessed'])
        download_done = True

        logging.info('Processing raw streams for event %s...' % event.id)
        pstreams = process_streams(rstreams, event, config=self.conf)
        with warnings.catch_warnings():
            warnings.simplefilter(
                "ignore", category=H5pyDeprecationWarning)
            workspace.addStreams(event, pstreams, label=process_tag)
            workspace.calcMetrics(
                event.id, labels=[process_tag], config=config,
                streams=pstreams, stream_label=process_tag,
                rupture_file=rupture_file)
        processing_done = True


import logging
import warnings

from gmprocess.commands.base import CoreModule
from gmprocess.waveform_processing.processing import process_streams


class ProcessModule(CoreModule):
    """
    Process data using steps defined in configuration file.
    """
    command_name = 'process'

    def __init__(self, eventid):
        pass

    def execute(self):
        """
        """
        logging.info('Getting raw streams from workspace...')
        with warnings.catch_warnings():
            warnings.simplefilter("ignore",
                                  category=H5pyDeprecationWarning)
            rstreams = workspace.getStreams(event.id,
                                            labels=['unprocessed'])
        download_done = True

        logging.info('Processing raw streams for event %s...' % event.id)
        pstreams = process_streams(rstreams, event, config=config)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore",
                                  category=H5pyDeprecationWarning)
            workspace.addStreams(event, pstreams, label=process_tag)
            workspace.calcMetrics(
                event.id, labels=[process_tag], config=config,
                streams=pstreams, stream_label=process_tag,
                rupture_file=rupture_file)
        processing_done = True

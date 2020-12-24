import logging


from gmprocess.commands.base import CoreModule
from gmprocess.io.fetch_utils import save_shakemap_amps


class ShakemapModule(CoreModule):
    """
    Generate ShakeMap-friendly peak ground motions data file.
    """
    command_name = 'shakemap'

    def __init__(self, eventid):
        pass

    def execute(self):
        """
        """
        logging.info(
            'Creating shakemap table for event %s...' % event.id)
        shakemap_file, jsonfile = save_shakemap_amps(
            pstreams, event, event_dir)
        append_file(files_created, 'shakemap', shakemap_file)
        append_file(files_created, 'shakemap', jsonfile)

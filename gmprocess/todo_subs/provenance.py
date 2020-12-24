import logging
import warnings
import os

from gmprocess.commands.base import CoreModule


class ProvenanceModule(CoreModule):
    """
    Generate provenance table
    """
    command_name = 'provenance'

    def __init__(self, eventid):
        pass

    def execute(self):
        """
        """
        logging.info(
            'Creating provenance table for event %s...' % event.id)
        with warnings.catch_warnings():
            warnings.simplefilter(
                "ignore", category=H5pyDeprecationWarning)
            provdata = workspace.getProvenance(
                event.id, labels=[process_tag])
        if output_format == 'csv':
            csvfile = os.path.join(event_dir, 'provenance.csv')
            append_file(files_created, 'Provenance', csvfile)
            provdata.to_csv(csvfile)
        else:
            excelfile = os.path.join(event_dir, 'provenance.xlsx')
            append_file(files_created, 'Provenance', excelfile)
            provdata.to_excel(excelfile, index=False)

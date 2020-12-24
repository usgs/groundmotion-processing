import logging


from gmprocess.commands.base import CoreModule


class FailuresModule(CoreModule):
    """
    Output failure information.

    Output can be in short form ("short"), long form ("long"), or network form
    ("net"). short: Two column table, where the columns are "failure reason"
    and "number of records". net: Three column table where the columns are
    "network", "number passed", and "number failed". long: Two column table,
    where columns are "station ID" and "failure reason"
    """
    command_name = 'failures'

    def __init__(self, eventid):
        pass

    def execute(self):
        """
        """
        if status == 'short':
            index = 'Failure reason'
            col = ['Number of records']
        elif status == 'long':
            index = 'Station ID'
            col = ['Failure reason']
        elif status == 'net':
            index = 'Network'
            col = ['Number of passed records', 'Number of failed records']

        status_info = pstreams.get_status(status)
        status_info.to_csv(os.path.join(event_dir, 'status.csv'), header=col,
                           index_label=index)

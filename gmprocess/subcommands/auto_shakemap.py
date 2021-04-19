#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from gmprocess.subcommands.arg_dicts import ARG_DICTS
from gmprocess.subcommands.base import SubcommandModule

from gmprocess.apps.gmrecords import GMrecordsApp
from gmprocess.subcommands.download import DownloadModule
from gmprocess.subcommands.import_data import ImportModule
from gmprocess.subcommands.assemble import AssembleModule
from gmprocess.subcommands.process_waveforms import ProcessWaveformsModule
from gmprocess.subcommands.compute_station_metrics import \
    ComputeStationMetricsModule
from gmprocess.subcommands.compute_waveform_metrics import \
    ComputeWaveformMetricsModule
from gmprocess.subcommands.export_metric_tables import ExportMetricTablesModule
from gmprocess.subcommands.export_shakemap import ExportShakeMapModule
from gmprocess.subcommands.generate_regression_plot import \
    GenerateRegressionPlotModule
from gmprocess.subcommands.generate_report import GenerateReportModule


class AutoShakemapModule(SubcommandModule):
    """Chain together subcommands to get shakemap ground motion file.
    """
    command_name = 'auto_shakemap'

    arguments = [
        ARG_DICTS['eventid'], {
            'short_flag': '-p',
            'long_flag': '--path',
            'help': ('Path to external data file or directory. If given, '
                     'then the download step is also skipped.'),
            'type': str,
            'default': None
        }, {
            'long_flag': '--skip-download',
            'help': 'Skip data downlaod step.',
            'default': False,
            'action': 'store_true'
        }, {
            'short_flag': '-d',
            'long_flag': '--diagnostics',
            'help': ('Include diagnostic outputs that are created after '
                     'ShakeMap data file is created.'),
            'default': False,
            'action': 'store_true'
        }
    ]

    def main(self, gmrecords):
        """Chain together subcommands to get shakemap ground motion file.
        """
        logging.info('Running subcommand \'%s\'' % self.command_name)
        gmrecords = GMrecordsApp()
        # Hard code overwrite to True since this is all meant to run end-to-end
        # without interruption.
        gmrecords.args.overwrite = True

        # Chain together relevant subcommand modules:
        if ((not gmrecords.args.skip_download)
                and (gmrecords.args.path is None)):
            DownloadModule().main(gmrecords)
        if gmrecords.args.path is not None:
            ImportModule().main(gmrecords)
        AssembleModule().main(gmrecords)
        ProcessWaveformsModule().main(gmrecords)
        ComputeStationMetricsModule().main(gmrecords)
        ComputeWaveformMetricsModule().main(gmrecords)
        ExportShakeMapModule().main(gmrecords)
        if gmrecords.args.diagnostics:
            ExportMetricTablesModule().main(gmrecords)
            GenerateRegressionPlotModule().main(gmrecords)
            GenerateReportModule().main(gmrecords)

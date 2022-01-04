#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import glob

from gmprocess.subcommands.lazy_loader import LazyLoader

pd = LazyLoader("pd", globals(), "pandas")

base = LazyLoader("base", globals(), "gmprocess.subcommands.base")
plot = LazyLoader("plot", globals(), "gmprocess.utils.plot")
const = LazyLoader("const", globals(), "gmprocess.utils.constants")


class GenerateRegressionPlotModule(base.SubcommandModule):
    """Generate multi-event \"regression\" plot."""

    command_name = "generate_regression_plot"
    aliases = ("regression",)

    arguments = []

    def main(self, gmrecords):
        """Generate multi-event \"regression\" plot.

        Args:
            gmrecords:
                GMrecordsApp instance.
        """
        logging.info(f"Running subcommand '{self.command_name}'")

        self.gmrecords = gmrecords
        self._check_arguments()

        imc_table_names = [
            file.replace("_README", "")
            for file in os.listdir(self.gmrecords.data_path)
            if "README" in file
        ]

        imc_tables = {}
        for file in imc_table_names:
            imckey = os.path.splitext(file)[0]
            imc_tables[imckey] = pd.read_csv(
                os.path.normpath(os.path.join(self.gmrecords.data_path, file))
            )
            if "fit_spectra_parameters" in imc_tables:
                del imc_tables["fit_spectra_parameters"]

        # TODO - where is this being written? Is it a requirement?
        # It appears this is being written in gmprocess2 and
        # generate_metric_tables.py, and it gets appended to when re-run.
        event_files = glob.glob(os.path.join(self.gmrecords.data_path, "*_events.*"))
        if len(event_files) == 1:
            event_file = event_files[0]
        elif len(event_files) == 0:
            print("No event file found. Cannot build regression plot.")
            print("Please run 'gmrecords export_metric_tables'.")
            sys.exit(1)
        else:
            print("Multiple event files found, please select one:")
            for e in event_files:
                print(f"\t{e}")
            event_file = input("> ")
        event_table = pd.read_csv(event_file).drop_duplicates()

        # make a regression plot of the most common imc/imt combination we
        # can find
        if not len(imc_tables):
            msg = """No IMC tables found. It is likely that no streams
            passed checks. If you created reports for the events you
            have been processing, check those to see if this is the case,
            then adjust your configuration as necessary to process the data.
            """
            logging.warning(msg)
        else:
            pref_imcs = [
                "rotd50.0",
                "greater_of_two_horizontals",
                "h1",
                "h2",
            ]
            pref_imts = ["PGA", "PGV", "SA(1.000)"]
            found_imc = None
            found_imt = None
            tab_key_list = list(imc_tables.keys())
            tab_key_imcs = [k.split("_")[-1] for k in tab_key_list]
            tab_key_dict = dict(zip(tab_key_imcs, tab_key_list))
            for imc in pref_imcs:
                if imc in tab_key_imcs:
                    for imt in pref_imts:
                        if imt in imc_tables[tab_key_dict[imc]].columns:
                            found_imt = imt
                            found_imc = imc
                            break
                    if found_imc:
                        break

            # now look for whatever IMC/IMTcombination we can find
            if imc_tables and not found_imc:
                found_imc = list(imc_tables.keys())[0]
                table_cols = set(imc_tables[found_imc].columns)
                imtlist = list(table_cols - const.NON_IMT_COLS)
                found_imt = imtlist[0]

            if found_imc and found_imt:
                pngfile = f"regression_{found_imc}_{found_imt}.png"
                regression_file = os.path.normpath(
                    os.path.join(self.gmrecords.data_path, pngfile)
                )
                plot.plot_regression(
                    event_table,
                    found_imc,
                    imc_tables[tab_key_dict[found_imc]],
                    found_imt,
                    regression_file,
                    distance_metric="EpicentralDistance",
                    colormap="viridis_r",
                )
                self.append_file("Multi-event regression plot", regression_file)

        self._summarize_files_created()

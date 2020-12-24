import os
import logging


from gmprocess.commands.base import CoreModule


class ExportModule(CoreModule):
    """
    Export ground motion metrics tables.
    """
    command_name = 'export'

    def __init__(self, eventid):
        pass

    def execute(self):
        """
        """
        if export_dir is not None:
            if not os.path.isdir(export_dir):
                os.makedirs(export_dir)
            outdir = export_dir

        labels = workspace.getLabels()
        if 'unprocessed' not in labels:
            fmt = ('Workspace file "%s" appears to have no unprocessed '
                   'data. Skipping.')
            logging.info(fmt % workspace_file)
        else:
            labels.remove('unprocessed')
            if not labels:
                fmt = ('Workspace file "%s" appears to have no processed '
                       'data. Skipping.')
                logging.info(fmt % workspace_file)
            else:
                logging.info('Creating tables for event %s...', event.id)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore",
                                          category=H5pyDeprecationWarning)
                    if recompute_metrics:
                        del workspace.dataset.auxiliary_data.WaveFormMetrics
                        del workspace.dataset.auxiliary_data.StationMetrics
                        workspace.calcMetrics(
                            event.id, labels=labels, config=config,
                            rupture_file=rupture_file)
                    event_table, imc_tables, readmes = workspace.getTables(
                        labels[0], streams=pstreams, stream_label=process_tag)
                    ev_fit_spec, fit_readme = workspace.getFitSpectraTable(
                        event.id, labels[0], pstreams)

                # Set the precisions for the imc tables, event table, and
                # fit_spectra table before writing
                imc_tables_formatted = {}
                for imc, imc_table in imc_tables.items():
                    imc_tables_formatted[imc] = set_precisions(imc_table)
                event_table_formatted = set_precisions(event_table)
                df_fit_spectra_formatted = set_precisions(ev_fit_spec)

                if not os.path.isdir(outdir):
                    os.makedirs(outdir)

                filenames = ['events'] + [
                    imc.lower() for imc in imc_tables_formatted.keys()] + [
                    imc.lower() + '_README' for imc in readmes.keys()] + [
                    'fit_spectra_parameters', 'fit_spectra_parameters_README']

                files = [event_table_formatted] + list(
                    imc_tables_formatted.values()) + list(
                    readmes.values()) + [df_fit_spectra_formatted, fit_readme]

                if output_format != 'csv':
                    output_format = 'xlsx'

                for filename, df in dict(zip(filenames, files)).items():
                    filepath = os.path.join(
                        outdir, filename + '.%s' % output_format)
                    if os.path.exists(filepath):
                        if 'README' in filename:
                            continue
                        else:
                            mode = 'a'
                            header = False
                    else:
                        mode = 'w'
                        header = True
                        append_file(files_created, 'Tables', filepath)
                    if output_format == 'csv':
                        df.to_csv(filepath, index=False,
                                  float_format=DEFAULT_FLOAT_FORMAT,
                                  na_rep=DEFAULT_NA_REP,
                                  mode=mode, header=header)
                    else:
                        df.to_excel(filepath, index=False,
                                    float_format=DEFAULT_FLOAT_FORMAT,
                                    na_rep=DEFAULT_NA_REP,
                                    mode=mode, header=header)

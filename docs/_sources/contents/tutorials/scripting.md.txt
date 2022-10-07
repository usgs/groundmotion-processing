---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: '0.8'
    jupytext_version: '1.4.1'
kernelspec:
  display_name: Python 3
  language: python
  name: python3
mystnb:
  execution_timeout: 120
---
# Scripting

You can write Python scripts that call the `GMrecordsApp` application to create high-level workflows.
In the example below we create a Python script to run several subcommands to download and process ground motions recorded close to the epicenter of a magnitude 4.5 earthquake, and then export the results to CSV files and generate a report summarizing the results.

## Local `gmprocess` configuration

In this example we specify parameters in the project configuration to produce a small dataset.
We use only the FDSN fetcher and limit the station distance to 0.1 degrees.
The configuration files are in the `conf/scripting` directory.
First, we first create the project `data` directory, and then we use the `projects` subcommand to select the project configuration `cli-tutorial` from the tutorial projects listed in the `.gmprocess/projects.conf` file.

```{code-cell} ipython3
!mkdir -p data/cli data/scripting
!gmrecords projects --switch scripting-tutorial
```

At this point we have an empty `data/scripting` directory.
The `conf/scripting` directory has two files: `fetchers/yml` and `user.yml`.
These configuration files hold parameters that override default values provided with the source code.
See [Configuration File](../manual/config_file) for more information.

## Download Data

In this example we will consider ground motions recorded for a [magnitude 4.5 earthquake](https://earthquake.usgs.gov/earthquakes/eventpage/nc73291880/executive) east of San Francisco, California.
We have cached the results of running `gmrecords download --eventid nc73291880` in the `tests/data/tutorials` directory.
Consequently, we simply copy the data from `tests/data/tutorials/nc73291880` to `data/scripting/nc73291880`.

```{code-cell} ipython3
!cp -r ../../../tests/data/tutorials/nc73291880 data/scripting/
```

### List Data

We now have earthquake rupture information and raw waveforms in the `data/scripting` directory.

```{code-cell} ipython3
!tree data/scripting
```

## Python Script

```{code-cell} ipython3
# Import the application
from gmprocess.apps.gmrecords import GMrecordsApp

# Create a list of subcommands we will run.
STEPS = (
    'assemble',
    'process_waveforms',
    'compute_station_metrics',
    'compute_waveform_metrics',
    'export_metric_tables',
    'generate_report',
    'generate_station_maps',
    )

# Initialize the application
app = GMrecordsApp()
app.load_subcommands()

# Create a dictionary with the arguments common to all subcommands.
# We must include arguments that normally are given default values by
# the command line argument parser.
args = {
    'debug': False,
    'quiet': False,
    'eventid': None,
    'textfile': None,
    'overwrite': False,
    }

# Loop through the subcommands.
for step in STEPS:
    print(f"Running '{step}'...")

    # Update the arguments dictionary with subcommand specific information.
    # Each step has its own log file with the name $STEP.log.
    step_args = {
        'subcommand': step,
        'func': app.classes[step]['class'],
        'log': f"{step}.log",
        }
    args.update(step_args)

    # Run the current subcommand
    app.main(**args)
```

Running the script will produce CSV files with the waveform metrics in the `data/scripting` directory and reports in the `data/scripting/nc73291880` directory.

```term
ls -1 data/scripting/*.csv

data/scripting/scripting-tutorial_default_events.csv
data/scripting/scripting-tutorial_default_fit_spectra_parameters.csv
data/scripting/scripting-tutorial_default_fit_spectra_parameters_README.csv
data/scripting/scripting-tutorial_default_metrics_h1.csv
data/scripting/scripting-tutorial_default_metrics_h1_README.csv
data/scripting/scripting-tutorial_default_metrics_h2.csv
data/scripting/scripting-tutorial_default_metrics_h2_README.csv
data/scripting/scripting-tutorial_default_metrics_rotd50.0.csv
data/scripting/scripting-tutorial_default_metrics_rotd50.0_README.csv
data/scripting/scripting-tutorial_default_metrics_z.csv
data/scripting/scripting-tutorial_default_metrics_z_README.csv
data/scripting/scripting-tutorial_default_snr.csv
data/scripting/scripting-tutorial_default_snr_README.csv
```

```term
ls -1 data/scripting/nc73291880/*.pdf data/scripting/nc73291880/*.html

data/scripting/nc73291880/scripting-tutorial_default_report_nc73291880.pdf
data/scripting/nc73291880/stations_map.html
```

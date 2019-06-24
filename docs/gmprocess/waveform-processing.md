# Waveform processing

:TODO: Add general description. Point to configuration.

## Processing waveforms from FDSN data centers

:TODO: Describe processing steps to be performed and parameters.

Run the following command:

```bash
gmprocess ~/data/us2000j4df \
    -i us2000j4df \
    -c ~/data/us2000j4df/fdsn_config.yml \
    --directory ~/data/us2000j4df/raw
```

lots of logging output will stream by - you can save this to a file to be
inspected later by amending the command:

```bash
gmprocess ~/data/us2000j4df \
    -i us2000j4df \
    -c ~/data/us2000j4df/fdsn_config.yml \
    --directory ~/data/us2000j4df/raw \
    -l ~/data/us2000j4df/process.log
```

Without all of the logging output, you should see results that look
something like this:
```bash
Data from 3 stations saved to /Users/USER/data/us2000j4df
Metrics: /Users/USER/data/us2000j4df/us2000j4df_metrics.xlsx
Waveforms: /Users/USER/data/us2000j4df/us2000j4df_workspace.hdf
Provenance (processing history): /Users/USER/data/us2000j4df/us2000j4df_provenance.xlsx
A station map has been saved to /Users/USER/data/us2000j4df/station_map.png
3 plots saved to /Users/USER/data/us2000j4df/plots.
Processing Report (PDF): /Users/USER/data/us2000j4df/gmprocess_report.pdf
```

If you open up the `gmprocess_report.pdf` file, you will see summary plots for
each station, each on their own page. You will notice that the Z channel for
the *BLUF* station failed an amplitude check. Without getting into why the
values for this channel are so high, let's modify the pre-testing portion of
the configuration to allow this channel to pass checks. Add the following
section to your custom config file (comments omitted here for brevity):

```yaml
processing:
    - check_free_field:
        reject_non_free_field: True

    - check_max_amplitude:
        min: 5
        ###################This is the field we are changing###############
        max: 3e6

    - max_traces:
        n_max: 3

    - detrend:
        detrending_method: demean

    - check_sta_lta:
        sta_length: 1.0
        lta_length: 20.0
        threshold: 3.0

    - remove_response:
        # Outuput units. Must be 'ACC', 'VEL', or 'DISP'.
        output: 'ACC'
        f1: 0.001
        f2: 0.005
        f3: Null
        f4: Null
        water_level: 60

    - detrend:
        detrending_method: linear

    - detrend:
        detrending_method: demean

    - compute_snr:
        bandwidth: 20.0
        check:
            threshold: 3.0
            min_freq: 0.2
            max_freq: 5.0

    - get_corner_frequencies:
        method: constant
        constant:
            highpass: 0.08
            lowpass: 20.0
        snr:
            same_horiz: True

    - cut:
        sec_before_split: 2.0

    - taper:
        type: hann
        width: 0.05
        side: both

    - highpass_filter:
        filter_order: 5
        number_of_passes: 2

    - lowpass_filter:
        filter_order: 5
        number_of_passes: 2

    - detrend:
        detrending_method: baseline_sixth_order

    - fit_spectra:
        kappa: 0.035

    - summary_plots:
        directory: 'plotdir'
```

Once those changes are saved, run the same command again:

```bash
gmprocess ~/data/us2000j4df \
    -i us2000j4df \
    -c ~/data/us2000j4df/fdsn_config.yml \
    --directory ~/data/us2000j4df/raw \
    -l ~/data/us2000j4df/process.log
```

Taking a look at the processing report shows that all streams have passed,
although at the time of this writing the P-wave pickers could stand to be
improved. (This is under consideration.)


## Processing Data From Other Sources

CESMD holds data for many historic U.S. events that cannot be found elsewhere,
and as noted in the *Formats* documentation, these data can come in a variety
of formats. As an example, the CESMD interface should allow you to find data
for the M5.7 Oklahoma event of November 6, 2011. We were able to find 6
stations of data, plus another two stations using the FDSN search capabilities
described above. If you save these files (CESMD files may be contained in a
couple of layers of zip files, these should be unpacked down to raw files) in a
directory with the data files found via FDSN, you can process them all using a
command similar to the one below:

```bash
gmprocess ~/tmp/usp000jadn \
    -i usp000jadn \
    --directory ~/data/usp000jadn/raw/
```

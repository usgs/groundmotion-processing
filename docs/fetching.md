# Fetching Data

We believe one of the common use cases with gmprocess will be to retrieve data
associated with a particular event, process it automatically, and generate
stream metrics (i.e., components Rotd50 and greater of two horizontals, and
intensity measures like PGA and MMI).

To this end we have created the `datafetch` program, which allows a mostly
automated workflow for finding, downloading, and processing significant motion
data and extracting summary information from it.

## Data Sources

Some sources of significant motion data are:

 - FDSN Services like IRIS in the United States and ORFEUS in Europe provide 
   access to continuous broadband/strong motion waveform data from many 
   networks around the globe.
 - The Center for Engineering Strong Motion Data (CESMD) in California, which 
   contains partially processed triggered records for older events inside the U.S.
 - GeoNet in New Zealand provides an FTP service for downloading partially 
   processed triggered strong motion sensor data.
 - The Japanese National Research Institute for Earth Science and Disaster 
   Resilience provides strong motion data from two networks, KNET and KikNet.
 - The National Strong-Motion Network of Turkey (TR-NSMN) provides partially 
   processed triggered strong motion sensor data.
 - The Taiwan Central Weather Bureau (CWB) collects triggered strong motion
   data, but it is not generally publicly available.
 - The Iranian Road, Housing & Urban Development Research Center (BHRC) provides partially 
   processed triggered strong motion sensor data on their website.

Data from some of these services (FDSN, GeoNet, KNET, and NSMN at the time of
this writing) can be downloaded automatically using the `datafetch` tool. Iran
provides a web interface for downloading data (with a usage/citation
agreement). Taiwan provides no public access to their data at this time. CESMD,
at the time of this writing, is implementing an FDSN-compatible web interface to
their extensive archive of data. 

## Datafetch

## Workflows

### Downloading FDSN Data

Particularly for data requests from FDSN networks, it can be helpful to iterate
with different fetching parameters before starting on processing the data and
extracting metrics. The `datafetch` program by default uses the configuration
file found in the gmprocess repository for fetching and processing data, as
well as calculating metrics. Optionally you can provide a custom configuration
file with different parameters. These custom files need not specify the
parameters for all of the sections.

Here is a sample configuration file that modifies only the FDSN portion of the
`fetchers` section:

```
fetchers:
    FDSNFetcher:
        # search radius in dd
        radius : 2
        # seconds before arrival time
        time_before : 5 
        # seconds after arrival time
        time_after : 90
        channels : ["HN[ZNE]"] # only get strong motion stations
```

If you know that your request is *not* in Japan, New Zealand, or Turkey, then
this is the only part of the fetchers configuration you need to modify. For the
purposes of this exercise, create a ~/data/us2000j4df directory. Save the
configuration snippet above to ~/data/us2000j4df/fdsn_config.yml.

*NB*: *us2000j4df* here is the ANSS Comprehensive Catalog (ComCat) ID for a M4.0
earthquake in Kansas in early 2019: https://earthquake.usgs.gov/earthquakes/eventpage/us2000j4df/executive

Run the following command:

```
datafetch ~/data/us2000j4df -i us2000j4df -f excel -c ~/data/us2000j4df/fdsn_config.yml -o
```

`datafetch` can use ComCat IDs like this to retrieve basic event information
or, if the event does not exist in ComCat (more likely for events less than
M4.5 in areas outside the U.S.), you can specify the event by calling
`datafetch` this way:

```
datafetch ~/data/us2000j4df -e 2019-01-16T03:34:30 37.065 -97.354 5.0 4.0 -f excel -c ~/data/us2000j4df/fdsn_config.yml -o
```

where the arguments to `-e` are time (YYYY-MM-DDTHH:MM:SS format), latitude,
longitude, depth, and magnitude.

Either way, this command should download three stations worth of data to
~/data/us2000j4df/raw as MiniSEED and StationXML files (what gmprocess
considers the "FDSN" format.) It will also use the Obspy plotting functionality
to make plots of these raw waveforms, like this:

<figure>
  <img width="800px" src="figs/OK.BLUF.HN_90sec.png" alt="Stream plot"/>
  <figcaption>Sample plot of a waveform stream downloaded via FDSN (95 seconds duration)</figcaption>
</figure>

The peaks are visible here, but we are perhaps cutting off some of the latter
part of the signal, so we can adjust the `time_after` field to be 180 seconds.

Edit your custom config file, and re-run the command above. Your time series plot should now look more like this:

<figure>
  <img width="800px" src="figs/OK.BLUF.HN_180sec.png" alt="Stream plot"/>
  <figcaption>Sample plot of a waveform stream downloaded via FDSN (185 seconds duration)</figcaption>
</figure>

Iterate with the configuration as you see fit. Once you are happy with the data
that's been downloaded, you can try processing and extracting metrics from the waveforms.

Run the following command:

```
datafetch ~/data/us2000j4df -i us2000j4df -f excel -c ~/data/us2000j4df/fdsn_config.yml --directory ~/data/us2000j4df/raw
```

lots of logging output will stream by - you can save this to a file to be inspected later by amending the command:

```
datafetch ~/data/us2000j4df -i us2000j4df -f excel -c ~/data/us2000j4df/fdsn_config.yml --directory ~/data/us2000j4df/raw -l ~/data/us2000j4df/process.log
```

Without all of the logging output, you should see results that look something like this:
```
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

```
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

```
datafetch ~/data/us2000j4df -i us2000j4df -f excel -c ~/data/us2000j4df/fdsn_config.yml --directory ~/data/us2000j4df/raw -l ~/data/us2000j4df/process.log
```

Taking a look at the processing report shows that all streams have passed,
although at the time of this writing the P-wave pickers could stand to be
improved. (This is under consideration.)

### Downloading Triggered Data

Downloading triggered data from one of the supported sites (Japan, New Zealand,
and Turkey) is somewhat easier, with Japan being a minor exception. In order to
download KNET/KikNet data, you must first create an account here:

https://hinetwww11.bosai.go.jp/nied/registration/?LANG=en

And then put your username and password information into the fetchers section
of a custom config file, inserting your new username and password:

```
fetchers:
    KNETFetcher:
        user: YOUR_USERNAME
        password: YOUR_PASSWORD
        # define the distance search radius (km)
        radius : 100
        # define the time search threshokd (sec)
        dt : 60
        # define the depth search threshokd (km)
        ddepth : 30
        # define the magnitude search threshokd (km)
        dmag : 0.3
```

Save this configuration to ~/data/jp_config.yml, then run the following command:

```
datafetch ~/data/us1000jd8k -i us1000jd8k -f excel -c ~/data/jp_config.yml
```

Triggered data like this does not allow for any customization of the search
window for individual traces - the parameters above are instead used to find
matching events on the source websites. For example, `datafetch` would take the
origin time and hypocenter for event *us1000jd8k* from ComCat, and search the
NIED website for events within a 100 km distance radius and a time window of
+/- 60 seconds. Depth and magnitude thresholds are not currently used, but may
be in the future.

The above command should download 160 stations, and processing may take tens of
minutes, depending on the performance of the system on which it is running.

Retrieving triggered data from New Zealand or Turkey should be much the same.

### Processing Data From Other Sources

CESMD holds data for many historic U.S. events that cannot be found elsewhere,
and as noted in the *Formats* documentation, these data can come in a variety
of formats. As an example, the CESMD interface should allow you to find data
for the M5.7 Oklahoma event of November 6, 2011. We were able to find 6
stations of data, plus another two stations using the FDSN search capabilities
described above. If you save these files (CESMD files may be contained in a
couple of layers of zip files, these should be unpacked down to raw files) in a
directory with the data files found via FDSN, you can process them all using a
command similar to the one below:

```
datafetch ~/tmp/usp000jadn -i usp000jadn -f excel --directory ~/data/usp000jadn/raw/
```


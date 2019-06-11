# Fetching waveforms from data centers using gmprocess

## The Anatomy of a gmprocess command

A `gmprocess` command has *positional* and *optional* parameters. The positional parameters
are:
 - The output directory where event data directories will be stored.
 - A set of *commands* that will perform various operations:
    - assemble: Download data from all available online sources, or load raw data from files if --directory is selected.
    - process: Process data using steps defined in configuration file.
    - report: Create a summary report for each event specified.
    - provenance: Generate provenance table in --format format.
    - export: Generate metrics tables (NGA-style "flat" files) for all events and IMCs.
    - shakemap: Generate ShakeMap-friendly peak ground motions table.

The optional parameters, generally speaking, are used to modify the behavior of the commands above.
There are four optional parameters that modify the behavior of the `assemble` command:
 - `-i`: Specify 1 to many ComCat event IDs.
 - `-e`: Specify information for a single event
 - `-t, --textfile`: Specify a text file with *either* a list of ComCat IDs OR space separated values of ID,TIME,LAT,LON,DEPTH,MAG.
 - `--directory`: Sidestep online data retrieval, read from local directory. This
    directory should contain any number of event data directories, which
    should contain data files in a known format and an event.json file,
    which should be the JSON form of a dictionary with fields: id, time,
    lat, lon, depth, magnitude. The id field must match the event
    directory name.

The commands can be specified in any order, but there are certain dependencies within the code:
 - processing requires that assembly has already occurred.
 - reporting, provenance, exporting, and shakemap file generation require that processing has been performed.

## gmprocess Output

Running gmprocess will generate a nested data structure. For example, the command:

```bash
gmprocess /data/nocal assemble process report provenance export -i nc72282711 nc72507396
```
 will result in a directory structure that looks like this:
```
 /data/nocal
            |
            +-- *.csv (IMC tables, plus events.csv)
            +-- <CHOSENIMC_CHOSEN_IMT>.png (regression plot)
            |    
            +-- nc72282711
            |  |  
            |  +-- report_nc72282711.pdf
            |  +-- stations_map.png
            |  +-- workspace.hdf
            |  +-- provenance.csv
            |    
            +-- nc72507396
            |  |  
            |  +-- report_nc72507396.pdf
            |  +-- stations_map.png
            |  +-- workspace.hdf
            |  +-- provenance.csv
```


## Downloading FDSN Data

Particularly for data requests from FDSN networks, it can be helpful to iterate
with different fetching parameters before starting on processing the data and
extracting metrics. The `gmprocess` program by default uses the configuration
file found in the gmprocess repository for fetching and processing data, as
well as calculating metrics. Optionally you can provide a custom configuration
file with different parameters. These custom files need not specify the
parameters for all of the sections.

Here is a sample configuration file that modifies only the FDSN portion of the
`fetchers` section:

```yaml
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
earthquake in Kansas in early 2019:
https://earthquake.usgs.gov/earthquakes/eventpage/us2000j4df/executive

Run the following command:

```bash
gmprocess ~/data/us2000j4df \
    ass \
    -i us2000j4df \
    -c ~/data/us2000j4df/fdsn_config.yml
```

`gmprocess` can use ComCat IDs like this to retrieve basic event information
or, if the event does not exist in ComCat (more likely for events less than
M4.5 in areas outside the U.S.), you can specify the event by calling
`gmprocess` this way:

```bash
gmprocess ~/data/us2000j4df \
    -o \
    -e 2019-01-16T03:34:30 37.065 -97.354 5.0 4.0 \
    -c ~/data/us2000j4df/fdsn_config.yml
```

where the arguments to `-e` are time (YYYY-MM-DDTHH:MM:SS format), latitude,
longitude, depth, and magnitude.

Either way, this command should download three stations worth of data to
~/data/us2000j4df/us2000j4df/raw as MiniSEED and StationXML files (what gmprocess
considers the "FDSN" format.) It will also use the Obspy plotting functionality
to make plots of these raw waveforms, like this:

<figure>
  <img width="800px" src="figs/OK.BLUF.HN_90sec.png" alt="Stream plot"/>
  <figcaption>Sample plot of a waveform stream downloaded via FDSN (95 seconds duration)</figcaption>
</figure>

The peaks are visible here, but we are perhaps cutting off some of the latter
part of the signal, so we can adjust the `time_after` field to be 180 seconds.

Edit your custom config file, and re-run the command above. Your time series
plot should now look more like this:

<figure>
  <img width="800px" src="figs/OK.BLUF.HN_180sec.png" alt="Stream plot"/>
  <figcaption>Sample plot of a waveform stream downloaded via FDSN (185 seconds duration)</figcaption>
</figure>

Iterate with the configuration as you see fit. Once you are happy with the
data that's been downloaded, you can try [processing](processing.md) and [extracting metrics](waveform_metrics.md)
from the waveforms.

## Downloading Triggered Data

Downloading triggered data from one of the supported sites (Japan, New Zealand,
and Turkey) is somewhat easier, with Japan being a minor exception. In order to
download KNET/KikNet data, you must first [create an account](https://hinetwww11.bosai.go.jp/nied/registration/?LANG=en).

After registering at the above link, put your username and password information
into the fetchers section of a custom config file, inserting your new username
and password:

```yaml
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

Save this configuration to `~/data/jp_config.yml`, then run the following
command:

```bash
gmprocess ~/data/us1000jd8k \
    -i us1000jd8k \
    -c ~/data/jp_config.yml
```

Triggered data like this does not allow for any customization of the search
window for individual traces - the parameters above are instead used to find
matching events on the source websites. For example, `gmprocess` would take the
origin time and hypocenter for event *us1000jd8k* from ComCat, and search the
NIED website for events within a 100 km distance radius and a time window of
+/- 60 seconds. Depth and magnitude thresholds are not currently used, but may
be in the future.

The above command should download 160 stations, and processing may take tens of
minutes, depending on the performance of the system on which it is running.

Retrieving triggered data from New Zealand or Turkey is similar.

## Downloading Multiple Events

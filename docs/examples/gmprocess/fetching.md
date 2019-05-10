# Fetching waveforms from data centers using gmprocess

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
    -o \
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
~/data/us2000j4df/raw as MiniSEED and StationXML files (what gmprocess
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

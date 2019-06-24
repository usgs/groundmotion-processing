# Fetching Data

We believe one of the common use cases with gmprocess will be to retrieve data
associated with a particular event, process it automatically, and generate
stream metrics (i.e., components Rotd50 and greater of two horizontals, and
intensity measures like PGA and MMI).

To this end we have created the `gmprocess` program, which allows a mostly
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
 - The Iranian Road, Housing & Urban Development Research Center (BHRC) provides
   partially  processed triggered strong motion sensor data on their website.

Data from some of these services (FDSN, GeoNet, KNET, and NSMN at the time of
this writing) can be downloaded automatically using `gmprocess`. Iran
provides a web interface for downloading data (with a usage/citation
agreement). Taiwan provides no public access to their data at this time. CESMD,
at the time of this writing, is implementing an FDSN-compatible web interface to
their extensive archive of data.


## Configuration

The default settings for the `fetchers` section of the configuration are below.
The sources of *triggered* data (KNET, GeoNet, Turkey) define settings that
help `gmprocess` find the events in their respective catalogs matching the
input event. Not all of these are used for all fetchers, but we define them
here to be "future-proof".

 - `radius` How far in kilometers should we search around input coordinates?
 - `dt` How many seconds before and after input time should we search?
 - `ddepth` How far above and below input depth (km) should we search?
 - `dmag` How far above and below input magnitude should we search?

The FDSNFetcher, which retrieves *continuous* data from any contributing FDSN
service, has it's own settings, which are mostly passed to the Obspy Mass
Downloader as the same name.

 - `radius` Search radius in decimal degrees around epicenter to look for stations.
 - `time_before` Seconds before origin time to retrieve continuous waveform data.
 - `time_after` Seconds after origin time to retrieve continuous waveform data.
 - `channels` List of channels to download. The default is to retrieve high-gain and accelerometer data.
 - `network`  Which networks (not FDSN services) from which to download data. The default is all of them.
 - `exclude_networks` Here a user can choose which networks to avoid. Default avoids "SY" (synthetic).
 - `reject_channels_with_gaps` Any channels with time gaps or overlaps can be avoided using this parameter.
 - `minimum_length` The minimum length of the data as a fraction of the requested time frame.
 - `sanitize` Only download data that has accompanying StationXML metadata.
 - `minimum_interstation_distance_in_m` Designed to avoid very close stations with the same data but different names.

```yaml
fetchers:
    KNETFetcher:
        # NIED requires a username and a password, obtain these by
        # visiting this page:
        # https://hinetwww11.bosai.go.jp/nied/registration/
        user: USERNAME
        password: PASSWORD
        # define the distance search radius (km)
        radius : 100
        # define the time search threshokd (sec)
        dt : 60
        # define the depth search threshokd (km)
        ddepth : 30
        # define the magnitude search threshokd (km)
        dmag : 0.3
    GeoNetFetcher:
        # define the distance search radius (km)
        radius : 100
        # define the time search threshokd (sec)
        dt : 16
        # define the depth search threshokd (km)
        ddepth : 30
        # define the magnitude search threshokd (km)
        dmag : 0.3
    TurkeyFetcher:
        # define the distance search radius (km)
        radius : 100
        # define the time search threshokd (sec)
        dt : 16
        # define the depth search threshokd (km)
        ddepth : 30
        # define the magnitude search threshokd (km)
        dmag : 0.3
    FDSNFetcher:
        # search radius in dd
        radius : 4
        # seconds before arrival time
        time_before : 30
        # seconds after arrival time
        time_after : 420
        channels : ["?H?", "?N?"] # only get strong motion and high-gain channels

        network : "*"

        # SY is a network for synthetic data
        exclude_networks :
            - SY

        # uncomment this section to add stations that should be avoided
        # exclude_stations:
        #    - ABC*

        # If True (default), MiniSEED files with gaps and/or overlaps will be rejected.
        reject_channels_with_gaps : True

        # The minimum length of the data as a fraction of the requested time frame.
        # After a channel has been downloaded it will be checked that its total
        # length is at least that fraction of the requested time span.
        # Will be rejected otherwise. Must be between 0.0 and 1.0.
        minimum_length : 0.1

        # Only download data that has accompanying StationXML metadata.
        sanitize : True

        # The minimum inter-station distance.
        # Data from any new station closer to any
        # existing station will not be downloaded.
        minimum_interstation_distance_in_m: 0.0
```

See [Fetching waveforms using `gmprocess`](examples/gmprocess/fetching.md) for examples of fetching data using `gmprocess`.

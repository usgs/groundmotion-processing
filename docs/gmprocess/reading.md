# Reading data

## Downloading Data from Remote Data Centers

Downloading triggered data from one of the supported sites (Japan, New Zealand,
and Turkey) is relatively easy. Japan is slightly more difficult because they
require you to
[create an account](https://hinetwww11.bosai.go.jp/nied/registration/?LANG=en).

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

Save this configuration to `jp_config.yml`, then run the following
command:

```bash
gmprocess -o japan_test \
    --assemble \
    --eventids us1000jd8k \
    --config jp_config.yml
```

This will create a `us1000jd8k` directory under `japan_test` (see gmprocess
overview). Warning: this will take at least a few minutes because Japan has
so much data available.

Triggered data like this does not allow for any customization of the search
window for individual traces. The parameters above are instead used to find
matching events on the source websites. For example, `gmprocess` would take the
origin time and hypocenter for event **us1000jd8k** from ComCat, and search the
NIED website for events within a 100 km distance radius and a time window of
+/- 60 seconds. Depth and magnitude thresholds are not currently used, but may
be in the future.

The above command should download about 160 stations, and processing may take tens of
minutes, depending on the performance of the system on which it is running.

Retrieving triggered data from New Zealand or Turkey is similar to the process
for Japan, but does not require a username and password.

## Reading Data from Local Files

There are many cases where data will need to be read from the local file system
and `gmprocess` also supports this use case via the `--directory` option.
To demonstrate how this works, we provide a directory of data in
`gmprocess/data/testdata/demo`. Its contents are:
```
demo
├── ci38038071
│   └── raw
│       ├── AZ.HSSP..HNE__20180829T023258Z__20180829T024028Z.mseed
│       ├── AZ.HSSP..HNN__20180829T023258Z__20180829T024028Z.mseed
│       ├── AZ.HSSP..HNZ__20180829T023258Z__20180829T024028Z.mseed
│       ├── AZ.HSSP.xml
│       ├── CE.23178.10.HNE__20180829T023318Z__20180829T023648Z.mseed
│       ├── CE.23178.10.HNN__20180829T023318Z__20180829T023648Z.mseed
│       ├── CE.23178.10.HNZ__20180829T023318Z__20180829T023648Z.mseed
│       ├── CE.23178.xml
│       └── CE23837.V1C
└── ci38457511
    └── raw
        ├── CICCC.RAW
        ├── CICLC.v1
        └── CITOW2.RAW
```
You can see that it has data for two events, and data in multiple file formats.

To assemble the data, run:
```bash
gmprocess -o test --assemble --directory demo
```

This leaves the data locted in `demo` in place, and creates the follow files:
```
test
├── ci38038071
│   ├── event.json
│   ├── raw
│   │   ├── AZ.HSSP.HN.png
│   │   ├── CE.23178.HN.png
│   │   └── CE.23837.HN.png
│   └── workspace.hdf
└── ci38457511
    ├── event.json
    ├── raw
    │   ├── ZZ.CCC.HN.png
    │   ├── ZZ.CLC.HN.png
    │   └── ZZ.TOW2.HN.png
    └── workspace.hdf
```
If the output directory were set to `demo` rather than `test` then the output files
be colocated with the origin input data directory. You can see a number of files
have been created:

- a `workspace.hdf` file has been created for each event,
- an `event.json` file for each event, and
- time series plots of the raw records are put in the raw directory for each event.

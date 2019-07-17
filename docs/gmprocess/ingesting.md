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

Save this configuration to `~/data/japan/jp_config.yml`, then run the following
command:

```bash
gmprocess ~/data/japan assemble -i us1000jd8k -c ~/data/japan/jp_config.yml
```

This will create a `us1000jd8k` directory under `~/data/japan` (see gmprocess
overview).

Triggered data like this does not allow for any customization of the search
window for individual traces - the parameters above are instead used to find
matching events on the source websites. For example, `gmprocess` would take the
origin time and hypocenter for event **us1000jd8k** from ComCat, and search the
NIED website for events within a 100 km distance radius and a time window of
+/- 60 seconds. Depth and magnitude thresholds are not currently used, but may
be in the future.

The above command should download 160 stations, and processing may take tens of
minutes, depending on the performance of the system on which it is running.

Retrieving triggered data from New Zealand or Turkey is similar to the process
for Japan, but does not require a username and password.

## Reading Data from Local Files

There are many cases where data will be found on the local file system, and not online.
`gmprocess` also supports this use case via the `--directory` option.

This option sidesteps online data retrieval, reading data from the local directory
specified with the `--directory` option. This directory must:

- Contain subdirectories for each event
- The event subdirectory names should match the event id

To assemble the data into a workspace HDF file:

```bash
$ ls -R test
ci38038071

test/ci38038071:
raw

test/ci38038071/raw:
AZ.HSSP..HNE__20180829T023258Z__20180829T024028Z.mseed		CE.23178.10.HNN__20180829T023318Z__20180829T023648Z.mseed
AZ.HSSP..HNN__20180829T023258Z__20180829T024028Z.mseed		CE.23178.10.HNZ__20180829T023318Z__20180829T023648Z.mseed
AZ.HSSP..HNZ__20180829T023258Z__20180829T024028Z.mseed		CE.23178.xml
AZ.HSSP.xml							CE23837.V1C
CE.23178.10.HNE__20180829T023318Z__20180829T023648Z.mseed

$ gmprocess -o test --assemble --directory test
$ ls -R test
ci38038071

test/ci38038071:
raw		workspace.hdf

test/ci38038071/raw:
AZ.HSSP..HNE__20180829T023258Z__20180829T024028Z.mseed		CE.23178.10.HNN__20180829T023318Z__20180829T023648Z.mseed
AZ.HSSP..HNN__20180829T023258Z__20180829T024028Z.mseed		CE.23178.10.HNZ__20180829T023318Z__20180829T023648Z.mseed
AZ.HSSP..HNZ__20180829T023258Z__20180829T024028Z.mseed		CE.23178.HN.png
AZ.HSSP.HN.png							CE.23178.xml
AZ.HSSP.xml							CE.23837.HN.png
CE.23178.10.HNE__20180829T023318Z__20180829T023648Z.mseed	CE23837.V1C
```

You can see that the file `test/ci38038071/workspace.hdf` has been created, as
well as plots of the raw data (the *.png files) in the `raw` directory. 

Note that the output directory (`-o`) and the data directory (`--directory`) need
not match.

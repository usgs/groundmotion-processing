# Data Assembly

## Downloading Data from Remote Data Centers

Downloading triggered data from one of the supported sites (Japan, New Zealand,
and Turkey) is somewhat easier, with Japan being a minor exception. In order to
download KNET/KikNet data from Japan, you must first [create an account](https://hinetwww11.bosai.go.jp/nied/registration/?LANG=en).

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

This will create a us1000jd8k directory under ~/data/japan (see gmprocess overview.)

Triggered data like this does not allow for any customization of the search
window for individual traces - the parameters above are instead used to find
matching events on the source websites. For example, `gmprocess` would take the
origin time and hypocenter for event *us1000jd8k* from ComCat, and search the
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

TODO: Add explanation
## Data Fetchers

This section includes subsections corresponding to the data fetchers that will
be used by the `download` subcommand. While each fetcher is optional, at least
one fetcher is required to run the `download` subcommand. Individual fetchers
can be "turned off" by deleting or commenting them out of the config file.

Note that some of the fetchers require the user to fill in information for
authentication purposes (e.g., an email address for the CESMD fetcher).

The CESMD fetcher is given as an example below. The full list set of examples
can be found in the config file in the repository 
[here](https://github.com/usgs/groundmotion-processing/blob/master/gmprocess/data/config_production.yml).

```yaml
fetchers:
    CESMDFetcher:
        # CESMD requires an email, register yours by
        # visiting this page:
        # https://strongmotioncenter.org/cgi-bin/CESMD/register.pl
        email: EMAIL
        process_type: raw
        station_type: Ground
        # define the distance search radius (km)
        eq_radius: 10.0
        # define the time search threshokd (sec)
        eq_dt: 10.0
        # station search radius (km)
        station_radius: 100.0
```


% Indices and tables

% ==================

% * :ref:`genindex`

% * :ref:`modindex`

% * :ref:`search`

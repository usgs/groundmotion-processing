#!/usr/bin/env python

from tempfile import mkdtemp
from datetime import datetime

from gmprocess.io.cosmos.cesmd_search import (get_records,
                                              get_metadata,
                                              get_stations_dataframe)


def test_get_metadata():
    metadata = get_metadata(eqlat=35.901,
                            eqlon=-117.750,
                            eqtime=datetime(2019, 7, 6, 3, 47, 53))

    dataframe = get_stations_dataframe(metadata['results']['events'][0])

    output = mkdtemp()
    email = 'mhearne@usgs.gov'
    return_type = 'metadata'
    station_latitude = 35.901
    station_longitude = -117.750
    radius_km = 200
    output, dfiles = get_records(output, email,
                                 return_type=return_type,
                                 station_latitude=station_latitude,
                                 station_longitude=station_longitude,
                                 radius_km=200)


if __name__ == '__main__':
    test_get_metadata()

#!/usr/bin/env python

from tempfile import mkdtemp
from datetime import datetime

from gmprocess.io.cosmos.cesmd_search import (
    get_records,
    get_metadata,
    get_stations_dataframe,
)


def _test_get_metadata():
    metadata = get_metadata(
        eqlat=35.901, eqlon=-117.750, eqtime=datetime(2019, 7, 6, 3, 47, 53)
    )
    assert metadata["count"] == 79
    dataframe = get_stations_dataframe(metadata["results"]["events"][0])
    assert len(dataframe) == 79


if __name__ == "__main__":
    test_get_metadata()

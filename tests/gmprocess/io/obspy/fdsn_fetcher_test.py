#!/usr/bin/env python

import pytest
import os
from datetime import datetime
import tempfile
import shutil

from gmprocess.utils.config import get_config
from gmprocess.utils.logging import setup_logger
from gmprocess.io.obspy.fdsn_fetcher import FDSNFetcher

setup_logger()


@pytest.fixture(scope="session")
def vcr_config():
    # note: set "record_mode" to "once" to record, then set to "none" when prior to
    # commiting the test. Can also be "rewrite".
    return {"record_mode": "once", "filter_headers": []}


@pytest.mark.vcr
def skip_test_fetcher():
    # nc72282711
    rawdir = tempfile.mkdtemp()
    try:
        config = get_config()
        config["fetchers"]["FDSNFetcher"]["domain"]["circular"]["maxradius"] = 0.1
        # 2014-08-24 10:20:44
        utime = datetime(2014, 8, 24, 10, 20, 44)
        eqlat = 38.215
        eqlon = -122.312
        eqdepth = 11.1
        eqmag = 6.0
        fetcher = FDSNFetcher(
            utime,
            eqlat,
            eqlon,
            eqdepth,
            eqmag,
            rawdir=rawdir,
            config=config,
            stream_collection=False,
        )
        fetcher.retrieveData()
        filenames = next(os.walk(rawdir), (None, None, []))[2]
        assert len(filenames) == 12
    except Exception as e:
        raise (e)
    finally:
        if os.path.exists(rawdir):
            shutil.rmtree(rawdir, ignore_errors=True)


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    skip_test_fetcher()

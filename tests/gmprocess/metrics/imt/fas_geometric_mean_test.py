#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

import numpy as np
import pandas as pd

from gmprocess.metrics.station_summary import StationSummary
from gmprocess.core.stationstream import StationStream
from gmprocess.core.stationtrace import StationTrace
from gmprocess.utils.constants import TEST_DATA_DIR


def test_fas():
    """
    Testing based upon the work provided in
    https://github.com/arkottke/notebooks/blob/master/effective_amp_spectrum.ipynb
    """
    fas_file = TEST_DATA_DIR / "fas_geometric_mean.pkl"
    p1 = TEST_DATA_DIR / "peer" / "RSN763_LOMAP_GIL067.AT2"
    p2 = TEST_DATA_DIR / "peer" / "RSN763_LOMAP_GIL337.AT2"

    stream = StationStream([])
    for idx, fpath in enumerate([p1, p2]):
        with open(fpath, encoding="utf-8") as file_obj:
            for _ in range(3):
                next(file_obj)
            meta = re.findall(r"[.0-9]+", next(file_obj))
            dt = float(meta[1])
            accels = np.array(
                [col for line in file_obj for col in line.split()], dtype=float
            )
        trace = StationTrace(
            data=accels,
            header={
                "channel": "HN" + str(idx),
                "delta": dt,
                "standard": {
                    "corner_frequency": np.nan,
                    "station_name": "",
                    "source": "json",
                    "instrument": "",
                    "instrument_period": np.nan,
                    "source_format": "json",
                    "comments": "",
                    "structure_type": "",
                    "sensor_serial_number": "",
                    "source_file": "",
                    "process_level": "raw counts",
                    "process_time": "",
                    "horizontal_orientation": np.nan,
                    "vertical_orientation": np.nan,
                    "units": "cm/s/s",
                    "units_type": "acc",
                    "instrument_sensitivity": np.nan,
                    "volts_to_counts": np.nan,
                    "instrument_damping": np.nan,
                },
            },
        )
        stream.append(trace)

    for tr in stream:
        response = {"input_units": "counts", "output_units": "cm/s^2"}
        tr.setProvenance("remove_response", response)

    target_df = pd.read_pickle(fas_file)
    ind_vals = target_df.index.values
    per = np.unique([float(i[0].split(")")[0].split("(")[1]) for i in ind_vals])
    freqs = 1 / per
    imts = ["fas" + str(p) for p in per]
    summary = StationSummary.from_stream(stream, ["geometric_mean"], imts, bandwidth=30)

    pgms = summary.pgms
    # pgms.to_pickle(fas_file)
    for idx, f in enumerate(freqs):
        fstr = f"FAS({1 / f:.3f})"
        fval1 = pgms.loc[fstr, "GEOMETRIC_MEAN"].Result
        fval2 = target_df.loc[fstr, "GEOMETRIC_MEAN"].Result
        np.testing.assert_allclose(fval1, fval2, rtol=1e-5, atol=1e-5)


if __name__ == "__main__":
    test_fas()

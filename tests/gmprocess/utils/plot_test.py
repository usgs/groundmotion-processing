#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import os.path
import matplotlib
import tempfile
import shutil

# third party imports
from gmprocess.io.read import read_data
from gmprocess.utils.plot import (
    plot_arias,
    plot_durations,
    plot_moveout,
    plot_regression,
)
import pandas as pd
from gmprocess.utils.test_utils import read_data_dir
from gmprocess.utils.constants import TEST_DATA_DIR


def test_regression():
    event_file = TEST_DATA_DIR / "events.xlsx"
    imc_file = TEST_DATA_DIR / "greater_of_two_horizontals.xlsx"
    imc = "G2H"
    event_table = pd.read_excel(event_file, engine="openpyxl")
    imc_table = pd.read_excel(imc_file, engine="openpyxl")
    imt = "PGA"

    tdir = tempfile.mkdtemp()
    try:
        tfile = os.path.join(tdir, "regression.png")
        tfile = os.path.join(os.path.expanduser("~"), "regression.png")
        plot_regression(event_table, imc, imc_table, imt, tfile, colormap="jet")
        print(tfile)
    except Exception as e:
        raise e
    finally:
        shutil.rmtree(tdir)


def test_plot():
    # read in data
    datafiles, _ = read_data_dir("cwb", "us1000chhc")
    streams = []
    for filename in datafiles:
        streams += read_data(filename)
    # One plot arias
    axes = plot_arias(streams[3])
    assert len(axes) == 3

    # Multiplot arias
    axs = matplotlib.pyplot.subplots(len(streams), 3, figsize=(15, 10))[1]
    axs = axs.flatten()
    idx = 0
    for stream in streams:
        axs = plot_arias(
            stream,
            axes=axs,
            axis_index=idx,
            minfontsize=15,
            show_maximum=False,
            title="18km NNE of Hualian, Taiwan",
        )
        idx += 3

    # One plot durations
    durations = [(0.05, 0.75), (0.2, 0.8), (0.05, 0.95)]
    axes = plot_durations(streams[3], durations)
    assert len(axes) == 3

    # Multiplot durations
    axs = matplotlib.pyplot.subplots(len(streams), 3, figsize=(15, 10))[1]
    axs = axs.flatten()
    idx = 0
    for stream in streams:
        axs = plot_durations(
            stream,
            durations,
            axes=axs,
            axis_index=idx,
            minfontsize=15,
            title="18km NNE of Hualian, Taiwan",
        )
        idx += 3

    # Moveout plots
    epicenter_lat = 24.14
    epicenter_lon = 121.69
    plot_moveout(
        streams,
        epicenter_lat,
        epicenter_lon,
        "1",
        figsize=(15, 10),
        minfontsize=16,
        normalize=True,
        factor=0.1,
    )


if __name__ == "__main__":
    os.environ["CALLED_FROM_PYTEST"] = "True"
    test_regression()
    test_plot()

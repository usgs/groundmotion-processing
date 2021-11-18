#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import os
import logging

# local imports
from gmprocess.core.streamcollection import StreamCollection
from gmprocess.utils.constants import WORKSPACE_NAME
from gmprocess.io.asdf.stream_workspace import StreamWorkspace
from gmprocess.io.read_directory import directory_to_streams
from gmprocess.utils.misc import get_rawdir

TIMEFMT2 = '%Y-%m-%dT%H:%M:%S.%f'


FLOAT_PATTERN = r'[-+]?[0-9]*\.?[0-9]+'


def assemble(event, config, directory, gmprocess_version):
    """Download data or load data from local directory, turn into Streams.

    Args:
        event (ScalarEvent):
            Object containing basic event hypocenter, origin time, magnitude.
        config (dict):
            Dictionary with gmprocess configuration information.
        directory (str):
            Path where data already exists. Must be organized in a 'raw'
            directory, within directories with names as the event ids. For
            example, if `directory` is 'proj_dir' and you have data for
            event id 'abc123' then the raw data to be read in should be
            located in `proj_dir/abc123/raw/`.
        gmprocess_version (str):
            Software version for gmprocess.

    Returns:
        tuple:
            - StreamWorkspace: Contains the event and raw streams.
            - str: Name of workspace HDF file.
            - StreamCollection: Raw data StationStreams.
            - str: Path to the rupture file.
    """

    # Make raw directory
    in_event_dir = os.path.join(directory, event.id)
    in_raw_dir = get_rawdir(in_event_dir)
    logging.debug('in_raw_dir: %s' % in_raw_dir)
    streams, _, _ = directory_to_streams(
        in_raw_dir, config=config)
    logging.debug('streams:')
    logging.debug(streams)
    tcollection = StreamCollection(streams, **config['duplicate'])

    if len(tcollection):
        logging.debug('tcollection.describe():')
        logging.debug(tcollection.describe())

    # Create the workspace file and put the unprocessed waveforms in it
    workname = os.path.join(in_event_dir, WORKSPACE_NAME)

    # Remove any existing workspace file
    if os.path.isfile(workname):
        os.remove(workname)

    workspace = StreamWorkspace(workname)
    workspace.addEvent(event)
    logging.debug('workspace.dataset.events:')
    logging.debug(workspace.dataset.events)
    workspace.addStreams(event, tcollection, label='unprocessed')
    logging.debug('workspace.dataset.waveforms.list():')
    logging.debug(workspace.dataset.waveforms.list())
    workspace.addConfig()
    workspace.addGmprocessVersion(gmprocess_version)
    logging.debug('workspace.dataset.config')

    return workspace

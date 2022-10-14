# stdlib imports
import zipfile
import io
import os.path
from datetime import timedelta
from pathlib import Path

# third party imports
import logging
from requests import Session, Request
from requests.exceptions import ConnectionError
import pandas as pd
import numpy as np

URL_TEMPLATE = "https://strongmotioncenter.org/wserv/records/query"
RETURN_TYPES = ["dataset", "metadata"]
PROCESS_LEVELS = ["processed", "raw", "plots", "all"]
GROUP_OPTIONS = ["station", "event"]

NETWORKS = {
    "08": "Hokkaido University",
    "AA": "AA - Anchorage Strong Motion Network",
    "AK": "AK - University of Alaska Geophysical Institute",
    "AZ": "AZ - Anza",
    "BG": "BG - Berkeley Geysers Network",
    "BK": "BK - Berkeley Digital Seismic Network",
    "C1": "C1 - Red Sismologica Nacional",
    "CB": "CB - Institute of Geophysics China Earthquake Administration (IGP)",
    "CE": "CE - California Strong Motion Instrumentation Program",
    "CF": "CF - Red Acelerografica Nacional de la Comision Federal de Electr",
    "CI": "CI - California Institute of Technology",
    "CU": "CU - Albuquerque Seismological Laboratory",
    "C_": "C_ - C&GS",
    "EC": "EC - Ecuador Seismic Network",
    "ES": "ES - Spanish Digital Seismic Network",
    "GI": "GI - Red Sismologica Nacional-Guatemala",
    "G_": "G_ - GEOSCOPE",
    "HV": "HV - Hawaiian Volcano Observatory Network",
    "IT": "IT - Italian Strong Motion Network",
    "IU": "IU - GSN - IRIS/USGS",
    "IV": "IV - Istituto Nazionale di Geofisica e Vulcanologia",
    "JP": "JP - BRI",
    "LA": "LA - Los Angeles Basin Seismic Network",
    "MN": "MN - Mediterranean Very Broadband Seismographic Network",
    "NC": "NC - USGS Northern California Regional Network",
    "ND": "ND - New Caledonia Broadband Seismic Network (SismoCal)",
    "NM": "NM - New Madrid Seismic Network",
    "NN": "NN - Nevada Seismic Network",
    "NP": "NP - National Strong Motion Project",
    "NZ": "NZ",
    "OK": "OK - Oklahoma Geological Survey",
    "OV": "OV - Observatorio Vulcanologico y Sismologico de Costa Rica",
    "PA": "PA - Observatorio Sismico del Occidente de Panamá",
    "PG": "PG",
    "PR": "PR - Puerto Rico Strong Motion Program (PRSMP)",
    "TO": "TO - Caltech Tectonic Observatory",
    "TU": "TU - Turkey Strong Motion Network",
    "US": "US - National Earthquake Information Center",
    "UW": "UW - PNSN",
    "WR": "WR - California Department of Water Resources",
    "_C": "_C - Chile",
}

STATION_TYPES = {
    "Array": "A",
    "Ground": "G",
    "Building": "B",
    "Bridge": "Br",
    "Dam": "D",
    "Tunnel": "T",
    "Wharf": "W",
    "Other": "O",
}

FAULT_TYPES = ["NM", "RS", "SS"]

# for those search parameters where the Python names differ from the ones
# defined by the web API, use this translation table.
KEY_TABLE = {
    "return_type": "rettype",
    "process_level": "download",
    "group_by": "groupby",
    "min_station_dist": "minepidist",
    "max_station_dist": "maxepidist",
    "network": "netid",
    "station_type": "sttype",
    "include_inactive": "abandoned",
    "station_name": "stname",
    "min_station_latitude": "minlat",
    "max_station_latitude": "maxlat",
    "min_station_longitude": "minlon",
    "max_station_longitude": "maxlon",
    "station_latitude": "slat",
    "station_longitude": "slon",
    "radius_km": "srad",
    "station_code": "stcode",
    "event_name": "evname",
    "fault_type": "faulttype",
    "min_event_latitude": "eminlat",
    "max_event_latitude": "emaxlat",
    "min_event_longitude": "eminlon",
    "max_event_longitude": "emaxlon",
    "event_latitude": "elat",
    "event_longitude": "elon",
    "event_radius": "erad",
}


def get_metadata(
    eqlat=None,
    eqlon=None,
    eqtime=None,
    eqradius=10,
    abandoned=False,
    station_type="Ground",
    eqtimewindow=10,  # seconds
    station_radius=200,
):
    f"""Retrieve station metadata JSON from CESMD web service.

    Args:
        eqlat (float):
            Earthquake latitude.
        eqlon (float):
            Earthquake longitude.
        eqtime (datetime):
            Earthquake origin time.
        eqradius (float):
            Earthquake search radius (km).
        abandoned (bool):
            Whether or not to include abandoned stations in the search.
        station_type (str):
            One of the following station types: [{','.join(STATION_TYPES)}]
        eqtimewidow (float):
            Earthquake time search window in sec.
        station_radius (str):
            Radius (km) to search for stations from epicenter.

    Returns:
        dict: Dictionary of event/station information.

    Raises:
        ValueError
        ConnectionError

    """
    params = {
        "rettype": "metadata",
        "groupby": "event",
        "format": "json",
        "nodata": 404,
        "sttype": STATION_TYPES[station_type],
        "abandoned": abandoned,
    }
    has_event_info = (
        (eqlat is not None) and (eqlon is not None) and (eqtime is not None)
    )

    if not has_event_info:
        raise ValueError("get_metadata must get either event id or event information.")
    else:
        starttime = eqtime - timedelta(seconds=eqtimewindow // 2)
        endtime = eqtime + timedelta(seconds=eqtimewindow // 2)
        params["elat"] = eqlat
        params["elon"] = eqlon
        params["erad"] = eqradius
        params["startdate"] = starttime.strftime("%Y-%m-%dT%H:%M:%S")
        params["enddate"] = endtime.strftime("%Y-%m-%dT%H:%M:%S")
        params["maxepidist"] = station_radius

    session = Session()
    request = Request("GET", URL_TEMPLATE, params=params).prepare()
    response = session.get(request.url)
    if response.status_code != 200:
        fmt = 'Could not retrieve data from url "%s": Server response %i'
        raise ConnectionError(fmt % (request.url, response.status_code))
    logging.debug("CESMD search url: %s", str(request.url))
    logging.debug("CESMD search response code: %s", response.status_code)
    metadata = response.json()

    return metadata


def get_stations_dataframe(metadata):
    """Return a dataframe of station information from one event in CESMD
    metadata.

    Args:
        metadata (dict): metata dictionary from CESMD.
    Returns:
        dataframe: Contains columns:
            - network
            - station_code
            - station_name
            - latitude
            - longitude
            - elevation
            - station_type
            - epidist
            - raw_avail
            - processed_avail

    """
    rows = {
        "network": [],
        "station_code": [],
        "station_name": [],
        "latitude": [],
        "longitude": [],
        "elevation": [],
        "station_type": [],
        "epidist": [],
        "raw_avail": [],
        "processed_avail": [],
    }
    for event in metadata["results"]["events"]:
        for station in event["stations"]:
            rows["network"].append(station["network"])
            rows["station_code"].append(station["code"])
            rows["station_name"].append(station["name"])
            rows["latitude"].append(station["latitude"])
            rows["longitude"].append(station["longitude"])
            elevation = station["elevation"]
            if elevation == "null" or elevation is None:
                rows["elevation"].append(np.nan)
            else:
                try:
                    rows["elevation"].append(float(elevation))
                except BaseException:
                    pass
            rows["station_type"].append(station["type"])
            record = station["record"]
            rows["epidist"].append(record["epidist"])
            avail = record["data_availability"]
            rows["raw_avail"].append(avail["raw"])
            rows["processed_avail"].append(avail["processed"])

    dataframe = pd.DataFrame(data=rows)
    return dataframe


def get_records(
    output,
    email,
    unpack=False,
    process_level="raw",
    group_by="event",
    minpga=None,
    maxpga=None,
    min_station_dist=None,
    max_station_dist=None,
    network=None,
    station_type="Ground",
    include_inactive=False,
    station_name=None,
    min_station_latitude=None,
    max_station_latitude=None,
    min_station_longitude=None,
    max_station_longitude=None,
    station_latitude=None,
    station_longitude=None,
    radius_km=None,
    station_code=None,
    event_name=None,
    minmag=None,
    maxmag=None,
    fault_type=None,
    startdate=None,
    enddate=None,
    min_event_latitude=None,
    max_event_latitude=None,
    min_event_longitude=None,
    max_event_longitude=None,
    event_latitude=None,
    event_longitude=None,
    event_radius=None,
    eventid=None,
):
    """Retrieve strong motion waveform records from CESMD website.

    Args:
        output (str or pathlib.Path):
            Filename or directory where downloaded zip data will be written.
        unpack (bool):
            If True, all zipped files will be unpacked (output will become a
            directory name.)
        email (str):
            Email address of requesting user.
        process_level (str):
            One of 'raw','processed','plots'.
        group_by (str):
            One of 'event', 'station'
        minpga (float):
            Minimum PGA value.
        maxpga (float):
            Maximum PGA value.
        min_station_dist (float):
            Minimum station distance from epicenter.
        max_station_dist (float):
            Maximum station distance from epicenter.
        network (str):
            Source network of strong motion data.
        station_type (str):
            Type of strong motion station (array, dam, etc.)
        include_inactive (bool):
            Include results from stations that are no longer active.
        station_name (str):
            Search only for station matching input name.
        min_station_latitude (float):
            Latitude station min when using a box search.
        max_station_latitude (float):
            Latitude station max when using a box search.
        min_station_longitude (float):
            Longitude station min when using a box search.
        max_station_longitude (float):
            Longitude station max when using a box search.
        station_latitude (float):
            Center latitude for station search.
        station_longitude (float):
            Center longitude for station search.
        radius_km (float):
            Radius (km) for station search.
        station_code (str):
            Particular station code to search for.
        event_name (str):
            Earthquake name to search for.
        minmag (float):
            Magnitude minimum when using a magnitude search.
        maxmag (float):
            Magnitude maximum when using a magnitude search.
        fault_type (str):
            Fault type.
        start_date (str):
            Start date/time in YYYY-MM-DD HH:MM:SS format
        end_date (str):
            End date/time in YYYY-MM-DD HH:MM:SS format
        min_event_latitude (float):
            Latitude event min when using a box search.
        max_event_latitude (float):
            Latitude event max when using a box search.
        min_event_longitude (float):
            Longitude event min when using a box search.
        max_event_longitude (float):
            Longitude event max when using a box search.
        event_latitude (float):
            Center earthquake latitude for radius search.
        event_longitude (float):
            Center earthquake longitude for radius search.
        event_radius (float):
            Earthquake search radius (km).
        eventid (str):
            NEIC or other ANSS event ID.

    Returns:
        tuple: (Top level output directory, list of data files)

    Raises:
        KeyError
    """
    output = Path(output)

    # getting the inputargs must be the first line of the method!
    inputargs = locals().copy()
    del inputargs["output"]
    del inputargs["unpack"]

    # note: this only supports one of the options or all of them,
    # no other combinations. ??
    if process_level not in PROCESS_LEVELS:
        fmt = "Only process levels of %s are supported (%s was input)"
        tpl = (",".join(PROCESS_LEVELS), process_level)
        raise KeyError(fmt % tpl)

    if group_by not in GROUP_OPTIONS:
        fmt = "Only process levels of %s are supported (%s was input)"
        tpl = (",".join(GROUP_OPTIONS), group_by)
        raise KeyError(fmt % tpl)

    # determine which network user wanted
    if network is not None and network not in NETWORKS:
        fmt = "Network with ID %s not found in list of supported networks."
        tpl = network
        raise KeyError(fmt % tpl)

    if station_type is not None and station_type not in STATION_TYPES:
        fmt = "Station type %s not found in list of supported types."
        tpl = station_type
        raise KeyError(fmt % tpl)

    # convert 'Ground' to 'G' for example
    inputargs["station_type"] = STATION_TYPES[inputargs["station_type"]]

    # check against list of fault types
    if fault_type is not None and fault_type not in FAULT_TYPES:
        fmt = "Fault type %s not found in supported fault types %s."
        tpl = (fault_type, ",".join(FAULT_TYPES))
        raise KeyError(fmt % tpl)

    # make sure there is only one method being used to select station
    # geographically
    if min_station_latitude is not None and station_latitude is not None:
        raise Exception(
            "Select stations either by bounding box or by radius, not both."
        )

    # make sure there is only one method being used to select events
    # geographically
    if min_event_latitude is not None and event_latitude is not None:
        raise Exception("Select events either by bounding box or by radius, not both.")

    # now convert process levels to string webservice expects
    levels = {"processed": "P", "raw": "R", "plots": "T", "all": "P,R,T"}
    inputargs["process_level"] = levels[process_level]

    # now convert input args to keys of parameters expected by
    params = {}
    for key, value in inputargs.items():
        if key in KEY_TABLE:
            params[KEY_TABLE[key]] = value
        else:
            params[key] = value

    # convert all booleans to strings that are 'true' and 'false'
    for key, value in params.items():
        if isinstance(value, bool):
            if value:
                params[key] = "true"
            else:
                params[key] = "false"

    # add in a couple of parameters that seem to be required
    params["orderby"] = "epidist-asc"
    params["nodata"] = "404"
    params["rettype"] = "dataset"

    session = Session()
    request = Request("GET", URL_TEMPLATE, params=params).prepare()
    url = request.url
    response = session.get(request.url)
    logging.debug("CESMD download url: %s", str(url))
    logging.debug("CESMD download response code: %s", response.status_code)

    if not response.status_code == 200:
        fmt = 'Your url "%s" returned a status code of %i with message: "%s"'
        raise ConnectionError(fmt % (url, response.status_code, response.reason))

    if unpack:
        output.mkdir(exist_ok=True)
        fbytes = io.BytesIO(response.content)
        myzip = zipfile.ZipFile(fbytes, mode="r")
        members = myzip.namelist()
        for member in members:
            finfo = myzip.getinfo(member)
            if finfo.is_dir():
                continue
            if not member.lower().endswith(".zip"):
                fin = myzip.open(member)
                flatfile = member.replace("/", "_")
                outfile = output / flatfile
                with open(str(outfile), "wb") as fout:
                    fout.write(fin.read())
                fin.close()
            else:
                zfiledata = io.BytesIO(myzip.read(member))
                try:
                    tmpzip = zipfile.ZipFile(zfiledata, mode="r")
                    tmp_members = tmpzip.namelist()
                    for tmp_member in tmp_members:
                        tfinfo = tmpzip.getinfo(tmp_member)
                        if not tfinfo.is_dir():
                            member_path = Path(member)
                            fin = tmpzip.open(tmp_member)
                            flatfile = tmp_member.replace("/", "_")
                            parent = str(member_path.parent / member_path.stem).replace(
                                "/", "_"
                            )
                            # sometimes the member ends with .zip.zip (??)
                            parent = parent.replace(".zip", "")
                            datadir = output / parent
                            datadir.mkdir(exist_ok=True)
                            outfile = datadir / flatfile
                            with open(str(outfile), "wb") as fout:
                                fout.write(fin.read())
                            fin.close()
                    tmpzip.close()
                    zfiledata.close()
                except BaseException as e:
                    fmt = (
                        'Could not unpack sub-zip file "%s" due to error '
                        '"%s". Skipping.'
                    )
                    print(fmt % (member, str(e)))
                    continue

        myzip.close()

        datafiles = []
        for root, fdir, files in os.walk(output):
            for tfile in files:
                if not tfile.endswith(".json"):
                    datafile = os.path.join(root, tfile)
                    datafiles.append(datafile)

        return (os.path.abspath(output), datafiles)
    else:
        if not output.endswith(".zip"):
            output += ".zip"
        with open(output, "wb", encoding="utf-8") as f:
            f.write(response.content)
        return (output, [])

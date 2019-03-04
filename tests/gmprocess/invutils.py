from obspy.core.inventory import Inventory, Network, Station, Channel, Site
from obspy.core.utcdatetime import UTCDateTime


def get_inventory():
    # We'll first create all the various objects. These strongly follow the
    # hierarchy of StationXML files.
    inv = Inventory(
        # We'll add networks later.
        networks=[],
        # The source should be the id whoever create the file.
        source="ObsPy-Tutorial")

    net = Network(
        # This is the network code according to the SEED standard.
        code="US",
        # A list of stations. We'll add one later.
        stations=[],
        description="A test stations.",
        # Start-and end dates are optional.
        start_date=UTCDateTime(2016, 1, 2))

    sta = Station(
        # This is the station code according to the SEED standard.
        code="ABCD",
        latitude=1.0,
        longitude=2.0,
        elevation=345.0,
        creation_date=UTCDateTime(2016, 1, 2),
        site=Site(name="First station"))

    cha1 = Channel(
        # This is the channel code according to the SEED standard.
        code="HN1",
        # This is the location code according to the SEED standard.
        location_code="11",
        # Note that these coordinates can differ from the station coordinates.
        latitude=1.0,
        longitude=2.0,
        elevation=345.0,
        depth=10.0,
        azimuth=0.0,
        dip=-90.0,
        sample_rate=1)
    cha2 = Channel(
        # This is the channel code according to the SEED standard.
        code="HN2",
        # This is the location code according to the SEED standard.
        location_code="11",
        # Note that these coordinates can differ from the station coordinates.
        latitude=1.0,
        longitude=2.0,
        elevation=345.0,
        depth=10.0,
        azimuth=90.0,
        dip=-90.0,
        sample_rate=1)
    cha3 = Channel(
        # This is the channel code according to the SEED standard.
        code="HNZ",
        # This is the location code according to the SEED standard.
        location_code="11",
        # Note that these coordinates can differ from the station coordinates.
        latitude=1.0,
        longitude=2.0,
        elevation=345.0,
        depth=10.0,
        azimuth=0.0,
        dip=-90.0,
        sample_rate=1)

    # Now tie it all together.
    sta.channels.append(cha1)
    sta.channels.append(cha2)
    sta.channels.append(cha3)
    net.stations.append(sta)
    inv.networks.append(net)

    return inv

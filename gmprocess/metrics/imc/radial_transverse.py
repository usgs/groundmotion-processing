import numpy as np

from gmprocess.metrics.exception import PGMException
from obspy.geodetics.base import gps2dist_azimuth


def calculate_radial_transverse(stream, origin, **kwargs):
    """
    Rotate channels to radial and tranvsere components, provided with
    an event origin location.

    NB: The input Stream should have already been "processed",
    i.e., filtered, detrended, tapered, etc.)

    Args:
        stream (Obspy Stream):
            Stream containing traces of acceleration data in gals.
        origin (Obspy event origin object):
            Origin for the event containing latitude and longitude.
    """

    st_copy = stream.copy()
    st_n = st_copy.select(component='[N1]')
    st_e = st_copy.select(component='[E2]')

    # Check that we have one northing and one easting channel
    if len(st_e) != 1 or len(st_n) != 1:
        raise PGMException('Stream must have one north and one east channel.')

    # Check that the orientations are orthogonal
    if abs(st_e[0].stats.standard.horizontal_orientation -
           st_n[0].stats.standard.horizontal_orientation) not in [90, 270]:
        raise PGMException('Channels must be orthogonal.')

    # Check that the lengths of the two channels are the same
    if st_e[0].stats.npts != st_n[0].stats.npts:
        raise PGMException('East and north channels must have same length.')

    # First, rotate to North-East components if not already
    if st_n[0].stats.standard.horizontal_orientation != 0:
        az_diff = 360 - st_n[0].stats.standard.horizontal_orientation
        az_diff = np.deg2rad(az_diff)
        rotation_matrix = np.array([[np.cos(az_diff), np.sin(az_diff)],
                                   [-np.sin(az_diff), np.cos(az_diff)]])
        data = np.array([st_n[0].data, st_e[0].data])
        newdata = np.matmul(rotation_matrix, data)

        st_n[0].data = newdata[0]
        st_e[0].data = newdata[1]

    st_n[0].stats.channel = st_n[0].stats.channel[:-1] + 'N'
    st_e[0].stats.channel = st_n[0].stats.channel[:-1] + 'E'

    # Calculate back azimuth and perform rotation to radial and transverse
    baz = gps2dist_azimuth(
        st_e[0].stats.coordinates.latitude,
        st_e[0].stats.coordinates.longitude,
        origin.latitude, origin.longitude)[1]
    st_copy.rotate(method='NE->RT', back_azimuth=baz)

    channels_dict = {}
    channels_dict['R'] = abs(st_copy.select(component='R')[0].max())
    channels_dict['T'] = abs(st_copy.select(component='T')[0].max())

    return channels_dict

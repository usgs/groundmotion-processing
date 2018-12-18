import warnings


def get_channel_name(sample_rate, is_acceleration=True,
                     is_vertical=False, is_north=True):
    """Create a SEED compliant channel name.

    SEED spec: http://www.fdsn.org/seed_manual/SEEDManual_V2.4_Appendix-A.pdf

    Args:
        sample_rate (int): Sample rate of sensor in Hz.
        is_acceleration (bool): Is this channel from an accelerometer.
        is_vertical (bool): Is this a vertical channel?
        is_north (bool): Is this channel vaguely pointing north or the channel
                         you want to be #1?
    Returns:
        str: Three character channel name according to SEED spec.

    """
    band = 'H'  # High Broad Band
    if sample_rate < 80 and sample_rate >= 10:
        band = 'B'

    code = 'N'
    if not is_acceleration:
        code = 'H'  # low-gain velocity sensors are very rare

    if is_vertical:
        number = 'Z'
    else:
        number = '2'
        if is_north:
            number = '1'

    channel = band+code+number
    return channel

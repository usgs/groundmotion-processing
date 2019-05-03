#!/usr/bin/env python

import os
from gmprocess.io.seedname import get_channel_name, is_channel_north


def test_channel():
    rate = 50
    tchannel1 = get_channel_name(rate, is_acceleration=True,
                                 is_vertical=False, is_north=True)
    assert tchannel1 == 'BN1'

    tchannel2 = get_channel_name(rate, is_acceleration=True,
                                 is_vertical=False, is_north=False)
    assert tchannel2 == 'BN2'

    tchannel3 = get_channel_name(rate, is_acceleration=True,
                                 is_vertical=True, is_north=False)
    assert tchannel3 == 'BNZ'

    rate = 100
    tchannel4 = get_channel_name(rate, is_acceleration=True,
                                 is_vertical=False, is_north=True)
    assert tchannel4 == 'HN1'

    tchannel5 = get_channel_name(rate, is_acceleration=True,
                                 is_vertical=False, is_north=False)
    assert tchannel5 == 'HN2'

    tchannel6 = get_channel_name(rate, is_acceleration=True,
                                 is_vertical=True, is_north=False)
    assert tchannel6 == 'HNZ'

    tchannel4 = get_channel_name(rate, is_acceleration=False,
                                 is_vertical=False, is_north=True)
    assert tchannel4 == 'HH1'


def test_north():
    # north-ish angles
    assert is_channel_north(0)
    assert is_channel_north(44)
    assert is_channel_north(136)
    assert is_channel_north(224)

    assert not is_channel_north(90)
    assert not is_channel_north(45)
    assert not is_channel_north(314)
    assert not is_channel_north(134)


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_channel()
    test_north()

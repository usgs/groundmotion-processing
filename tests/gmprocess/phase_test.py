#!/usr/bin/env python

from gmprocess.io.read import read_data
from gmprocess.phase import PowerPicker
from obspy import read, UTCDateTime
import os

homedir = os.path.dirname(os.path.abspath(__file__))
datadir = os.path.join(homedir, '..', 'data', 'process')


def test_p_pick():

    # Testing a strong motion channel
    tr = read(datadir + '/ALCTENE.UW..sac')[0]
    chosen_ppick = UTCDateTime('2001-02-28T18:54:47')
    ppick = PowerPicker(tr)
    assert len(ppick) == 1
    ppick = ppick[0]
    assert (abs(chosen_ppick - ppick)) < 0.2

    # Testing a broadband channel
    tr = read(datadir + '/HAWABHN.US..sac')[0]
    chosen_ppick = UTCDateTime('2003-01-15T03:42:12.5')
    ppick = PowerPicker(tr)
    assert len(ppick) == 1
    ppick = ppick[0]
    print(ppick)
    assert (abs(chosen_ppick - ppick)) < 0.2

    # Testing Northridge data
    tr = read_data(datadir + '/3822a.smc')[0]
    chosen_ppick = UTCDateTime('1994-01-17T12:32:09')
    ppick = PowerPicker(tr)
    print(ppick)
    assert len(ppick) == 1
    ppick = ppick[0]
    print(ppick)
    assert (abs(chosen_ppick - ppick)) < 0.2


if __name__ == '__main__':
    test_p_pick()

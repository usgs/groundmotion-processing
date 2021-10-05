#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module is for waveform procesisng simple sanity checks.
"""

import numpy as np


def check_tail(st, duration, max_vel_ratio=0.1, max_dis_ratio=0.5):
    """Check for abnormally arge values in the tail of the stream.

    This QA check looks for the presence of abnomally large values in the tail
    velocity and displacement traces. This can occur due to baseline shifts or
    long period noise that has not been properly filtered out that manifest
    as long-period drifts in the velocity and/or displacement traces.

    Note that an additional problem that this check should eliminate is records
    in which the time window has not captured the full duration of shaking.

    Args:
        st (StationStream):
            StationStream object.
        duration (float):
            Duration of tail.
        max_vel_ratio (float):
            Trace is labeled as failed if the max absolute velocity in the tail
            is greater than max_vel_ratio times the max absolute velocity of
            the whole trace.
        max_dis_ratio (float):
            Trace is labeled as failed if the max absolute displacement in the
            tail is greater than max_disp_ratio times the max absolute
            displacement of the whole trace.

    Returns:

    """
    if not st.passed:
        return st

    start_time = st[0].stats.starttime
    end_time = st[0].stats.endtime
    new_start_time = end_time - duration
    if new_start_time < start_time:
        for tr in st:
            tr.fail('Cannot apply tail check because tail duration exceeds'
                    'record duration.')
        return st

    vel = st.copy().integrate()
    dis = vel.copy().integrate()
    vel_trim = vel.copy()
    dis_trim = dis.copy()

    for tr in vel_trim:
        tr.trim(starttime=new_start_time)
    for tr in dis_trim:
        tr.trim(starttime=new_start_time)

    for i in range(len(st)):
        tr = st[i]
        abs_max_vel = np.max(np.abs(vel[i].data))
        abs_max_vel_trim = np.max(np.abs(vel_trim[i].data))
        abs_max_dis = np.max(np.abs(dis[i].data))
        abs_max_dis_trim = np.max(np.abs(dis_trim[i].data))
        vel_ratio = abs_max_vel_trim / abs_max_vel
        dis_ratio = abs_max_dis_trim / abs_max_dis
        if vel_ratio > max_vel_ratio:
            tr.fail('Velocity ratio is greater than %s' % max_vel_ratio)
        if dis_ratio > max_dis_ratio:
            tr.fail('Displacement ratio is greater than %s' % max_dis_ratio)
        tail_conf = {
            'max_vel_ratio': max_vel_ratio,
            'max_dis_ratio': max_dis_ratio,
            'start_time': new_start_time
        }
        tr.setParameter('tail_conf', tail_conf)
    return st

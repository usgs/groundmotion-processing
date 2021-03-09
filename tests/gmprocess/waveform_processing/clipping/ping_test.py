#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

from gmprocess.waveform_processing.clipping.ping import Ping

if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

from gmprocess.waveform_processing.clipping.histogram import Histogram

if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
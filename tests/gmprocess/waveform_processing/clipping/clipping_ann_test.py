#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from gmprocess.waveform_processing.clipping.clipping_ann import clipNet


def test_nnet():
    # Instantiate the clipNet class
    cN = clipNet()

    # Input list:
    #     mag, dist, 6M amplitude check, histogram check, ping check.
    input = [7.3, 201.6630574, 0, 0, 0]
    prob_clip = cN.evaluate(input)[0][0]
    np.testing.assert_allclose(prob_clip, 0.012965727663876212)

    input = [7.3, 223.0055032, 0, 1, 0]
    prob_clip = cN.evaluate(input)[0][0]
    np.testing.assert_allclose(prob_clip, 0.853443027535108)

    input = [5.7, 59.8610546076, 0, 1, 1]
    prob_clip = cN.evaluate(input)[0][0]
    np.testing.assert_allclose(prob_clip, 0.9898910827653756)


if __name__ == '__main__':
    test_nnet()

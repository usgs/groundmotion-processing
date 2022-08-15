#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import numpy as np
import copy
from scipy.integrate import cumtrapz
import os
import logging
import pathlib
from gmprocess.waveform_processing.processing_step import ProcessingStep


@ProcessingStep
def NNet_QA(st, acceptance_threshold, model_name, config=None):
    """
    Assess the quality of a stream by analyzing its two horizontal components
    as described in Bellagamba et al. (2019). Performs three steps:
    1) Compute the quality metrics (see paper for more info)
    2) Preprocess the quality metrics (deskew, standardize and decorrelate)
    3) Evaluate the quality using a neural network-based model
    Two models are available: 'Cant' and 'CantWell'.
    To minimize the number of low quality ground motion included, the natural
    acceptance threshold 0.5 can be raised (up to an extreme value of 0.95).
    Recommended parameters are:
    -   acceptance_threshold = 0.5 or 0.6
    -   model_name = 'CantWell'

    Args:
        st (list of traces):
            The ground motion record to analyze. Should contain at least 2
            orthogonal  horizontal traces.
        acceptance_threshold (float):
            Threshold from which GM records are considered acceptable.
        model_name (string):
            name of the used model ('Cant' or 'CantWell')
        config (dict):
            Configuration dictionary (or None). See get_config().

    Returns:
        st: stream of traces tagged with quality scores and flags,
        used model name and acceptance threshold
    """

    # This check only works if we have two horizontal components in the stream
    if st.num_horizontal != 2:
        for tr in st:
            tr.fail(
                "Stream does not contain two horiztonal components. "
                "NNet QA check will not be performed."
            )
        return st

    # Also need to check that we don't have data arrays of all zeros, as this
    # will cause problems
    all_zeros = False
    for tr in st:
        if np.all(tr.data == 0):
            all_zeros = True

    if all_zeros:
        for tr in st:
            tr.fail(
                "The data contains all zeros, so the "
                "NNet_QA check is not able to be performed."
            )
        return st

    # Check that we have the required trace parameters
    have_params = True
    for tr in st:
        if not {"signal_spectrum", "noise_spectrum", "snr"}.issubset(
            set(tr.getCachedNames())
        ):
            have_params = False

    if not have_params:
        for tr in st:
            tr.fail(
                "One or more traces in the stream does have the required "
                "trace parameters to perform the NNet_QA check."
            )
        return st

    # Create the path to the NN folder based on model name
    nn_path = pathlib.Path(__file__).parent / ".." / "data" / "nn_qa" / model_name

    # Compute the quality metrics
    qm = computeQualityMetrics(st)

    # Pre-process the qualtiy metrics
    qm = preprocessQualityMetrics(qm, model_name)

    # Instanciate the NN (based on model_name)
    NN = neuralNet()
    NN.loadNN(nn_path)

    # Use NN
    scores = NN.useNN(qm)[0]

    # Accepted?
    flag_accept = False
    if scores[1] >= acceptance_threshold:
        flag_accept = True

    # Add parameters to Stream (acceptance threshold, model_name, score_lowQ,
    # score_highQ, highQualityFlag)
    nnet_dict = {
        "accept_thres": acceptance_threshold,
        "model_name": model_name,
        "score_LQ": scores[0],
        "score_HQ": scores[1],
        "pass_QA": flag_accept,
    }
    st.setStreamParam("nnet_qa", nnet_dict)
    if not flag_accept:
        for tr in st:
            tr.fail("Failed NNet QA check.")

    return st


def isNumber(s):
    """
    Check if given input is a number.

    Args:
        s (any type):
            Data to test

    Returns:
        bool: True if is a number, False if isn't
    """
    try:
        float(s)
        return True

    except ValueError:
        return False


def loadCSV(data_path, row_ignore=0, col_ignore=0):
    """
    Load csv files from a given path and returns a list of list.
    For all imported data, check if is a number. If so, returns a
    float. If not, returns a string.

    Args:
        data_path (string): path to the csv to load
        row_ignore (int): number of rows to ignore
        col_ignore (int) : number of columns to ignore

    Returns:
        list of list: containing the data from the csv
    """

    M = []
    with open(data_path, encoding="utf-8") as csvfile:
        readCSV = csv.reader(csvfile)

        # Skip header
        for i in range(row_ignore):
            next(csvfile)

        for row in readCSV:
            # Input vector
            single_line = []
            for i in range(col_ignore, len(row)):
                if isNumber(row[i]):
                    single_line.append(float(row[i]))
                else:
                    single_line.append(row[i])
            M.append(single_line)

    return M


def sigmoid(v_input):
    """
    Performs a sigmoid operation on the input (1/(e(-x)+1))

    Args:
        v_input (float): a number defined on R (real)

    Returns:
        float: sigmoid result (a number between 0 and 1)
    """
    v_act = []
    for x in v_input:
        v_act.append(1.0 / (1 + np.exp(-x)))
    return v_act


def tanh(v_input):
    """
    Performs a hyperbolic tangent operation on the input (2/(e(2x)+1))

    Args:
        v_input (float) a number defined on R (real)

    Returns:
        float: tanh result (a number between -1 and 1)
    """
    v_act = []
    for x in v_input:
        v_act.append(np.tanh(x))
    return v_act


class neuralNet:
    """
    Class allowing the instantiation and use of simple (1 or 2 layers)
    neural networks
    """

    def __init__(self):
        """
        Instantiate an empty neural network (no weights, functions, or
        biases loaded
        """
        self.n_input = 0
        self.n_neuron_H1 = 0
        self.n_neuron_H2 = -1
        self.n_output = 0
        self.activation_H1 = "NA"
        self.activation_H2 = "NA"
        self.activation_output = "NA"
        self.w_H1 = []
        self.w_H2 = []
        self.b_H1 = []
        self.b_H2 = []
        self.w_output = []
        self.b_output = []

    # loadNN: load and build neural network model
    def loadNN(self, nn_path):
        """
        Populate an instantated neural netowrk with data contained in a
        specific folder.

        Args:
            nn_path (string): path to the folder containing the required
            information (masterF.txt, weights.csv, biases.csv)
        """
        data_path = os.path.join(nn_path, "masterF.txt")
        with open(data_path, encoding="utf-8") as masterF:
            readCSV = csv.reader(masterF)
            for row in readCSV:
                if len(row) == 7:
                    self.n_input = int(row[0])
                    self.n_neuron_H1 = int(row[1])
                    self.n_neuron_H2 = int(row[3])
                    self.n_output = int(row[5])
                    self.activation_H1 = row[2]
                    self.activation_H2 = row[4]
                    self.activation_output = row[6]
                elif len(row) == 5:
                    self.n_input = int(row[0])
                    self.n_neuron_H1 = int(row[1])
                    self.n_output = int(row[3])
                    self.activation_H1 = row[2]
                    self.activation_output = row[4]

        masterF.close()

        # Load weights and biases
        # Weights first hidden layer
        data_path = os.path.join(nn_path, "weight_1.csv")
        self.w_H1 = np.asarray(loadCSV(data_path))
        # Biases first hidden layer
        data_path = os.path.join(nn_path, "bias_1.csv")
        self.b_H1 = np.asarray(loadCSV(data_path))
        # Weights output layer
        data_path = os.path.join(nn_path, "weight_output.csv")
        self.w_output = np.asarray(loadCSV(data_path))
        # Biases output layer
        data_path = os.path.join(nn_path, "bias_output.csv")
        self.b_output = np.asarray(loadCSV(data_path))

        # Second hidden layer
        if self.n_neuron_H2 != -1:
            # Weights second hidden layer
            data_path = os.path.join(nn_path, "weight_2.csv")
            self.w_H2 = np.asarray(loadCSV(data_path))
            # Biases second hidden layer
            data_path = os.path.join(nn_path, "bias_2.csv")
            self.b_H2 = np.asarray(loadCSV(data_path))

    def useNN(self, v_input):
        """
        Use a populated neural network (i.e. from the input, returns the
        classification score or the regression result).

        Args:
            v_input (list or np.array): list or numpy array of the inputs
            (must be all numerical). Size must be equal to the NN input layer
            size.

        Returns:
            v_inter (np.array): numpy array containing the results.
        """
        v_inter = np.array([])
        # Transform input if required
        if isinstance(v_input, list):
            v_input = np.asarray(v_input)

        # First layer
        if self.activation_H1 == "sigmoid":
            v_inter = sigmoid(np.dot(v_input.T, self.w_H1) + self.b_H1)
        elif self.activation_H1 == "tanh":
            v_inter = tanh(np.dot(v_input.T, self.w_H1) + self.b_H1)
        else:
            v_inter = np.dot(v_input.T, self.w_H1) + self.b_H1

        # If second layer exist
        if self.n_neuron_H2 != -1:
            if self.activation_H2 == "sigmoid":
                v_inter = sigmoid(np.dot(v_inter, self.w_H2) + self.b_H2)
            elif self.activation_H2 == "tanh":
                v_inter = tanh(np.dot(v_inter, self.w_H2) + self.b_H2)
            else:
                v_inter = np.dot(v_inter, self.w_H2) + self.b_H2

        # Final layer
        if self.activation_output == "sigmoid":
            v_inter = sigmoid(np.dot(v_inter, self.w_output) + self.b_output)
        elif self.activation_output == "tanh":
            v_inter = tanh(np.dot(v_inter, self.w_output) + self.b_output)
        else:
            v_inter = np.dot(v_inter, self.w_output) + self.b_output

        return v_inter


def deskewData(data, model_name):
    """
    Performs the deskewing operations used in Bellagamba et al. (2019) on the
    quality metrics vector. Depending on the selected model.

    Args:
        data (list of floats): 20 quality metrics computed as described in the
        paper
        model_name (string): name of the selected model. Available 'Cant' and
        'CantWell' as described in the paper

    Returns:
        list of float: processed (deskewed) data
    """
    if model_name == "Cant":
        for i in range(len(data)):
            if i == 0 or i == 1 or i == 11 or i == 15 or i == 16:
                data[i] = np.log(data[i])
            elif i == 17:
                data[i] = -1.0 / data[i] ** 1.2
            elif i == 2:
                data[i] = data[i] ** (-0.2)
            elif i == 10:
                data[i] = data[i] ** (-0.06)
            elif i == 19:
                data[i] = data[i] ** 0.43
            elif i == 7:
                data[i] = data[i] ** 0.25
            elif i == 8:
                data[i] = data[i] ** 0.23
            elif i == 9:
                data[i] = data[i] ** 0.05
            elif i == 18:
                data[i] = data[i] ** 0.33
            elif i == 3:
                data[i] = data[i] ** (0.12)
            elif i == 5:
                data[i] = data[i] ** (0.48)
            elif i == 6:
                data[i] = data[i] ** (0.37)
            elif i == 12:
                data[i] = data[i] ** 0.05
            elif i == 13:
                data[i] = data[i] ** 0.08
            elif i == 4:
                data[i] = data[i] ** (0.16)
            elif i == 14:
                data[i] = data[i] ** (0.1)
        return data

    elif model_name == "CantWell":
        for i in range(len(data)):
            if i == 0 or i == 1 or i == 11 or i == 15 or i == 16:
                data[i] = np.log(data[i])
            elif i == 17:
                data[i] = -1.0 / data[i] ** 1.2
            elif i == 2:
                data[i] = data[i] ** (-0.2)
            elif i == 10:
                data[i] = data[i] ** (-0.06)
            elif i == 19:
                data[i] = data[i] ** 0.43
            elif i == 7:
                data[i] = data[i] ** 0.1
            elif i == 8:
                data[i] = data[i] ** 0.23
            elif i == 9:
                data[i] = data[i] ** 0.2
            elif i == 18:
                data[i] = data[i] ** 0.33
            elif i == 3:
                data[i] = data[i] ** (0.05)
            elif i == 5:
                data[i] = data[i] ** (0.3)
            elif i == 6:
                data[i] = data[i] ** (0.37)
            elif i == 12:
                data[i] = data[i] ** 0.05
            elif i == 13:
                data[i] = data[i] ** 0.08
            elif i == 4:
                data[i] = data[i] ** (0.05)
            elif i == 14:
                data[i] = data[i] ** (0.05)
        return data


def standardizeData(data, mu, sigma):
    """
    Performs a standardization operation on the given data ((X-mu)/sigma)

    Args:
        data (list of float):
            data to standardize (size represents the dimensionality of the data
            and not the number of point to standardize)
        mu (list of float):
            means
        sigma (list of float):
            standard deviation

    Returns:
        list o float: standardized data
    """
    for i in range(len(data)):
        data[i] = (data[i] - mu[i]) / sigma[i]

    return data


def decorrelateData(data, M):
    """
    Decorrelate the data based on a Mahalanobis tranform. The transformation
    matrix is given as an input.

    Args:
        data (np.array):
            numpy array containing the data to be decorrelated (size = N).
        M (np.array):
            decorrelation matrix (size NxN)

    Returns:
        list of float containing the decorrelated data
    """
    M = np.array(M)
    data = M.dot(data)
    data = np.transpose(data)

    return data.tolist()


def preprocessQualityMetrics(qm, model_name):
    """
    Pre-process the quality metrics according to Bellagamba et al. (2019)
    (i.e. deskews, standardizes and decorrelates the quality metrics)

    Args:
        qm (list of float):
            quality metrics estimated according to the paper
        model_name (string):
            name of the used model for processing. Available: 'Cant' and
            'CantWell'.

    Returns:
        list of float containing the pre-processed quality metrics.
    """
    # Building dir path from model name
    data_path = pathlib.Path(__file__).parent / ".." / "data" / "nn_qa" / model_name

    # Get resource from the correct dir
    M = loadCSV(os.path.join(data_path, "M.csv"))
    csv_dir = os.path.join(data_path, "mu_sigma.csv")
    [mu, sigma] = loadCSV(csv_dir)

    # Deskew, standardize and decorrelate data
    qm = deskewData(qm, model_name)
    qm = standardizeData(qm, mu, sigma)
    qm = decorrelateData(qm, M)

    return qm


def get_husid(acceleration, time_vector):
    """
    Returns the Husid vector, defined as int{acceleration ** 2.}

    Args:
        acceleration (np.array):
            Vector of acceleration values
        time_vector (np.array):
            Time vector in seconds
    """
    husid = np.hstack([0.0, cumtrapz(acceleration**2.0, time_vector)])
    AI = husid / max(husid)
    return husid, AI


def getFreqIndex(ft_freq, lower, upper):
    """
    Gets the indices of a frequency range in the frequency vector

    Args:
        ft_freq (list of float):
            list of ordred frequencies
        lower (float):
            lower boud of the frequency range
        upper (float):
            upper bound of the frequency range

    Returns:
        int, int: the indices bounding the range
    """
    lower_indices = [i for i, x in enumerate(ft_freq) if x > lower]
    upper_indices = [i for i, x in enumerate(ft_freq) if x < upper]
    lower_index = min(lower_indices)
    upper_index = max(upper_indices)
    return lower_index, upper_index


def getHusidIndex(husid, threshold):
    """
    Returns the index of the husid for a particular threshold

    Args:
        husid (list of float):
            husid vector
        threshold (float):
            threshold not to be exceeded

    Returns:
        int: the index of the latest value below the threshold
    """
    husid_indices = [i for i, x in enumerate(husid) if x > threshold]
    husid_index = min(husid_indices)
    return husid_index


def calculateSNR_min(ft_freq, snr):
    """
    Calculate the SNR min between 0.1 and 20 Hz

    Args:
        ft_freq (list of float):
            vector of frequencies used in the Fourier spectrum
        snr (list of float):
            vector of the snr at the frequencies in ft_freq

    Returns:
        float: min snr between 0.1 and 20 Hz
    """
    # Frequencies must be available between 0.1 and 20 Hz
    lower_index, upper_index = getFreqIndex(ft_freq, 0.1, 20)
    snr_min = min(snr[lower_index:upper_index])
    return snr_min


def calculateHusid(acc, t):
    """
    Calculate the husid and Arias of a signal.

    Args:
        acc (np.array):
            accelerogram vector
        t (np.array):
            time vector (constant time step)

    Returns:
        husid: vector of floats
        AI: vector of floats
        Arias: float, max value of AI
        husid index at 5, 75 and 95% (used for duration)
    """
    husid, AI = get_husid(acc, t)
    Arias = max(husid)
    husid_index_5 = getHusidIndex(AI, 0.05)
    husid_index_75 = getHusidIndex(AI, 0.75)
    husid_index_95 = getHusidIndex(AI, 0.95)
    return husid, AI, Arias, husid_index_5, husid_index_75, husid_index_95


def getClassificationMetrics(tr, p_pick, delta_t):
    """
    Compute the quality metrics as in Bellagamba et al. (2019). More details
    in the paper.

    WARNINGS: - Acceleration untis changed into g at the beginning!
              - Vertical component is not used!

    Args:
        tr (list of list of float):
            each list contains an horizontal trace
        p_pick (float):
            estimated P-wave arrival time (in seconds) from the start of the
            record
        delta_t (float):
            time step used in the record in seconds (decimal)

    Returns:
        List of float containing the quality metrics (size = 20)
    """
    ########################################
    # Acceleration units changed into g!!! #
    #    Vertical component not used!!!    #
    ########################################

    # Extract data from dictionary
    # First horizontal comp
    acc_comp1 = np.asarray(tr["acc_comp1"]) / 981.0
    smooth_ft1 = np.asarray(tr["smooth_ft1"]) / 981.0
    smooth_ft1_freq = np.asarray(tr["smooth_ft1_freq"])
    smooth_ft1_pe = np.asarray(tr["smooth_ft1_pe"]) / 981.0
    snr1_freq = np.asarray(tr["snr1_freq"])

    # Second horizontal comp
    acc_comp2 = np.asarray(tr["acc_comp2"]) / 981.0
    smooth_ft2 = np.asarray(tr["smooth_ft2"]) / 981.0
    smooth_ft2_pe = np.asarray(tr["smooth_ft2_pe"]) / 981.0

    # Sample rate
    sample_rate = 1.0 / delta_t

    # Index of the P-wave arrival time
    index_p_arrival = int(np.floor(np.multiply(p_pick, sample_rate)))

    # recreate a time vector
    t = np.arange(len(acc_comp1)) * delta_t

    # set up a copy of accelerations for plotting later (they get changed
    # by window/taper in the ft step)
    acc1 = copy.deepcopy(acc_comp1)
    acc2 = copy.deepcopy(acc_comp2)

    # calculate husid and Arias intensities
    (
        husid1,
        AI1,
        Arias1,
        husid_index1_5,
        husid_index1_75,
        husid_index1_95,
    ) = calculateHusid(acc1, t)
    (
        husid2,
        AI2,
        Arias2,
        husid_index2_5,
        husid_index2_75,
        husid_index2_95,
    ) = calculateHusid(acc2, t)

    # calculate max amplitudes of acc time series, final is geomean
    PGA1 = np.max(np.abs(acc1))
    PGA2 = np.max(np.abs(acc2))
    amp1_pe = max(abs(acc1[0:index_p_arrival]))
    amp2_pe = max(abs(acc2[0:index_p_arrival]))
    PGA = np.sqrt(PGA1 * PGA2)
    PN = np.sqrt(amp1_pe * amp2_pe)
    PN_average = np.sqrt(
        np.average(abs(acc1[0:index_p_arrival]))
        * np.average(abs(acc2[0:index_p_arrival]))
    )
    PNPGA = PN / PGA

    # calculate effective head and tail lengths
    tail_duration = min([5.0, 0.1 * t[-1]])
    tail_length = int(tail_duration * sample_rate)
    tail_average1 = np.mean(abs(acc1[-tail_length:]))
    tail_average2 = np.mean(abs(acc2[-tail_length:]))
    if PGA1 != 0 and PGA2 != 0:
        tail_ratio1 = tail_average1 / PGA1
        tail_ratio2 = tail_average2 / PGA2
        tail_ratio = np.sqrt(tail_ratio1 * tail_ratio2)
        tailnoise_ratio = tail_ratio / PN_average
    else:
        logging.debug("PGA1 or PGA2 is 0")
        tail_ratio1 = 1.0
        tail_ratio2 = 1.0
        tail_ratio = 1.0

    mtail_duration = min([2.0, 0.1 * t[-1]])
    mtail_length = int(mtail_duration * sample_rate)
    mtail_max1 = np.max(abs(acc1[-mtail_length:]))
    mtail_max2 = np.max(abs(acc2[-mtail_length:]))
    if PGA1 != 0 and PGA2 != 0:
        mtail_ratio1 = mtail_max1 / PGA1
        mtail_ratio2 = mtail_max2 / PGA2
        mtail_ratio = np.sqrt(mtail_ratio1 * mtail_ratio2)
        mtailnoise_ratio = mtail_ratio / PN
    else:
        logging.debug("PGA1 or PGA2 is 0")
        mtail_ratio1 = 1.0
        mtail_ratio2 = 1.0
        mtail_ratio = 1.0

    head_duration = 1.0
    head_length = int(head_duration * sample_rate)
    head_average1 = np.max(abs(acc1[0:head_length]))
    head_average2 = np.max(abs(acc2[0:head_length]))
    if PGA1 != 0 and PGA2 != 0:
        head_ratio1 = head_average1 / PGA1
        head_ratio2 = head_average2 / PGA2
        head_ratio = np.sqrt(head_ratio1 * head_ratio2)
    else:
        logging.debug("PGA1 or PGA2 is 0")
        head_ratio1 = 1.0
        head_ratio2 = 1.0
        head_ratio = 1.0

    # bracketed durations between 10%, 20%, 30%, 40% and 50% of PGA
    # first get all vector indices where abs max acc is greater than or
    # equal, and less than or equal to x*PGA
    hindex1_10 = [
        i for (i, a) in enumerate(acc1) if np.abs(a) >= (0.10 * np.max(np.abs(acc1)))
    ]
    hindex2_10 = [
        i for (i, a) in enumerate(acc2) if np.abs(a) >= (0.10 * np.max(np.abs(acc2)))
    ]
    hindex1_20 = [
        i for (i, a) in enumerate(acc1) if np.abs(a) >= (0.20 * np.max(np.abs(acc1)))
    ]
    hindex2_20 = [
        i for (i, a) in enumerate(acc2) if np.abs(a) >= (0.20 * np.max(np.abs(acc2)))
    ]

    # get bracketed duration (from last and first time the index is exceeded)
    if len(hindex1_10) != 0 and len(hindex2_10) != 0:
        bracketedPGA_10 = np.sqrt(
            ((max(hindex1_10) - min(hindex1_10)) * delta_t)
            * ((max(hindex2_10) - min(hindex2_10)) * delta_t)
        )
    else:
        bracketedPGA_10 = 9999.0

    if len(hindex1_20) != 0 and len(hindex2_20) != 0:
        bracketedPGA_20 = np.sqrt(
            ((max(hindex1_20) - min(hindex1_20)) * delta_t)
            * ((max(hindex2_20) - min(hindex2_20)) * delta_t)
        )
    else:
        bracketedPGA_20 = 9999.0

    bracketedPGA_10_20 = bracketedPGA_10 / bracketedPGA_20

    # calculate Ds575 and Ds595
    Ds575 = np.sqrt(
        ((husid_index1_75 - husid_index1_5) * delta_t)
        * ((husid_index2_75 - husid_index2_5) * delta_t)
    )
    Ds595 = np.sqrt(
        ((husid_index1_95 - husid_index1_5) * delta_t)
        * ((husid_index2_95 - husid_index2_5) * delta_t)
    )

    # geomean of fourier spectra
    smooth_ftgm = np.sqrt(np.multiply(abs(smooth_ft1), abs(smooth_ft2)))
    smooth_ftgm_pe = np.sqrt(np.multiply(abs(smooth_ft1_pe), abs(smooth_ft2_pe)))

    # snr metrics - min, max and averages
    lower_index, upper_index = getFreqIndex(smooth_ft1_freq, 0.1, 20)
    with np.errstate(invalid="ignore"):
        snrgm = np.divide(smooth_ftgm, smooth_ftgm_pe)
    snr_min = min(snrgm[lower_index:upper_index])
    snr_max = max(snrgm)

    lower_index_average, upper_index_average = getFreqIndex(snr1_freq, 0.1, 10)
    snr_average = np.trapz(
        snrgm[lower_index_average:upper_index_average],
        snr1_freq[lower_index_average:upper_index_average],
    ) / (snr1_freq[upper_index_average] - snr1_freq[lower_index_average])

    lower_index_average, upper_index_average = getFreqIndex(snr1_freq, 0.1, 0.5)
    ft_a1 = np.trapz(
        smooth_ftgm[lower_index_average:upper_index_average],
        snr1_freq[lower_index_average:upper_index_average],
    ) / (snr1_freq[upper_index_average] - snr1_freq[lower_index_average])
    snr_a1 = np.trapz(
        snrgm[lower_index_average:upper_index_average],
        snr1_freq[lower_index_average:upper_index_average],
    ) / (snr1_freq[upper_index_average] - snr1_freq[lower_index_average])

    lower_index_average, upper_index_average = getFreqIndex(snr1_freq, 0.5, 1.0)
    ft_a2 = np.trapz(
        smooth_ftgm[lower_index_average:upper_index_average],
        snr1_freq[lower_index_average:upper_index_average],
    ) / (snr1_freq[upper_index_average] - snr1_freq[lower_index_average])
    snr_a2 = np.trapz(
        snrgm[lower_index_average:upper_index_average],
        snr1_freq[lower_index_average:upper_index_average],
    ) / (snr1_freq[upper_index_average] - snr1_freq[lower_index_average])

    lower_index_average, upper_index_average = getFreqIndex(snr1_freq, 1.0, 2.0)
    snr_a3 = np.trapz(
        snrgm[lower_index_average:upper_index_average],
        snr1_freq[lower_index_average:upper_index_average],
    ) / (snr1_freq[upper_index_average] - snr1_freq[lower_index_average])

    lower_index_average, upper_index_average = getFreqIndex(snr1_freq, 2.0, 5.0)
    snr_a4 = np.trapz(
        snrgm[lower_index_average:upper_index_average],
        snr1_freq[lower_index_average:upper_index_average],
    ) / (snr1_freq[upper_index_average] - snr1_freq[lower_index_average])

    lower_index_average, upper_index_average = getFreqIndex(snr1_freq, 5.0, 10.0)
    snr_a5 = np.trapz(
        snrgm[lower_index_average:upper_index_average],
        snr1_freq[lower_index_average:upper_index_average],
    ) / (snr1_freq[upper_index_average] - snr1_freq[lower_index_average])

    ft_a1_a2 = ft_a1 / ft_a2

    # calculate lf to max signal ratios
    signal1_max = np.max(smooth_ft1)
    lf1 = np.trapz(smooth_ft1[0:lower_index], smooth_ft1_freq[0:lower_index]) / (
        smooth_ft1_freq[lower_index] - smooth_ft1_freq[0]
    )
    lf1_pe = np.trapz(smooth_ft1_pe[0:lower_index], smooth_ft1_freq[0:lower_index]) / (
        smooth_ft1_freq[lower_index] - smooth_ft1_freq[0]
    )

    signal2_max = max(smooth_ft2)
    lf2 = np.trapz(smooth_ft2[0:lower_index], smooth_ft1_freq[0:lower_index]) / (
        smooth_ft1_freq[lower_index] - smooth_ft1_freq[0]
    )
    lf2_pe = np.trapz(smooth_ft2_pe[0:lower_index], smooth_ft1_freq[0:lower_index]) / (
        smooth_ft1_freq[lower_index] - smooth_ft1_freq[0]
    )

    signal_ratio_max = max([lf1 / signal1_max, lf2 / signal2_max])
    signal_pe_ratio_max = max([lf1_pe / signal1_max, lf2_pe / signal2_max])

    return [
        signal_pe_ratio_max,
        signal_ratio_max,
        snr_min,
        snr_max,
        snr_average,
        tail_ratio,
        mtail_ratio,
        tailnoise_ratio,
        mtailnoise_ratio,
        head_ratio,
        snr_a1,
        snr_a2,
        snr_a3,
        snr_a4,
        snr_a5,
        ft_a1_a2,
        PNPGA,
        bracketedPGA_10_20,
        Ds575,
        Ds595,
    ]


def computeQualityMetrics(st):
    """
    Get the 2 horizontal components and format the P-wave arrival time before
    launching the computation of the qualtiy metrics as in Bellagamba et al.
    (2019)

    Args:
        st (list of trace): a list of trace as defined in gmprocess (USGS)

    Returns:
        List of float containing the 20 quality metrics
    """
    # Initialize dictionary of variables necessary to the computation of the QM
    tr = {}

    # Determine if traces are horizontal or vertical
    ind = []
    i = 1
    for tr_i in st:
        if "Z" not in tr_i.stats["channel"].upper():
            ind.append(str(i))
            i = i + 1
        else:
            ind.append("v")

    # Extract required info from each trace in the stream
    i = 0
    for tr_i in st:
        if ind[i] != "v":
            # Raw accelerogram (debiased and detrended)
            str_i = "acc_comp" + ind[i]
            tr[str_i] = tr_i.data

            # Fourier spectrum
            str_i = "ft" + ind[i]
            tr[str_i] = tr_i.getCached("signal_spectrum")["spec"]

            # Frequ of the Fourier spectrum
            str_i = "ft" + ind[i] + "_freq"
            tr[str_i] = tr_i.getCached("signal_spectrum")["freq"]

            # Smoothed Fourier spectrum
            str_i = "smooth_ft" + ind[i]
            sig_spec = tr_i.getCached("smooth_signal_spectrum")["spec"]
            sig_spec = np.where(np.isnan(sig_spec), 0.0, sig_spec)
            tr[str_i] = sig_spec

            # Freq of he smoothed Fourier spectrum
            str_i = "smooth_ft" + ind[i] + "_freq"
            tr[str_i] = tr_i.getCached("smooth_signal_spectrum")["freq"]

            # Fourier spectrum of the pre-event trace
            str_i = "ft" + ind[i] + "_pe"
            tr[str_i] = tr_i.getCached("noise_spectrum")["spec"]

            # Frequ of the Fourier spectrum (pre-event trace)
            str_i = "ft" + ind[i] + "_freq_pe"
            tr[str_i] = tr_i.getCached("noise_spectrum")["freq"]

            # Smoothed Fourier spectrum of the pre-event trace
            str_i = "smooth_ft" + ind[i] + "_pe"
            noise_spec = tr_i.getCached("smooth_noise_spectrum")["spec"]
            noise_spec = np.where(np.isnan(noise_spec), 0.0, noise_spec)
            tr[str_i] = noise_spec

            # SNR
            str_i = "snr" + ind[i]
            tr[str_i] = tr_i.getCached("snr")["snr"]

            # SNR freq
            str_i = "snr" + ind[i] + "_freq"
            tr[str_i] = tr_i.getCached("snr")["freq"]

        i = i + 1

    # P-wave arrival time
    split_prov = st[0].getParameter("signal_split")
    if isinstance(split_prov, list):
        split_prov = split_prov[0]
    split_time = split_prov["split_time"]
    start_time = st[0].stats.starttime
    p_pick = split_time - start_time

    # Get the delta t
    delta_t = st[0].stats.delta

    # Compute the QM
    qm = getClassificationMetrics(tr, p_pick, delta_t)

    return qm

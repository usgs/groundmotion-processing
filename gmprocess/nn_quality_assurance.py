import csv
import numpy as np
import copy
from scipy.integrate import cumtrapz
import pkg_resources
import os


def isNumber(s):
    """
    Check if a string is a number
    """
    try:
        float(s)
        return True

    except ValueError:
        return False


def loadCSV(data_path, row_ignore=0, col_ignore=0):
    """
    Load the csv data file
    """
    M = []
    with open(data_path) as csvfile:
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
    Compute sigmoid function for each array entry
    """
    v_act = []
    for x in v_input:
        v_act.append(1./(1+np.exp(-x)))
    return v_act


def tanh(v_input):
    """
    Compute tanh function for each array entry
    """
    v_act = []
    for x in v_input:
        v_act.append(np.tanh(x))
    return v_act


class neuralNet():
    """
    Class to encapsulate the Bellagamba et al. neural net data
    screening method.
    """

    def __init__(self):
        self.n_input = 0
        self.n_neuron_H1 = 0
        self.n_neuron_H2 = -1
        self.n_output = 0
        self.activation_H1 = 'NA'
        self.activation_H2 = 'NA'
        self.activation_output = 'NA'
        self.w_H1 = []
        self.w_H2 = []
        self.b_H1 = []
        self.b_H2 = []
        self.w_output = []
        self.b_output = []

    # loadNN: load and build neural network model
    def loadNN(self, nn_path):
        data_path = os.path.join(nn_path, 'masterF.txt')
        with open(data_path) as masterF:
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
        data_path = os.path.join(nn_path, 'weight_1.csv')
        self.w_H1 = np.asarray(loadCSV(data_path))
        # Biases first hidden layer
        data_path = os.path.join(nn_path, 'bias_1.csv')
        self.b_H1 = np.asarray(loadCSV(data_path))
        # Weights output layer
        data_path = os.path.join(nn_path, 'weight_output.csv')
        self.w_output = np.asarray(loadCSV(data_path))
        # Biases output layer
        data_path = os.path.join(nn_path, 'bias_output.csv')
        self.b_output = np.asarray(loadCSV(data_path))

        # Second hidden layer
        if self.n_neuron_H2 != -1:
            # Weights second hidden layer
            data_path = os.path.join(nn_path, 'weight_2.csv')
            self.w_H2 = np.asarray(loadCSV(data_path))
            # Biases second hidden layer
            data_path = os.path.join(nn_path, 'bias_2.csv')
            self.b_H2 = np.asarray(loadCSV(data_path))

    def useNN(self, v_input):
        v_inter = np.array([])
        # Transform input if required
        if isinstance(v_input, list):
            v_input = np.asarray(v_input)

        # First layer
        if self.activation_H1 == 'sigmoid':
            v_inter = sigmoid(np.dot(v_input.T, self.w_H1) + self.b_H1)
        elif self.activation_H1 == 'tanh':
            v_inter = tanh(np.dot(v_input.T, self.w_H1) + self.b_H1)
        else:
            v_inter = np.dot(v_input.T, self.w_H1) + self.b_H1

        # If second layer exist
        if self.n_neuron_H2 != -1:
            if self.activation_H2 == 'sigmoid':
                v_inter = sigmoid(np.dot(v_inter, self.w_H2) + self.b_H2)
            elif self.activation_H2 == 'tanh':
                v_inter = tanh(np.dot(v_inter, self.w_H2) + self.b_H2)
            else:
                v_inter = np.dot(v_inter, self.w_H2) + self.b_H2

        # Final layer
        if self.activation_output == 'sigmoid':
            v_inter = sigmoid(np.dot(v_inter, self.w_output) + self.b_output)
        elif self.activation_output == 'tanh':
            v_inter = tanh(np.dot(v_inter, self.w_output) + self.b_output)
        else:
            v_inter = np.dot(v_inter, self.w_output) + self.b_output

        return v_inter


def deskewData(data, model_name):
    """
    Deskew the data according to chosen model
    """
    if model_name == 'Cant':
        for i in range(len(data)):
            if i == 0 or i == 1 or i == 11 or i == 15 or i == 16:
                data[i] = np.log(data[i])
            elif i == 17:
                data[i] = -1.0/data[i]**1.2
            elif i == 2:
                data[i] = data[i]**(-.2)
            elif i == 10:
                data[i] = data[i]**(-.06)
            elif i == 19:
                data[i] = data[i]**.43
            elif i == 7:
                data[i] = data[i]**.25
            elif i == 8:
                data[i] = data[i]**.23
            elif i == 9:
                data[i] = data[i]**.05
            elif i == 18:
                data[i] = data[i]**.33
            elif i == 3:
                data[i] = data[i]**(.12)
            elif i == 5:
                data[i] = data[i]**(.48)
            elif i == 6:
                data[i] = data[i]**(.37)
            elif i == 12:
                data[i] = data[i]**.05
            elif i == 13:
                data[i] = data[i]**.08
            elif i == 4:
                data[i] = data[i]**(.16)
            elif i == 14:
                data[i] = data[i]**(.1)
        return data

    elif model_name == 'CantWell':
        for i in range(len(data)):
            if i == 0 or i == 1 or i == 11 or i == 15 or i == 16:
                data[i] = np.log(data[i])
            elif i == 17:
                data[i] = -1.0/data[i]**1.2
            elif i == 2:
                data[i] = data[i]**(-.2)
            elif i == 10:
                data[i] = data[i]**(-.06)
            elif i == 19:
                data[i] = data[i]**.43
            elif i == 7:
                data[i] = data[i]**.1
            elif i == 8:
                data[i] = data[i]**.23
            elif i == 9:
                data[i] = data[i]**.2
            elif i == 18:
                data[i] = data[i]**.33
            elif i == 3:
                data[i] = data[i]**(.05)
            elif i == 5:
                data[i] = data[i]**(.3)
            elif i == 6:
                data[i] = data[i]**(.37)
            elif i == 12:
                data[i] = data[i]**.05
            elif i == 13:
                data[i] = data[i]**.08
            elif i == 4:
                data[i] = data[i]**(.05)
            elif i == 14:
                data[i] = data[i]**(.05)
        return data


def standardizeData(data, mu, sigma):
    """
    Apply transform functions to data
    """
    for i in range(len(data)):
        data[i] = (data[i]-mu[i])/sigma[i]

    return data


def decorrelateData(data, M):
    """
    Apply Mahalanobis transform on data
    """
    M = np.array(M)
    data = M.dot(data)
    data = np.transpose(data)

    return data.tolist()


def preprocessQualityMetrics(qm, model_name):
    """
    preprocessQualtiyMetrics: deskew, standardize and decorrelate the QM
    """
    # Building dir path from model name
    data_path = os.path.join('data', 'nn_qa')
    data_path = os.path.join(data_path, model_name)
    data_path = pkg_resources.resource_filename('gmprocess', data_path)

    # Get resource from the correct dir
    M = loadCSV(os.path.join(data_path, 'M.csv'))
    csv_dir = os.path.join(data_path, 'mu_sigma.csv')
    [mu, sigma] = loadCSV(csv_dir)

    # Deskew, standardize and decorrelate data
    qm = deskewData(qm, model_name)
    qm = standardizeData(qm, mu, sigma)
    qm = decorrelateData(qm, M)

    return qm


def get_husid(acceleration, time_vector):
    """
    Returns the Husid vector, defined as \int{acceleration ** 2.}
    :param numpy.ndarray acceleration:
        Vector of acceleration values
    :param float time_step:
        Time-step of record (s)
    """
    husid = np.hstack([0., cumtrapz(acceleration ** 2., time_vector)])
    AI = husid / max(husid)
    return husid, AI


def getFreqIndex(ft_freq, lower, upper):
    """
    Returns the upper and lower indices of a range of frequencies

    """
    lower_indices = [i for i, x in enumerate(ft_freq) if x > lower]
    upper_indices = [i for i, x in enumerate(ft_freq) if x < upper]
    lower_index = min(lower_indices)
    upper_index = max(upper_indices)
    return lower_index, upper_index


def getHusidIndex(husid, threshold):
    husid_indices = [i for i, x in enumerate(husid) if x > threshold]
    husid_index = min(husid_indices)
    return husid_index


def calculateSNR_min(ft_freq, snr):
    # Frequencies must be available between 0.1 and 20 Hz
    lower_index, upper_index = getFreqIndex(ft_freq, 0.1, 20)
    snr_min = min(snr[lower_index:upper_index])
    return snr_min


def calculateHusid(acc, t):
    """
    Uses the obspy function to estimate the Arias and index of duration
    """
    husid, AI = get_husid(acc, t)
    Arias = max(husid)
    husid_index_5 = getHusidIndex(AI, 0.05)
    husid_index_75 = getHusidIndex(AI, 0.75)
    husid_index_95 = getHusidIndex(AI, 0.95)
    return husid, AI, Arias, husid_index_5, husid_index_75, husid_index_95


def getClassificationMetrics(tr, p_pick, delta_t):

    ########################################
    # Acceleration units changed into g!!! #
    #    Vertical component not used!!!    #
    ########################################

    # Extract data from dictionary
    # First horizontal comp
    acc_comp1 = np.asarray(tr['acc_comp1'])/981.
    ft1_freq = np.asarray(tr['ft1_freq'])
    ft1 = np.asarray(tr['ft1'])/981.
    smooth_ft1 = np.asarray(tr['smooth_ft1'])/981.
    smooth_ft1_freq = np.asarray(tr['smooth_ft1_freq'])
    ft1_pe = np.asarray(tr['ft1_pe'])/981.
    ft1_freq_pe = np.asarray(tr['ft1_freq_pe'])
    smooth_ft1_pe = np.asarray(tr['smooth_ft1_pe'])/981.
    snr1 = np.asarray(tr['snr1'])
    snr1_freq = np.asarray(tr['snr1_freq'])

    # Second horizontal comp
    acc_comp2 = np.asarray(tr['acc_comp2'])/981.
    ft2_freq = np.asarray(tr['ft2_freq'])
    ft2 = np.asarray(tr['ft2'])/981.
    smooth_ft2 = np.asarray(tr['smooth_ft2'])/981.
    ft2_pe = np.asarray(tr['ft2_pe'])/981.
    ft2_freq_pe = np.asarray(tr['ft2_freq_pe'])
    smooth_ft2_pe = np.asarray(tr['smooth_ft2_pe'])/981.
    snr2 = np.asarray(tr['snr2'])

    # Sample rate
    sample_rate = 1./delta_t

    # Index of the P-wave arrival time
    index_p_arrival = int(np.floor(np.multiply(p_pick, sample_rate)))

    # recreate a time vector
    t = np.arange(len(acc_comp1))*delta_t

    # set up a copy of accelerations for plotting later (they get changed
    # by window/taper in the ft step)
    acc1 = copy.deepcopy(acc_comp1)
    acc2 = copy.deepcopy(acc_comp2)

    # calculate husid and Arias intensities
    husid1, AI1, Arias1, husid_index1_5, husid_index1_75, husid_index1_95 = \
        calculateHusid(acc1, t)
    husid2, AI2, Arias2, husid_index2_5, husid_index2_75, husid_index2_95 = \
        calculateHusid(acc2, t)

    # calculate max amplitudes of acc time series, final is geomean
    PGA1 = np.max(np.abs(acc1))
    PGA2 = np.max(np.abs(acc2))
    amp1_pe = max(abs(acc1[0:index_p_arrival]))
    amp2_pe = max(abs(acc2[0:index_p_arrival]))
    PGA = np.sqrt(PGA1*PGA2)
    PN = np.sqrt(amp1_pe*amp2_pe)
    PN_average = np.sqrt(np.average(abs(acc1[0:index_p_arrival])) *
                         np.average(abs(acc2[0:index_p_arrival])))
    PNPGA = PN/PGA

    # calculate effective head and tail lengths
    tail_duration = min([5.0, 0.1*t[-1]])
    tail_length = int(tail_duration * sample_rate)
    tail_average1 = np.mean(abs(acc1[-tail_length:]))
    tail_average2 = np.mean(abs(acc2[-tail_length:]))
    if PGA1 != 0 and PGA2 != 0:
        tail_ratio1 = tail_average1 / PGA1
        tail_ratio2 = tail_average2 / PGA2
        tail_ratio = np.sqrt(tail_ratio1*tail_ratio2)
        tailnoise_ratio = tail_ratio / PN_average
    else:
        print('PGA1 or PGA2 is 0')
        tail_ratio1 = 1.0
        tail_ratio2 = 1.0
        tail_ratio = 1.0

    mtail_duration = min([2.0, 0.1*t[-1]])
    mtail_length = int(mtail_duration * sample_rate)
    mtail_max1 = np.max(abs(acc1[-mtail_length:]))
    mtail_max2 = np.max(abs(acc2[-mtail_length:]))
    if PGA1 != 0 and PGA2 != 0:
        mtail_ratio1 = mtail_max1 / PGA1
        mtail_ratio2 = mtail_max2 / PGA2
        mtail_ratio = np.sqrt(mtail_ratio1*mtail_ratio2)
        mtailnoise_ratio = mtail_ratio / PN
    else:
        print('PGA1 or PGA2 is 0')
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
        head_ratio = np.sqrt(head_ratio1*head_ratio2)
    else:
        print('PGA1 or PGA2 is 0')
        head_ratio1 = 1.0
        head_ratio2 = 1.0
        head_ratio = 1.0

    # bracketed durations between 10%, 20%, 30%, 40% and 50% of PGA
    # first get all vector indices where abs max acc is greater than or
    # equal, and less than or equal to x*PGA
    hindex1_10 = [i for (i, a) in enumerate(acc1)
                  if np.abs(a) >= (0.10*np.max(np.abs(acc1)))]
    hindex2_10 = [i for (i, a) in enumerate(acc2)
                  if np.abs(a) >= (0.10*np.max(np.abs(acc2)))]
    hindex1_20 = [i for (i, a) in enumerate(acc1)
                  if np.abs(a) >= (0.20*np.max(np.abs(acc1)))]
    hindex2_20 = [i for (i, a) in enumerate(acc2)
                  if np.abs(a) >= (0.20*np.max(np.abs(acc2)))]

    # get bracketed duration (from last and first time the index is exceeded)
    if len(hindex1_10) != 0 and len(hindex2_10) != 0:
        bracketedPGA_10 = np.sqrt(((max(hindex1_10)-min(hindex1_10))*delta_t) *
                                  ((max(hindex2_10)-min(hindex2_10))*delta_t))
    else:
        bracketedPGA_10 = 9999.0

    if len(hindex1_20) != 0 and len(hindex2_20) != 0:
        bracketedPGA_20 = np.sqrt(((max(hindex1_20)-min(hindex1_20))*delta_t) *
                                  ((max(hindex2_20)-min(hindex2_20))*delta_t))
    else:
        bracketedPGA_20 = 9999.0

    bracketedPGA_10_20 = bracketedPGA_10/bracketedPGA_20

    # calculate Ds575 and Ds595
    Ds575 = np.sqrt(((husid_index1_75-husid_index1_5)*delta_t) *
                    ((husid_index2_75-husid_index2_5)*delta_t))
    Ds595 = np.sqrt(((husid_index1_95-husid_index1_5)*delta_t) *
                    ((husid_index2_95-husid_index2_5)*delta_t))

    # geomean of fourier spectra
    smooth_ftgm = np.sqrt(np.multiply(abs(smooth_ft1), abs(smooth_ft2)))
    smooth_ftgm_pe = np.sqrt(np.multiply(abs(smooth_ft1_pe),
                                         abs(smooth_ft2_pe)))

    # snr metrics - min, max and averages
    lower_index, upper_index = getFreqIndex(smooth_ft1_freq, 0.1, 20)
    snrgm = np.divide(smooth_ftgm, smooth_ftgm_pe)
    snr_min = min(snrgm[lower_index:upper_index])
    snr_max = max(snrgm)

    lower_index_average, upper_index_average = getFreqIndex(snr1_freq, 0.1, 10)
    snr_average = (np.trapz(
        snrgm[lower_index_average:upper_index_average],
        snr1_freq[lower_index_average:upper_index_average]) /
        (snr1_freq[upper_index_average]-snr1_freq[lower_index_average]))

    lower_index_average, upper_index_average = getFreqIndex(
        snr1_freq, 0.1, 0.5)
    ft_a1 = (np.trapz(
        smooth_ftgm[lower_index_average:upper_index_average],
        snr1_freq[lower_index_average:upper_index_average]) /
        (snr1_freq[upper_index_average]-snr1_freq[lower_index_average]))
    snr_a1 = (np.trapz(
        snrgm[lower_index_average:upper_index_average],
        snr1_freq[lower_index_average:upper_index_average]) /
        (snr1_freq[upper_index_average]-snr1_freq[lower_index_average]))

    lower_index_average, upper_index_average = getFreqIndex(
        snr1_freq, 0.5, 1.0)
    ft_a2 = (np.trapz(
        smooth_ftgm[lower_index_average:upper_index_average],
        snr1_freq[lower_index_average:upper_index_average]) /
        (snr1_freq[upper_index_average]-snr1_freq[lower_index_average]))
    snr_a2 = (np.trapz(
        snrgm[lower_index_average:upper_index_average],
        snr1_freq[lower_index_average:upper_index_average]) /
        (snr1_freq[upper_index_average]-snr1_freq[lower_index_average]))

    lower_index_average, upper_index_average = getFreqIndex(
        snr1_freq, 1.0, 2.0)
    snr_a3 = (np.trapz(
        snrgm[lower_index_average:upper_index_average],
        snr1_freq[lower_index_average:upper_index_average]) /
        (snr1_freq[upper_index_average]-snr1_freq[lower_index_average]))

    lower_index_average, upper_index_average = getFreqIndex(
        snr1_freq, 2.0, 5.0)
    snr_a4 = (np.trapz(
        snrgm[lower_index_average:upper_index_average],
        snr1_freq[lower_index_average:upper_index_average]) /
        (snr1_freq[upper_index_average]-snr1_freq[lower_index_average]))

    lower_index_average, upper_index_average = getFreqIndex(
        snr1_freq, 5.0, 10.0)
    snr_a5 = (np.trapz(
        snrgm[lower_index_average:upper_index_average],
        snr1_freq[lower_index_average:upper_index_average]) /
        (snr1_freq[upper_index_average]-snr1_freq[lower_index_average]))

    ft_a1_a2 = ft_a1 / ft_a2

    # calculate lf to max signal ratios
    signal1_max = np.max(smooth_ft1)
    lf1 = (np.trapz(
        smooth_ft1[0:lower_index],
        smooth_ft1_freq[0:lower_index]) /
        (smooth_ft1_freq[lower_index]-smooth_ft1_freq[0]))
    lf1_pe = (np.trapz(
        smooth_ft1_pe[0:lower_index],
        smooth_ft1_freq[0:lower_index]) /
        (smooth_ft1_freq[lower_index]-smooth_ft1_freq[0]))

    signal2_max = max(smooth_ft2)
    lf2 = (np.trapz(
        smooth_ft2[0:lower_index],
        smooth_ft1_freq[0:lower_index]) /
        (smooth_ft1_freq[lower_index]-smooth_ft1_freq[0]))
    lf2_pe = (np.trapz(
        smooth_ft2_pe[0:lower_index],
        smooth_ft1_freq[0:lower_index]) /
        (smooth_ft1_freq[lower_index]-smooth_ft1_freq[0]))

    signal_ratio_max = max([lf1/signal1_max, lf2/signal2_max])
    signal_pe_ratio_max = max([lf1_pe/signal1_max, lf2_pe/signal2_max])

    return [signal_pe_ratio_max,
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
            Ds595]


def computeQualityMetrics(st):
    """
    Compute quality metrics as in Bellagamba et al. (2019)
    """
    # Initialize dictionary of variables necessary to the computation of the QM
    tr = {}

    # Determine if traces are horizontal or vertical
    ind = []
    i = 1
    for tr_i in st:
        if 'Z' not in tr_i.stats['channel'].upper():
            ind.append(str(i))
            i = i + 1
        else:
            ind.append('v')

    # Extract required info from each trace in the stream
    i = 0
    for tr_i in st:
        if ind[i] != 'v':
            # Raw accelerogram (debiased and detrended)
            str_i = 'acc_comp' + ind[i]
            tr[str_i] = tr_i.data

            # Fourier spectrum
            str_i = 'ft' + ind[i]
            tr[str_i] = tr_i.getParameter('signal_spectrum')['spec']

            # Frequ of the Fourier spectrum
            str_i = 'ft' + ind[i] + '_freq'
            tr[str_i] = tr_i.getParameter('signal_spectrum')['freq']

            # Smoothed Fourier spectrum
            str_i = 'smooth_ft' + ind[i]
            tr[str_i] = tr_i.getParameter('smooth_signal_spectrum')['spec']

            # Freq of he smoothed Fourier spectrum
            str_i = 'smooth_ft' + ind[i] + '_freq'
            tr[str_i] = tr_i.getParameter('smooth_signal_spectrum')['freq']

            # Fourier spectrum of the pre-event trace
            str_i = 'ft' + ind[i] + '_pe'
            tr[str_i] = tr_i.getParameter('noise_spectrum')['spec']

            # Frequ of the Fourier spectrum (pre-event trace)
            str_i = 'ft' + ind[i] + '_freq_pe'
            tr[str_i] = tr_i.getParameter('noise_spectrum')['freq']

            # Smoothed Fourier spectrum of the pre-event trace
            str_i = 'smooth_ft' + ind[i] + '_pe'
            tr[str_i] = tr_i.getParameter('smooth_noise_spectrum')['spec']

            # SNR
            str_i = 'snr' + ind[i]
            tr[str_i] = tr_i.getParameter('snr')['snr']

            # SNR freq
            str_i = 'snr' + ind[i] + '_freq'
            tr[str_i] = tr_i.getParameter('snr')['freq']

        i = i + 1

    # P-wave arrival time
    split_prov = st[0].getParameter('signal_split')
    if isinstance(split_prov, list):
        split_prov = split_prov[0]
    split_time = split_prov['split_time']
    start_time = st[0].stats.starttime
    p_pick = split_time - start_time

    # Get the delta t
    delta_t = st[0].stats.delta

    # Compute the QM
    qm = getClassificationMetrics(tr, p_pick, delta_t)

    return qm


def NNet_QA(st, acceptance_threshold, model_name):
    """
    Main function for computing  QA metrics as in Bellagamba et al. (2019)

    """
    # Create the path to the NN folder based on model name
    nn_path = os.path.join('data', 'nn_qa')
    nn_path = os.path.join(nn_path, model_name)
    nn_path = pkg_resources.resource_filename('gmprocess', nn_path)

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

    print(scores)
    print(flag_accept)
    # Add parameters to Stream (acceptance threshold, model_name, score_lowQ,
    # score_highQ, highQualityFlag)
    nnet_dict = {
        'accept_thres': acceptance_threshold,
        'model_name': model_name,
        'score_LQ': scores[0],
        'score_HQ': scores[1],
        'pass_QA': flag_accept
    }
    st.setStreamParam(
        'nnet_qa', nnet_dict
    )
    if not flag_accept:
        for tr in st:
            tr.fail('Failed NNet QA check.')

    return st

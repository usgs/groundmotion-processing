import matplotlib.pyplot as plt
import numpy as np
import datetime as dt
from scipy.signal import butter, lfilter, hilbert


def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y


# Adapted form MATLAB script
def AICPicker(data, triggers, search_window, sps, debugPlot=False):

    refined_triggers = []
    data = data - np.median(data)
    searchwindowpts = int(sps * search_window)

    for trigpts in triggers:

        trigstart = (trigpts - (2 * searchwindowpts))
        trigend = trigpts + 1 * searchwindowpts

        if(trigstart > 0 and trigend < np.size(data)):
            data_select = data[trigstart:trigend]
        else:
            print(np.size(data), trigstart, trigend)
            continue

        time_select = np.arange(np.size(data_select)) / sps - 2 * (search_window)
        pts_select = np.arange(np.size(data_select)) - 2 * searchwindowpts

        AIC = np.zeros(np.size(data_select))

        for n in range(1, np.size(AIC) - 2):
            s1 = np.var(data_select[0:n])
            if(s1 <= 0): s1 = 0
            else: s1 = np.log(s1)

            s2 = np.var(data_select[(n + 1):-1])
            if(s2 <= 0): s2 = 0
            else: s2 = np.log(s2)
            AIC[n] = (n * s1) + ((np.size(AIC) - n + 1) * s2)

        if(debugPlot):
            fig2 = plt.figure()
            ax = fig2.add_subplot(111)
            ax.plot(time_select, data_select,)
            axt = ax.twinx()
            axt.plot(time_select, AIC, 'r')

        AIC[0:5] = np.inf
        AIC[-5:] = np.inf

        refined_triggers.append(pts_select[np.argmin(AIC) + 1] + trigpts)

    return refined_triggers


def STALTA_Earle(data, datao, sps, STAW, STAW2, LTAW, hanning, threshold, threshold2, threshdrop):
    data_hil = hilbert(data)
    envelope = np.abs(data_hil)
    envelope = np.convolve(envelope, np.hanning(hanning * sps), mode='same')

    sta_samples = int(STAW * sps)
    sta_samples2 = int(STAW2 * sps)
    lta_samples = int(LTAW * sps)

    sta = np.zeros(np.size(envelope))
    sta2 = np.zeros(np.size(envelope))
    lta = np.zeros(np.size(envelope))

    for i in range(np.size(envelope) - lta_samples - 1):
        lta[i + lta_samples + 1] = np.sum(envelope[i:i + lta_samples])
        sta[i + lta_samples + 1] = np.sum(envelope[i + lta_samples + 1:i + lta_samples + sta_samples + 1])
        sta2[i + lta_samples + 1] = np.sum(envelope[i + lta_samples + 1:i + lta_samples + sta_samples2 + 1])

    lta = lta / float(lta_samples)
    sta = sta / float(sta_samples)
    sta2 = sta2 / float(sta_samples2)

    lta[lta < 0.00001] = 0.00001

    ratio = sta / lta
    ratio2 = sta2 / lta

    trigger = False
    triggers_on = []
    triggers_off = []

    for i in range(np.size(ratio) - 1):
        if(trigger == False and ratio[i] >= threshold and ratio2[i] >= threshold2 and ratio[i] > ratio[i + 1]):
            triggers_on.append(i)
            trigger = True
        elif(trigger == True and ratio[i] <= threshdrop):
            triggers_off.append(i)
            trigger = False

    refined_triggers = AICPicker(data, triggers_on, 4., sps)

    return refined_triggers, triggers_on, triggers_off, ratio, ratio2, envelope, sta, lta


def PowerPicker(tr, highpass=1.4, lowpass=6, order=3, sta=3.0, sta2=3.0,
                lta=20.0, hanningWindow=3.0, threshDetect=2.5,
                threshDetect2=2.5, threshRestart=1.5):

    tr_copy = tr.copy()
    tr_copy.resample(20)
    tr_copy.detrend()
    data = tr_copy.data
    sps = tr_copy.stats.sampling_rate

    datahigh = butter_bandpass_filter(data, highpass, lowpass, sps, order=order)

    rt, ton, toff, ratio, ratio2, envelope, sta, lta = STALTA_Earle(datahigh, data, sps, sta, sta2, lta, hanningWindow, threshDetect, threshDetect2, threshRestart)

    rt2 = []
    for r in rt:
        rt2.append(tr_copy.stats.starttime + dt.timedelta(seconds=(r / sps)))
    return rt2

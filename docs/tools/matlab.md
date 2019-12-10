# Matlab utilities

As ASDF files are a particular specification of the more general HDF format, they are accessible from any language that has implemented an HDF library. Matlab is one of those such languages, and has excellent support for HDF.

For the convenience of Matlab users, we have provided three functions that access different sections of the ASDF files:

 - get_events.m Return a structure containing all the earthquakes found.
 - get_all_waveforms.m Return a structure containing all waveforms found.
 - get_waveform_metrics.m Return a structure containing tables of peak ground motions.

## get_events usage

```
>> events = get_events('workspace.hdf');

>> disp(events)
      
      eventid: 'us2000k7yn'
         time: 7.3752e+05
     latitude: 37.5063
    longitude: 29.3787
        depth: 10
    magnitude: 5.1000
```

## get_all_waveforms usage

```
>> waveforms = get_all_waveforms('workspace.hdf');
>> disp(waveforms)
  1×480 struct array with fields:

    network
    station
    location
    channel
    label
    eventid
    starttime
    sampling_rate
    data
    times

>> network = waveforms(1).network;
>> station = waveforms(1).station;
>> channel = waveforms(1).channel;
>> location = waveforms(1).location;
>> time = waveforms(1).starttime;
>> tstr = sprintf('%s.%s.%s.%s %s',network,station,channel,location,datestr(time));
>> plot(waveforms(1).times,waveforms(1).data);
>> title(tstr);
```

![Waveform plot from Matlab](waveform.png)

<!-- <figure>
  <img src="./waveform.png" alt="Waveform plot from Matlab"/>
</figure> -->

## get_waveform_metrics usage

```
>> peaks = get_waveform_metrics(h5file);
>> disp(peaks)
                            h2: [80×10 table]
                            h1: [80×10 table]
    greater_of_two_horizontals: [80×10 table]
                             z: [80×10 table]

>> disp(peaks.h2)
      pgv         sa2p0        sa3p0        pga        sa1p0        event       network    station    location    channel
    ________    _________    _________    ________    ________    __________    _______    _______    ________    _______

     0.01297    0.0075111    0.0041874    0.010496    0.014267    us2000k7yn    GE         KARP       --          HN     
    0.012928    0.0075072    0.0041827    0.010452    0.014251    us2000k7yn    GE         KARP       --          SN     
      6998.4       2.9476       2.9476        1.59      2.9476    us2000k7yn    IU         ANTO       20          LN     
     0.34561      0.26216      0.10769     0.32923     0.48932    us2000k7yn    TK         0302       --          HN     
     0.14121      0.13998     0.038559     0.10427     0.14042    us2000k7yn    TK         0308       --          HN     
    0.095555     0.038772     0.032787    0.086026     0.16059    us2000k7yn    TK         0314       --          HN     
     0.12106      0.14991     0.047052    0.074251     0.17323    us2000k7yn    TK         0315       --          HN     
    0.030213     0.023683    0.0097845    0.021834    0.053781    us2000k7yn    TK         0705       --          HN     
    0.047034     0.018479     0.016809      0.0406    0.061787    us2000k7yn    TK         0707       --          HN     
    0.031103      0.01682    0.0081732    0.034182     0.04773    us2000k7yn    TK         0708       --          HN     
    0.073574     0.032256     0.016026    0.061253     0.21487    us2000k7yn    TK         0712       --          HN     
    0.026615     0.015955     0.010826    0.015979    0.039799    us2000k7yn    TK         0717       --          HN  
...
```
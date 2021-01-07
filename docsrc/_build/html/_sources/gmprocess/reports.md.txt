# Processing reports

The processing reports can be generated with
```bash
gmprocess -o test --report
```

New report PDF files have been created for each event:
```
test
├── ci38038071
│   ├── event.json
│   ├── plots
│   │   ├── ci38038071_AZ.HSSP.HN.png
│   │   ├── ci38038071_CE.23178.HN.png
│   │   └── ci38038071_CE.23837.HN.png
│   ├── raw
│   │   ├── AZ.HSSP.HN.png
│   │   ├── CE.23178.HN.png
│   │   └── CE.23837.HN.png
│   ├── report_ci38038071.pdf
│   ├── stations_map.png
│   └── workspace.hdf
└── ci38457511
    ├── event.json
    ├── plots
    │   ├── ci38457511_ZZ.CCC.HN.png
    │   ├── ci38457511_ZZ.CLC.HN.png
    │   └── ci38457511_ZZ.TOW2.HN.png
    ├── raw
    │   ├── ZZ.CCC.HN.png
    │   ├── ZZ.CLC.HN.png
    │   └── ZZ.TOW2.HN.png
    ├── report_ci38457511.pdf
    ├── stations_map.png
    └── workspace.hdf
```

The reports include

- Title page with the version of the code used to generate the report and
  a simple map of the earthquake epicenter and the stations. Note that the
  stations are colored green if they have passed all QA checks, and red if
  they have failed any checks.
- One page per station that summarises the results, including plots of the
  data, a table giving the provenance of the data, the method that was used
  to compute the noise/signal split time, and the reason for the QA failure
  (if the station has failed).
- The left header includes event information; the right header includes the
  network, stsation, and instrument code (first two characters of the
  channel code). Note that if a station code includes multiple instruments
  of different types (e.g., strong motion and broad band) then the channels
  for the different instrument are treated as separate stations.
- The top row of plots are the acceleration time history (top row) with the
  noise/signal split time marked as a vertical dashed line. Note that if the
  station/instrument has more than three channels, only the first three are
  displayed.
- The second row of plots are the velocity time histories.
- The third row of plots gives the **signal** Fourier amplitude spectrum in
  blue (thin/light is the raw FFT, thick/dark is the smoothed spectrum) and
  the **noise** spectrum in red. We also give fit a simple Brune spectrum to
  the signal for the horizontal channels (black dashed line) and show the
  Brune corner frequency as a vertical dashed line.
- The fourth row gives the signal-to-noise ratio (SNR) as the blue line; the
  parameters of the SNR QA check are given as thick gray lines: the minimum
  SNR threshold is the horizontal bar, and the vertical bars indicate the
  band across which the threshold must be exceeded; the selected highpass and
  lowpass corner frequencies are given as vertical dashed black lines. 

Example summary plots are given below for two stations

- CE.23178.HN passed all QA checks.
- AZ.HSSP.HN failed because the SNR did not meet the criteria on the HN1
  channel. 


<figure>
  <img src="../figs/ci38038071_CE.23178.HN.png"
  alt="Summary plot of CE.23178.HN"/>
</figure>

<figure>
  <img src="../figs/ci38038071_AZ.HSSP.HN.png"
  alt="Summary plot of AZ.HSSP.HN"/>
</figure>

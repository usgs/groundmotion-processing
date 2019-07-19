# Waveform processing


Once the data has been assembled into the output directory, one can review
the raw data plots that have been created in the `<eventid>/raw` directory
to look for potential issues.

The next step is to process the records.


```bash
$ ls -R demo2
ci38038071

demo2/ci38038071:
raw		workspace.hdf

demo2/ci38038071/raw:
AZ.HSSP..HNE__20180829T023258Z__20180829T024028Z.mseed		CE.23178.10.HNN__20180829T023318Z__20180829T023648Z.mseed
AZ.HSSP..HNN__20180829T023258Z__20180829T024028Z.mseed		CE.23178.10.HNZ__20180829T023318Z__20180829T023648Z.mseed
AZ.HSSP..HNZ__20180829T023258Z__20180829T024028Z.mseed		CE.23178.xml
AZ.HSSP.xml							CE.23837.HN.png
CE.23178.10.HNE__20180829T023318Z__20180829T023648Z.mseed	CE23837.V1C
$ gmprocess -o demo2 --process --directory demo2
```
This will be followed by a lot of messages to the terminal about the processing
steps. No new files will be created but the processed waveforms will be added
to the workspace file.

In order to review the processed waveforms and see which records did not pass
any of the initial quality controll checks, it is useful to generate the
processing report with
```bash
gmprocess -o demo2 --report --directory demo2
```




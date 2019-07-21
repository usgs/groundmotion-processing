# Waveform processing


Once the data has been assembled into the output directory, one can review
the raw data plots that have been created in the `<eventid>/raw` directory
to look for potential issues.

The next step is to process the records, which can be done with:
```bash
gmprocess -o test --process
```

The output directory structure has not changed:
```
test
├── ci38038071
│   ├── event.json
│   ├── raw
│   │   ├── AZ.HSSP.HN.png
│   │   ├── CE.23178.HN.png
│   │   └── CE.23837.HN.png
│   └── workspace.hdf
└── ci38457511
    ├── event.json
    ├── raw
    │   ├── ZZ.CCC.HN.png
    │   ├── ZZ.CLC.HN.png
    │   └── ZZ.TOW2.HN.png
    └── workspace.hdf
```

But the processed waveforms have been added to the workspace files. 
To review the processing results, it is easiest to view the processing
reports, which are generated in the next step.

# Exporting data

Currently, station and waveform metrics are all computed via the `gmprocess`
command when processing is done, and they are stored in the workspace file.
Use the `--export` argument to write the results to tables that are easy
to import into other programs.

Following the examples in the prior sections:
```bash
gmprocess -o test --export
```
Which creates additional files in the output directory:
```
test
├── GREATER_OF_TWO_HORIZONTALS_PGA.png
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
├── ci38457511
│   ├── event.json
│   ├── plots
│   │   ├── ci38457511_ZZ.CCC.HN.png
│   │   ├── ci38457511_ZZ.CLC.HN.png
│   │   └── ci38457511_ZZ.TOW2.HN.png
│   ├── raw
│   │   ├── ZZ.CCC.HN.png
│   │   ├── ZZ.CLC.HN.png
│   │   └── ZZ.TOW2.HN.png
│   ├── report_ci38457511.pdf
│   ├── stations_map.png
│   └── workspace.hdf
├── events.csv
├── greater_of_two_horizontals.csv
├── h1.csv
├── h2.csv
└── z.csv
```
A few notes:

- We now have a summary plot of all of the data in the output directory
  named `GREATER_OF_TWO_HORIZONTALS_PGA.png`. This file can be useful
  for spotting outlies in the data that may require additional investigation.
- `events.csv` is a summary table for event information.
- The waveform and station metrics are output into separate tables for each
  intensity measure component (IMc). In this example, this includes:
    - `greater_of_two_horizontals.csv`
    - `h1.csv`
    - `h2.csv`
    - `z.csv`
  If the config file was modified to include additional IMCs, then more
  tables would be created (e.g., `rotd50.csv`).
- The IMT tables include columns for each intensity measure type (IMT) that
  was specified in the config file.
  
# gmprocess Python script

The `gmprocess` command has *positional* and *optional* parameters. The positional parameters
are:
 - The output directory where event data directories will be stored.
 - A set of *commands* that will perform various operations:
    - assemble: Download data from all available online sources, or load raw data from files if --directory is selected.
    - process: Process data using steps defined in configuration file.
    - report: Create a summary report for each event specified.
    - provenance: Generate provenance table in --format format.
    - export: Generate metrics tables (NGA-style "flat" files) for all events and IMCs.
    - shakemap: Generate ShakeMap-friendly peak ground motions table.

The optional parameters, generally speaking, are used to modify the behavior of the commands above.
There are four optional parameters that modify the behavior of the `assemble` command:
 - `-i`: Specify 1 to many ComCat event IDs.
 - `-e`: Specify information for a single event
 - `-t, --textfile`: Specify a text file with *either* a list of ComCat IDs OR space separated values of ID,TIME,LAT,LON,DEPTH,MAG.
 - `--directory`: Sidestep online data retrieval, read from local directory. This
    directory should contain any number of event data directories, which
    should contain data files in a known format and an event.json file,
    which should be the JSON form of a dictionary with fields: id, time,
    lat, lon, depth, magnitude. The id field must match the event
    directory name.

The `-f, --format` option dictates whether tabular output (provenance and export tables) are in 
CSV or Excel format.

The `-p, --process-tag` option allows the user to set the tag associated with processed data in the 
workspace.hdf files. If not specified, the tag is set to the current date/time, in YYYYMMDDHHMMSS format.

The `-c, --config` option allows the user to specify a different configuration file than the one that is 
found by default. This can be used in concert with the -r option (see below) to recompute the metrics
(i.e., not use those that are in the event workspace.hdf file.)

The `-r, --recompute-metrics` option allows the user to recompute metrics when used with `-c` option 
described above.

The `-l, --log-file` option allows the user to specify a log file to capture all of the output
that would normally go to the screen.




The commands can be specified independently from each other, and in any order, but there are certain dependencies within the code:
 - processing requires that assembly has already occurred.
 - reporting, provenance, exporting, and shakemap file generation require that processing has been performed.

Details about the commands:
 - `assemble` will download or read from files raw data files, 
    write them to the event workspace.hdf file, and make plots of the unprocessed waveforms
    in the `raw` directory.
 - `process` will take the raw waveforms, run them through the processing defined in 
    either the default config.yml file, or a custom one, write processed waveforms to
    the event workspace.hdf file, and also calculate station metrics (distances) and stream
    metrics (IMC/IMT combinations) and save them to the workspace file as well.
 - `provenance` will generate a spreadsheet detailing the processing steps applied to each 
    waveform.
 - `report` will generate per-event diagnostic reports, with a front page containing a map
    of stations, and then one page per station with a series of diagnostic plots and a table
    of processing provenance. Each page will also indicate whether the waveform data
    passed all pre-processing checks, and if not will indicate the reason why.
 - `shakemap` will generate a spreadsheet that can be used as input to the ShakeMap program.
    This may be deprecated in the future.
 - `export` will generate a series of spreadsheet files, one per Intensity Measure Component (IMC)
    (greater of two horizontals, rotd50, etc.), with columns containing station information and then
    columns of all selected/appropriate Intensity Measure Types (IMT). There will be an additional 
    events spreadsheet containing summaries of all the earthquakes represented.

## gmprocess Output

Running gmprocess will generate a nested data structure. For example, the command:

```bash
gmprocess /data/nocal assemble process report provenance export -i nc72282711 nc72507396
```
 will result in a directory structure that looks like this:
```
 /data/nocal
            |
            +-- *.csv (IMC tables, plus events.csv)
            +-- <CHOSENIMC_CHOSEN_IMT>.png (regression plot)
            |    
            +-- nc72282711
            |  |  
            |  +-- report_nc72282711.pdf
            |  +-- stations_map.png
            |  +-- workspace.hdf
            |  +-- provenance.csv
            |  +-- raw
            |      |
            |      +--(raw data files)
            |      +--(PNG plots of raw data files, grouped by station)
            |   
            |  +-- plots
            |      |
            |      +--(diagnostic plots of each waveform)
            +-- nc72507396
            |  |  
            |  +-- report_nc72507396.pdf
            |  +-- stations_map.png
            |  +-- workspace.hdf
            |  +-- provenance.csv
            |  +-- raw
            |      |
            |      +--(raw data files)
            |      +--(PNG plots of raw data files, grouped by station)
            |  +-- plots
            |      |
            |      +--(diagnostic plots of each waveform)
```
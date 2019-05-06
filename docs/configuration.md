# Configuration

gmprocess uses a format called Yet Another Markup Language (YAML) for
configuring data retrieval, processing steps, report generation, etc. There is
a default configuration file in the gmprocess repository, which can be viewed here:

https://github.com/usgs/groundmotion-processing/blob/master/gmprocess/data/config.yml

This file will be installed with the software on your system. A custom copy of
this config can be created by using the `gmsetup` program:

`gmsetup --help`

```
usage: gmsetup [-h] [-d | -q] [-f FULL_NAME [FULL_NAME ...]] [-e EMAIL] [-l]
               [-s SECTIONS [SECTIONS ...]] [-o]
               config_file

Setup gmprocess config files.

positional arguments:
  config_file           Path to desired output config file.

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Print all informational messages.
  -q, --quiet           Print only errors.
  -f FULL_NAME [FULL_NAME ...], --full-name FULL_NAME [FULL_NAME ...]
                        Supply the config with your name
  -e EMAIL, --email EMAIL
                        Supply the config with your email address
  -l, --list-sections   List the sections in the config and exit.
  -s SECTIONS [SECTIONS ...], --sections SECTIONS [SECTIONS ...]
                        Supply list of section names to include in output
                        file.
  -o, --overwrite       Overwrite existing config file at the same location.
```

## Sections

### fetchers

See the [configuration section of "Fetching Data"](fetching.md#configuration "Fetchers configuration")

### read

### windows

### processing

### build_report

### metrics

### pickers



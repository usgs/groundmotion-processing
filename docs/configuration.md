# Configuration

The primary method for specifying parameters is a configuration file in the [Yet Another Markup Language (YAML)](https://yaml.org/). A default configuration file [gmprocess/data/config.yml](https://github.com/usgs/groundmotion-processing/blob/master/gmprocess/data/config.yml) is bundled with the code.

You can generate a custom copy of this configuration file using the `gmsetup`
program:

```
$ gmsetup --help

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

## Sections in the configuration file

### fetchers

See the [configuration section of "Fetching Data"](fetching.md#configuration "Fetchers configuration")

### read

### windows

### processing

### build_report

### metrics

### pickers

#!/usr/bin/env python

# stdlib imports
import os
import argparse
import sys

# third party imports
import pkg_resources
from ruamel.yaml import YAML

# local imports
from gmprocess.utils.constants import CONFIG_FILE_PRODUCTION
from gmprocess.utils.args import add_shared_args


def main():
    description = 'Setup gmprocess config files.'
    parser = argparse.ArgumentParser(description=description)

    # Shared arguments
    parser = add_shared_args(parser)
    parser.add_argument('config_file',
                        help='Path to desired output config file.')
    parser.add_argument('-f', '--full-name', nargs='+',
                        help='Supply the config with your name')
    parser.add_argument('-e', '--email',
                        help='Supply the config with your email address')
    parser.add_argument('-l', '--list-sections', action='store_true',
                        help='List the sections in the config and exit.')
    parser.add_argument('-s', '--sections', nargs='+',
                        help='Supply list of section names to include '
                             'in output file.')
    parser.add_argument('-o', '--overwrite', action='store_true',
                        help='Overwrite existing config file at the '
                             'same location.')
    args = parser.parse_args()

    if os.path.exists(args.config_file) and not args.overwrite:
        print('Existing config file found. Run with -o option to overwrite.')
        sys.exit(1)

    data_path = pkg_resources.resource_filename('gmprocess', 'data')
    config_file = os.path.join(data_path, CONFIG_FILE_PRODUCTION)
           
    yaml = YAML()
    yaml.preserve_quotes = True

    if args.list_sections:
        with open(config_file, 'rt', encoding='utf-8') as f:
            config = yaml.load(f)
            sections = list(config.keys())
            print('Supported sections:')
            for section in sections:
                print('\t%s' % section)
        sys.exit(0)

    # what directory does the user want to write the config file to?
    install_dir, cfg_file = os.path.split(args.config_file)
    if not os.path.isdir(install_dir):
        os.makedirs(install_dir)

    with open(config_file, 'rt', encoding='utf-8') as f:
        config = yaml.load(f)
        kill_sections = []
        if args.sections is not None:
            for section in config:
                if section not in args.sections:
                    kill_sections.append(section)

        for section in kill_sections:
            del config[section]

        # if users specified user name/email at the command line, add that to
        # newly created file.
        if args.full_name or args.email:
            userinfo = {}
            if args.full_name:
                userinfo['name'] = ' '.join(args.full_name)
            if args.email:
                userinfo['email'] = args.email
            config['user'] = userinfo

        fout = open(args.config_file, 'wt', encoding='utf-8')
        yaml.dump(config, fout)
        fout.close()


if __name__ == '__main__':
    main()

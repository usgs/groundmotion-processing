#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import textwrap
import shutil


def query_yes_no(question, default="yes"):
    """
    Ask a yes/no question via raw_input() and return their answer.

    Args:
        question (str):
            A string that is presented to the user.
        default (str):
            The presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    Returns:
        bool: The "answer" return value is True for "yes" or False for "no".

    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError(f"invalid default answer: '{default}'")

    while True:
        sys.stdout.write(question + prompt)
        choice = input("> ").lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


def make_dir(pathstr, default):
    max_tries = 3
    ntries = 1
    make_ok = False
    ppath = ""
    while not make_ok:
        ppath = input(f"Please enter the {pathstr}: [{default}] ")
        if not len(ppath.strip()):
            ppath = default
        try:
            os.makedirs(ppath, exist_ok=True)
            make_ok = True
        except OSError:
            msg = "Cannot make directory: %s.  Please try again (%d " "of %d tries)."
            print("\n".join(textwrap.wrap(msg % (ppath, ntries, max_tries))))
            ntries += 1
        if ntries > max_tries:
            break
    return (ppath, make_ok)


def set_project_paths(default_conf, default_data):
    """
    Function to set project directories.
    """
    new_conf_path, conf_ok = make_dir("conf path", default_conf)
    if not conf_ok:
        print(
            "\n".join(
                textwrap.wrap(
                    "Please try to find a path that can be created on this "
                    "system and then try again. Exiting."
                )
            )
        )
        shutil.rmtree(new_conf_path)
        sys.exit(1)
    new_data_path, data_ok = make_dir("data path", default_data)
    if not data_ok:
        print(
            "\n".join(
                textwrap.wrap(
                    "Please try to find a path that can be created on this "
                    "system and then try again. Exiting."
                )
            )
        )
        shutil.rmtree(new_data_path)
        sys.exit(1)
    return (new_conf_path, new_data_path)


def get_default_project_paths(project):
    """
    Function to get default project paths.
    """
    default_project_path = os.path.join(
        os.path.expanduser("~"), "gmprocess_projects", project
    )
    default_conf = os.path.join(default_project_path, "conf")
    default_data = os.path.join(default_project_path, "data")
    print(
        "\n".join(
            textwrap.wrap(
                "You will be prompted to supply two directories for this project:"
            )
        )
    )
    print(
        "\n   ".join(
            textwrap.wrap(
                " - A *config* path, which will store the gmprocess config files."
            )
        )
    )
    print(
        "\n   ".join(
            textwrap.wrap(
                " - A *data* path, under which will be created directories for "
                "each event processed.\n"
            )
        )
    )
    return (default_conf, default_data)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
import re


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


def get_directory(label, default):
    """Prompt user to enter a directory and return the answer.

    Args:
        label (str):
            Label for the directory.
        default (str):
            Default value for the directory.
    """
    filepath = input(f"Please enter the {label}: [{default}] ")
    if not len(filepath.strip()):
        filepath = default
    return Path(filepath)


def get_user_info():
    """ """
    EMAIL_PATTERN = r"^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$"

    print("Please enter your name and email. This information will be added")
    print("to the config file and reported in the provenance of the data")
    print("processed in this project.")
    user_info = {}
    user_info["name"] = input("\tName: ")
    if not len(user_info["name"].strip()):
        print("User name is required.")
        return
    user_info["email"] = input("\tEmail address: ")
    if not re.search(EMAIL_PATTERN, user_info["email"]):
        print("Invalid Email address.")
        return
    return user_info

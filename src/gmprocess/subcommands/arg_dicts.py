#!/usr/bin/env python
# -*- coding: utf-8 -*-

ARG_DICTS = {
    "output_format": {
        "short_flag": "-f",
        "long_flag": "--output-format",
        "help": "Output file format.",
        "type": str,
        "default": "csv",
        "choices": ["excel", "csv"],
        "metavar": "FORMAT",
    },
}

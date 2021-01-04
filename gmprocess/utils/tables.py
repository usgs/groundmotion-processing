#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that provides functions for manipulating the various tables
(pandas DataFrames) produced by gmprocess.
"""

import re
from gmprocess.utils.constants import TABLE_FLOAT_STRING_FORMAT


def set_precisions(df):
    """
    Sets the string format for float point number columns in the DataFrame.

    Args:
        df (pandas.DataFrame):
            Table for setting precision.

    Returns:
        pandas.DataFrame: The modified table.
    """

    # Create a copy so we're not modifying the original DF
    df = df.copy()
    for regex, str_format in TABLE_FLOAT_STRING_FORMAT.items():
        r = re.compile(regex, re.IGNORECASE)
        columns = list(filter(r.match, df.columns))
        for col in columns:
            df[col] = df[col].map(lambda x: str_format % x)
    return df

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# stdlib imports
import os
import json


from gmprocess.utils.config import merge_dicts


def test_merge_dicts():
    test_subject = [
        {
            "a": "yes",
            "b": [0, 1, 2],
            "c": 1.0,
            "d": 2.0,
            "e": {
                "e.1": 2,
                "e.2": [1, 2],
                "e.3": {
                    "e.3.1": "a",
                    "e.3.2": 12.0,
                },
            },
            "h": {
                "h.1": 10.0,
                "h.2": 11.0,
            },
        },
        {
            "c": 1.1,  # change value
            "e": {
                "e.2": [1, 2, 3],  # change array
            },
        },
        {
            "d": {  # change value to dict
                "d.1": 2.2,
                "d.2": 3.3,
            },
            "e": {  # change value in nested dict
                "e.3": {
                    "e.3.1": "ccc",
                },
            },
        },
        {
            "f": 4.4,  # add value
        },
        {
            "g": {  # add nested dict
                "g.1": 2,
                "g.2": 3,
            },
            "h": 0.1,  # change dict to value
        },
    ]

    result_expected = {
        "a": "yes",
        "b": [0, 1, 2],
        "c": 1.1,
        "d": {
            "d.1": 2.2,
            "d.2": 3.3,
        },
        "e": {
            "e.1": 2,
            "e.2": [1, 2, 3],
            "e.3": {
                "e.3.1": "ccc",
                "e.3.2": 12.0,
            },
        },
        "f": 4.4,
        "g": {
            "g.1": 2,
            "g.2": 3,
        },
        "h": 0.1,
    }

    test_result = merge_dicts(test_subject)

    dump_expected = json.dumps(result_expected, sort_keys=True)
    dump_result = json.dumps(test_result, sort_keys=True)
    assert(dump_expected == dump_result)


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_merge_dicts()

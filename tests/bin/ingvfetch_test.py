#!/usr/bin/env python

# stdlib imports
import os
import tempfile

# third party imports
from lxml import etree

from impactutils.io.cmd import get_command_output


def test_ingvfetch():
    homedir = os.path.dirname(os.path.abspath(__file__))
    ingvfetch = os.path.join(homedir, '..', '..', 'bin', 'ingvfetch')
    usgs_eventid = 'us10006g7d'
    ingv_eventid = '7073641'
    usgs_tmp = tempfile.mkstemp()[1]
    ingv_tmp = tempfile.mkstemp()[1]

    cmd = '%s %s %s %s' % (ingvfetch, usgs_eventid, 'USGS', usgs_tmp)
    res, stdout, stderr = get_command_output(cmd)

    cmd = '%s %s %s %s' % (ingvfetch, ingv_eventid, 'INGV', ingv_tmp)
    res, stdout, stderr = get_command_output(cmd)
    usgs_tree = etree.tostring(etree.parse(usgs_tmp)).decode()
    ingv_tree = etree.tostring(etree.parse(ingv_tmp)).decode()
    idx = usgs_tree.find("created=")
    usgs_tree = usgs_tree[idx + 21:]
    ingv_tree = ingv_tree[idx + 21:]

    assert usgs_tree == ingv_tree
    os.remove(usgs_tmp)
    os.remove(ingv_tmp)


if __name__ == '__main__':
    test_ingvfetch()

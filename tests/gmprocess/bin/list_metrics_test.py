#!/usr/bin/env python


def test_list_metrics(script_runner):
    ret = script_runner.run('list_metrics')
    assert ret.success


if __name__ == '__main__':
    test_list_metrics()

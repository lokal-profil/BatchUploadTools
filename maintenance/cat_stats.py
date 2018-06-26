#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Produce basic category statistics from make_info output file."""
import sys
from collections import Counter

import batchupload.helpers as helpers
import batchupload.common as common


def run(filename):
    data = common.open_and_read_file(filename, as_json=True)

    num_cats = Counter()
    num_meta_cats = Counter()
    meta_cats = Counter()
    cats = Counter()
    for k, v in data.items():
        c = v.get('cats') or []
        mc = v.get('meta_cats') or []
        num_cats.update([len(c)])
        num_meta_cats.update([len(mc)])
        cats.update(c)
        meta_cats.update(mc)

    print('Number of cats per file: {}'.format(
        num_cats.most_common()))
    print('Number of metacats per file: {}'.format(
        num_meta_cats.most_common()))
    for cat, num in meta_cats.most_common():
        print('* [[Category:{}]] - {}'.format(cat, num))


if __name__ == '__main__':
    usage = 'Usage:\tpython maintanance/cat_stats.py <data_file path>'
    argv = sys.argv[1:]
    if len(argv) == 1:
        run(helpers.convertFromCommandline(argv[0]))
    else:
        print(usage)

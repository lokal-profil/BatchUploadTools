#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Create a wikitext preview for a selection of images.

Also supports skipped files if a log of the format
"key -- reason" was outputted.
"""
import os
import sys

import batchupload.make_info as mi
import batchupload.common as common


DEFAULTS = {
    'selection': '¤generator.log',
    'output': 'preview.wikitext',
    'media_ext': '<ext>'
}


def run(data, selection, log_file, output, media_ext):
    # fall back on defaults
    data_dir = os.path.split(data)[0]
    if not selection:
        selection = os.path.join(data_dir, DEFAULTS.get('selection'))
    selection_dir = os.path.split(selection)[0]
    if not output:
        output = os.path.join(selection_dir, DEFAULTS.get('output'))

    data = common.open_and_read_file(data, as_json=True)
    demo = common.open_and_read_file(selection, as_json=True)

    # load log
    log = {}
    if log_file:
        log_text = common.open_and_read_file(log_file)
        for l in log_text.split('\n'):
            if ' -- ' in l:
                idno, reason = l.split(' -- ')
                log[idno] = reason

    out = []
    for idno in sorted(demo.keys()):
        info = ''
        if idno in data:
            info = mi.make_info_page(data[idno], preview=True)
            if media_ext:
                info = info.replace('<ext>', media_ext)
        elif log:
            info = log[idno]
        else:
            info = 'no make_info data found'
        out.append('== {idno} -- {reason} ==\n{info}'.format(
            reason=demo.get(idno), idno=idno, info=info))

    common.open_and_write_file(output, '\n\n'.join(out))


def handle_args(args):
    """
    Parse and load all of the basic arguments.

    :param args: arguments to be handled
    :return: list of options
    """
    usage = ('Usage:\tpython maintanance/make_preview.py -data:PATH\n'
             '\tdata: path to the make_info output file\n'
             '\tselection: [optional] file specifying selection for preview '
             'defaults to <data dir>/{selection}\n'
             '\tlog_file: [optional] path to the skipped images log file if '
             'any exists\n'
             '\toutput: [optional] path to the desired output file '
             'defaults to <selection dir>{output}\n'
             '\tmedia_ext: [optional] file extension to use for media files '
             'e.g. "tif", defaults to {media_ext}').format(**DEFAULTS)
    options = {
        'data': None,
        'selection': None,
        'log_file': None,
        'output': None,
        'media_ext': None
    }

    for arg in args:
        option, sep, value = arg.partition(':')
        if option.startswith('-') and option[1:] in options:
            options[option[1:]] = value
        else:
            print('Invalid option: "{}"\n{}'.format(arg, usage))
            exit()

    # without defaults
    if not options.get('data'):
        print('data must be given\n{}'.format(usage))
        exit()

    return options


if __name__ == '__main__':
    options = handle_args(sys.argv[1:])
    run(**options)

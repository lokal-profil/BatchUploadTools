#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Did you accidentally run prepUpload only to discover something was missing?

This allows you to rename the media files back to their original filenames
assuming you kept the ¤generator.log file.
"""
import os
import sys

DEFAULTS = {
    'filename': '¤generator.log',
    'target_dir': 're_rename'
}


def run(base_dir, filename, target_dir):
    # fall back on defaults
    if not filename:
        filename = os.path.join(base_dir, DEFAULTS.get('filename'))
    if not target_dir:
        target_dir = os.path.join(base_dir, DEFAULTS.get('target_dir'))

    f = open(filename)
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)

    for line in f:
        if not line:
            continue
        old, _, current = line.strip().partition('|')
        current_path = os.path.join(base_dir, current)
        new_path = os.path.join(target_dir, old)
        if os.path.isfile(current_path):
            os.rename(current_path, new_path)


def handle_args(args):
    """
    Parse and load all of the basic arguments.

    :param args: arguments to be handled
    :return: list of options
    """
    usage = ('Usage:\tpython maintanance/restore_filenames.py -base_dir:PATH\n'
             '\tbase_dir: the directory in which the files are found\n'
             '\ttarget_dir: [optional] directory to which the renamed files '
             'should be moved defaults to <base_dir>/{target_dir}/\n'
             '\tfilename: [optional] path to the generator log_file to use, '
             'defaults to <base_dir>{filename}').format(**DEFAULTS)
    options = {
        'base_dir': None,
        'filename': None,
        'target_dir': None
    }

    for arg in args:
        option, sep, value = arg.partition(':')
        if option.startswith('-') and option[1:] in options:
            options[option[1:]] = value
        else:
            print('Invalid option: "{}"\n{}'.format(arg, usage))
            exit()

    # without defaults
    if not options.get('base_dir'):
        print('base_dir must be given\n{}'.format(usage))
        exit()

    return options


if __name__ == '__main__':
    options = handle_args(sys.argv[1:])
    run(**options)

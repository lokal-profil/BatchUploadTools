#!/usr/bin/python
# -*- coding: UTF-8  -*-
"""Prepare files for upload by creating Information pages and renaming them."""
from __future__ import unicode_literals
from builtins import open
import os
from batchupload.make_info import make_info_page
import batchupload.common as common
import pywikibot

FILE_EXTS = ('.tif', '.jpg', '.tiff', '.jpeg', '.wav')


def run(in_path, out_path, data_path, file_exts=None):
    """
    Prepare an upload.

    Prepare an upload by:
        1. Find files in in_path (with subdirs) with file_exts file extension,
        2. Match these against the keys in the makeInfo output data
        3. Make info files and rename found file (in new target folder)

    @todo: throw errors on failed file read/write

    @param in_path: path to directory where unprocessed files live
    @param out_path: path to directory where renamed files and info should live
    @param data_path: path to .json containing makeInfo output data
    @param file_exts: tupple of allowed file extensions (case insensitive)
    """
    # Load data
    data = common.open_and_read_file(data_path, codec='utf-8', as_json=True)

    # set filExts
    file_exts = file_exts or FILE_EXTS

    # Find candidate files
    if not os.path.isdir(in_path):
        raise common.MyError(
            'The provided inPath was not a valid directory: %s' % in_path)
    found_files = find_files(path=in_path, file_exts=file_exts)

    # Find matches
    hitlist = makeHitlist(found_files, data)

    # make info and rename
    makeAndRename(hitlist, out_path)

    # clean up any empty subdirectories
    removeEmptyDirectories(in_path)


def find_files(path, file_exts, subdir=True):
    """
    Identify all files with a given extension in a given directory.

    @param path: path to directory to look in
    @param file_exts: tuple of allowed file extensions (case insensitive)
    @param subdir: whether subdirs should also be searched
    @return: list of paths to found files
    """
    # os.listdir cannot handle unicode filenames unless the path is unicode
    path = common.to_unicode(path)

    files = []
    subdirs = []
    for filename in os.listdir(path):
        if os.path.splitext(filename)[1].lower() in file_exts:
            files.append(os.path.join(path, filename))
        elif os.path.isdir(os.path.join(path, filename)):
            subdirs.append(os.path.join(path, filename))
    if subdir:
        for subdir in subdirs:
            files += find_files(path=subdir, file_exts=file_exts)
    return files


def makeHitlist(files, data):
    """
    Given a list of paths to file and target filenames construct a hitlist.

    The hitlist is made up by the (lower case) extension and the
    extensionless basename of the file.

    The data file should be a dict where the keys are the (extensionless)
    target filenames.

    @param files: list of file paths
    @param data: dict containing target filenames as keys
    @return: list of hitList[key] = {ext, path, data}
    """
    hitlist = []
    processed_keys = []  # stay paranoid
    for f in files:
        key, ext = os.path.splitext(os.path.basename(f))
        if key not in data:
            continue
        elif key in processed_keys:
            raise common.MyError('non-unique file key: %s' % key)
        processed_keys.append(key)
        hitlist.append({'path': f, 'ext': ext.lower(),
                        'data': data[key], 'key': key})
    return hitlist


def makeAndRename(hitlist, outPath):
    """
    Given a hitlist create the info files and rename the matched file.

    @param hitlist: the output of makeHitlist
    @param outPath: the directory in which to store info + renamed files
    """
    # create outPath if it doesn't exist
    common.create_dir(outPath)

    # logfile
    logfile = os.path.join(outPath, '¤generator.log')
    flog = open(logfile, 'a', encoding='utf-8')

    for hit in hitlist:
        base_name = os.path.join(outPath, hit['data']['filename'])

        # output info file
        common.open_and_write_file('%s.info' % base_name,
                                   make_info_page(hit['data']))

        # rename/move matched file
        outfile = '%s%s' % (base_name, hit['ext'])
        os.rename(hit['path'], outfile)
        flog.write('%s|%s\n' % (os.path.basename(hit['path']),
                                os.path.basename(outfile)))
    flog.close()
    pywikibot.output('Created %s' % logfile)


def removeEmptyDirectories(path, top=True):
    """
    Remove any empty directories and subdirectories.

    @param path: path to directory to start deleting from
    @param top: set to True to not delete the starting directory
    """
    if not os.path.isdir(path):
        return

    # remove empty sub-directory
    files = os.listdir(path)
    for f in files:
        fullpath = os.path.join(path, f)
        if os.path.isdir(fullpath):
            removeEmptyDirectories(fullpath, top=False)

    # re-read and delete directory if empty,
    files = os.listdir(path)
    if not top:
        if len(files) == 0:
            os.rmdir(path)
        else:
            pywikibot.output('Not removing non-empty directory: %s' % path)


def main(*args):
    """Command line entry-point."""
    usage = \
        'Usage:\tpython prepUpload.py '\
        '-in_path:PATH -out_path:PATH -data_path:PATH\n' \
        '\tExamples:\n' \
        '\tpython prepUpload.py -in_path:../diskkopia -out_path:./toUpload ' \
        '-data_path:./datafile.json \n'
    in_path = None
    out_path = None
    data_path = None

    # Load pywikibot args and handle local args
    for arg in pywikibot.handle_args(args):
        option, sep, value = arg.partition(':')
        if option == '-in_path':
            in_path = common.convert_from_commandline(value)
        elif option == '-out_path':
            out_path = common.convert_from_commandline(value)
        elif option == '-data_path':
            data_path = common.convert_from_commandline(value)
        elif option == '-usage':
            pywikibot.output(usage)
            return

    if in_path and out_path and data_path:
        run(in_path, out_path, data_path)
    else:
        pywikibot.output(usage)


if __name__ == "__main__":
    main()

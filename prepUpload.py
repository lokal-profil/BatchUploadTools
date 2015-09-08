#!/usr/bin/python
# -*- coding: UTF-8  -*-
"""
Prepares files for upload by creating Information pages and renaming them
"""
import os
import codecs
import json

FILEEXTS = (u'.tif', u'.jpg', u'.tiff', u'.jpeg')


def run(inPath, outPath, dataPath, fileExts=None):
    """
    Prepares an upload by:
        1. Finds files in inpath (with subdirs) with the right file extension,
        2. Matching these against the keys in the makeInfo output data
        3. Making info files and renaming found file (in new target folder)
    param inPath: path to directory where unprocessed files live
    param outPath: path to directory where renamed files and info should live
    param dataPath: path to .json containing makeInfo output data
    param fileExts: tupple of allowed file extensions (case insensitive)

    @todo: throw errors on failed file read/write
    """
    # Load data
    data = json.load(codecs.open(dataPath, 'r', 'utf-8'))

    # set filExts
    if fileExts is None:
        fileExts = FILEEXTS

    # Find candidate files
    if not os.path.isdir(inPath):
        print u'The provided inPath was not a valid directory: %s' % inPath
        exit()
    foundFiles = findFiles(path=inPath, fileExts=fileExts)

    # Find matches
    hitlist = makeHitlist(foundFiles, data)

    # make info and rename
    makeAndRename(hitlist, outPath)

    # clean up any empty subdirectories
    removeEmptyDirectories(inPath)


def findFiles(path, fileExts, subdir=True):
    """
    Identify all files with a given extension in a given directory
    param path: path to look in
    param fileExts: tupple of allowed file extensions (case insensitive)
    param subdir: Whether subdirs should also be searched
    return list of paths to found files
    """
    files = []
    subdirs = []
    for filename in os.listdir(path):
        if os.path.splitext(filename)[1].lower() in fileExts:
            files.append(os.path.join(path, filename))
        elif os.path.isdir(os.path.join(path, filename)):
            subdirs.append(os.path.join(path, filename))
    if subdir:
        for subdir in subdirs:
            files += findFiles(path=subdir, fileExts=fileExts)
    return files


def makeHitlist(files, data):
    """
    Given a list of paths to files extract the extension (lower case) and the
    extensionless basename.
    param files: list of file paths
    return list of hitList[key] = {ext, path, data}
    """
    hitlist = []
    processedKeys = []  # stay paranoid
    for f in files:
        key, ext = os.path.splitext(os.path.basename(f))
        if key not in data.keys():
            continue
        elif key in processedKeys:
            # @todo: throw error
            print 'non-unique file key: %s' % key
            exit(1)
        processedKeys.append(key)
        hitlist.append({'path': f, 'ext': ext.lower(),
                        'data': data[key], 'key': key})
    return hitlist


def makeAndRename(hitlist, outPath):
    """
    Given a hitlist create the info files and and rename the matched file
    param hitlist: the output of makeHitlist
    param outPath: the directory in which to store info + renamed files
    """
    # create outPath if it doesn't exist
    if not os.path.isdir(outPath):
        os.mkdir(outPath)

    # logfile
    logfile = os.path.join(outPath, u'¤generator.log')
    flog = codecs.open(logfile, 'a', 'utf-8')

    for hit in hitlist:
        baseName = os.path.join(outPath, hit['data']['filename'])

        # output info file
        f = codecs.open(u'%s.info' % baseName, 'w', 'utf-8')
        f.write(makeInfoPage(hit['data']))
        f.close()

        # rename/move matched file
        outfile = u'%s%s' % (baseName, hit['ext'])
        os.rename(hit['path'], outfile)
        flog.write(u'%s|%s\n' % (hit['key'], os.path.basename(outfile)))
    flog.close()
    print u'Created %s' % logfile


def removeEmptyDirectories(path, top=True):
    """
    Remove any empty directories under a given directory
    param top: set to True to not delete the current directory
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
            print 'Not removing non-empty directory: %s' % path


def makeInfoPage(data):
    """
    Given the data from a makeInfo output item create a complete Info page
    param data: dict with {cats, metaCats, info, filename}
    @todo: make this a function in generic makeInfo

    return str the Info page
    """
    catSeparator = u'\n\n'  # standard separation before categories
    txt = data['info']

    if len(data['metaCats']) > 0:
        txt += catSeparator
        txt += u'<!-- Metadata categories -->\n'
        for cat in data['metaCats']:
            txt += u'[[Category:%s]]\n' % cat

    if len(data['cats']) > 0:
        txt += catSeparator
        txt += u'<!-- Content categories -->\n'
        for cat in data['cats']:
            txt += u'[[Category:%s]]\n' % cat

    return txt


if __name__ == '__main__':
    import sys
    usage = u'Usage:\tpython prepUpload.py inPath, outPath, dataPath\n' \
        u'\tExamples:\n' \
        u'\tpython prepUpload.py ../diskkopia ./toUpload ./datafil.json \n'
    argv = sys.argv[1:]
    if len(argv) == 3:
        # str to unicode
        inPath = argv[0].decode(sys.getfilesystemencoding())
        outPath = argv[1].decode(sys.getfilesystemencoding())
        dataPath = argv[2].decode(sys.getfilesystemencoding())
        run(inPath, outPath, dataPath)
    else:
        print usage
# EoF

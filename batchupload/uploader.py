#!/usr/bin/python
# -*- coding: utf-8  -*-
import codecs
import os
import common  # used for loadJsonConfig
import WikiApi as wikiApi
import prepUpload
import json

FILEEXTS = (u'.tif', u'.jpg', u'.tiff', u'.jpeg')


def openConnection(configPath=None, verbose=True):
    """
    Open a connection to Commons using the specified config file
    param configPath: path to config.json file
    return wikiApi
    """
    # load config
    config = common.loadJsonConfig(filename=configPath)

    # open connections
    comApi = wikiApi.CommonsApi.setUpApi(user=config['w_username'],
                                         password=config['w_password'],
                                         site=config['com_site'],
                                         scriptidentify=u'batchUploader/0.1',
                                         verbose=verbose)
    return comApi


def upAll(in_path, config_path, cutoff=None, target=u'Uploaded', file_exts=None,
          test=False, verbose=True):
    """
    Upload all matched files in the supplied directory to Commons and
    moves any processed files to the target folder.
    :param in_path: path to directory with files to upload
    :param config_path: path to JSON config file (defaults to config.json)
    :param cutoff: number of files to upload (defaults to all)
    :param target: sub-directory for uploaded files (defaults to Uploaded)
    :param file_exts: tuple of allowed file extensions (defaults to FILEEXTS)
    :param test: set to True to test but not upload
    :param verbose: print out confirmations
    :return: None
    """
    # set defaults unless overridden
    file_exts = file_exts or FILEEXTS

    comApi = openConnection(config_path, verbose=verbose)

    # Verify inPath
    if not os.path.isdir(in_path):
        print u'The provided inPath was not a valid directory: %s' % in_path
        exit()

    # create target directories if they don't exist
    done_dir = os.path.join(in_path, target)
    error_dir = u'%s_errors' % done_dir
    warnings_dir = u'%s_warnings' % done_dir
    if not os.path.isdir(done_dir):
        os.mkdir(done_dir)
    if not os.path.isdir(error_dir):
        os.mkdir(error_dir)
    if not os.path.isdir(warnings_dir):
        os.mkdir(warnings_dir)

    # logfile
    logfile = os.path.join(in_path, u'¤uploader.log')
    flog = codecs.open(logfile, 'a', 'utf-8')

    # find all content files
    found_files = prepUpload.findFiles(path=in_path, fileExts=file_exts,
                                       subdir=False)
    counter = 1
    for f in found_files:
        if cutoff and counter > cutoff:
            break
        # verify that there is a matching info file
        info_file = u'%s.info' % os.path.splitext(f)[0]
        base_name = os.path.basename(f)
        if not os.path.exists(info_file):
            flog.write(u'%s: Found tif/jpg without info' % base_name)
            continue

        # prepare upload
        fin = codecs.open(info_file, 'r', 'utf-8')
        txt = fin.read()
        fin.close()

        if test:
            print base_name
            print txt
            continue

        # stop here if testing
        result = comApi.chunkupload(base_name, f, txt, txt,
                                    uploadifbadprefix=True)

        # parse results and move files
        base_info_name = os.path.basename(info_file)
        details = ''
        jresult = json.loads(result[result.find('{'):])
        target_dir = None
        if 'error' in jresult.keys():
            details = json.dumps(jresult['error'], ensure_ascii=False)
            target_dir = error_dir
        elif 'upload' in jresult.keys() and \
                'warnings' in jresult['upload'].keys():
            details = json.dumps(jresult['upload'], ensure_ascii=False)
            target_dir = warnings_dir
        else:
            details = json.dumps(jresult['upload']['filename'],
                                 ensure_ascii=False)
            target_dir = done_dir
        os.rename(f, os.path.join(target_dir, base_name))
        os.rename(info_file, os.path.join(target_dir, base_info_name))

        # logging
        counter += 1
        result_text = result[:result.find('{')].strip().decode('utf8')
        flog.write(u'%s %s\n' % (result_text, details))
        flog.flush()

    flog.close()
    print u'Created %s' % logfile


if __name__ == '__main__':
    import sys
    usage = u'Usage:\tpython uploader.py in_path, config_path cutoff\n' \
            u'\tcutoff is optional and allows the upload to stop after ' \
            u'the specified number of files\n' \
            u'\tExamples:\n' \
            u'\tpython uploader.py ../diskkopia ./SMM/config.json 100\n'
    argv = sys.argv[1:]
    if len(argv) in (2, 3):
        # str to unicode
        in_path = argv[0].decode(sys.getfilesystemencoding())
        config_path = argv[1].decode(sys.getfilesystemencoding())
        cutoff = None
        if len(argv) == 3:
            cutoff = int(argv[2])
        upAll(in_path, config_path, cutoff=cutoff)
    else:
        print usage
# EoF

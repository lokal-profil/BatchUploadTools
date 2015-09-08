#!/usr/bin/python
# -*- coding: utf-8  -*-
import codecs
import os
import common  # used for loadJsonConfig
import WikiApi as wikiApi
import prepUpload
import json


def openConnection(configPath=None):
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
                                         verbose=True)
    return comApi


def upAll(inPath, configPath, cutoff=None, fileExts=(u'.tif', u'.jpg'),
          test=False, verbose=False):
    """
    Upload all matched files in the supplied directory
    """
    comApi = openConnection(configPath)

    # Verify inPath
    if not os.path.isdir(inPath):
        print u'The provided inPath was not a valid directory: %s' % inPath
        exit()

    # create target directories if they don't exist
    doneDir = os.path.join(inPath, u'Uploaded')
    errorDir = u'%s_errors' % doneDir
    warningsDir = u'%s_warnings' % doneDir
    if not os.path.isdir(doneDir):
        os.mkdir(doneDir)
    if not os.path.isdir(errorDir):
        os.mkdir(errorDir)
    if not os.path.isdir(warningsDir):
        os.mkdir(warningsDir)

    # logfile
    logfile = os.path.join(inPath, u'¤uploader.log')
    flog = codecs.open(logfile, 'a', 'utf-8')

    # find all content files
    foundFiles = prepUpload.findFiles(path=inPath, fileExts=fileExts,
                                      subdir=False)
    counter = 1
    for f in foundFiles:
        if cutoff and counter > cutoff:
            break
        # verify that there is a matching info file
        infoFile = u'%s.info' % os.path.splitext(f)[0]
        baseName = os.path.basename(f)
        if not os.path.exists(infoFile):
            flog.write(u'%s: Found tif/jpg without info' %
                       baseName)
            continue

        # prepare upload
        fin = codecs.open(infoFile, 'r', 'utf-8')
        txt = fin.read()
        fin.close()

        if test:
            print baseName
            print txt
            continue

        # stop here if testing
        result = comApi.chunkupload(baseName, f, txt, txt)

        # parse results and move files
        baseInfoName = os.path.basename(infoFile)
        details = ''
        jresult = json.loads(result[result.find('{'):])
        if 'error' in jresult.keys():
            details = json.dumps(jresult['error'], ensure_ascii=False)
            os.rename(f, os.path.join(errorDir, baseName))
            os.rename(infoFile, os.path.join(errorDir, baseInfoName))
        elif 'upload' in jresult.keys() and \
                'warnings' in jresult['upload'].keys():
            details = json.dumps(jresult['upload'], ensure_ascii=False)
            os.rename(f, os.path.join(warningsDir, baseName))
            os.rename(infoFile, os.path.join(warningsDir, baseInfoName))
        else:
            details = json.dumps(jresult['upload']['filename'],
                                 ensure_ascii=False)
            os.rename(f, os.path.join(doneDir, baseName))
            os.rename(infoFile, os.path.join(doneDir, baseInfoName))

        # logging
        counter += 1
        resultText = result[:result.find('{')].strip().decode('utf8')
        flog.write(u'%s %s\n' % (resultText, details))
        flog.flush()

    flog.close()
    print u'Created %s' % logfile


if __name__ == '__main__':
    import sys
    usage = u'Usage:\tpython uploader.py inPath, configPath cutoff\n' \
            u'\tcutoff is optional and allows the upload to stop after ' \
            u'the specified number of files\n' \
            u'\tExamples:\n' \
            u'\tpython prepUpload.py ../diskkopia ./SMM/config.json 100\n'
    argv = sys.argv[1:]
    if len(argv) in (2, 3):
        # str to unicode
        inPath = argv[0].decode(sys.getfilesystemencoding())
        configPath = argv[1].decode(sys.getfilesystemencoding())
        cutoff = None
        if len(argv) == 3:
            cutoff = int(argv[2])
        upAll(inPath, configPath, cutoff=cutoff)
    else:
        print usage
# EoF

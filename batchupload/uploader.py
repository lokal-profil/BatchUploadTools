#!/usr/bin/python
# -*- coding: utf-8  -*-
#
import codecs
import os
import prepUpload
import common
import pywikibot

FILEEXTS = (u'.tif', u'.jpg', u'.tiff', u'.jpeg')


def upload_single_file(file_name, media_file, text, target_site,
                       chunk_size=5, overwrite_page_exists=False,
                       upload_if_duplicate=False, upload_if_badprefix=False,
                       ignore_all_warnings=False):
    """
    Upload a single file in chunks.

    @param file_name: sanitized filename to use for upload
    @param media_file: path to media file to upload
    @param text: file description page
    @param target_site: pywikibot.Site object wo whih file should be uploaded
    @param chunk_size: Size of chunks (in MB) in which to upload file
    @param overwrite_page_exists: Ignore filepage already exists warning
    @param upload_if_duplicate: Ignore duplicate file warning
    @param upload_if_badprefix: Ignore bad-prefix warning
    @param ignore_all_warnings: Ignore all warnings
    """
    def allow_warnings(warning_list):
        """Given a list of warnings determine if all oare acceptable or not."""
        for w in warning_list:
            if w.code not in ignored_warnings:
                result['warning'] = w
                return False
        return True

    result = {'warning': None, 'error': None, 'log': ''}

    # handle warnings to ignore
    ignore_warnings = False
    ignored_warnings = []
    if overwrite_page_exists:
        ignored_warnings.append('page-exists')
    if upload_if_duplicate:
        ignored_warnings.append('duplicate')
    if upload_if_badprefix:
        ignored_warnings.append('bad-prefix')
    if ignore_all_warnings:
        ignore_warnings = True
    elif ignored_warnings:
        ignore_warnings = allow_warnings

    # convert chunksize to Mb
    chunk_size *= 1048576

    # store description in filepage (used for comment and description)
    file_page = pywikibot.FilePage(target_site, file_name)
    file_page.text = text

    try:
        success = target_site.upload(
            file_page, source_filename=media_file,
            ignore_warnings=ignore_warnings,
            report_success=False, chunk_size=chunk_size)
    except pywikibot.data.api.APIError as error:
        result['error'] = error
        result['log'] = u'Error: %s: %s' % (file_page.title(), error)
    except Exception as e:
        result['error'] = e
        result['log'] = u'Error: %s: Unhandled error: %s' % (
                        file_page.title(), e)
    else:
        if result.get('warning'):
            result['log'] = u'Warning: %s: %s' % (file_page.title(),
                                                  result['warning'])
        elif success:
            result['log'] = u'%s: success' % file_page.title()
        else:
            result['error'] = u"No warning/error but '%s' didn't upload?" % \
                              file_page.title()
            result['log'] = u'Error: %s: %s' % (file_page.title(),
                                                result['error'])
    finally:
        return result


def up_all(in_path, cutoff=None, target=u'Uploaded', file_exts=None,
           verbose=False, test=False, target_site=None):
    """
    Upload all matched files in the supplied directory.

    Moves any processed files to the target folders.

    @param in_path: path to directory with files to upload
    @param cutoff: number of files to upload (defaults to all)
    @param target: sub-directory for uploaded files (defaults to "Uploaded")
    @param file_exts: tuple of allowed file extensions (defaults to FILEEXTS)
    @param verbose: whether to output confirmation after each upload
    @param test: set to True to test but not upload (deprecated?)
    @param target_site: pywikibot.Site to which file should be uploaded,
        defaults to Commons.
    """
    # set defaults unless overridden
    file_exts = file_exts or FILEEXTS
    target_site = target_site or pywikibot.Site('commons', 'commons')
    target_site.login()

    # Verify in_path
    if not os.path.isdir(in_path):
        pywikibot.output(u'The provided in_path was not a valid '
                         u'directory: %s' % in_path)
        exit()

    # create target directories if they don't exist
    done_dir = os.path.join(in_path, target)
    error_dir = u'%s_errors' % done_dir
    warnings_dir = u'%s_warnings' % done_dir
    common.create_dir(done_dir)
    common.create_dir(error_dir)
    common.create_dir(warnings_dir)

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
        base_info_name = os.path.basename(info_file)
        if not os.path.exists(info_file):
            flog.write(u'%s: Found multimedia file without info\n' % base_name)
            continue

        # prepare upload
        txt = common.open_and_read_file(info_file)

        if test:
            pywikibot.output(u'Test upload "%s" with the following '
                             u'description: %s\n' % (base_name, txt))
            continue
        # stop here if testing

        target_dir = None
        result = upload_single_file(base_name, f, txt, target_site,
                                    upload_if_badprefix=True)
        if result.get('error'):
            target_dir = error_dir
        elif result.get('warning'):
            target_dir = warnings_dir
        else:
            target_dir = done_dir
        if verbose:
            pywikibot.output(result.get('log'))

        flog.write(u'%s\n' % result.get('log'))
        os.rename(f, os.path.join(target_dir, base_name))
        os.rename(info_file, os.path.join(target_dir, base_info_name))
        counter += 1
        flog.flush()

    flog.close()
    pywikibot.output(u'Created %s' % logfile)


def main(*args):
    """Command line entry-point."""
    usage = u'Usage:' \
            u'\tpython uploader.py -in_path:PATH -dir:PATH -cutoff:NUM\n' \
            u'\t-in_path:PATH path to the directory containing the media files\n' \
            u'\t-dir:PATH specifies the path to the directory containing a ' \
            u'user_config.py file (optional)\n' \
            u'\t-cutoff:NUM stop the upload after the specified number of files ' \
            u'(optional)\n' \
            u'\t-confirm Whether to output a confirmation after each upload ' \
            u'attempt (optional)\n' \
            u'\tExample:\n' \
            u'\tpython uploader.py -in_path:../diskkopia -cutoff:100\n'
    cutoff = None
    in_path = None
    test = False
    confirm = False

    # Load pywikibot args and handle local args
    for arg in pywikibot.handle_args(args):
        option, sep, value = arg.partition(':')
        if option == '-cutoff':
            if common.is_pos_int(value):
                cutoff = int(value)
        if option == '-in_path':
            in_path = value
        if option == '-test':
            test = True
        if option == '-confirm':
            confirm = True

    if in_path:
        up_all(in_path, cutoff=cutoff, test=test, verbose=confirm)
    else:
        pywikibot.output(usage)

if __name__ == "__main__":
    main()

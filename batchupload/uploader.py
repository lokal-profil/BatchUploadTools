#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Tool for uploading a single or multiple files from disc or url."""
from __future__ import unicode_literals
import batchupload.common as common
import batchupload.prepUpload as prepUpload
from batchupload.make_info import make_info_page
import os
import pywikibot

FILE_EXTS = ('.tif', '.jpg', '.tiff', '.jpeg', '.wav')
URL_PROTOCOLS = ('http', 'https')  # @todo: extend with supported protocols


def upload_single_file(file_name, media_file, text, target_site,
                       chunk_size=5, chunked=True, overwrite_page_exists=False,
                       upload_if_duplicate=False, upload_if_badprefix=False,
                       ignore_all_warnings=False):
    """
    Upload a single file in chunks.

    @param file_name: sanitized filename to use for upload
    @param media_file: path or URL to media file to upload
    @param text: file description page
    @param target_site: pywikibot.Site object to which file should be uploaded
    @param chunk_size: Size of chunks (in MB) in which to upload file
    @param chunked: Whether to do chunked uploading or not.
    @param overwrite_page_exists: Ignore filepage already exists warning
    @param upload_if_duplicate: Ignore duplicate file warning
    @param upload_if_badprefix: Ignore bad-prefix warning
    @param ignore_all_warnings: Ignore all warnings
    """
    def allow_warnings(warning_list):
        """Given a list of warnings determine if all are acceptable or not."""
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
        ignored_warnings.append('exists')
    if upload_if_duplicate:
        ignored_warnings.append('duplicate')
    if upload_if_badprefix:
        ignored_warnings.append('bad-prefix')
    if ignore_all_warnings:
        ignore_warnings = True
    else:
        ignore_warnings = allow_warnings

    # convert chunksize to Mb
    if chunked:
        chunk_size *= 1048576
    else:
        chunk_size = 0

    # store description in filepage (used for comment and description)
    file_page = pywikibot.FilePage(target_site, file_name)
    file_page.text = text

    # support upload_by_url: cannot just look for :// due to file://
    source_filename = source_url = None
    protocol, _, rest = media_file.partition('://')
    if protocol in URL_PROTOCOLS:
        source_url = media_file
    else:
        source_filename = media_file

    try:
        success = target_site.upload(
            file_page,
            source_filename=source_filename,
            source_url=source_url,
            ignore_warnings=ignore_warnings,
            report_success=False,
            chunk_size=chunk_size)
    except pywikibot.data.api.APIError as error:
        result['error'] = error
        result['log'] = 'Error: %s: %s' % (file_page.title(), error)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        result['error'] = '%r' % e
        result['log'] = 'Error: %s: Unhandled error: %s' % (
                        file_page.title(), e)
    else:
        if result.get('warning'):
            result['log'] = 'Warning: %s: %s' % (file_page.title(),
                                                 result['warning'])
        elif success:
            result['log'] = '%s: success' % file_page.title()
        else:
            result['error'] = "No warning/error but '%s' didn't upload?" % \
                              file_page.title()
            result['log'] = 'Error: %s: %s' % (file_page.title(),
                                               result['error'])
    finally:
        return result


def up_all(in_path, cutoff=None, target='Uploaded', file_exts=None,
           verbose=False, test=False, target_site=None, chunked=True):
    """
    Upload all matched media files in the supplied directory.

    Media files and metadata files with the expected extension .info
    should be in the same directory. Metadata files should contain the entirety
    of the desired description page (in wikitext).

    Moves each file to one the target folders after processing.

    @param in_path: path to directory with files to upload
    @param cutoff: number of files to upload (defaults to all)
    @param target: sub-directory for uploaded files (defaults to "Uploaded")
    @param file_exts: tuple of allowed file extensions (defaults to FILE_EXTS)
    @param verbose: whether to output confirmation after each upload
    @param test: set to True to test but not upload
    @param target_site: pywikibot.Site to which file should be uploaded,
        defaults to Commons.
    @param chunked: Whether to do chunked uploading or not.
    """
    # set defaults unless overridden
    file_exts = file_exts or FILE_EXTS
    target_site = target_site or pywikibot.Site('commons', 'commons')
    target_site.login()

    # Verify in_path
    if not os.path.isdir(in_path):
        pywikibot.output('The provided in_path was not a valid '
                         'directory: %s' % in_path)
        exit()

    # create target directories if they don't exist
    done_dir = os.path.join(in_path, target)
    error_dir = '%s_errors' % done_dir
    warnings_dir = '%s_warnings' % done_dir
    common.create_dir(done_dir)
    common.create_dir(error_dir)
    common.create_dir(warnings_dir)

    # logfile
    flog = common.LogFile(in_path, '¤uploader.log')

    # find all content files
    found_files = prepUpload.find_files(path=in_path, file_exts=file_exts,
                                        subdir=False)
    counter = 1
    for f in found_files:
        if cutoff and counter > cutoff:
            break
        # verify that there is a matching info file
        info_file = '%s.info' % os.path.splitext(f)[0]
        base_name = os.path.basename(f)
        base_info_name = os.path.basename(info_file)
        if not os.path.exists(info_file):
            flog.write_w_timestamp(
                '{0}: Found multimedia file without info'.format(base_name))
            continue

        # prepare upload
        txt = common.open_and_read_file(info_file)

        if test:
            pywikibot.output('Test upload "%s" with the following '
                             'description:\n%s\n' % (base_name, txt))
            counter += 1
            continue
        # stop here if testing

        result = upload_single_file(base_name, f, txt, target_site,
                                    upload_if_badprefix=True, chunked=chunked)

        target_dir = None
        if result.get('error'):
            target_dir = error_dir
        elif result.get('warning'):
            target_dir = warnings_dir
        else:
            target_dir = done_dir
        if verbose:
            pywikibot.output(result.get('log'))

        flog.write_w_timestamp(result.get('log'))
        os.rename(f, os.path.join(target_dir, base_name))
        os.rename(info_file, os.path.join(target_dir, base_info_name))
        counter += 1

    pywikibot.output(flog.close_and_confirm())


def up_all_from_url(info_path, cutoff=None, target='upload_logs',
                    file_exts=None, verbose=False, test=False,
                    target_site=None, only=None, skip=None):
    """
    Upload all media files provided as urls in a make_info json file.

    Outputs separate logfiles for files triggering errors, warnings (and
    successful) so that these can be used in latter runs.

    @param info_path: path to the make_info json file
    @param cutoff: number of files to upload (defaults to all)
    @param target: sub-directory for log files (defaults to "upload_logs")
    @param file_exts: tuple of allowed file extensions (defaults to FILE_EXTS)
    @param verbose: whether to output confirmation after each upload
    @param test: set to True to test but not upload
    @param target_site: pywikibot.Site to which file should be uploaded,
        defaults to Commons.
    @param only: list of urls to upload, if provided all others will be skipped
    @param skip: list of urls to skip, all others will be uploaded
    """
    # set defaults unless overridden
    file_exts = file_exts or FILE_EXTS
    target_site = target_site or pywikibot.Site('commons', 'commons')
    target_site.login()

    # load info file
    info_datas = common.open_and_read_file(info_path, as_json=True)

    # create target directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(info_path), target)
    common.create_dir(output_dir)

    # create all log files
    logs = {
        'success': common.LogFile(output_dir, 'success.log'),
        'warning': common.LogFile(output_dir, 'warnings.log'),
        'error': common.LogFile(output_dir, 'errors.log'),
        'general': common.LogFile(output_dir, 'uploader.log')
    }

    # shortcut to the general/verbose logfile
    flog = logs['general']

    # filtering based on entries in only/skip
    kill_list = set()
    if only:
        kill_list |= set(info_datas.keys()) - set(only)  # difference
    if skip:
        kill_list |= set(info_datas.keys()) & set(skip)  # intersection
    for key in kill_list:
        del info_datas[key]
    flog.write_w_timestamp('{} files remain to upload after filtering'.format(
        len(info_datas)))

    counter = 1
    for url, data in info_datas.items():
        if cutoff and counter > cutoff:
            break

        # verify that the file extension is ok
        try:
            ext = verify_url_file_extension(url, file_exts)
        except common.MyError as e:
            flog.write_w_timestamp(e)
            continue

        # verify that info and output filenames are provided
        if not data['info']:
            flog.write_w_timestamp(
                '{url}: Found url missing the info field (at least)'.format(
                    url=url))
            continue
        elif not data['filename']:
            flog.write_w_timestamp(
                '{url}: Found url missing the output filename'.format(
                    url=url))
            continue

        # prepare upload
        txt = make_info_page(data)
        filename = '{filename}{ext}'.format(filename=data['filename'], ext=ext)

        if test:
            pywikibot.output(
                'Test upload "{filename}" from "{url}" with the following '
                'description:\n{txt}\n'.format(
                    filename=filename, url=url, txt=txt))
            counter += 1
            continue
        # stop here if testing

        result = upload_single_file(
            filename, url, txt, target_site, upload_if_badprefix=True)
        if result.get('error'):
            logs['error'].write(url)
        elif result.get('warning'):
            logs['warning'].write(url)
        else:
            logs['success'].write(url)
        if verbose:
            pywikibot.output(result.get('log'))

        flog.write_w_timestamp(result.get('log'))
        counter += 1

    for log in logs.values():
        pywikibot.output(log.close_and_confirm())


def verify_url_file_extension(url, file_exts, url_protocols=None):
    """
    Verify that a url contains a file extension and that it is allowed.

    Also checks that the protocol is whitelisted.

    @param url: the url to check
    @param file_exts: tuple of allowed file extensions
    @param url_protocols: tuple of allowed url protocols
    @return: the file extension
    @raises: common.MyError
    """
    url_protocols = url_protocols or URL_PROTOCOLS

    protocol, _, rest = url.partition('://')
    if protocol not in url_protocols:
        raise common.MyError(
            '{0}: Found url with a disallowed protocol'.format(url))

    try:
        ext = os.path.splitext(url)[1]
    except IndexError:
        raise common.MyError(
            '{0}: Found url without a file extension'.format(url))
    else:
        if not ext:
            raise common.MyError(
                '{0}: Found url without a file extension'.format(url))

    if ext not in file_exts:
        raise common.MyError(
            '{0}: Found url with a disallowed file extension ({1})'.format(
                url, ext))

    return ext


def main(*args):
    """Command line entry-point."""
    usage = (
        'Usage:'
        '\tpython uploader.py -in_path:PATH -dir:PATH -cutoff:NUM\n'
        '\t-in_path:PATH path to the directory containing the media files or '
        'to the make_info output file if "-type" is set to url\n'
        '\t-type:STRING the type of upload to make. Must be either "FILES" '
        'or "URL". Defaults to FILES (optional)\n'
        '\t-dir:PATH specifies the path to the directory containing a '
        'user_config.py file (optional)\n'
        '\t-cutoff:NUM stop the upload after the specified number of files '
        '(optional)\n'
        '\t-confirm Whether to output a confirmation after each upload '
        'attempt (optional)\n'
        '\t-test Whether to do mock upload, simply outputting to commandline. '
        '(optional)\n'
        '\t-nochunk Whether to turn off chunked uploading, this is slow '
        'and does not support files > 100Mb (optional, type:FILES only)\n'
        '\t-only:PATH to file containing list of urls to upload, skipping all '
        'others. One entry per line. (optional, type:URL only)\n'
        '\t-skip:PATH to file containing list of urls to skip, uploading all '
        'others. Can be combined with "-only" for further filtering, e.g '
        '"-only:<list of vase images> -skip:<list of blue images>" to get '
        'non-blue vase images. One entry per line. (optional, type:URL only)\n'
        '\tExample:\n'
        '\tpython uploader.py -in_path:../diskkopia -cutoff:100\n'
    )
    cutoff = None
    in_path = None
    test = False
    confirm = False
    chunked = True
    typ = 'files'
    only = None
    skip = None

    # Load pywikibot args and handle local args
    for arg in pywikibot.handle_args(args):
        option, sep, value = arg.partition(':')
        if option == '-cutoff':
            if common.is_pos_int(value):
                cutoff = int(value)
        elif option == '-in_path':
            in_path = value
        elif option == '-test':
            test = True
        elif option == '-confirm':
            confirm = True
        elif option == '-nochunk':
            chunked = False
        elif option == '-type':
            if value.lower() == 'url':
                typ = 'url'
            elif value.lower() not in ('url', 'files'):
                pywikibot.output(usage)
                return
        elif option == '-only':
            only = common.trim_list(
                common.open_and_read_file(value).split('\n'))
        elif option == '-skip':
            skip = common.trim_list(
                common.open_and_read_file(value).split('\n'))
        elif option == '-usage':
            pywikibot.output(usage)
            return

    if in_path:
        if typ == 'files':
            up_all(in_path, cutoff=cutoff, test=test, verbose=confirm,
                   chunked=chunked)
        elif typ == 'url':
            up_all_from_url(in_path, cutoff=cutoff, only=only, skip=skip,
                            test=test, verbose=confirm)
    else:
        pywikibot.output(usage)


if __name__ == "__main__":
    main()

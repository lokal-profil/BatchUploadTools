#!/usr/bin/python
# -*- coding: utf-8  -*-
#
# Tool for scraping existing wiki lists from commons and
# storing these as correctly formatted local files
#
# Rebuilt from LSH-Redux
# TODO:
#   import mappings output from py_makeMappings
#
import os
import common
import pywikibot

OUT_PATH = u'connections'


def parseEntries(contents,
                 row_t=u'User:Lokal Profil/LSH3',
                 default_params=None):
    """
    Return a list of all parameters for instances of a given template.

    "/" in parameter values are interpreted as a separator for list entries.
    For non-empty entries a list of values is always returned.
    "<small>"-tags are striped from the input.

    :param content: wikicode
    :param row_t: row template
    :default_params: dict of expected params and their default values
    :return list: of entry-dict items
    """
    default_params = default_params or {
        u'name': '',
        u'more': '',
        u'frequency': '',
        u'technique': '',
        u'creator': '',
        u'link': '',
        u'category': '',
        u'other': ''}

    entries = common.get_all_template_entries(contents, row_t)
    units = []
    for entry in entries:
        params = default_params.copy()
        for key, value in entry.iteritems():
            value = value.replace(u'<small>', '').replace(u'</small>', '')
            value = value.strip()  # in case of empty <small>-tags
            if not value:
                continue
            if key in params.keys():
                params[key] = value.split(u'/')
            else:
                pywikibot.output(u'Unrecognised parameter: %s = %s' % (
                                 key, value))
        units.append(params.copy())
    return units


def formatEntry(u):
    """
    Given an mapping unit remove skipped entries, leave only category as a list
    and make frequency a number
    """
    # remove any -, make frequency and int
    for k, v in u.iteritems():
        # handle lists
        if k == 'category':
            if v == '':
                v = []
        elif isinstance(v, list):
            v = v[0]

        # format values
        if v:
            if k == 'frequency':
                v = int(v)
            elif isinstance(v, (str, unicode)) and v == '-':
                v = ''
            elif isinstance(v, list) and v[0] == '-':
                v = []
        u[k] = v
    return u


def scrape(pages, prefix, working_path=None, out_path=None, site=None):
    """
    Scrape lists on commons and overwrite local files

    :param pages: A mapping of Commons pages to output files
        where Commons pages get the format prefix*
        and output file the format: commons-*.json
        example: {u'People': u'People',
                  u'Keywords': u'Keywords',
                  u'Materials': u'Materials',
                  u'Places': u'Places'}

    :param prefix: prefix under which lists are found
        example: u'Commons:Batch uploading/LSH'
    :param working_path: path to directory in which to work (if not current)
        modifies out_path
    :param out_path: path to directory in which output files are put
    :param site: pywikibot.site object, default Commons
    """
    out_path = out_path or OUT_PATH

    # modify out_path by working_path if present
    if working_path:
        if not os.path.isdir(working_path):
            raise common.MyError(u'working_path not a directory: %s' %
                                 working_path)
        out_path = os.path.join(working_path, out_path)

    # create out_path if it doesn't exist
    if not os.path.isdir(out_path):
        os.mkdir(out_path)

    site = site or pywikibot.Site('commons', 'commons')

    # fetch, parse and save each page
    for k, v in pages.iteritems():
        page_title = u'%s/%s' % (prefix, k)
        page = pywikibot.Page(site, title=page_title)
        if not page.exists():
            raise common.MyError('The list page "%s" does not exist!' %
                                 page_title)
        units = parseEntries(page.get())
        filename = os.path.join(out_path, u'commons-%s.json' % v)
        common.open_and_write_file(filename, units, as_json=True)

        print u'Created %s' % filename


# functions for producing lists
def mergeWithOld(sorted_dict, pagename, output_wiki,
                 working_path=None, out_path=None):
    """
    Output mapping lists in wiki format, merging with any existing.

    :param sorted_dict prefix under which lists are found
        example: u'Commons:Batch uploading/LSH'
    :param pagename: name of the list
    :param output_wiki: function for outputting wikitext
    :param working_path: path to directory in which to work (if not current)
        modifies out_path
    :param out_path: path to directory in which output files are put
    """
    out_path = out_path or OUT_PATH

    # modify out_path by working_path if present
    if working_path:
        if not os.path.isdir(working_path):
            raise common.MyError(u'working_path not a directory: %s' %
                                 working_path)
        out_path = os.path.join(working_path, out_path)

    # create out_path if it doesn't exist
    if not os.path.isdir(out_path):
        os.mkdir(out_path)

    # load local json file (if any)
    old_mapping = []
    mapping_file = os.path.join(out_path, u'commons-%s.json' % pagename)
    if os.path.exists(mapping_file):
        old_mapping = common.open_and_read_file(mapping_file, as_json=True)

    # reset frequency and turn into dict
    previous = {}
    for entry in old_mapping:
        entry['frequency'] = 0
        previous[entry['name'][0]] = entry  # since these are all lists

    # add frequency + any new objects
    new_mapping = []
    for entry in sorted_dict:
        if entry[0] in previous.keys():
            new_mapping.append(
                makeEntry(entry[0], entry[1], previous[entry[0]]))
            del previous[entry[0]]
        else:
            new_mapping.append(makeEntry(entry[0], entry[1]))

    # preserve any remaining mappings
    for k, v in previous.iteritems():
        new_mapping.append(makeEntry(k, 0, v))

    # create output and write to .wiki
    wiki = output_wiki(new_mapping)
    wikifile = os.path.join(
        out_path, u'%s.wiki' % mapping_file[:-len('.json')])
    common.open_and_write_file(wikifile, wiki)


def makeEntry(name, frequency, previous=None):
    """
    Create a list entry in the relevant format, either from scratch or
    by reusing mappings.
    return entry
    """
    if frequency > 0:
        if previous:
            previous['frequency'] = frequency
            return previous
        else:
            return {u'name': [name, ],
                    u'more': '',
                    u'frequency': frequency,
                    u'technique': '',
                    u'creator': '',
                    u'link': '',
                    u'category': '',
                    u'other': ''}
    if previous:
        for k, v in previous.iteritems():
            # if any entry is non-empty
            if k not in (u'name', u'frequency') and v:
                return previous

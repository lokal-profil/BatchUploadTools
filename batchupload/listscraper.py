#!/usr/bin/python
# -*- coding: utf-8  -*-
#
# Tool for scraping existing wiki lists from commons and
# storing these as correctly formated local files
#
# Rebuilt from LSH-Redux
# TODO:
#   import mappings output from py_makeMappings
#
import os
import common  # used for get_all_template_entries, loadJsonConfig
import codecs
import json
import WikiApi as wikiApi
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
    Given an unit remove skipped entries, leave only category as a list
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


def scrape(pages, commonsPrefix, workingPath=None, outPath=OUT_PATH):
    """
    Scrape lists on commons and overwrite local files

    param pages: A mapping of Commons pages to output files
        where Commons pages get the format commonsPrefix*
        and outputfile the format: commons-*.json
        example: {u'People': u'People',
                  u'Keywords': u'Keywords',
                  u'Materials': u'Materials',
                  u'Places': u'Places'}
    param commonsPrefix prefix under which lists are found
        example: u'Commons:Batch uploading/LSH'
    param workingPath: path to directory in which to work (if not current)
        modifies out_path
    param outPath: path to directory in which to put outputfiles
    """
    # set cwd
    cwd = os.getcwd()
    if workingPath:
        if not os.path.isdir(workingPath):
            print u'workingPath not a directory: %s' % workingPath
        os.chdir(workingPath)

    # open connections
    config = common.loadJsonConfig()
    comApi = wikiApi.WikiApi.setUpApi(user=config['w_username'],
                                      password=config['w_password'],
                                      site=config['com_site'],
                                      scriptidentify=u'batchUploader/0.1')

    # create out_path if it doesn't exist
    if not os.path.isdir(outPath):
        os.mkdir(outPath)
    # fetch, parse and save each page
    for k, v in pages.iteritems():
        pageTitle = u'%s/%s' % (commonsPrefix, k)
        contents = comApi.getPage(pageTitle)
        units = parseEntries(contents[pageTitle])
        filename = os.path.join(outPath, u'commons-%s.json' % v)
        out = codecs.open(filename, 'w', 'utf8')
        out.write(json.dumps(units, ensure_ascii=False))
        out.close()
        print u'Created %s' % filename

    # reset cwd
    if workingPath:
        os.chdir(cwd)


# functions for producing lists
def mergeWithOld(sortedDictionary, pagename, outputWiki,
                 workingPath=None, outPath=OUT_PATH):
    """
    Given a sortedDict, list of (name, frequency), and an existing
    mapping file merge the result and output localy
    outputWiki should be a function
    """
    # set cwd
    cwd = os.getcwd()
    if workingPath:
        if not os.path.isdir(workingPath):
            print u'workingPath not a directory: %s' % workingPath
        os.chdir(workingPath)

    # create out_path if it doesn't exist
    if not os.path.isdir(outPath):
        os.mkdir(outPath)

    # load local json file (if any)
    oldMapping = []
    mappingfile = os.path.join(OUT_PATH, u'commons-%s.json' % pagename)
    if os.path.exists(mappingfile):
        f = codecs.open(mappingfile, 'r', 'utf-8')
        oldMapping = json.load(f)
        f.close()
    # reset frequency and turn into dict
    previous = {}
    for entry in oldMapping:
        entry['frequency'] = 0
        previous[entry['name'][0]] = entry  # since these are all lists

    # add frequency + any new objects
    newMapping = []
    for entry in sortedDictionary:
        if entry[0] in previous.keys():
            newMapping.append(
                makeEntry(entry[0], entry[1], previous[entry[0]]))
            del previous[entry[0]]
        else:
            newMapping.append(makeEntry(entry[0], entry[1]))

    # preserve Preserved mappings
    for k, v in previous.iteritems():
        newMapping.append(makeEntry(k, 0, v))

    # create output and write to .wiki
    wiki = outputWiki(newMapping)
    wikifile = u'%s.wiki' % mappingfile[:-len('.json')]
    f = codecs.open(wikifile, 'w', 'utf-8')
    f.write(wiki)
    f.close()

    # reset cwd
    if workingPath:
        os.chdir(cwd)


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

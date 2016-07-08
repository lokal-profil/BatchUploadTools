#!/usr/bin/python
# -*- coding: utf-8  -*-

"""
Shared methods.

To be merged with helpers.py
"""
import pywikibot
import json
import codecs


def loadJsonConfig(filename='config.json'):
    """
    Load and return json config file as a dict.

    Looks in local directory first.
    If file isn't there then looks in user directory.
    If file is in neither location then error is raised
    :param filename: name of json config file
    :return: dict
    """
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
            f.close()
    except IOError, e:
        if e.errno == 2:  # file not found
            import os
            path = os.getenv("HOME")
            with open(os.path.join(path, filename), 'r') as f:
                config = json.load(f)
                f.close()
        else:
            raise
    return config


def open_and_read_file(filename, codec='utf-8', json=False):
    """
    Open and read a file using the provided codec.

    Automatically closes the file on return.

    :param filename: the file to open
    :param codec: the used encoding (defaults to "utf-8")
    :param json: load as json instead of reading
    """
    with codecs.open(filename, 'r', codec) as f:
        if json:
            return json.load(f)
        return f.read()


def open_and_write_file(filename, text, codec='utf-8', json=False):
    """
    Open and write to a file using the provided codec.

    Automatically closes the file on return.

    :param filename: the file to open
    :param text: the text to output to the file
    :param codec: the used encoding (defaults to "utf-8")
    :param json: text is an object which should be dumped as json
    """
    with codecs.open(filename, 'w', codec) as f:
        if json:
            json.dumps(text, ensure_ascii=False)
        else:
            f.write(text)


def strip_dict_entries(dict_in):
    """Strip whitespace from all keys and (string) values in a dictionary."""
    dict_out = {}
    try:
        for k, v in dict_in.iteritems():
            if isinstance(v, basestring):
                v = v.strip()
            dict_out[k.strip()] = v
        return dict_out
    except AttributeError:
        raise MyError('strip_dict_entries() expects a dictionary object'
                      'as input but found "%s"' % type(dict_in).__name__)


def get_all_template_entries(wikitext, template_name):
    """Return a list of all arguments for instances of a given template."""
    templates = pywikibot.textlib.extract_templates_and_params(wikitext)
    result = []
    for tp in templates:
        if tp[0] == template_name:
            result.append(strip_dict_entries(tp[1]))
    return result


def get_all_template_entries_from_page(page, template_name):
    """Return a list of all arguments for instances of a given template."""
    templates = page.templatesWithParams()
    result = []
    for tp in templates:
        if tp[0].title() == template_name:
            result.append(tp[1])
    return result


class MyError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

#!/usr/bin/python
# -*- coding: utf-8  -*-

"""
Shared methods.

To be merged with helpers.py
"""
import pywikibot
import codecs
import json


def is_int(value):
    """Check if the given value is an integer.

    @param value: The value to check
    @type value: str, or int
    @return bool
    """
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False


def is_pos_int(value):
    """Check if the given value is a positive integer.

    @param value: The value to check
    @type value: str, or int
    @return bool
    """
    if is_int(value) and int(value) > 0:
        return True
    return False


def open_and_read_file(filename, codec='utf-8', as_json=False):
    """
    Open and read a file using the provided codec.

    Automatically closes the file on return.

    @param filename: the file to open
    @param codec: the used encoding (defaults to "utf-8")
    @param json: load as json instead of reading
    """
    with codecs.open(filename, 'r', codec) as f:
        if as_json:
            return json.load(f)
        return f.read()


def open_and_write_file(filename, text, codec='utf-8', as_json=False):
    """
    Open and write to a file using the provided codec.

    Automatically closes the file on return.

    @param filename: the file to open
    @param text: the text to output to the file
    @param codec: the used encoding (defaults to "utf-8")
    @param json: text is an object which should be dumped as json
    """
    with codecs.open(filename, 'w', codec) as f:
        if as_json:
            f.write(json.dumps(text, ensure_ascii=False))
        else:
            f.write(text)


def strip_dict_entries(dict_in):
    """Strip whitespace from all keys and (string) values in a dictionary."""
    dict_out = {}
    if not isinstance(dict_in, dict):
        raise MyError('strip_dict_entries() expects a dictionary object'
                      'as input but found "%s"' % type(dict_in).__name__)
    for k, v in dict_in.iteritems():
        if isinstance(v, basestring):
            v = v.strip()
        dict_out[k.strip()] = v
    return dict_out


def strip_list_entries(list_in):
    """Strip whitespace from all entries in a list."""
    list_out = []
    if not isinstance(list_in, list):
        raise MyError('strip_list_entries() expects a list object'
                      'as input but found "%s"' % type(list_in).__name__)
    for l in list_in:
        if isinstance(l, basestring):
            l = l.strip()
        list_out.append(l)
    return list_out


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

    """Home made errors"""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

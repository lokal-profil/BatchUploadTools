#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Common functions not specifically related to batchuploads or wiki."""
from __future__ import unicode_literals
from builtins import dict, open
import json
import os
import operator  # needed by sorted_dict
import sys  # needed by convert_from_commandline()
import locale  # needed by convert_from_commandline()
from pywikibot.tools import deprecated


# avoid having to use from past.builtins import basestring
try:
    basestring  # attempt to evaluate basestring
except NameError:
    def is_str(s):
        return isinstance(s, str)
else:
    def is_str(s):
        return isinstance(s, basestring)


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
    with open(filename, 'r', encoding=codec) as f:
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
    @param json: if text is an object which should be dumped as json
    """
    with open(filename, 'w', encoding=codec) as f:
        if as_json:
            f.write(json.dumps(text, indent=4, ensure_ascii=False))
        else:
            f.write(text)


def sorted_dict(ddict):
    """
    Turn a dict into a sorted list.

    @param ddict: dict to sort
    @type ddict: dict
    @return: list of tuples
    """
    sorted_ddict = sorted(ddict.items(),
                          key=operator.itemgetter(1),
                          reverse=True)
    return sorted_ddict


def strip_dict_entries(dict_in):
    """Strip whitespace from all keys and (string) values in a dictionary."""
    dict_out = dict()
    if not isinstance(dict_in, dict):
        raise MyError('strip_dict_entries() expects a dictionary object'
                      'as input but found "%s"' % type(dict_in).__name__)
    for k, v in dict_in.items():
        if is_str(v):
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
        if is_str(l):
            l = l.strip()
        list_out.append(l)
    return list_out


def trim_list(old_list):
    """Given a list remove any empty entries."""
    # return any empty or None
    if not old_list:
        return old_list

    old_list = strip_list_entries(old_list)
    new_list = []
    for l in old_list:
        if l:
            new_list.append(l)
    return new_list


def listify(value):
    """Turn the given value, which might or might not be a list, into a list.

    @param value: The value to listify
    @type value: any
    @rtype: list, or None
    """
    if value is None:
        return None
    elif isinstance(value, list):
        return value
    else:
        return [value, ]


def deep_sort(obj):
    """Recursively sort list or dict of nested lists."""
    if isinstance(obj, dict):
        _sorted = dict()
        for key in sorted(obj):
            _sorted[key] = deep_sort(obj[key])
    elif isinstance(obj, list):
        new_list = []
        for val in obj:
            new_list.append(deep_sort(val))
        _sorted = sorted(new_list)
    else:
        _sorted = obj
    return _sorted


def add_or_increment(dictionary, val, key=None):
    """
    Add a value to the dictionary or increments the counter for the value.

    @param dictionary: the dictionary to update
    @param val: the value to look for in the dictionary
    @param key: the key holding the counter
    """
    if val not in dictionary:
        if key:
            dictionary[val] = {key: 0}
        else:
            dictionary[val] = 0
    if key:
        dictionary[val][key] += 1
    else:
        dictionary[val] += 1


@deprecated('helpers.get_all_template_entries')
def get_all_template_entries(wikitext, template_name):
    """Return a list of all arguments for instances of a given template."""
    import batchupload.helpers as helpers
    return helpers.get_all_template_entries(wikitext, template_name)


@deprecated('helpers.get_all_template_entries_from_page')
def get_all_template_entries_from_page(page, template_name):
    """Return a list of all arguments for instances of a given template."""
    import batchupload.helpers as helpers
    return helpers.get_all_template_entries_from_page(page, template_name)


def modify_path(base_path, out_path):
    """
    Modify a path by appending it to a base path, if one is given.

    @param base_path: The prefixing path
    @param out_path: The path to modify, prefix
    @return: string, the modified base_path
    """
    if base_path:
        if not os.path.isdir(base_path):
            raise MyError('"%s" is not a directory.' % base_path)
        out_path = os.path.join(base_path, out_path)
    return out_path


def create_dir(out_path):
    """
    Create a directory if it doesn't exist.

    @param out_path: directory to create
    """
    if not out_path:
        raise MyError('Cannot create directory without a name.')
    if not os.path.exists(out_path):
        os.mkdir(out_path)
    elif os.path.isfile(out_path):
        raise MyError('Cannot create the directory "%s" as a file with that '
                      'name already exists.' % out_path)


def to_unicode(text):
    """
    Converts a str to unicode (if python2).

    @param text: text to convert
    @return: unicode string
    """
    try:
        unicode
    except NameError:
        # python 3 so don't worry
        pass
    else:
        if isinstance(text, str):
            text = unicode(text)
    return text


def convert_from_commandline(string):
    """
    Convert a string read from the commandline to a standard unicode format.

    @param string: string to convert
    @return: str
    """
    return string.decode(sys.stdin.encoding or
                         locale.getpreferredencoding(True))


class MyError(Exception):

    """Home made errors"""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

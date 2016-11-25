#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Methods and helpers for csv handling."""
from batchupload.common import (
    MyError,
    open_and_read_file,
    open_and_write_file,
    strip_list_entries,
    trim_list
)


def open_csv_file(filename, delimiter='|', codec='utf-8'):
    """
    Open a csv file and returns the header row plus following lines.

    @param filename: the file to open
    @param delimiter: the used delimiter (defaults to "|")
    @param codec: the used encoding (defaults to "utf-8")
    @return: tuple(array(str), array(str))
    """
    lines = open_and_read_file(filename, codec).strip().split('\n')
    header = lines.pop(0).split(delimiter)
    return strip_list_entries(header), strip_list_entries(lines)


def validate_key_col(key_col, lists, non_unique, keep, header):
    """
    Validate key_col in terms of type and not being in any special column.

    @param key_col: the (label of the) column to use as a key in the dict
                   str or tuple of strs to combine (with a ":")
    @param lists: tuple of columns to treat as lists
    @param non_unique: tuple of non-unique column headings
    @param keep: tuple of columns to keep
    @param header: list of column labels
    @raise MyError
    """
    # verify type is valid
    if not isinstance(key_col, (tuple, basestring)):
        raise MyError('key_col must be tuple or str')
    if isinstance(key_col, tuple) and \
            not all(isinstance(key, basestring) for key in key_col):
        raise MyError('each key_col entry must be a str')

    # verify no key_col is empty or any list or non_unique column
    test_key_col = key_col
    if not isinstance(key_col, tuple):
        test_key_col = (key_col, )

    for test_key in test_key_col:
        if not test_key:
            raise MyError(u'no key_col must not be empty')
        if test_key in (lists or []) or key_col in (non_unique or []):
            raise MyError(u'no key_col must be a list column or a '
                          u'non-unique column')
        if test_key not in header:
            raise MyError(u'every key_col must be present in the header')
        if test_key not in keep:
            raise MyError(u'every key_col must be present in the kept columns')


def find_cols(find, label, header, default_all=False):
    """
    Identify the column numbers for a given list of columns.

    @param find: a tuple of the column labels to look for
    @param label: a label for the search, used in error message
    @param header: list of column headers
    @param default_all: if result should default to all columns
        (defaults to False)
    @return dict
    """
    # set up columns to keep
    cols = {}
    if find is None:
        if default_all:
            cols = dict.fromkeys(header)
    else:
        # check all find columns in header
        if any(f not in header for f in find):
            raise MyError("All '%s'-columns must be in header" % label)
        cols = dict.fromkeys(find)
    for c in cols.keys():
        cols[c] = header.index(c)
    return cols


def find_non_unique_cols(header, keep, non_unique):
    """
    Identify any columns with non-unique labels.

    @param header: list of column headers
    @param keep: list of columns to keep
    @param non_unique: whether non_unique columns are expected/allowed
    @return dict
    """
    # find non-unique columns
    cols = {}
    handled = {}
    for i, v in enumerate(header):
        if v in handled.keys():
            continue
        else:
            handled[v] = [i, ]
        while True:
            try:
                j = header.index(v, i + 1)
                handled[v].append(j)
                i = j
            except ValueError:
                break
        if len(handled[v]) > 1:
            cols[v] = tuple(handled[v])

    # raise error if we are not expecting these in the results
    if cols and not non_unique and any(k in cols.keys() for k in keep):
        raise MyError(u"Unexpected non-unique columns found: %s" %
                      ', '.join(cols.keys()))
    return cols


def csv_file_to_dict(filename, key_col, header_check, non_unique=False,
                     keep=None, lists=None, delimiter='|', list_delimiter=';',
                     codec='utf-8'):
    """
    Open a csv file and returns a dict of dicts, using the header row for keys.

    Non-unique columns are concatenated into lists. Note that this structure
    does not survive the csv_file_to_dict -> dict_to_csv_file roundtrip.

    @param filename: the file to open
    @param key_col: the (label of the) column to use as a key in the dict
        str or tuple of strs to combine (with a ":")
    @param header_check: a string to check against the header row
    @param non_unique: whether non-unique column headings are expected
        (defaults to False)
    @param keep: tuple of columns to keep (defaults to None=all)
    @param lists: tuple of columns to treat as lists (defaults to None=none)
    @param delimiter: the used delimiter (defaults to "|")
    @param list_delimiter: the used delimiter when encountering a list
    @param codec: the used encoding (defaults to "utf-8")
    @return: dict
    """
    # load and parse file
    header, lines = open_csv_file(filename, delimiter=delimiter, codec=codec)

    # verify header == headerCheck (including order)
    if header_check.split(delimiter) != header:
        raise MyError("Header missmatch.\nExpected: %s\nFound:%s" % (
                      header_check, delimiter.join(header)))

    # convert txt key to numeric key
    try:
        key_col_num = None
        if isinstance(key_col, tuple):
            key_col_num = []
            for key in key_col:
                key_col_num.append(header.index(key))
            key_col_num = tuple(key_col_num)
        else:
            key_col_num = header.index(key_col)
    except ValueError:
        raise MyError("key_col not found in header")

    # set up columns to keep and listify columns
    cols = find_cols(keep, 'keep', header, default_all=True)
    non_unique_cols = find_non_unique_cols(header, cols.keys(), non_unique)
    listify = find_cols(lists, 'lists', header, default_all=False)

    # verify key_col is valid
    validate_key_col(key_col, lists, non_unique_cols, cols.keys(), header)

    # load to dict
    d = {}
    for l in lines:
        if not l:
            continue
        parts = l.split(delimiter)

        # set key
        key = None
        if isinstance(key_col_num, tuple):
            keys = []
            for key_num in key_col_num:
                keys.append(parts[key_num].strip())
            key = ':'.join(keys)
        else:
            key = parts[key_col_num].strip()

        # check uniqueness
        if key in d.keys():
            raise MyError("Non-unique key found: %s" % key)

        d[key] = {}
        for k, v in cols.iteritems():
            if k in non_unique_cols.keys():
                d[key][k] = []
                for nv in non_unique_cols[k]:
                    if k in listify.keys():
                        d[key][k] += parts[nv].strip().split(list_delimiter)
                    else:
                        d[key][k].append(parts[nv].strip())
                d[key][k] = trim_list(d[key][k])
            else:
                if k in listify.keys():
                    d[key][k] = trim_list(
                        parts[v].strip().split(list_delimiter))
                else:
                    d[key][k] = parts[v].strip()

    return d


def dict_to_csv_file(filename, d, header, delimiter='|', list_delimiter=';',
                     codec='utf-8'):
    """
    Save a dict as csv file given a header string encoding the columns.

    @param filename: the target file
    @param d: the dictionary to convert
    @param header: a string giving parameters to output and their order
    @param delimiter: the used delimiter (defaults to "|")
    @param list_delimiter: the used delimiter when encountering a list
    @param codec: the used encoding (defaults to "utf-8")
    @return: None
    """
    # load file and write header
    output = u'%s\n' % header

    # find keys to compare with header
    cols = d.iteritems().next()[1].keys()
    header = header.split(delimiter)

    # verify all header fields are present
    if any(h not in cols for h in header):
        raise MyError("Header missmatch")

    # output rows
    for k, v in d.iteritems():
        row = []
        for h in header:
            if isinstance(v[h], list):
                row.append(list_delimiter.join(v[h]))
            else:
                row.append(v[h])
        output += u'%s\n' % delimiter.join(row)

    # close
    open_and_write_file(filename, output, codec=codec)

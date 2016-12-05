#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Helper tools related to wiki specific formatting or restrictions."""
from __future__ import unicode_literals
from builtins import range  # ,dict
from pywikibot.tools import deprecated
import pywikibot.textlib
import batchupload.common as common

# limitations on namelength
# shorten if longer than GOODLENGTH cut if longer than MAXLENGTH
GOODLENGTH = 100
MAXLENGTH = 128

# black-lists
bad_dates = ('n.d', 'odaterad')


def flip_name(name):
    """
    Given a single name return any "Last, First" as "First Last".

    Strings with more or less than one comma are returned unchanged.

    @param name: string to be flipped
    @return: list
    """
    p = name.split(',')
    if len(p) == 2:
        return '%s %s' % (p[1].strip(), p[0].strip())
    else:
        return name


def flip_names(names):
    """
    Given a list of strings send each on through flip_name().

    Any strings not of the form "Last, First" are returned unchanged.

    @param names: list of strings to be flipped
    @return: list
    """
    flipped = []
    for name in names:
        flipped.append(flip_name(name))
    return flipped


@deprecated('common.sorted_dict')
def sortedDict(ddict):
    """Turn a dict into a sorted list."""
    return common.sorted_dict(ddict)


@deprecated('common.add_or_increment')
def addOrIncrement(dictionary, val, key=None):
    """
    Add a value to the dictionary or increments the counter for the value.

    @param dictionary: the dictionary to update
    @param val: the value to look for in the dictionary
    @param key: the key holding the counter
    """
    common.add_or_increment(dictionary, val, key)


def get_all_template_entries(wikitext, template_name):
    """Return a list of all arguments for instances of a given template."""
    templates = pywikibot.textlib.extract_templates_and_params(wikitext)
    result = []
    for tp in templates:
        if tp[0] == template_name:
            result.append(common.strip_dict_entries(tp[1]))
    return result


def get_all_template_entries_from_page(page, template_name):
    """Return a list of all arguments for instances of a given template."""
    templates = page.templatesWithParams()
    result = []
    for tp in templates:
        if tp[0].title() == template_name:
            result.append(tp[1])
    return result


# methods for handling filenames
def format_filename(descr, institution, idno, delimiter=None):
    """
    Given the three components of a filename return the final string.

    Does not include file extension.

    @Todo: should possibly live elsewhere?

    @param descr: a short description of the file contents
    @param institution: the institution name or abbreviation
    @param idno: the unique identifier
    @param delimiter: the delimiter to use between the parts
    @return: str
    """
    delimiter = delimiter or ' - '
    descr = desc_cleanup_routine(descr, delimiter)
    institution = cleanString(institution)
    idno = cleanString(idno)
    filename = delimiter.join((descr, institution, idno))
    return filename.replace(' ', '_')


def cleanString(text):
    """Remove characters which are forbidden/undesired in filenames."""
    # bad characters  - extend as more are identified
    # Note that ":" is complicated as it has several different interpretaions.
    # Currently first replacing possesive case and sentence break then
    # dealing with stand alone :
    # maybe also ? ' and &nbsp; symbol
    bad_char = {'\\': '-', '/': '-', '|': '-', '#': '-',
                '[': '(', ']': ')', '{': '(', '}': ')',
                ':s': 's', ': ': ', ',
                ' ': ' ', ' ': ' ', '	': ' ',  # unusual whitespace
                'e´': 'é',
                '”': ' ', '"': ' ', '“': ' '}
    for k, v in bad_char.items():
        text = text.replace(k, v)

    # replace any remaining colons
    if ':' in text:
        text = text.replace(':', '-')

    # replace double space by single space
    text = text.replace('  ', ' ')
    return text.strip()


def touchup(text, delimiter=None, delimiter_replacement=None):
    """
    Perform various cleanup processes on a string.

    Tweaks a string by:
    * removing surrounding bracket or quotes
    * remove some trailing punctuation.

    @param text: the text to touch up
    @param delimiter: a delimiter to replace
    @param delimiter_replacement: what to replace the delimiter by. Defaults to
        ", ".
    @return string
    """
    delimiter_replacement = delimiter_replacement or ', '

    # If string starts and ends with bracket or quotes then remove
    brackets = {'(': ')', '[': ']', '{': '}', '"': '"'}
    for k, v in brackets.items():
        if text.startswith(k) and text.endswith(v) and \
                text[:-1].count(k) == 1:
            # Last check is so as to not remove non-matching brackets
            # with slice in use is due to cases where k=v.
            text = text[1:-1]

    # Get rid of leading/trailing punctuation
    text = text.strip(' .,;')

    # Make sure first character is upper case
    text = text[:1].upper() + text[1:]

    # Replace any use of the institution/id delimiter
    if delimiter:
        text = text.replace(delimiter, delimiter_replacement)

    return text


def shortenString(text):
    """
    Shorten strings longer than GOODLENGTH.

    @param text: the text to shorten
    @return string
    """
    badchar = '-., '  # maybe also "?
    if '<!>' in text:
        text = text[:text.find('<!>')]
    # is ok?
    if len(text) < GOODLENGTH:
        return text
    # attempt fixing
    # remove trailing brackets
    if text.endswith(')'):
        pos = text.rfind('(')
        if pos > 0:
            return shortenString(text[:pos].strip(badchar))
    # split string at certain character
    pos = text.rfind('.')
    if pos < 0:
        pos = text.rfind(' - ')
        if pos < 0:
            pos = text.rfind(';')
            if pos < 0:
                pos = text.rfind(',')
                if pos < 0:
                    # try something else
                    if len(text) > MAXLENGTH:
                        text = '%s...' % text[:MAXLENGTH - 3]
                    return text
    return shortenString(text[:pos].strip(badchar))


def desc_cleanup_routine(text, delimiter=None, delimiter_replacement=None):
    """
    Run the full cleanup routine on a description string.

    @param text: the text to clean
    @type text: string
    @param delimiter: a delimiter to replace
    @type delimiter: string|None
    @param delimiter_replacement: what to replace the delimiter by
    @type delimiter_replacement: string|None
    @return: string
    """
    text = cleanString(text)
    if not text.strip('0123456789,.- '):
        # if no relevant info left
        text = ''
    else:
        text = shortenString(text)
        text = touchup(text, delimiter, delimiter_replacement)

    return text


# methods for handling dates
def std_date_range(date, range_delimiter=' - '):
    """
    Given a date, which could be a range, return a standardised Commons date.

    Note that care must be taken so that the delimiter only denotes ranges.
    If only one date is found, or the dates are the same then only that is
    returned.

    Main logic is found in stdDate().

    @param date: the string to be parsed as a range of dates
    @param range_delimiter: delimiter used between two dates
    @return string|None
    """
    # is this a range?
    dates = date.split(range_delimiter)
    if len(dates) == 2:
        d1 = stdDate(dates[0])
        d2 = stdDate(dates[1])
        if d1 is not None and d2 is not None:
            if d1 == d2:
                return d1
            else:
                return '{{other date|-|%s|%s}}' % (d1, d2)
    else:
        d = stdDate(date)
        if d is not None:
            return d

    # if you get here you have failed
    return None


def stdDate(date):
    """
    Given a single date, not a range, return a standardised Commons date.

    Standardised Commons date means either ISO-form or using the Other_date
    template.

    Note that care must be taken so that ranges are separated prior to
    this since YYYY-MM and YYYY-YY are otherwise indistinguisable.

    @param date: the string to be parsed as a date
    @return string|None
    """
    # No date
    date = date.strip('.  ')
    if len(date) == 0 or date.lower() in bad_dates:
        return ''  # this is equivalent to '{{other date|unknown}}'
    date = date.replace(' - ', '-')

    # A single date
    endings = {
        '?': '?',
        '(?)': '?',
        'c': 'ca',
        'ca': 'ca',
        'cirka': 'ca',
        'andra hälft': '2half',
        'första hälft': '1half',
        'början': 'early',
        'slut': 'end',
        'slutet': 'end',
        'mitt': 'mid',
        'första fjärdedel': '1quarter',
        'andra fjärdedel': '2quarter',
        'tredje fjärdedel': '3quarter',
        'fjärde fjärdedel': '4quarter',
        'sista fjärdedel': '4quarter',
        'före': '<',
        'efter': '>',
        '-': '>'}
    starts = {
        'tidigt': 'early',
        'br av': 'early',
        'början av': 'early',
        'tid ': 'early',
        'sent': 'late',
        'sl av': 'late',
        'slutet av': 'end',
        'andra hälften av': '2half',
        'första hälften av': '1half',
        'mitten av': 'mid',
        'första fjärdedel av': '1quarter',
        'andra fjärdedel av': '2quarter',
        'tredje fjärdedel av': '3quarter',
        'fjärde fjärdedel av': '4quarter',
        'sista fjärdedel av': '4quarter',
        'ca': 'ca',
        'våren': 'spring',
        'sommaren': 'summer',
        'hösten': 'fall',
        'vintern': 'winter',
        'sekelskiftet': 'turn of the century',
        'före': '<',
        'efter': '>',
        '-': '<'}
    tal_endings = ('-talets', '-tal', '-talet', ' talets')
    modality = ('troligen', 'sannolikt')
    for k, v in starts.items():
        if date.lower().startswith(k):
            again = stdDate(date[len(k):])
            if again:
                return '{{other date|%s|%s}}' % (v, again)
            else:
                return None
    for k, v in endings.items():
        if date.lower().endswith(k):
            again = stdDate(date[:-len(k)])
            if again:
                return '{{other date|%s|%s}}' % (v, again)
            else:
                return None
    for k in modality:
        found = False
        if date.lower().endswith(k):
            date = date[:-len(k)].strip('.,  ')
            found = True
        elif date.lower().startswith(k):
            date = date[len(k):].strip('.,  ')
            found = True
        if found:
            again = stdDate(date)
            if again:
                return '%s {{Probably}}' % again
            else:
                return None
    for k in tal_endings:
        if date.lower().endswith(k):
            date = date[:-len(k)].strip('.  ')
            if date[-2:] == '00':
                v = 'century'
                if len(date) == 4:
                    return '{{other date|%s|%r}}' % (v, int(date[:2]) + 1)
                else:
                    return None
            else:
                v = 'decade'
            again = stdDate(date)  # needed?
            if again:
                return '{{other date|%s|%s}}' % (v, again)
            else:
                return None

    # ISO-forms
    return isoDate(date)


def isoDate(date):
    """Given a string this returns an iso date (if possible)."""
    item = date[:len('YYYY-MM-DD')].split('-')
    if len(item) == 3 and all(common.is_pos_int(x) for x in item) and \
            int(item[1][:len('MM')]) in range(1, 12 + 1) and \
            int(item[2][:len('DD')]) in range(1, 31 + 1):
        # 1921-09-17Z or 2014-07-11T08:14:46Z
        return '%s-%s-%s' % (item[0], item[1], item[2])
    elif len(item) == 1 and common.is_pos_int(item[0][:len('YYYY')]):
        # 1921Z
        return item[0]
    elif len(item) == 2 and \
            all(common.is_pos_int(x) for x in (item[0], item[1][:len('MM')])) and \
            int(item[1][:len('MM')]) in range(1, 12 + 1):
        # 1921-09Z
        return '%s-%s' % (item[0], item[1])
    else:
        return None


def italicize(s):
    """Given a string return the same string italicized (in wikitext)."""
    return '\'\'%s\'\'' % s


@deprecated('common.convert_from_commandline')
def convertFromCommandline(s):
    """
    Convert a string read from the commandline to a standard unicode format.

    :param s: string to convert
    :return: str
    """
    return common.convert_from_commandline(s)

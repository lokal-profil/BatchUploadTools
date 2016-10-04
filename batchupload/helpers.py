#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Helper tools related to batchUploads."""
import operator
import sys  # needed by convertFromCommandline()
import locale  # needed by convertFromCommandline()
import batchupload.common as common

# limitations on namelength
# shorten if longer than GOODLENGTH cut if longer than MAXLENGTH
GOODLENGTH = 100
MAXLENGTH = 128

# black-lists
bad_dates = (u'n.d', u'odaterad')


def flip_name(name):
    """
    Given a single name return any "Last, First" as "First Last".

    Strings with more or less than one comma are returned unchanged.

    @param name: string to be flipped
    @return: list
    """
    p = name.split(',')
    if len(p) == 2:
        return u'%s %s' % (p[1].strip(), p[0].strip())
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


def sortedDict(ddict):
    """Turn a dict into a sorted list."""
    sorted_ddict = sorted(ddict.iteritems(),
                          key=operator.itemgetter(1),
                          reverse=True)
    return sorted_ddict


def addOrIncrement(dictionary, val, key=None):
    """
    Add a value to the dictionary or increments the counter for the value.

    @param dictionary: the dictionary to update
    @param val: the value to look for in the dictionary
    @param key: the key holding the counter
    """
    if val not in dictionary.keys():
        if key:
            dictionary[val] = {key: 0}
        else:
            dictionary[val] = 0
    if key:
        dictionary[val][key] += 1
    else:
        dictionary[val] += 1


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
    delimiter = delimiter or u' - '
    descr = shortenString(touchup(cleanString(descr), delimiter))
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
    bad_char = {u'\\': u'-', u'/': u'-', u'|': u'-', u'#': u'-',
                u'[': u'(', u']': u')', u'{': u'(', u'}': u')',
                u':s': u's', u': ': u', ',
                u' ': u' ', u' ': u' ', u'	': u' ',  # unusual whitespace
                u'e´': u'é',
                u'”': u' ', u'"': u' ', u'“': u' '}
    for k, v in bad_char.iteritems():
        text = text.replace(k, v)

    # replace any remaining colons
    if u':' in text:
        text = text.replace(u':', u'-')

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
    @param delimiter_replacement: what to replace the delimiter by
    @return string
    """
    delimiter_replacement = delimiter_replacement or ', '

    # If string starts and ends with bracket or quotes then remove
    brackets = {u'(': ')', u'[': ']', u'{': '}', u'"': '"'}
    for k, v in brackets.iteritems():
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
    badchar = u'-., '  # maybe also "?
    if u'<!>' in text:
        text = text[:text.find(u'<!>')]
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
                        text = u'%s...' % text[:MAXLENGTH - 3]
                    return text
    return shortenString(text[:pos].strip(badchar))


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
                return u'{{other date|-|%s|%s}}' % (d1, d2)
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
    date = date.strip(u'.  ')
    if len(date) == 0 or date.lower() in bad_dates:
        return u''  # this is equivalent to u'{{other date|unknown}}'
    date = date.replace(u' - ', u'-')

    # A single date
    endings = {
        u'?': u'?',
        u'(?)': u'?',
        u'c': u'ca',
        u'ca': u'ca',
        u'cirka': u'ca',
        u'andra hälft': u'2half',
        u'första hälft': u'1half',
        u'början': u'early',
        u'slut': u'end',
        u'slutet': u'end',
        u'mitt': u'mid',
        u'första fjärdedel': u'1quarter',
        u'andra fjärdedel': u'2quarter',
        u'tredje fjärdedel': u'3quarter',
        u'fjärde fjärdedel': u'4quarter',
        u'sista fjärdedel': u'4quarter',
        u'före': u'<',
        u'efter': u'>',
        u'-': u'>'}
    starts = {
        u'tidigt': u'early',
        u'br av': u'early',
        u'tid ': u'early',
        u'sent': u'late',
        u'sl av': u'late',
        u'ca': u'ca',
        u'våren': u'spring',
        u'sommaren': u'summer',
        u'hösten': u'fall',
        u'vintern': u'winter',
        u'sekelskiftet': u'turn of the century',
        u'före': u'<',
        u'efter': u'>',
        u'-': u'<'}
    tal_endings = (u'-talets', u'-tal', u'-talet', u' talets')
    modality_endings = (u'troligen', u'sannolikt')
    for k, v in starts.iteritems():
        if date.lower().startswith(k):
            again = stdDate(date[len(k):])
            if again:
                return u'{{other date|%s|%s}}' % (v, again)
            else:
                return None
    for k, v in endings.iteritems():
        if date.lower().endswith(k):
            again = stdDate(date[:-len(k)])
            if again:
                return u'{{other date|%s|%s}}' % (v, again)
            else:
                return None
    for k in modality_endings:
        if date.lower().endswith(k):
            date = date[:-len(k)].strip(u'.,  ')
            again = stdDate(date)
            if again:
                return u'%s {{Probably}}' % again
            else:
                return None
    for k in tal_endings:
        if date.lower().endswith(k):
            date = date[:-len(k)].strip(u'.  ')
            if date[-2:] == u'00':
                v = u'century'
                if len(date) == 4:
                    return u'{{other date|%s|%r}}' % (v, int(date[:2]) + 1)
                else:
                    return None
            else:
                v = u'decade'
            again = stdDate(date)  # needed?
            if again:
                return u'{{other date|%s|%s}}' % (v, again)
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
        return u'%s-%s-%s' % (item[0], item[1], item[2])
    elif len(item) == 1 and common.is_pos_int(item[0][:len('YYYY')]):
        # 1921Z
        return item[0]
    elif len(item) == 2 and \
            all(common.is_pos_int(x) for x in (item[0], item[1][:len('MM')])) and \
            int(item[1][:len('MM')]) in range(1, 12 + 1):
        # 1921-09Z
        return u'%s-%s' % (item[0], item[1])
    else:
        return None


def italicize(s):
    """Given a string return the same string italicized (in wikitext)."""
    return u'\'\'%s\'\'' % s


def convertFromCommandline(s):
    """
    Convert a string read from the commandline to a standard unicode format.

    :param s: string to convert
    :return: str
    """
    return s.decode(sys.stdin.encoding or
                    locale.getpreferredencoding(True))

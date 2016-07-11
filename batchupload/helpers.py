#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Helper tools related to batchUploads
"""
import operator
import sys  # needed by convertFromCommandline()
import locale  # needed by convertFromCommandline()
import batchupload.common as common

# limitations on namelength
# shorten if longer than GOODLENGTH cut if longer than MAXLENGTH
GOODLENGTH = 100
MAXLENGTH = 128

# black-lists
badDates = (u'n.d', u'odaterad')


def flipName(name):
    """
    Given a single name return any Last, First as First Last,
    otherwise returns the input unchanged.
    """
    p = name.split(',')
    if len(p) == 2:
        return u'%s %s' % (p[1].strip(), p[0].strip())
    else:
        return name


def trimList(oldList):
    """Given a list remove any empty entries."""
    newList = []
    for l in oldList:
        if len(l.strip()) > 0:
            newList.append(l.strip())
    return newList


def sortedDict(ddict):
    """Turn a dict into a sorted list."""
    sorted_ddict = sorted(ddict.iteritems(),
                          key=operator.itemgetter(1),
                          reverse=True)
    return sorted_ddict


def addOrIncrement(dictionary, val, key=None):
    """
    Add a value to the dictionary or increments the
    counter for the value.

    param key: the key holding the counter
    """
    if val in dictionary.keys():
        if key:
            dictionary[val][key] += 1
        else:
            dictionary[val] += 1
    else:
        if key:
            dictionary[val] = {key: 1}
        else:
            dictionary[val] = 1


def cleanString(text):
    """Remove characters which are forbidden/undesired in filenames."""
    # bad characters  - extend as more are identified
    # Note that ":" is complicated as it has several different interpretaions.
    # Currently first replacing possesive case and sentence break then
    # dealing with stand alone :
    # maybe also ? ' and &nbsp; symbol
    badChar = {u'\\': u'-', u'/': u'-', u'|': u'-', u'#': u'-',
               u'[': u'(', u']': u')', u'{': u'(', u'}': u')',
               u':s': u's', u': ': u', ',
               u' ': u' ', u' ': u' ', u'	': u' ',  # unusual whitespace
               u'e´': u'é',
               u'”': u' ', u'"': u' ', u'“': u' '}
    for k, v in badChar.iteritems():
        text = text.replace(k, v)

    # replace any remaining colons
    if u':' in text:
        text = text.replace(u':', u'-')

    # replace double space by single space
    text = text.replace('  ', ' ')
    return text.strip()


def touchup(text):
    """
    Tweaks a string by removing surrounding bracket or quotes as well as
    some trailing punctuation.
    """
    # If string starts and ends with bracket or quotes then remove
    brackets = {u'(': ')', u'[': ']', u'{': '}', u'"': '"'}
    for k, v in brackets.iteritems():
        if text.startswith(k) and text.endswith(v):
            if text[:-1].count(k) == 1:
                # so as to not remove non-matching brackets.
                # slice in check is due to quote-bracket
                text = text[1:-1]

    # Get rid of leading/trailing punctuation
    text = text.strip(' .,;')

    # Make sure first character is upper case
    text = text[:1].upper() + text[1:]
    return text


def shortenString(text):
    '''
    If a string is larger than GOODLENGTH then this tries to
    find a sensibel shortening.
    '''
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


def stdDate(date):
    """
    Given a single date (not a range) this returns a standardised date
    in ISO-form or using the Other_Date template.

    Note that care must be taken so that ranges are separated prior to
    this since YYYY-MM and YYYY-YY are otherwise indistinguisable.

    return string|None
    """
    # No date
    date = date.strip(u'.  ')
    if len(date) == 0 or date.lower() in badDates:
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
    talEndings = (u'-talets', u'-tal', u'-talet', u' talets')
    modalityEndings = (u'troligen', u'sannolikt')
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
    for k in modalityEndings:
        if date.lower().endswith(k):
            date = date[:-len(k)].strip(u'.,  ')
            again = stdDate(date)
            if again:
                return u'%s {{Probably}}' % again
            else:
                return None
    for k in talEndings:
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

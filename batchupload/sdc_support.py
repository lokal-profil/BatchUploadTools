#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Support functionality to allow upload of Structured Data to new uploads.

Internally used format briefly described in docs/SDC_file_example.json

Stopgap until proper support is implemented in Pywikibot T223820.
Heavily inspired by hack by Abbe98:
https://byabbe.se/2020/09/15/writing-structured-data-on-commons-with-python
"""
from __future__ import unicode_literals
from builtins import dict
import json
import pywikibot
import batchupload.common as common


def upload_single_sdc_data(target_site, file_page, sdc_data):
    """
    Upload the Structured Data corresponding to the recently uploaded file.

    @param target_site: pywikibot.Site object to which file should be uploaded
    @param file_page: pywikibot.FilePage object corresponding to the
        recently uploaded file
    @param sdc_data: internally formatted Structured data in json format
    @return: dict of potential issues
    """
    media_identifier = 'M{}'.format(file_page.pageid)
    try:
        sdc_payload = format_sdc_payload(target_site, sdc_data)
    except Exception as error:
        return {
            'type': 'error',
            'data': error,
            'log': '{0} Error uploading SDC data: {1}'.format(
                file_page.title(), error)
        }

    # verify that there is no data yet
    request = target_site._simple_request(
        action='wbgetentities', ids=media_identifier)
    raw = request.submit()
    if raw.get('entities').get(media_identifier).get('pageid'):
        return {
            'type': 'warning',
            'data': 'pre-existing sdc-data',
            'log': 'Warning: Found pre-existing SDC data, no new '
                   'data will be added. Found data: {}'.format(
                    raw.get('entities').get(media_identifier))
        }

    # upload sdc data
    summary = sdc_data.get('edit_summary',
                           'upload SDC data corresponding to recent upload')
    payload = {
        'action': 'wbeditentity',
        'format': u'json',
        'id': media_identifier,
        'data': json.dumps(sdc_payload, separators=(',', ':')),
        'token': target_site.tokens['csrf'],
        'summary': summary,
        'bot': target_site.has_right('bot')
    }

    request = target_site._simple_request(**payload)
    try:
        request.submit()
    except pywikibot.data.api.APIError as error:
        return {
            'type': 'error',
            'data': error,
            'log': '{0} Error uploading SDC data: {1}'.format(
                file_page.title(), error)
        }


def format_sdc_payload(target_site, data):
    """
    Translate from internal sdc data format to that expected by MediaWiki.

    This takes no responsibility for validating the passed in sdc data.

    @param target_site: pywikibot.Site object to which file was uploaded
    @param data: internally formatted sdc data.
    @return dict formated sdc data payload
    """
    allowed_non_property_keys = ('caption', 'summary')
    payload = dict()

    if data.get('caption'):
        payload['labels'] = dict()
        for k, v in data['caption'].items():
            payload['labels'][k] = {'language': k, 'value': v}

    if not set(data.keys()) - set(allowed_non_property_keys):
        return payload
    payload['claims'] = []
    prop_data = {key: data[key] for key in data.keys() if is_prop_key(key)}
    for prop, value in prop_data.items():
        if isinstance(value, list):
            for v in value:
                claim = make_claim(v, prop, target_site)
                payload['claims'].append(claim.toJSON())
        else:
            claim = make_claim(value, prop, target_site)
            payload['claims'].append(claim.toJSON())
    return payload


def make_claim(value, prop, target_site):
    """
    Create a pywikibot Claim representation of the internally formatted value.

    @param value: str|dict The internally formatted claim value
    @param prop: str Property of the claim
    @param target_site: pywikibot.Site to which SDC is uploaded
    @return: pywikibot.Claim
    """
    repo = target_site.data_repository()
    claim = pywikibot.Claim(repo, prop)
    if common.is_str(value):
        claim.setTarget(format_claim_value(claim, value, target_site))
    elif isinstance(value, dict):
        set_dict_claim_value(value, claim, target_site)
    else:
        raise ValueError(
            'Incorrectly formatted property value: {}'.format(value))
    return claim


def set_dict_claim_value(value, claim, target_site):
    """
    Populate a more complex claim.

    A complex claim is either one with a multi-part data type, or with the
    prominent flag or with qualifiers.

    @param value: str|dict The internally formatted claim value
    @param claim: pywikibot.Claim for which value is being set
    @param target_site: pywikibot.Site to which SDC is uploaded
    @return: pywikibot.Claim
    """
    # more complex data types or values with e.g. qualifiers
    claim.setTarget(format_claim_value(claim, value['_'], target_site))

    # set prominent flag
    if value.get('prominent'):
        claim.setRank('preferred')

    # add qualifiers
    qual_prop_data = {key: value[key] for key in value.keys()
                      if is_prop_key(key)}
    for qual_prop, qual_value in qual_prop_data.items():
        if isinstance(qual_value, list):
            for q_v in qual_value:
                claim.addQualifier(
                    format_qualifier_claim_value(
                        q_v, qual_prop, claim, target_site))
        else:
            claim.addQualifier(
                format_qualifier_claim_value(
                    qual_value, qual_prop, claim, target_site))
    return claim


def format_qualifier_claim_value(value, prop, claim, target_site):
    """
    Populate a more complex claim.

    A complex claim is either one with a multi-part data type, or with the
    prominent flag or with qualifiers.

    @param value: str|dict The internally formatted qualifier value
    @param prop: str Property of qualifier
    @param claim: pywikibot.Claim to which qualifier is being added
    @param target_site: pywikibot.Site to which SDC is uploaded
    @return: pywikibot.Claim
    """
    if common.is_str(value) or isinstance(value, dict):
        qual_claim = pywikibot.Claim(claim.repo, prop)
        qual_claim.setTarget(
            format_claim_value(qual_claim, value, target_site))
        return qual_claim
    else:
        raise ValueError(
            'Incorrectly formatted qualifier: {}'.format(value))


def format_claim_value(claim, value, target_site):
    """
    Reformat the internal claim as the relevant pywikibot object.

    @param claim: pywikibot.Claim to which value should be added
    @param value: str och dict encoding the value to be added
    @param target_site: pywikibot.Site to which sdc data is being added
    @return pywikibot representation of the claim value
    """
    repo = target_site.data_repository()
    if claim.type == 'wikibase-item':
        return pywikibot.ItemPage(repo, value)
    elif claim.type == 'commonsMedia':
        return pywikibot.FilePage(target_site, value)
    elif claim.type == 'geo-shape':
        return pywikibot.WbGeoShape(pywikibot.Page(target_site, value))
    elif claim.type == 'tabular-data':
        return pywikibot.WbTabularData(pywikibot.Page(target_site, value))
    elif claim.type == 'monolingualtext':
        return pywikibot.WbMonolingualText(
            value.get('text'), value.get('lang'))
    elif claim.type == 'globe-coordinate':
        return pywikibot.Coordinate(value.get('lat'), value.get('lon'))
    elif claim.type == 'quantity':
        if isinstance(value, dict):
            return pywikibot.WbQuantity(
                value.get('amount'),
                pywikibot.ItemPage(repo, value.get('unit')))
        else:
            return pywikibot.WbQuantity(value)
    elif claim.type == 'time':
        try:
            # note that Wikidata only supports precision down to day
            datetimestr = '+{}Z'.format(value.lstrip('+0').rstrip('Z'))
            return pywikibot.WbTime.fromTimestr(datetimestr, precision=11)
        except ValueError:
            return iso_to_wbtime(value)

    # simple strings/numbers
    return value


def is_prop_key(key):
    """
    Check that a key is a valid property reference.

    @param key: key to test
    @return if key is a valid property reference
    """
    return (
        common.is_str(key)
        and key[0] == 'P'
        and common.is_pos_int(key[1:]))


# copied from wikidataStuff.helpers.iso_to_wbtime
def iso_to_wbtime(date):
    """
    Convert ISO date string into WbTime object.

    Given an ISO date object (1922-09-17Z or 2014-07-11T08:14:46Z)
    this returns the equivalent WbTime object

    @param item: An ISO date string
    @type item: basestring
    @return: The converted result
    @rtype: pywikibot.WbTime
    """
    date = date[:len('YYYY-MM-DD')].split('-')
    if len(date) == 3 and all(common.is_int(x) for x in date):
        # 1921-09-17Z or 2014-07-11T08:14:46Z
        d = int(date[2])
        if d == 0:
            d = None
        m = int(date[1])
        if m == 0:
            m = None
        return pywikibot.WbTime(
            year=int(date[0]),
            month=m,
            day=d)
    elif len(date) == 1 and common.is_int(date[0][:len('YYYY')]):
        # 1921Z
        return pywikibot.WbTime(year=int(date[0][:len('YYYY')]))
    elif (len(date) == 2
            and all(common.is_int(x) for x in (date[0], date[1][:len('MM')]))):
        # 1921-09Z
        m = int(date[1][:len('MM')])
        if m == 0:
            m = None
        return pywikibot.WbTime(
            year=int(date[0]),
            month=m)

    # once here all interpretations have failed
    raise pywikibot.Error(
        'An invalid ISO-date string received: {}'.format(date))

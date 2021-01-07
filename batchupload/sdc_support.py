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


def upload_single_sdc_data(target_site, file_page, sdc_data, result):
    """
    Upload the Structured Data corresponding to the recently uploaded file.

    @param target_site: pywikibot.Site object to which file should be uploaded
    @param file_page: pywikibot.FilePage object corresponding to the
        recently uploaded file
    @param sdc_data: internally formatted Structured data in json format
    @param result: joint result dict for media file and sdc upload
    """
    media_identifier = 'M{}'.format(file_page.pageid)
    sdc_payload = format_sdc_payload(target_site, sdc_data)

    # verify that there is no data yet
    request = target_site._simple_request(
        action='wbgetentities', ids=media_identifier)
    raw = request.submit()
    if raw.get('entities').get(media_identifier).get('pageid'):
        result['warning'] = 'pre-existing sdc-data'
        result['log'] += '\n\tWarning: Found pre-existing SDC data, no new ' \
            'data will be added. Found data: '.format(
            raw.get('entities').get(media_identifier))
        return

    # upload sdc data
    summary = sdc_data.get('comment',
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
        result['error'] = error
        result['log'] += '\n\t{0} Error uploading SDC data: {1}'.format(
            file_page.title(), error)


def format_sdc_payload(target_site, data):
    """
    Translate from internal sdc data format to that expected by MediaWiki.

    This takes no responsibility for validating the passed in sdc data.

    @param target_site: pywikibot.Site object to which file was uploaded
    @param data: internally formatted sdc data.
    @return dict formated sdc data payload
    """
    allowed_non_property_keys = ('caption', 'summary')
    repo = target_site.data_repository()
    payload = dict()

    if data.get('caption'):
        payload['labels'] = dict()
        for k, v in data['captions'].items():
            payload['labels'][k] = {'language': k, 'value': v}

    if not set(data.keys()) - set(allowed_non_property_keys):
        return payload
    payload['claims'] = []
    prop_data = {key: data[key] for key in data.keys() if is_prop_key(key)}
    for prop, value in prop_data.items():
        claim = pywikibot.Claim(repo, prop)
        if common.is_str(value):
            claim.setTarget(format_claim_value(claim, value, target_site))
        elif isinstance(value, list):
            # multiple values for same property
            raise NotImplementedError
        elif isinstance(value, dict):
            # more complex data types or values with e.g. qualifiers
            claim.setTarget(format_claim_value(claim, value['_'], target_site))
            # set prominent flag
            if value.get('prominent'):
                claim.setRank('preferred')
            # add qualifiers
            qual_prop_data = {key: value[key] for key in value.keys()
                              if is_prop_key(key)}
            for qual_prop, qual_value in qual_prop_data.items():
                qual_claim = pywikibot.Claim(repo, qual_prop)
                if common.is_str(qual_value):
                    qual_claim.setTarget(
                        format_claim_value(
                            qual_claim, qual_value, target_site))
                elif isinstance(qual_value, list):
                    # multiple values for same property
                    raise NotImplementedError
                elif isinstance(qual_value, dict):
                    # more complex data types or values with e.g. qualifiers
                    qual_claim.setTarget(
                        format_claim_value(
                            qual_claim, qual_value['_'], target_site))
                claim.addQualifier(qual_claim)
        payload['claims'].append(claim.toJSON())
    return payload


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
        return pywikibot.WbQuantity(
            value.get('amount'),
            pywikibot.ItemPage(repo, value.get('unit')))
    elif claim.type == 'time':
        # pywikibot.WbTime - @see wikidataStuff.helpers.iso_to_wbtime
        raise NotImplementedError

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
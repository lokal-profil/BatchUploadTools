# -*- coding: utf-8  -*-
"""Unit tests for converters."""

import unittest
from batchupload.common import (
    strip_dict_entries,
    get_all_template_entries,
    MyError
)


class TestStripDictEntries(unittest.TestCase):

    """Test the strip_dict_entries method."""

    def test_strip_dict_entries_empty_dict(self):
        self.assertEquals(strip_dict_entries({}), {})

    def test_strip_dict_entries(self):
        input_value = {'id': 'identifiant'}
        expected = {u'id': u'identifiant'}
        self.assertEquals(strip_dict_entries(input_value), expected)

    def test_strip_dict_entries_with_whitespace_in_key(self):
        input_value = {' id\n ': 'identifiant'}
        expected = {u'id': u'identifiant'}
        self.assertEquals(strip_dict_entries(input_value), expected)

    def test_strip_dict_entries_with_whitespace_in_value(self):
        input_value = {'id': ' \t\nidentifiant '}
        expected = {u'id': u'identifiant'}
        self.assertEquals(strip_dict_entries(input_value), expected)

    def test_strip_dict_entries_ignore_non_string_values(self):
        input_value = {'int': 5, 'list': ['aa', ' aa']}
        expected = {u'int': 5, u'list': ['aa', ' aa']}
        self.assertEquals(strip_dict_entries(input_value), expected)

    def test_strip_dict_entries_error_on_non_dict(self):
        input_value = 'a string'
        with self.assertRaises(MyError) as cm:
            strip_dict_entries(input_value)
        self.assertEquals(cm.exception.value,
                          'strip_dict_entries() expects a dictionary object'
                          'as input but found "str"')


class TestGetAllTemplateEntries(unittest.TestCase):

    """Test the get_all_template_entries method."""

    def test_get_all_template_entries_empty(self):
        self.assertEquals(get_all_template_entries('', ''), [])

    def test_get_all_template_entries_single(self):
        template = 'a'
        wikitext = u'{{a|A|b=b|c={{c|c=pling}}}}'
        expected = [{u'1': u'A', u'c': u'{{c|c=pling}}', u'b': u'b'}]
        self.assertListEqual(get_all_template_entries(wikitext, template),
                             expected)

    def test_get_all_template_entries_multiple(self):
        template = 'a'
        wikitext = u'{{a|b=b}} {{a|b=b}} {{a|c}}'
        expected = [{u'b': u'b'}, {u'b': u'b'}, {u'1': u'c'}]
        self.assertListEqual(get_all_template_entries(wikitext, template),
                             expected)

#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Unit tests for helpers.py."""
from __future__ import unicode_literals
import unittest
from collections import OrderedDict

from batchupload.helpers import (
    flip_name,
    flip_names,
    get_all_template_entries,
    cleanString,
    output_block_template
)


class TestFlipName(unittest.TestCase):

    """Test the flip_name method."""

    def test_flip_name_empty(self):
        self.assertEqual(flip_name(''), '')

    def test_flip_name_one_part(self):
        input_value = 'The Name'
        expected = 'The Name'
        self.assertEqual(flip_name(input_value), expected)

    def test_flip_name_two_parts(self):
        input_value = 'Last, First'
        expected = 'First Last'
        self.assertEqual(flip_name(input_value), expected)

    def test_flip_name_three_parts(self):
        input_value = 'Last, Middle, First'
        expected = 'Last, Middle, First'
        self.assertEqual(flip_name(input_value), expected)


class TestFlipNames(unittest.TestCase):

    """Test the flip_names method."""

    def test_flip_names_empty(self):
        self.assertEqual(flip_names([]), [])

    # @TODO: add test counting calls to flip_names and number/content of output


class TestGetAllTemplateEntries(unittest.TestCase):

    """Test the get_all_template_entries method."""

    def test_get_all_template_entries_empty(self):
        self.assertEqual(get_all_template_entries('', ''), [])

    def test_get_all_template_entries_single(self):
        template = 'a'
        wikitext = '{{a|A|b=b|c={{c|c=pling}}}}'
        expected = [{'1': 'A', 'c': '{{c|c=pling}}', 'b': 'b'}]
        self.assertListEqual(get_all_template_entries(wikitext, template),
                             expected)

    def test_get_all_template_entries_multiple(self):
        template = 'a'
        wikitext = '{{a|b=b}} {{a|b=b}} {{a|c}}'
        expected = [{'b': 'b'}, {'b': 'b'}, {'1': 'c'}]
        self.assertListEqual(get_all_template_entries(wikitext, template),
                             expected)


class TestCleanString(unittest.TestCase):

    """Test the cleanString method."""

    def test_clean_string_empty(self):
        self.assertEqual(cleanString(''), '')

    def test_clean_string_normal_whitespace(self):
        test_string = ' a\tb\nc\xa0d  '
        expected = 'a b c d'
        self.assertEqual(cleanString(test_string), expected)

    def test_clean_string_unusual_whitespace(self):
        test_string = 'a\x8fb'
        expected = 'a b'
        self.assertEqual(cleanString(test_string), expected)

    def test_clean_string_brackets(self):
        test_string = '[{()}]'
        expected = '((()))'
        self.assertEqual(cleanString(test_string), expected)

    def test_clean_string_separators(self):
        test_string = '#|/\\'
        expected = '----'
        self.assertEqual(cleanString(test_string), expected)

    def test_clean_string_colons(self):
        test_string = ':s,a: ,:'
        expected = 's,a, ,-'
        self.assertEqual(cleanString(test_string), expected)


class TestOutputBlockTemplate(unittest.TestCase):

    """Test the output_block_template method."""

    def setUp(self):
        self.name = 'TemplateName'
        self.data = OrderedDict()
        self.data['param1'] = 'text1'
        self.data['param10'] = 'text10'
        self.data['param100'] = 'text100'

    def test_output_block_template_empty(self):
        expected = "{{\n}}"
        self.assertEqual(output_block_template('', {}, 0), expected)

    def test_output_block_template_unordered_dict(self):
        data = {'param1': 'text1'}
        expected = "{{TemplateName\n" \
                   "| param1 = text1\n" \
                   "}}"
        self.assertEqual(
            output_block_template(self.name, data, 0),
            expected)

    def test_output_block_template_set_padding(self):
        expected = "{{TemplateName\n" \
                   "| param1        = text1\n" \
                   "| param10       = text10\n" \
                   "| param100      = text100\n" \
                   "}}"
        self.assertEqual(
            output_block_template(self.name, self.data, 15),
            expected)

    def test_output_block_template_no_padding(self):
        expected = "{{TemplateName\n" \
                   "| param1 = text1\n" \
                   "| param10 = text10\n" \
                   "| param100 = text100\n" \
                   "}}"
        self.assertEqual(
            output_block_template(self.name, self.data, 0),
            expected)

    def test_output_block_template_auto_padding(self):
        expected = "{{TemplateName\n" \
                   "| param1   = text1\n" \
                   "| param10  = text10\n" \
                   "| param100 = text100\n" \
                   "}}"
        self.assertEqual(
            output_block_template(self.name, self.data, None),
            expected)

    def test_output_block_template_ommit_entry(self):
        self.data['special'] = None
        expected = "{{TemplateName\n" \
                   "| param1   = text1\n" \
                   "| param10  = text10\n" \
                   "| param100 = text100\n" \
                   "}}"
        self.assertEqual(
            output_block_template(self.name, self.data, None),
            expected)

    def test_output_block_template_empty_entry(self):
        self.data['special'] = ''
        expected = "{{TemplateName\n" \
                   "| param1   = text1\n" \
                   "| param10  = text10\n" \
                   "| param100 = text100\n" \
                   "| special  = \n" \
                   "}}"
        self.assertEqual(
            output_block_template(self.name, self.data, None),
            expected)

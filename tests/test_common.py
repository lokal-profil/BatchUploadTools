# -*- coding: utf-8  -*-
"""Unit tests for converters."""

import unittest
import tempfile
import os
import json
from batchupload.common import (
    strip_dict_entries,
    strip_list_entries,
    get_all_template_entries,
    is_int,
    is_pos_int,
    open_and_read_file,
    open_and_write_file,
    MyError
)


class TestStripDictEntries(unittest.TestCase):

    """Test the strip_dict_entries method."""

    def test_strip_dict_entries_empty_dict(self):
        self.assertEquals(strip_dict_entries({}), {})

    def test_strip_dict_entries(self):
        input_value = {'id': 'identifier'}
        expected = {u'id': u'identifier'}
        self.assertEquals(strip_dict_entries(input_value), expected)

    def test_strip_dict_entries_with_whitespace_in_key(self):
        input_value = {' id\n ': 'identifier'}
        expected = {u'id': u'identifier'}
        self.assertEquals(strip_dict_entries(input_value), expected)

    def test_strip_dict_entries_with_whitespace_in_value(self):
        input_value = {'id': ' \t\nidentifier '}
        expected = {u'id': u'identifier'}
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


class TestStriplistEntries(unittest.TestCase):

    """Test the strip_list_entries method."""

    def test_strip_list_entries_empty_list(self):
        self.assertEquals(strip_list_entries([]), [])

    def test_strip_list_entries(self):
        input_value = ['id', 'identifier']
        expected = ['id', 'identifier']
        self.assertEquals(strip_list_entries(input_value), expected)

    def test_strip_list_entries_with_whitespace(self):
        input_value = [' id\n', 'identifier']
        expected = ['id', 'identifier']
        self.assertEquals(strip_list_entries(input_value), expected)

    def test_strip_list_entries_ignore_non_string_values(self):
        input_value = [5, ['aa', ' aa']]
        expected = [5, ['aa', ' aa']]
        self.assertEquals(strip_list_entries(input_value), expected)

    def test_strip_list_entries_error_on_non_list(self):
        input_value = 'a string'
        with self.assertRaises(MyError) as cm:
            strip_list_entries(input_value)
        self.assertEquals(cm.exception.value,
                          'strip_list_entries() expects a list object'
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


class TestIsInt(unittest.TestCase):

    """Test the is_int method."""

    def test_empty_string_fail(self):
        s = ''
        result = is_int(s)
        self.assertEqual(result, False)

    def test_none_fail(self):
        s = None
        result = is_int(s)
        self.assertEqual(result, False)

    def test_random_string_fail(self):
        s = 'random_string'
        result = is_int(s)
        self.assertEqual(result, False)

    def test_float_fail(self):
        s = '123.456'
        result = is_int(s)
        self.assertEqual(result, False)

    def test_valid_negative_int_succeed(self):
        s = '-123'
        result = is_int(s)
        self.assertEqual(result, True)

    def test_valid_int_succeed(self):
        s = '123'
        result = is_int(s)
        self.assertEqual(result, True)


class TestIsPosInt(unittest.TestCase):

    """Test the is_pos_int method."""

    def test_empty_string_fail(self):
        s = ''
        result = is_pos_int(s)
        self.assertEqual(result, False)

    def test_none_fail(self):
        s = None
        result = is_pos_int(s)
        self.assertEqual(result, False)

    def test_random_string_fail(self):
        s = 'random_string'
        result = is_pos_int(s)
        self.assertEqual(result, False)

    def test_float_fail(self):
        s = '123.456'
        result = is_pos_int(s)
        self.assertEqual(result, False)

    def test_negative_int_fail(self):
        s = '-123'
        result = is_pos_int(s)
        self.assertEqual(result, False)

    def test_valid_int_succeed(self):
        s = '123'
        result = is_pos_int(s)
        self.assertEqual(result, True)


class TestOpenFileBase(unittest.TestCase):

    """Test base for open_and_read_file() and open_and_write_file()."""

    def setUp(self):
        # Create a temporary file
        self.test_data = u'{"list": ["a", "b", "c"], "två": "2", "ett": 1}'
        self.test_infile = tempfile.NamedTemporaryFile()
        self.test_outfile = tempfile.NamedTemporaryFile(delete=False)
        self.test_infile.write(self.test_data.encode('utf-8'))
        self.test_infile.seek(0)

    def tearDown(self):
        # Closes and removes the file
        self.test_infile.close()
        os.remove(self.test_outfile.name)


class TestOpenReadFile(TestOpenFileBase):

    """Test open_and_read_file()."""

    def test_read_data(self):
        expected_data = u'{"list": ["a", "b", "c"], "två": "2", "ett": 1}'
        result = open_and_read_file(self.test_infile.name)
        self.assertEquals(result, expected_data)

    def test_read_json_data(self):
        expected_data = {'list': ['a', 'b', 'c'], u'två': '2', 'ett': 1}
        result = open_and_read_file(self.test_infile.name, as_json=True)
        self.assertItemsEqual(result, expected_data)


class TestOpenWriteFile(TestOpenFileBase):

    """Test open_and_read_file()."""

    def test_write_data(self):
        to_write = u'{"list": ["a", "b", "c"], "två": "2", "ett": 1}'
        open_and_write_file(self.test_outfile.name, to_write)
        self.assertEquals(self.test_outfile.read(),
                          self.test_data.encode('utf-8'))

    def test_write_json_data(self):
        to_write = {'list': ['a', 'b', 'c'], u'två': '2', 'ett': 1}
        open_and_write_file(self.test_outfile.name, to_write, as_json=True)
        self.assertItemsEqual(json.loads(self.test_outfile.read()),
                              json.loads(self.test_data.encode('utf-8')))

# -*- coding: utf-8  -*-
"""Unit tests for converters.

TODO:
* Test smaller csv functions
* rebuild using mock instead of tempfile,
** mocking open_and_read_file() and open_and_write_file()
"""
from __future__ import unicode_literals
from builtins import object
import unittest
import tempfile
import os
from batchupload.common import (
    MyError,
    deep_sort,
    strip_list_entries
)
from batchupload.csv_methods import (
    csv_file_to_dict,
    open_csv_file,
    dict_to_csv_file,
)


class CustomAssertions(object):
    """Custom assertions."""

    @staticmethod
    def sort_lines(text):
        """Sort the lines of a text."""
        return '\n'.join(sorted(text.split('\n')))

    def assert_equal_with_unordered_lines(self, first, second, msg=None):
        """
        Assert that two strings are equal, up to the order of any lines.

        :param first: a string
        :param second: a string
        """
        self.assertEqual(CustomAssertions.sort_lines(first),
                         CustomAssertions.sort_lines(second),
                         msg=msg)


class TestCSVFileBase(unittest.TestCase):

    """Test base for open_csv_file, csv_file_to_dict and dict_to_csv_file."""

    def setUp(self, test_header=None, test_in_data=None):
        # Create a temporary file
        self.test_header = test_header or 'ett|två|tre|fyra|fem|lista'
        # Testdata has the folowing features
        # empty line at the end
        # trailing and leading whitespace on the line
        # an empty cell
        # trailing and leading whitespace in a cell
        # an empty list entry
        # trailing and leading whitespace in a list entry
        self.test_in_data = test_in_data or \
            'ett|två|tre|fyra|fem|lista\n' \
            ' 1|2|3|4||1;2;3;;4;5 \n' \
            'a1|a2| a3 |a4|a5|a1;a2; a3 ;a4;a5\n'
        self.test_out_data = \
            'ett|två|tre|fyra|fem|lista\n' \
            '1|2|3|4|5|1;2;3;4;5\n' \
            'a1|a2|a3|a4|a5|a1;a2;a3;a4;a5\n'
        self.test_infile = tempfile.NamedTemporaryFile()
        self.test_outfile = tempfile.NamedTemporaryFile(delete=False)
        self.test_infile.write(self.test_in_data.encode('utf-8'))
        self.test_infile.seek(0)

    def tearDown(self):
        # Closes and removes the file
        self.test_infile.close()
        os.remove(self.test_outfile.name)


class TestOpenCSVFile(TestCSVFileBase):

    """Test open_csv_file()."""

    def test_read_data(self):
        expected_header = self.test_header.split('|')
        expected_lines = [
            '1|2|3|4||1;2;3;;4;5',
            'a1|a2| a3 |a4|a5|a1;a2; a3 ;a4;a5'
        ]
        result_header, result_lines = open_csv_file(self.test_infile.name)
        self.assertEqual(result_header, expected_header)
        self.assertEqual(result_lines, expected_lines)


class TestCSVFileToDict(TestCSVFileBase):

    """Test csv_file_to_dict()."""

    def test_read_data(self):
        key_col = self.test_header.split('|')[1]
        expected = {
            '2': {
                'ett': '1', 'lista': '1;2;3;;4;5', 'fem': '',
                'tre': '3', 'två': '2', 'fyra': '4'},
            'a2': {
                'lista': 'a1;a2; a3 ;a4;a5',
                'ett': 'a1', 'fem': 'a5', 'tre': 'a3',
                'två': 'a2', 'fyra': 'a4'}}
        result = csv_file_to_dict(self.test_infile.name, key_col,
                                  self.test_header)
        self.assertDictEqual(result, expected)

    def test_read_list_data(self):
        key_col = self.test_header.split('|')[1]
        lists = ('lista', )
        expected = {
            '2': {
                'ett': '1',
                'lista': ['1', '2', '3', '4', '5'],
                'fem': '', 'tre': '3', 'två': '2', 'fyra': '4'},
            'a2': {
                'lista': ['a1', 'a2', 'a3', 'a4', 'a5'],
                'ett': 'a1', 'fem': 'a5', 'tre': 'a3',
                'två': 'a2', 'fyra': 'a4'}}
        result = csv_file_to_dict(self.test_infile.name, key_col,
                                  self.test_header, lists=lists)
        self.assertDictEqual(result, expected)

    def test_read_data_tuple_key_col(self):
        key_col = ('ett', 'två')
        expected = {
            '1:2': {
                'ett': '1', 'lista': '1;2;3;;4;5', 'fem': '',
                'tre': '3', 'två': '2', 'fyra': '4'},
            'a1:a2': {
                'lista': 'a1;a2; a3 ;a4;a5',
                'ett': 'a1', 'fem': 'a5', 'tre': 'a3',
                'två': 'a2', 'fyra': 'a4'}}
        result = csv_file_to_dict(self.test_infile.name, key_col,
                                  self.test_header)
        self.assertDictEqual(result, expected)


class TestCSVFileToDictNonUnique(TestCSVFileBase):

    """Test csv_file_to_dict() with non-unique columns."""

    def setUp(self):
        # set up data with non-unique columns
        test_header = 'ett|ett|tre|fyra|lista|lista'
        test_in_data = \
            'ett|ett|tre|fyra|lista|lista\n' \
            ' 1|2|3|4||1;2;3;;4;5 \n' \
            'a1|a2| a3 |a4|a5|a1;a2; a3 ;a4;a5\n'
        super(TestCSVFileToDictNonUnique, self).setUp(
            test_header=test_header, test_in_data=test_in_data)

    def test_read_non_unique_data(self):
        key_col = 'tre'
        lists = ('lista', )
        expected = {
            '3': {
                'ett': ['1', '2'],
                'lista': ['1', '2', '3', '4', '5'],
                'tre': '3', 'fyra': '4'},
            'a3': {
                'ett': ['a1', 'a2'],
                'lista': ['a1', 'a2', 'a3', 'a4', 'a5', 'a5'],
                'tre': 'a3', 'fyra': 'a4'}}
        result = csv_file_to_dict(self.test_infile.name, key_col,
                                  self.test_header, lists=lists,
                                  non_unique=True)
        self.assertEqual(deep_sort(result),
                         deep_sort(expected))

    def test_read_non_unique_data_unexpected_error(self):
        key_col = 'tre'
        expected_msg = 'Unexpected non-unique columns found'
        expected_items = sorted(['lista', 'ett'])
        with self.assertRaises(MyError) as cm:
            csv_file_to_dict(self.test_infile.name, key_col,
                             self.test_header, non_unique=False)
        # ensure error message is the same
        result_msg, _, result_items = cm.exception.value.partition(':')
        result_items = strip_list_entries(result_items.split(','))
        self.assertEqual(result_msg, expected_msg)
        self.assertEqual(sorted(result_items), expected_items)


class TestDictToCSVFile(TestCSVFileBase, CustomAssertions):

    """Test dict_to_csv_file()."""

    def test_write_data(self):
        test_data = {
            '2': {
                'ett': '1', 'lista': '1;2;3;4;5', 'fem': '5',
                'tre': '3', 'två': '2', 'fyra': '4'},
            'a2': {
                'lista': 'a1;a2;a3;a4;a5',
                'ett': 'a1', 'fem': 'a5', 'tre': 'a3',
                'två': 'a2', 'fyra': 'a4'}}
        dict_to_csv_file(self.test_outfile.name,
                         test_data, self.test_header)
        self.assert_equal_with_unordered_lines(
            self.test_outfile.read().decode('utf-8'),
            self.test_out_data)

    def test_write_list_data(self):
        test_data = {
            '2': {
                'ett': '1',
                'lista': ['1', '2', '3', '4', '5'],
                'fem': '5', 'tre': '3', 'två': '2', 'fyra': '4'},
            'a2': {
                'lista': ['a1', 'a2', 'a3', 'a4', 'a5'],
                'ett': 'a1', 'fem': 'a5', 'tre': 'a3',
                'två': 'a2', 'fyra': 'a4'}}
        dict_to_csv_file(self.test_outfile.name,
                         test_data, self.test_header)
        self.assert_equal_with_unordered_lines(
            self.test_outfile.read().decode('utf-8'),
            self.test_out_data)

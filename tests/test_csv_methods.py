# -*- coding: utf-8  -*-
"""Unit tests for converters.

TODO:
* Test smaller csv functions
* rebuild using mock instead of tempfile,
** mocking open_and_read_file() and open_and_write_file()
"""

import unittest
import tempfile
import os
from batchupload.common import (
    MyError,
    deep_sort,
)
from batchupload.csv_methods import (
    csv_file_to_dict,
    open_csv_file,
    dict_to_csv_file,
)


class TestCSVFileBase(unittest.TestCase):

    """Test base for open_csv_file, csv_file_to_dict and dict_to_csv_file."""

    def setUp(self, test_header=None, test_in_data=None):
        # Create a temporary file
        self.test_header = test_header or u'ett|två|tre|fyra|fem|lista'
        # Testdata has the folowing features
        # empty line at the end
        # trailing and leading whitespace on the line
        # an empty cell
        # trailing and leading whitespace in a cell
        # an empty list entry
        # trailing and leading whitespace in a list entry
        self.test_in_data = test_in_data or \
            u'ett|två|tre|fyra|fem|lista\n' \
            u' 1|2|3|4||1;2;3;;4;5 \n' \
            u'a1|a2| a3 |a4|a5|a1;a2; a3 ;a4;a5\n'
        self.test_out_data = \
            u'ett|två|tre|fyra|fem|lista\n' \
            u'1|2|3|4|5|1;2;3;4;5\n' \
            u'a1|a2|a3|a4|a5|a1;a2;a3;a4;a5\n'
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
            u'1|2|3|4||1;2;3;;4;5',
            u'a1|a2| a3 |a4|a5|a1;a2; a3 ;a4;a5'
        ]
        result_header, result_lines = open_csv_file(self.test_infile.name)
        self.assertEquals(result_header, expected_header)
        self.assertEquals(result_lines, expected_lines)


class TestCSVFileToDict(TestCSVFileBase):

    """Test csv_file_to_dict()."""

    def test_read_data(self):
        key_col = self.test_header.split('|')[1]
        expected = {
            u'2': {
                u'ett': u'1', u'lista': u'1;2;3;;4;5', u'fem': u'',
                u'tre': u'3', u'två': u'2', u'fyra': u'4'},
            u'a2': {
                u'lista': u'a1;a2; a3 ;a4;a5',
                u'ett': u'a1', u'fem': u'a5', u'tre': u'a3',
                u'två': u'a2', u'fyra': u'a4'}}
        result = csv_file_to_dict(self.test_infile.name, key_col,
                                  self.test_header)
        self.assertDictEqual(result, expected)

    def test_read_list_data(self):
        key_col = self.test_header.split('|')[1]
        lists = ('lista', )
        expected = {
            u'2': {
                u'ett': u'1',
                u'lista': [u'1', u'2', u'3', u'4', u'5'],
                u'fem': u'', u'tre': u'3', u'två': u'2', u'fyra': u'4'},
            u'a2': {
                u'lista': [u'a1', u'a2', u'a3', u'a4', u'a5'],
                u'ett': u'a1', u'fem': u'a5', u'tre': u'a3',
                u'två': u'a2', u'fyra': u'a4'}}
        result = csv_file_to_dict(self.test_infile.name, key_col,
                                  self.test_header, lists=lists)
        self.assertDictEqual(result, expected)

    def test_read_data_tuple_key_col(self):
        key_col = (u'ett', u'två')
        expected = {
            u'1:2': {
                u'ett': u'1', u'lista': u'1;2;3;;4;5', u'fem': u'',
                u'tre': u'3', u'två': u'2', u'fyra': u'4'},
            u'a1:a2': {
                u'lista': u'a1;a2; a3 ;a4;a5',
                u'ett': u'a1', u'fem': u'a5', u'tre': u'a3',
                u'två': u'a2', u'fyra': u'a4'}}
        result = csv_file_to_dict(self.test_infile.name, key_col,
                                  self.test_header)
        self.assertDictEqual(result, expected)


class TestCSVFileToDictNonUnique(TestCSVFileBase):

    """Test csv_file_to_dict() with non-unique columns."""

    def setUp(self):
        # set up data with non-unique columns
        test_header = u'ett|ett|tre|fyra|lista|lista'
        test_in_data = \
            u'ett|ett|tre|fyra|lista|lista\n' \
            u' 1|2|3|4||1;2;3;;4;5 \n' \
            u'a1|a2| a3 |a4|a5|a1;a2; a3 ;a4;a5\n'
        super(TestCSVFileToDictNonUnique, self).setUp(
            test_header=test_header, test_in_data=test_in_data)

    def test_read_non_unique_data(self):
        key_col = u'tre'
        lists = ('lista', )
        expected = {
            u'3': {
                u'ett': [u'1', u'2'],
                u'lista': [u'1', u'2', u'3', u'4', u'5'],
                u'tre': u'3', u'fyra': u'4'},
            u'a3': {
                u'ett': [u'a1', u'a2'],
                u'lista': [u'a1', u'a2', u'a3', u'a4', u'a5', u'a5'],
                u'tre': u'a3', u'fyra': u'a4'}}
        result = csv_file_to_dict(self.test_infile.name, key_col,
                                  self.test_header, lists=lists,
                                  non_unique=True)
        self.assertEqual(deep_sort(result),
                         deep_sort(expected))

    def test_read_non_unique_data_unexpected_error(self):
        key_col = u'tre'
        with self.assertRaises(MyError) as cm:
            csv_file_to_dict(self.test_infile.name, key_col,
                             self.test_header, non_unique=False)
        self.assertEquals(cm.exception.value,
                          'Unexpected non-unique columns found: lista, ett')


class TestDictToCSVFile(TestCSVFileBase):

    """Test dict_to_csv_file()."""

    def test_write_data(self):
        test_data = {
            u'2': {
                u'ett': u'1', u'lista': u'1;2;3;4;5', u'fem': u'5',
                u'tre': u'3', u'två': u'2', u'fyra': u'4'},
            u'a2': {
                u'lista': u'a1;a2;a3;a4;a5',
                u'ett': u'a1', u'fem': u'a5', u'tre': u'a3',
                u'två': u'a2', u'fyra': u'a4'}}
        dict_to_csv_file(self.test_outfile.name,
                         test_data, self.test_header)
        self.assertEquals(self.test_outfile.read(),
                          self.test_out_data.encode('utf-8'))

    def test_write_list_data(self):
        test_data = {
            u'2': {
                u'ett': u'1',
                u'lista': [u'1', u'2', u'3', u'4', u'5'],
                u'fem': u'5', u'tre': u'3', u'två': u'2', u'fyra': u'4'},
            u'a2': {
                u'lista': [u'a1', u'a2', u'a3', u'a4', u'a5'],
                u'ett': u'a1', u'fem': u'a5', u'tre': u'a3',
                u'två': u'a2', u'fyra': u'a4'}}
        dict_to_csv_file(self.test_outfile.name,
                         test_data, self.test_header)
        self.assertEquals(self.test_outfile.read(),
                          self.test_out_data.encode('utf-8'))

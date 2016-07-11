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
from batchupload.tmp import (
    csv_file_to_dict,
    open_csv_file,
    dict_to_csv_file,
)


class TestCSVFileBase(unittest.TestCase):

    """Test base for open_csv_file, csv_file_to_dict and dict_to_csv_file."""

    def setUp(self):
        # Create a temporary file
        self.test_header = u'ett|två|tre|fyra|fem|lista'
        # the trailing newline reflects that this is added during a write+close
        test_data = u'ett|två|tre|fyra|fem|lista\n' \
                    u'1|2|3|4|5|1;2;3;4;5\n' \
                    u'a1|a2|a3|a4|a5|a1;a2;a3;a4;a5\n'
        self.test_infile = tempfile.NamedTemporaryFile()
        self.test_outfile = tempfile.NamedTemporaryFile(delete=False)
        self.test_infile.write(test_data.encode('utf-8'))
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
            u'1|2|3|4|5|1;2;3;4;5',
            u'a1|a2|a3|a4|a5|a1;a2;a3;a4;a5'
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
                u'ett': u'1', u'lista': u'1;2;3;4;5', u'fem': u'5',
                u'tre': u'3', u'två': u'2', u'fyra': u'4'},
            u'a2': {
                u'lista': u'a1;a2;a3;a4;a5',
                u'ett': u'a1', u'fem': u'a5', u'tre': u'a3',
                u'två': u'a2', u'fyra': u'a4'}}
        result = csv_file_to_dict(self.test_infile.name, key_col,
                                  self.test_header)
        self.assertItemsEqual(result, expected)

    def test_read_list_data(self):
        key_col = self.test_header.split('|')[1]
        lists = ('lista', )
        expected = {
            u'2': {
                u'ett': u'1',
                u'lista': [u'1', u'2', u'3', u'4', u'5'],
                u'fem': u'5', u'tre': u'3', u'två': u'2', u'fyra': u'4'},
            u'a2': {
                u'lista': [u'a1', u'a2', u'a3', u'a4', u'a5'],
                u'ett': u'a1', u'fem': u'a5', u'tre': u'a3',
                u'två': u'a2', u'fyra': u'a4'}}
        result = csv_file_to_dict(self.test_infile.name, key_col,
                                  self.test_header, lists=lists)
        self.assertItemsEqual(result, expected)

    def test_read_data_tuple_key_col(self):
        key_col = (u'ett', u'två')
        expected = {
            u'1:2': {
                u'ett': u'1', u'lista': u'1;2;3;4;5', u'fem': u'5',
                u'tre': u'3', u'två': u'2', u'fyra': u'4'},
            u'a1:a2': {
                u'lista': u'a1;a2;a3;a4;a5',
                u'ett': u'a1', u'fem': u'a5', u'tre': u'a3',
                u'två': u'a2', u'fyra': u'a4'}}
        result = csv_file_to_dict(self.test_infile.name, key_col,
                                  self.test_header)
        self.assertItemsEqual(result, expected)

    def test_read_non_unique_data(self):
        self.test_header.replace(u'två', u'ett').replace(u'fem', u'lista')
        key_col = self.test_header.split('|')[1]
        lists = ('lista', )
        expected = {
            u'2': {
                u'ett': [u'1', u'2'],
                u'lista': [u'1', u'2', u'3', u'4', u'5', u'5'],
                u'tre': u'3', u'fyra': u'4'},
            u'a2': {
                u'ett': [u'a1', u'a2'],
                u'lista': [u'a1', u'a2', u'a3', u'a4', u'a5', u'a5'],
                u'tre': u'a3', u'fyra': u'a4'}}
        result = csv_file_to_dict(self.test_infile.name, key_col,
                                  self.test_header, lists=lists)
        self.assertItemsEqual(result, expected)


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
        self.assertEquals(self.test_outfile.read(), self.test_infile.read())

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
        self.assertEquals(self.test_outfile.read(), self.test_infile.read())


class TestDictToCSVFileRountrip(TestCSVFileBase):

    """Test csv_file_to_dict() and dict_to_csv_file() compatibility."""

    def test_read_write_roundtrip(self):
        key_col = self.test_header.split('|')[1]
        read_data = csv_file_to_dict(self.test_infile.name, key_col,
                                     self.test_header)
        dict_to_csv_file(self.test_outfile.name,
                         read_data, self.test_header)
        self.assertEquals(self.test_outfile.read(), self.test_infile.read())

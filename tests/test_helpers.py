#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Unit tests for helpers.py."""
from __future__ import unicode_literals
import unittest
from batchupload.helpers import (
    flip_name,
    flip_names,
    sortedDict,
    addOrIncrement
)


class TestFlipName(unittest.TestCase):

    """Test the flip_name method."""

    def test_flip_name_empty(self):
        self.assertEquals(flip_name(''), '')

    def test_flip_name_one_part(self):
        input_value = 'The Name'
        expected = 'The Name'
        self.assertEquals(flip_name(input_value), expected)

    def test_flip_name_two_parts(self):
        input_value = 'Last, First'
        expected = 'First Last'
        self.assertEquals(flip_name(input_value), expected)

    def test_flip_name_three_parts(self):
        input_value = 'Last, Middle, First'
        expected = 'Last, Middle, First'
        self.assertEquals(flip_name(input_value), expected)


class TestFlipNames(unittest.TestCase):

    """Test the flip_names method."""

    def test_flip_names_empty(self):
        self.assertEquals(flip_names([]), [])

    # @TODO: add test counting calls to flip_names and number/content of output


class TestSortedDict(unittest.TestCase):

    """Test the sortedDict method."""

    def test_sorted_dict_empty(self):
        self.assertEquals(sortedDict({}), [])

    def test_sorted_dict_sort(self):
        input_value = {'a': 1, 'b': 3, 'c': 2}
        expected = [('b', 3), ('c', 2), ('a', 1)]
        self.assertEquals(sortedDict(input_value), expected)


class TestAddOrIncrement(unittest.TestCase):

    """Test the addOrIncrement method."""

    def test_add_or_increment_new_wo_key(self):
        dictionary = {}
        val = 'hej'
        expected = {'hej': 1}
        addOrIncrement(dictionary, val)
        self.assertEquals(dictionary, expected)

    def test_add_or_increment_new_w_key(self):
        dictionary = {}
        key = 'freq'
        val = 'hej'
        expected = {'hej': {'freq': 1}}
        addOrIncrement(dictionary, val, key)
        self.assertEquals(dictionary, expected)

    def test_add_or_increment_old_wo_key(self):
        dictionary = {'hej': 1}
        val = 'hej'
        expected = {'hej': 2}
        addOrIncrement(dictionary, val)
        self.assertEquals(dictionary, expected)

    def test_add_or_increment_old_w_key(self):
        dictionary = {'hej': {'freq': 1}}
        key = 'freq'
        val = 'hej'
        expected = {'hej': {'freq': 2}}
        addOrIncrement(dictionary, val, key)
        self.assertEquals(dictionary, expected)

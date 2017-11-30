#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Unit tests for make_info.py."""
from __future__ import unicode_literals
import unittest
from batchupload.make_info import make_info_page


class TestMakeInfoPage(unittest.TestCase):

    """Test the make_info_page method."""

    def setUp(self):
        self.data = {
            'info': '{{Infobox\n| param1 = value1 \n}}',
            'meta_cats': [
                'A meta_Cat'
            ],
            'cats': [
                'cat1',
                'cat2'
            ],
            'filename': 'The_filename'
        }

    def test_make_info_page(self):
        expected = (
            '{{Infobox\n| param1 = value1 \n}}\n\n'
            '<!-- Metadata categories -->\n'
            '[[Category:A meta_Cat]]'
            '\n\n'
            '<!-- Content categories -->\n'
            '[[Category:cat1]]\n'
            '[[Category:cat2]]')
        self.assertEqual(
            make_info_page(self.data),
            expected)

    def test_make_info_page_preview(self):
        expected = (
            "Filename: The_filename.<ext>\n"
            "{{Infobox\n| param1 = value1 \n}}\n\n"
            "''Metadata categories:''\n"
            "* [[:Category:A meta_Cat]]"
            "\n\n"
            "''Content categories:''\n"
            "* [[:Category:cat1]]\n"
            "* [[:Category:cat2]]")
        self.assertEqual(
            make_info_page(self.data, preview=True),
            expected)

    def test_make_info_page_no_meta_cats(self):
        self.data['meta_cats'] = []
        expected = (
            '{{Infobox\n| param1 = value1 \n}}\n\n'
            '<!-- Content categories -->\n'
            '[[Category:cat1]]\n'
            '[[Category:cat2]]')
        self.assertEqual(
            make_info_page(self.data),
            expected)

    def test_make_info_page_no_content_cats(self):
        self.data['cats'] = []
        expected = (
            '{{Infobox\n| param1 = value1 \n}}\n\n'
            '<!-- Metadata categories -->\n'
            '[[Category:A meta_Cat]]')
        self.assertEqual(
            make_info_page(self.data),
            expected)

    def test_make_info_page_no_cats(self):
        self.data['meta_cats'] = []
        self.data['cats'] = []
        expected = '{{Infobox\n| param1 = value1 \n}}'
        self.assertEqual(
            make_info_page(self.data),
            expected)

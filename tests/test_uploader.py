#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Unit tests for uploader.py."""
from __future__ import unicode_literals
import unittest

from batchupload.common import MyError
from batchupload.uploader import verify_url_file_extension


class TestVerifyUrlFileExtension(unittest.TestCase):

    """Test the verify_url_file_extension method."""

    def setUp(self):
        self.file_exts = ('.tif', '.jpg', '.tiff', '.jpeg')
        self.protocols = ('http', 'https')

    def test_verify_url_file_extension_empty(self):
        expected_error = ': Found url with a disallowed protocol'
        with self.assertRaises(MyError) as cm:
            verify_url_file_extension('', tuple(), tuple())
        self.assertEqual(
            cm.exception.value, expected_error)

    def test_verify_url_file_extension_no_ext(self):
        expected_error = 'https://github.com/lokal-profil/BatchUploadTools: Found url without a file extension'  # noqa E501
        url = 'https://github.com/lokal-profil/BatchUploadTools'
        with self.assertRaises(MyError) as cm:
            verify_url_file_extension(url, self.file_exts)
        self.assertEqual(
            cm.exception.value, expected_error)

    def test_verify_url_file_extension_dissalowed_ext(self):
        expected_error = 'https://github.com/lokal-profil/BatchUploadTools.txt: Found url with a disallowed file extension (.txt)'  # noqa E501
        url = 'https://github.com/lokal-profil/BatchUploadTools.txt'
        with self.assertRaises(MyError) as cm:
            verify_url_file_extension(url, self.file_exts)
        self.assertEqual(
            cm.exception.value, expected_error)

    def test_verify_url_file_extension_dissalowed_protocol(self):
        expected_error = 'ftp://github.com/lokal-profil/BatchUploadTools.jpg: Found url with a disallowed protocol'  # noqa E501
        url = 'ftp://github.com/lokal-profil/BatchUploadTools.jpg'
        with self.assertRaises(MyError) as cm:
            verify_url_file_extension(url, self.file_exts, self.protocols)
        self.assertEqual(
            cm.exception.value, expected_error)

    def test_verify_url_file_extension_ok(self):
        url = 'https://github.com/lokal-profil/BatchUploadTools.jpg'
        ext = verify_url_file_extension(url, self.file_exts, self.protocols)
        self.assertEqual(ext, '.jpg')

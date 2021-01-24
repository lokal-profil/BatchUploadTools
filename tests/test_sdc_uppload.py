#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Unit tests for helpers.py."""
from __future__ import unicode_literals
import unittest
import mock

import pywikibot

from batchupload.sdc_support import (
    is_prop_key,
    iso_to_wbtime,
    coord_precision,
    merge_strategy
)


class TestIsPropKey(unittest.TestCase):
    """Test the is_prop_key method."""

    def test_is_prop_key_empty_fail(self):
        self.assertFalse(is_prop_key(''))

    def test_is_prop_key_short_pid(self):
        self.assertTrue(is_prop_key('P1'))

    def test_is_prop_key_long_pid(self):
        self.assertTrue(is_prop_key('P968434'))

    def test_is_prop_key_qid_fail(self):
        self.assertFalse(is_prop_key('Q42'))

    def test_is_prop_key_p_fail(self):
        self.assertFalse(is_prop_key('P'))

    def test_is_prop_key_int_fail(self):
        self.assertFalse(is_prop_key('42'))


class TestIsoToWbtime(unittest.TestCase):
    """Test the iso_to_wbtime method."""

    def test_iso_to_wbtime_empty_raises(self):
        with self.assertRaises(pywikibot.Error):
            iso_to_wbtime('')

    def test_iso_to_wbtime_invalid_date_raises(self):
        with self.assertRaises(pywikibot.Error):
            iso_to_wbtime('late 1980s')

    def test_iso_to_wbtime_date_and_time(self):
        date = '2014-07-11T08:14:46Z'
        expected = pywikibot.WbTime(year=2014, month=7, day=11)
        self.assertEqual(iso_to_wbtime(date), expected)

    def test_iso_to_wbtime_date_and_timezone(self):
        date = '2014-07-11Z'
        expected = pywikibot.WbTime(year=2014, month=7, day=11)
        self.assertEqual(iso_to_wbtime(date), expected)

    def test_iso_to_wbtime_date(self):
        date = '2014-07-11'
        expected = pywikibot.WbTime(year=2014, month=7, day=11)
        self.assertEqual(iso_to_wbtime(date), expected)

    def test_iso_to_wbtime_year_and_timezone(self):
        date = '2014Z'
        expected = pywikibot.WbTime(year=2014)
        self.assertEqual(iso_to_wbtime(date), expected)

    def test_iso_to_wbtime_year(self):
        date = '2014'
        expected = pywikibot.WbTime(year=2014)
        self.assertEqual(iso_to_wbtime(date), expected)

    def test_iso_to_wbtime_year_month_and_timezone(self):
        date = '2014-07Z'
        expected = pywikibot.WbTime(year=2014, month=7)
        self.assertEqual(iso_to_wbtime(date), expected)

    def test_iso_to_wbtime_year_month(self):
        date = '2014-07'
        expected = pywikibot.WbTime(year=2014, month=7)
        self.assertEqual(iso_to_wbtime(date), expected)


class TestCoordPrecision(unittest.TestCase):
    """Test the coord_precision method."""

    def test_coord_precision_empty_raises(self):
        with self.assertRaises(ValueError):
            coord_precision('')

    def test_coord_precision_float_raises(self):
        with self.assertRaises(ValueError):
            coord_precision(0.200)

    def test_coord_precision_dms_raises(self):
        with self.assertRaises(ValueError):
            coord_precision("15°10'15''")

    def test_coord_precision_zero(self):
        self.assertEqual(coord_precision('0'), 1)

    def test_coord_precision_decimal_zero(self):
        self.assertEqual(coord_precision('0.0'), 0.1)

    def test_coord_precision_one(self):
        self.assertEqual(coord_precision('1'), 1)

    def test_coord_precision_decimal_one(self):
        self.assertEqual(coord_precision('1.0'), 0.1)

    def test_coord_precision_padded_one(self):
        self.assertEqual(coord_precision('01'), 1)

    def test_coord_precision_ten(self):
        self.assertEqual(coord_precision('20'), 10)

    def test_coord_precision_hundred_hits_max(self):
        self.assertEqual(coord_precision('300'), 10)

    def test_coord_precision_hundred_respects_last_digit(self):
        self.assertEqual(coord_precision('301'), 1)

    def test_coord_precision_no_integer_part(self):
        self.assertEqual(coord_precision('0.2'), 0.1)

    def test_coord_precision_no_integer_part_explicit_sig_fig(self):
        self.assertEqual(coord_precision('0.200'), 0.001)

    def test_coord_precision_long_digit(self):
        self.assertEqual(coord_precision('12.34456'), 0.00001)


class TestMergeStrategy(unittest.TestCase):
    """Test the merge_strategy method."""

    def setUp(self):
        self.mid = 'M123'
        self.base_sdc = {
            "caption": {
                "en": "Foo",
                "sv": "Bar",
            },
            "P123": "Q456",
        }
        self.empty_response = {
            'entities': {
                self.mid: {}
            }
        }

        self.mock_site = mock.MagicMock()
        self.mock_site._simple_request.return_value.submit.return_value = \
            self.empty_response

    def set_mock_response_data(self, captions=None, claims=None):
        """Set the mock response of the API call."""
        data = {
            'entities': {
                self.mid: {
                    'pageid': '123',
                    'labels': captions or {},
                    'statements': claims or {}
                }
            }
        }
        self.mock_site._simple_request.return_value.submit.return_value = data

    def test_merge_strategy_unknown_strategy_no_data(self):
        result = merge_strategy(self.mid, self.mock_site, self.base_sdc, 'foo')
        self.assertIsNone(result)

    def test_merge_strategy_unknown_strategy_some_data_raises(self):
        self.set_mock_response_data(captions={'sv': 'hello'})
        with self.assertRaises(ValueError) as ve:
            merge_strategy(self.mid, self.mock_site, self.base_sdc, 'foo')
        self.assertTrue(
            str(ve.exception).startswith('The `strategy` parameter'))
        self.assertTrue('foo' in str(ve.exception))

    def test_merge_strategy_none_strategy_no_data(self):
        result = merge_strategy(self.mid, self.mock_site, self.base_sdc, None)
        self.assertIsNone(result)

    def test_merge_strategy_none_strategy_some_non_conflicting_data(self):
        self.set_mock_response_data(captions={'fr': 'hello'})
        result = merge_strategy(self.mid, self.mock_site, self.base_sdc, None)
        self.assertIsNotNone(result)

    def test_merge_strategy_new_strategy_no_data(self):
        result = merge_strategy(
            self.mid, self.mock_site, self.base_sdc, 'New')
        self.assertIsNone(result)

    def test_merge_strategy_new_strategy_some_non_conflicting_data(self):
        self.set_mock_response_data(
            captions={'fr': 'hello'}, claims={'P456': [{}]})
        result = merge_strategy(
            self.mid, self.mock_site, self.base_sdc, 'New')
        self.assertIsNone(result)

    def test_merge_strategy_new_strategy_some_conflicting_label_data(self):
        self.set_mock_response_data(captions={'sv': 'hello'})
        result = merge_strategy(
            self.mid, self.mock_site, self.base_sdc, 'New')
        self.assertIsNotNone(result)

    def test_merge_strategy_new_strategy_some_conflicting_claim_data(self):
        self.set_mock_response_data(claims={'P123': [{}]})
        result = merge_strategy(
            self.mid, self.mock_site, self.base_sdc, 'New')
        self.assertIsNotNone(result)

    def test_merge_strategy_blind_strategy_no_data(self):
        result = merge_strategy(
            self.mid, self.mock_site, self.base_sdc, 'Blind')
        self.assertIsNone(result)

    def test_merge_strategy_blind_strategy_some_non_conflicting_data(self):
        self.set_mock_response_data(
            captions={'fr': 'hello'}, claims={'P456': [{}]})
        result = merge_strategy(
            self.mid, self.mock_site, self.base_sdc, 'Blind')
        self.assertIsNone(result)

    def test_merge_strategy_blind_strategy_some_conflicting_data(self):
        self.set_mock_response_data(
            captions={'sv': 'hello'}, claims={'P123': [{}]})
        result = merge_strategy(
            self.mid, self.mock_site, self.base_sdc, 'Blind')
        self.assertIsNone(result)

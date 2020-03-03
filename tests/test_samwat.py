#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_samwat
----------------------------------

Tests for `bikram.bikram` module.
"""

import sys
import unittest
from datetime import date, timedelta

from bikram import samwat, convert_ad_to_bs, convert_bs_to_ad


class TestSamwat(unittest.TestCase):
    '''
    Test `bikram.bikram.samwat` class
    '''

    def setUp(self):
        self.bs_date = samwat(2073, 7, 28)
        self.ad_date = date(2016, 11, 13)

        self.bs_today = samwat.today()
        self.ad_today = date.today()

        if sys.version_info < (3, 0):
            # in python version less than 3 assertRaisesRegex is assertRaisesRegexp
            self.assertRaisesRegex = self.assertRaisesRegexp

    def test_today(self):
        self.assertEqual(self.bs_today.ad, date.today())

    def test_from_ad(self):
        self.assertEqual(samwat.from_ad(self.ad_date), self.bs_date)

    def test_from_iso(self):
        self.assertEqual(samwat.from_iso("2073-07-28"), samwat(2073, 7, 28))

        invalid_datestrs = [
            "207307,28",
            "rubbish",
        ]

        for datestr in invalid_datestrs:
            with self.subTest(datestr=datestr):
                with self.assertRaisesRegex(ValueError, "Invalid datestr provided."):
                    samwat.from_iso(datestr)

    def test_parse(self):
        patterns = [
            ("2073-07-28", "%Y-%m-%d"),
            ("2073/07-28", "%Y/%m-%d"),
            ("2073/07\\28", "%Y/%m\\%d"),
            ("2073.07.28", "%Y.%m.%d"),

            ("07-2073-28", "%m-%Y-%d"),
            ("28-07-2073", "%d-%m-%Y"),
            ("07-28-2073", "%m-%d-%Y"),
            ("07,28,2073", "%m,%d,%Y"),

            ("73-07-28", "%y-%m-%d"),

            ("2073-7-28", "%Y-%-m-%d"),
            ("2073,Kartik,28", "%Y,%B,%d"),
            ("2073,Kar,28", "%Y,%B,%d"),
            ("2073,kartik,28", "%Y,%B,%d"),
            ("2073,kar,28", "%Y,%B,%d"),
            ("2073,कार्तिक,28", "%Y,%B,%d"),

            ("2073 07 28", "%Y %m %d"),

            # test devanagari digits
            ("२०७३ ०७ २८", "%Yne %mne %dne"),
            ("२०७३ ७ २८", "%Yne %-mne %dne"),
        ]
        for datestr, pattern in patterns:
            with self.subTest(datestr=datestr, pattern=pattern):
                self.assertEqual(samwat.parse(datestr, pattern), samwat(2073, 7, 28))

    def test_parse_unique_codes(self):
        invalid_patterns = [
            ("%Y-%d-%-d", "2073-07-28"),
            ("%Y-%m-%-m", "2073-07-28"),
        ]
        for pattern, datestr in invalid_patterns:
            with self.subTest(datestr=datestr, pattern=pattern):
                with self.assertRaisesRegex(ValueError, 'Invalid number of date codes'):
                    samwat.parse(datestr, pattern)

    def test_ad(self):
        '''
        Make sure that a samwat.ad always returns a correct A.D. date
        '''
        self.assertEqual(self.bs_date.ad, self.ad_date)
        self.assertEqual(self.bs_today.ad, self.ad_today)

    def test_as_tuple(self):
        self.assertEqual(self.bs_date.as_tuple(), (2073, 7, 28))

    def test_replace(self):
        self.assertEqual(self.bs_date.replace(2025, 11, 4), samwat(2025, 11, 4))
        self.assertEqual(self.bs_date.replace(2026, 8, 4), samwat(2026, 8, 4))

    def test__repr__and__str__(self):
        self.assertEqual(repr(self.bs_date), 'samwat(2073, 7, 28)')
        self.assertEqual(str(self.bs_date), '2073-7-28')

    def test__add__(self):
        ten_days_added = self.bs_date + timedelta(days=10)

        self.assertTrue(isinstance(ten_days_added, samwat))
        self.assertTrue(isinstance(ten_days_added.ad, date))
        self.assertEqual(ten_days_added.ad, date(2016, 11, 23))

        with self.assertRaisesRegex(
                TypeError, 'Addition only supported for datetime.timedelta type'):
            self.bs_date + date.today()

    def test__radd__(self):
        added_ten_days = timedelta(days=10) + self.bs_date
        self.assertEqual(added_ten_days.ad, date(2016, 11, 23))

    def test__iadd__(self):
        some_bs_date = samwat(2052, 6, 1)
        some_bs_date += timedelta(days=5)
        self.assertEqual(some_bs_date, samwat(2052, 6, 6))
        self.assertEqual(some_bs_date.ad, date(1995, 9, 22))

    def test__sub__(self):
        ten_days_early_bs = samwat(2073, 7, 18)

        # test that we can subtract datetime.timedelta
        self.assertEqual(self.bs_date - timedelta(days=10), ten_days_early_bs)

        # test that we can subtract bikram.samwat
        self.assertEqual(self.bs_date - ten_days_early_bs, timedelta(days=10))

        # test that we can also subtract datetime.date
        self.assertEqual(self.bs_date - date(2016, 11, 3), timedelta(days=10))

        # test that exception is raised while trying to subtract something other than
        # datetime.timedelta, datetime.date and bikram.samwat
        _msg = (
            'Subtraction only supported for datetime.timedelta, '
            'datetime.date and bikram.samwat types, not'
        )
        with self.assertRaisesRegex(TypeError, _msg):
            self.bs_date - 10

    def test__rsub__(self):
        # test positive delta
        self.assertEqual(date(2016, 11, 14) - self.bs_date, timedelta(days=1))
        self.assertEqual(samwat(2073, 7, 29) - self.bs_date, timedelta(days=1))

        # test negative delta
        self.assertEqual(date(2016, 11, 12) - self.bs_date, timedelta(days=-1))
        self.assertEqual(samwat(2073, 7, 27) - self.bs_date, timedelta(days=-1))

        # make sure that we don't subtract date from timedelta
        with self.assertRaisesRegex(TypeError, 'Unsupported operand types'):
            timedelta(days=10) - self.bs_date

    def test__isub__(self):
        some_bs_date = samwat(2052, 6, 6)
        some_bs_date -= timedelta(days=5)
        self.assertEqual(some_bs_date, samwat(2052, 6, 1))
        self.assertEqual(some_bs_date.ad, date(1995, 9, 17))

    def test__hash__(self):
        if sys.version_info < (3, 8):
            bs_hash = -8898535882159624709
        else:
            bs_hash = 4148514807028171473
        self.assertEqual(hash(self.bs_date), bs_hash)

    def test__eq__(self):
        self.assertTrue(samwat(2073, 3, 4) == samwat(2073, 3, 4))
        self.assertTrue(samwat(2073, 7, 27) == date(2016, 11, 12))
        with self.assertRaisesRegex(TypeError, 'Cannot compare bikram.samwat'):
            self.bs_date == 10

    def test__lt__(self):
        self.assertTrue(samwat(2073, 3, 4) < samwat(2073, 3, 5))
        self.assertTrue(samwat(2073, 7, 27) < date(2016, 11, 13))
        with self.assertRaisesRegex(TypeError, 'Cannot compare bikram.samwat'):
            self.bs_date < 10


class TestDateConverters(unittest.TestCase):

    def test_convert_ad_to_bs(self):
        self.assertEqual(convert_ad_to_bs(date(2015, 10, 22)), samwat(2072, 7, 5))
        self.assertEqual(convert_ad_to_bs(date(2014, 9, 30)), samwat(2071, 6, 14))

    def test_convert_bs_to_ad(self):
        self.assertEqual(convert_bs_to_ad(samwat(2072, 7, 5)), date(2015, 10, 22))
        self.assertEqual(convert_bs_to_ad(samwat(2071, 6, 14)), date(2014, 9, 30))


class TestSamwatFormatters(unittest.TestCase):
    '''
    Test formatters for samwat class
    '''

    def setUp(self):
        self.bs_date = samwat(2076, 1, 4)

    def test_formatters(self):
        # २०७६ ०१ ०४
        formats = [
            ("%y-%m-%d", "76-01-04"),
            ("%Y-%B-%d", "2076-Baisakh-04"),

            ("%Y-%-m-%d", "2076- 1-04"),
            ("%Y-%m-%-d", "2076-01- 4"),

            ("%yne-%mne-%dne", "७६-०१-०४"),
            ("%Yne-%mne-%d", "२०७६-०१-04"),

            ("%Yne/%-mne/%dne", "२०७६/ १/०४"),
            ("%Yne/%mne/%-dne", "२०७६/०१/ ४"),

            ("%Yne %B %dne", "२०७६ Baisakh ०४"),
            ("%Yne %Bne %-dne", "२०७६ वैशाख  ४"),
            ("%Yne %Bne %dne", "२०७६ वैशाख ०४"),
        ]

        for formatstr, formatted_str in formats:
            self.assertEqual(self.bs_date.strftime(formatstr), formatted_str)
            print('PASSED', formatstr, formatted_str)

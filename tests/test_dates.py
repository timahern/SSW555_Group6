import unittest
from datetime import date

from gedcom_parser import parseGedDate, formatGedDate


class TestGedcomDates(unittest.TestCase):
    def test_parse_full_date(self):
        d = parseGedDate('15 MAR 1990')
        self.assertIsNotNone(d)
        self.assertEqual(d, date(1990, 3, 15))

    def test_parse_month_year_defaults_day_to_first(self):
        d = parseGedDate('MAR 1990')
        self.assertIsNotNone(d)
        self.assertEqual(d, date(1990, 3, 1))

    def test_parse_year_only_defaults_to_jan_first(self):
        d = parseGedDate('1990')
        self.assertIsNotNone(d)
        self.assertEqual(d, date(1990, 1, 1))

    def test_invalid_inputs_return_none(self):
        # Invalid month in month-year form
        self.assertIsNone(parseGedDate('FOO 1990'))
        # Empty or special GEDCOM 'Y' value should yield None
        self.assertIsNone(parseGedDate(''))
        self.assertIsNone(parseGedDate('Y'))

    def test_formatGedDate_with_partial_and_invalid(self):
        # Partial dates should be normalized to ISO with defaulted components
        self.assertEqual(formatGedDate('MAR 1990'), '1990-03-01')
        self.assertEqual(formatGedDate('1990'), '1990-01-01')
        # Invalid parses format to 'NA'
        self.assertEqual(formatGedDate('FOO 1990'), 'NA')
        self.assertEqual(formatGedDate(''), 'NA')


if __name__ == '__main__':
    unittest.main()
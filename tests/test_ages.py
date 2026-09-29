import unittest
from datetime import date

from gedcom_parser import ageYears
from tests import TestLogger


class TestIndividualAges(unittest.TestCase):

    def test_current_age(self):
        with TestLogger("ageYears computes age 27 from birth 1999-07-01 as of 2026-09-27"):
            birth = date(1999, 7, 1)
            current_date = date(2026, 9, 27)
            self.assertEqual(ageYears(birth, current_date), 27)


if __name__ == '__main__':
    unittest.main()

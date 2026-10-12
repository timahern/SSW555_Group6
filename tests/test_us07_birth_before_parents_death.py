import unittest
from io import StringIO

from gedcom_parser import validate_gedcom_lines
from tests import TestLogger


class TestUS09BirthBeforeParentsDeath(unittest.TestCase):
    def test_child_after_mothers_death_is_flagged(self):
        # Child born on or after mother's death should raise US09
        lines = [
            "0 @I1@ INDI",
            "1 NAME Dad /Doe/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 1 JAN 1960",
            "0 @I2@ INDI",
            "1 NAME Mom /Doe/",
            "1 SEX F",
            "1 BIRT",
            "2 DATE 1 JAN 1962",
            "1 DEAT",
            "2 DATE 1 JAN 1990",
            "0 @I3@ INDI",
            "1 NAME Kid /Doe/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 1 JAN 1990",  # same day as mom's death -> invalid (must be strictly before)
            "0 @F1@ FAM",
            "1 HUSB @I1@",
            "1 WIFE @I2@",
            "1 CHIL @I3@",
            "1 MARR",
            "2 DATE 1 JAN 1980",
        ]
        with TestLogger("US09: child on/after mother's death is flagged"):
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            self.assertTrue(any(e.code == 'US09' for e in errors), f"Expected US09 error, got: {errors}")

    def test_child_more_than_9_months_after_fathers_death_is_flagged(self):
        # Father dies on 1 JAN 1990; child born after 272 days window should be flagged
        lines = [
            "0 @I1@ INDI",
            "1 NAME Dad /Doe/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 1 JAN 1960",
            "1 DEAT",
            "2 DATE 1 JAN 1990",
            "0 @I2@ INDI",
            "1 NAME Mom /Doe/",
            "1 SEX F",
            "1 BIRT",
            "2 DATE 1 JAN 1962",
            "0 @I3@ INDI",
            "1 NAME Kid /Doe/",
            "1 SEX F",
            "1 BIRT",
            "2 DATE 2 OCT 1990",  # more than 272 days after Jan 1, 1990 -> invalid
            "0 @F1@ FAM",
            "1 HUSB @I1@",
            "1 WIFE @I2@",
            "1 CHIL @I3@",
            "1 MARR",
            "2 DATE 1 JAN 1980",
        ]
        with TestLogger("US09: child >9 months after father's death is flagged"):
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            self.assertTrue(any(e.code == 'US09' for e in errors), f"Expected US09 error, got: {errors}")

    def test_child_within_9_months_after_fathers_death_is_ok(self):
        # Father dies on 1 JAN 1990; child born exactly 272 days later should be OK
        # 272 days from Jan 1, 1990 is 30 SEP 1990 (non-leap year 1990)
        lines = [
            "0 @I1@ INDI",
            "1 NAME Dad /Doe/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 1 JAN 1960",
            "1 DEAT",
            "2 DATE 1 JAN 1990",
            "0 @I2@ INDI",
            "1 NAME Mom /Doe/",
            "1 SEX F",
            "1 BIRT",
            "2 DATE 1 JAN 1962",
            "0 @I3@ INDI",
            "1 NAME Kid /Doe/",
            "1 SEX F",
            "1 BIRT",
            "2 DATE 30 SEP 1990",  # boundary day should be allowed
            "0 @F1@ FAM",
            "1 HUSB @I1@",
            "1 WIFE @I2@",
            "1 CHIL @I3@",
            "1 MARR",
            "2 DATE 1 JAN 1980",
        ]
        with TestLogger("US09: child within 9 months after father's death passes"):
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            us09_errors = [e for e in errors if e.code == 'US09']
            self.assertEqual(us09_errors, [], f"Unexpected US09 errors: {errors}")

    def test_missing_dates_skip_checks(self):
        # Missing child birth or parent deaths should not produce US09 errors
        lines = [
            "0 @I1@ INDI",
            "1 NAME Dad /Doe/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 1 JAN 1960",
            "0 @I2@ INDI",
            "1 NAME Mom /Doe/",
            "1 SEX F",
            "1 BIRT",
            "2 DATE 1 JAN 1962",
            "0 @I3@ INDI",
            "1 NAME Kid /Doe/",
            "1 SEX F",
            # Missing BIRT/DATE for child
            "0 @F1@ FAM",
            "1 HUSB @I1@",
            "1 WIFE @I2@",
            "1 CHIL @I3@",
            "1 MARR",
            "2 DATE 1 JAN 1980",
        ]
        with TestLogger("US09: missing dates skip checks (no US09 errors)"):
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            self.assertFalse(any(e.code == 'US09' for e in errors), f"Did not expect US09 errors: {errors}")


if __name__ == '__main__':
    unittest.main()

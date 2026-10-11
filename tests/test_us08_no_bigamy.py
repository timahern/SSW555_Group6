import unittest
from io import StringIO

from gedcom_parser import validate_gedcom_lines
from tests import TestLogger


class TestUS08NoBigamy(unittest.TestCase):
    def test_overlapping_marriages_are_flagged(self):
        # I1 marries I2 on 1 JAN 1990 and then marries I3 on 1 JAN 1995 with no divorce -> overlap
        lines = [
            "0 @I1@ INDI",
            "1 NAME Alex /Doe/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 1 JAN 1970",
            "0 @I2@ INDI",
            "1 NAME Beth /Roe/",
            "1 SEX F",
            "1 BIRT",
            "2 DATE 1 JAN 1972",
            "0 @I3@ INDI",
            "1 NAME Cara /Moe/",
            "1 SEX F",
            "1 BIRT",
            "2 DATE 1 JAN 1973",
            "0 @F1@ FAM",
            "1 HUSB @I1@",
            "1 WIFE @I2@",
            "1 MARR",
            "2 DATE 1 JAN 1990",
            "0 @F2@ FAM",
            "1 HUSB @I1@",
            "1 WIFE @I3@",
            "1 MARR",
            "2 DATE 1 JAN 1995",
        ]
        with TestLogger("US08: overlapping marriages produce error"):
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            self.assertTrue(any(e.code == 'US08' for e in errors), f"Expected US08 error, got: {errors}")

    def test_divorce_before_second_marriage_is_ok(self):
        # I1 marries I2 in 1990, divorces in 1994, then marries I3 in 1995 -> no overlap
        lines = [
            "0 @I1@ INDI",
            "1 NAME Alex /Doe/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 1 JAN 1970",
            "0 @I2@ INDI",
            "1 NAME Beth /Roe/",
            "1 SEX F",
            "1 BIRT",
            "2 DATE 1 JAN 1972",
            "0 @I3@ INDI",
            "1 NAME Cara /Moe/",
            "1 SEX F",
            "1 BIRT",
            "2 DATE 1 JAN 1973",
            "0 @F1@ FAM",
            "1 HUSB @I1@",
            "1 WIFE @I2@",
            "1 MARR",
            "2 DATE 1 JAN 1990",
            "1 DIV",
            "2 DATE 1 JUN 1994",
            "0 @F2@ FAM",
            "1 HUSB @I1@",
            "1 WIFE @I3@",
            "1 MARR",
            "2 DATE 1 JAN 1995",
        ]
        with TestLogger("US08: divorce before second marriage passes"):
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            self.assertFalse(any(e.code == 'US08' for e in errors), f"Unexpected US08 errors: {errors}")

    def test_spouse_death_allows_new_marriage(self):
        # I1 marries I2 in 1990, I2 dies in 1994, then I1 marries I3 in 1995 -> no overlap
        lines = [
            "0 @I1@ INDI",
            "1 NAME Alex /Doe/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 1 JAN 1970",
            "0 @I2@ INDI",
            "1 NAME Beth /Roe/",
            "1 SEX F",
            "1 BIRT",
            "2 DATE 1 JAN 1972",
            "1 DEAT",
            "2 DATE 1 JUN 1994",
            "0 @I3@ INDI",
            "1 NAME Cara /Moe/",
            "1 SEX F",
            "1 BIRT",
            "2 DATE 1 JAN 1973",
            "0 @F1@ FAM",
            "1 HUSB @I1@",
            "1 WIFE @I2@",
            "1 MARR",
            "2 DATE 1 JAN 1990",
            "0 @F2@ FAM",
            "1 HUSB @I1@",
            "1 WIFE @I3@",
            "1 MARR",
            "2 DATE 1 JAN 1995",
        ]
        with TestLogger("US08: spouse death before new marriage passes"):
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            self.assertFalse(any(e.code == 'US08' for e in errors), f"Unexpected US08 errors: {errors}")

    def test_missing_marriage_date_skips_interval(self):
        # First family missing MARR/DATE (will trigger FAM_MARR) but should not create US08
        lines = [
            "0 @I1@ INDI",
            "1 NAME Alex /Doe/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 1 JAN 1970",
            "0 @I2@ INDI",
            "1 NAME Beth /Roe/",
            "1 SEX F",
            "1 BIRT",
            "2 DATE 1 JAN 1972",
            "0 @I3@ INDI",
            "1 NAME Cara /Moe/",
            "1 SEX F",
            "1 BIRT",
            "2 DATE 1 JAN 1973",
            "0 @F1@ FAM",
            "1 HUSB @I1@",
            "1 WIFE @I2@",
            "1 MARR",  # Missing DATE intentionally
            "0 @F2@ FAM",
            "1 HUSB @I1@",
            "1 WIFE @I3@",
            "1 MARR",
            "2 DATE 1 JAN 1995",
        ]
        with TestLogger("US08: missing MARR date does not raise US08 (though FAM_MARR may appear)"):
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            self.assertFalse(any(e.code == 'US08' for e in errors), f"Unexpected US08 errors: {errors}")


if __name__ == '__main__':
    unittest.main()

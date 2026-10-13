import unittest
from io import StringIO

from gedcom_parser import validate_gedcom_lines
from tests import TestLogger


def _indi(indi_id, name, sex, birth, death=None):
    lines = [
        f"0 {indi_id} INDI",
        f"1 NAME {name}",
        f"1 SEX {sex}",
        "1 BIRT",
        f"2 DATE {birth}",
    ]
    if death is not None:
        lines.extend(["1 DEAT", f"2 DATE {death}"])
    return lines


class TestUS02AgeAtMarriage(unittest.TestCase):
    def test_spouse_born_after_marriage_is_flagged(self):
        with TestLogger("US02: Spouse born after marriage is flagged at the family line"):
            lines = []
            lines.extend(_indi("@I1@", "John /Doe/", "M", "1 JAN 1990"))
            lines.extend(_indi("@I2@", "Jane /Doe/", "F", "1 JAN 2015"))
            lines.extend([
                "0 @F1@ FAM",
                "1 HUSB @I1@",
                "1 WIFE @I2@",
                "1 MARR",
                "2 DATE 1 JUN 2010",
            ])
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            us02 = [e for e in errors if e.code == 'US02']
            self.assertEqual(len(us02), 1)
            self.assertEqual(us02[0].line_no, 11)
            self.assertIn('Wife I02', us02[0].message)

    def test_spouse_under_14_is_flagged(self):
        with TestLogger("US02: Spouse younger than 14 at marriage is flagged"):
            lines = []
            lines.extend(_indi("@I1@", "John /Doe/", "M", "1 JAN 2000"))
            lines.extend(_indi("@I2@", "Jane /Doe/", "F", "1 JAN 1980"))
            lines.extend([
                "0 @F1@ FAM",
                "1 HUSB @I1@",
                "1 WIFE @I2@",
                "1 MARR",
                "2 DATE 1 JAN 2013",
            ])
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            us02 = [e for e in errors if e.code == 'US02']
            self.assertEqual(len(us02), 1)
            self.assertIn('Husband I01', us02[0].message)
            self.assertIn('14', us02[0].message)

    def test_both_spouses_can_be_flagged(self):
        with TestLogger("US02: Both spouses under 14 produce two US02 errors"):
            lines = []
            lines.extend(_indi("@I1@", "John /Doe/", "M", "1 JAN 2005"))
            lines.extend(_indi("@I2@", "Jane /Doe/", "F", "1 JAN 2006"))
            lines.extend([
                "0 @F1@ FAM",
                "1 HUSB @I1@",
                "1 WIFE @I2@",
                "1 MARR",
                "2 DATE 1 JAN 2010",
            ])
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            self.assertEqual(len([e for e in errors if e.code == 'US02']), 2)

    def test_birth_on_marriage_date_is_flagged(self):
        with TestLogger("US02: Birth on the marriage date is not before marriage"):
            lines = []
            lines.extend(_indi("@I1@", "John /Doe/", "M", "1 JAN 1980"))
            lines.extend(_indi("@I2@", "Jane /Doe/", "F", "1 JUN 2000"))
            lines.extend([
                "0 @F1@ FAM",
                "1 HUSB @I1@",
                "1 WIFE @I2@",
                "1 MARR",
                "2 DATE 1 JUN 2000",
            ])
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            us02 = [e for e in errors if e.code == 'US02']
            self.assertEqual(len(us02), 1)
            self.assertIn('born before marriage', us02[0].message)

    def test_exactly_14_is_not_flagged(self):
        with TestLogger("US02: A spouse who turns 14 on the marriage date is allowed"):
            lines = []
            lines.extend(_indi("@I1@", "John /Doe/", "M", "1 JAN 2000"))
            lines.extend(_indi("@I2@", "Jane /Doe/", "F", "15 MAR 1980"))
            lines.extend([
                "0 @F1@ FAM",
                "1 HUSB @I1@",
                "1 WIFE @I2@",
                "1 MARR",
                "2 DATE 1 JAN 2014",
            ])
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            self.assertFalse(any(e.code == 'US02' for e in errors))

    def test_day_before_14th_birthday_is_flagged(self):
        with TestLogger("US02: Marriage the day before the 14th birthday is flagged"):
            lines = []
            lines.extend(_indi("@I1@", "John /Doe/", "M", "2 JAN 2000"))
            lines.extend(_indi("@I2@", "Jane /Doe/", "F", "1 JAN 1980"))
            lines.extend([
                "0 @F1@ FAM",
                "1 HUSB @I1@",
                "1 WIFE @I2@",
                "1 MARR",
                "2 DATE 1 JAN 2014",
            ])
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            us02 = [e for e in errors if e.code == 'US02']
            self.assertEqual(len(us02), 1)
            self.assertIn('Husband I01', us02[0].message)


class TestUS04MarriageDivorceDeathOrder(unittest.TestCase):
    def _family(self, husband_death=None, wife_death=None, married="1 JUN 2000", divorced="1 JUN 2010"):
        lines = []
        lines.extend(_indi("@I1@", "John /Doe/", "M", "1 JAN 1980", husband_death))
        lines.extend(_indi("@I2@", "Jane /Doe/", "F", "1 JAN 1982", wife_death))
        lines.extend([
            "0 @F1@ FAM",
            "1 HUSB @I1@",
            "1 WIFE @I2@",
            "1 MARR",
            f"2 DATE {married}",
        ])
        if divorced is not None:
            lines.extend(["1 DIV", f"2 DATE {divorced}"])
        return lines

    def test_divorce_before_marriage_is_flagged(self):
        with TestLogger("US04: Divorce before marriage is flagged at the family line"):
            lines = self._family(married="1 JUN 2010", divorced="1 JUN 2005")
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            us04 = [e for e in errors if e.code == 'US04']
            self.assertEqual(len(us04), 1)
            self.assertIn('before divorce', us04[0].message)
            self.assertEqual(us04[0].line_no, 11)

    def test_divorce_on_marriage_date_is_flagged(self):
        with TestLogger("US04: Divorce on the marriage date is an impossible order"):
            lines = self._family(married="1 JUN 2010", divorced="1 JUN 2010")
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            self.assertTrue(any(e.code == 'US04' and 'before divorce' in e.message for e in errors))

    def test_divorce_after_husband_death_is_flagged(self):
        with TestLogger("US04: Divorce after the husband death is flagged"):
            lines = self._family(husband_death="1 JAN 2008", divorced="1 JUN 2010")
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            us04 = [e for e in errors if e.code == 'US04']
            self.assertEqual(len(us04), 1)
            self.assertIn('husband I01', us04[0].message)

    def test_divorce_after_wife_death_is_flagged(self):
        with TestLogger("US04: Divorce after the wife death is flagged"):
            lines = self._family(wife_death="1 JAN 2008", divorced="1 JUN 2010")
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            us04 = [e for e in errors if e.code == 'US04']
            self.assertEqual(len(us04), 1)
            self.assertIn('wife I02', us04[0].message)

    def test_divorce_on_death_date_is_flagged(self):
        with TestLogger("US04: Divorce on a spouse death date is an impossible order"):
            lines = self._family(husband_death="1 JUN 2010", divorced="1 JUN 2010")
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            self.assertTrue(any(e.code == 'US04' and 'husband I01' in e.message for e in errors))

    def test_both_deaths_before_divorce_are_flagged(self):
        with TestLogger("US04: Divorce after both deaths produces two US04 errors"):
            lines = self._family(
                husband_death="1 JAN 2008",
                wife_death="1 FEB 2008",
                divorced="1 JUN 2010",
            )
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            self.assertEqual(len([e for e in errors if e.code == 'US04']), 2)

    def test_divorce_before_marriage_and_after_death(self):
        with TestLogger("US04: Impossible marriage-divorce order and divorce-death order are both reported"):
            lines = self._family(
                husband_death="1 JAN 2004",
                married="1 JUN 2010",
                divorced="1 JAN 2005",
            )
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            us04 = [e for e in errors if e.code == 'US04']
            self.assertEqual(len(us04), 2)

    def test_valid_order_is_not_flagged(self):
        with TestLogger("US04: Marriage, then divorce, then death is allowed"):
            lines = self._family(
                husband_death="1 JAN 2020",
                wife_death="1 JAN 2021",
                married="1 JUN 2000",
                divorced="1 JUN 2010",
            )
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            self.assertFalse(any(e.code == 'US04' for e in errors))
            self.assertFalse(any(e.code == 'US02' for e in errors))

    def test_no_divorce_does_not_flag_death_order(self):
        with TestLogger("US04: A marriage with no divorce does not report US04"):
            lines = self._family(husband_death="1 JAN 2015", divorced=None)
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            self.assertFalse(any(e.code == 'US04' for e in errors))


if __name__ == '__main__':
    unittest.main()

import unittest
from io import StringIO

from gedcom_parser import validate_gedcom_lines


# Helpers that build small fake GEDCOM records
def indi(id, name, sex, birth, death=None):
    lines = [f"0 {id} INDI", f"1 NAME {name}", f"1 SEX {sex}", "1 BIRT", f"2 DATE {birth}"]
    if death:
        lines += ["1 DEAT", f"2 DATE {death}"]
    return lines


def fam(id, marr, husb=None, wife=None, children=(), div=None):
    lines = [f"0 {id} FAM"]
    if husb:
        lines.append(f"1 HUSB {husb}")
    if wife:
        lines.append(f"1 WIFE {wife}")
    for c in children:
        lines.append(f"1 CHIL {c}")
    lines += ["1 MARR", f"2 DATE {marr}"]
    if div:
        lines += ["1 DIV", f"2 DATE {div}"]
    return lines


def errors_with(code, lines):
    _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
    return [e for e in errors if e.code == code]


class TestUS05MarriageBeforeDeath(unittest.TestCase):
    def test_husband_died_before_marriage_is_flagged(self):
        msg = "US05: Marriage after husband's death should be flagged at the family's line"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M", "15 MAR 1960", death="1 JAN 1990") + \
                indi("@I2@", "Jane /Doe/", "F", "20 APR 1962") + \
                fam("@F1@", "10 JUN 1995", husb="@I1@", wife="@I2@")
        errs = errors_with('US05', lines)
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs[0].line_no, 13)  # family starts on line 13
        print(f"[PASS] {msg}")

    def test_wife_died_before_marriage_is_flagged(self):
        msg = "US05: Marriage after wife's death should be flagged and name the wife"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M", "15 MAR 1960") + \
                indi("@I2@", "Jane /Doe/", "F", "20 APR 1962", death="1 JAN 1990") + \
                fam("@F1@", "10 JUN 1995", husb="@I1@", wife="@I2@")
        errs = errors_with('US05', lines)
        self.assertEqual(len(errs), 1)
        self.assertIn('wife', errs[0].message)
        print(f"[PASS] {msg}")

    def test_both_spouses_died_before_marriage_flagged_twice(self):
        msg = "US05: Marriage after both spouses' deaths should produce two errors"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M", "15 MAR 1960", death="1 JAN 1990") + \
                indi("@I2@", "Jane /Doe/", "F", "20 APR 1962", death="2 FEB 1991") + \
                fam("@F1@", "10 JUN 1995", husb="@I1@", wife="@I2@")
        self.assertEqual(len(errors_with('US05', lines)), 2)
        print(f"[PASS] {msg}")

    def test_death_after_marriage_not_flagged(self):
        msg = "US05: Spouse dying after the marriage should not be flagged"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M", "15 MAR 1960", death="1 JAN 2010") + \
                indi("@I2@", "Jane /Doe/", "F", "20 APR 1962") + \
                fam("@F1@", "10 JUN 1995", husb="@I1@", wife="@I2@")
        self.assertEqual(errors_with('US05', lines), [])
        print(f"[PASS] {msg}")

    def test_death_on_wedding_day_not_flagged(self):
        msg = "US05: Spouse dying on the wedding day should not be flagged"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M", "15 MAR 1960", death="10 JUN 1995") + \
                indi("@I2@", "Jane /Doe/", "F", "20 APR 1962") + \
                fam("@F1@", "10 JUN 1995", husb="@I1@", wife="@I2@")
        self.assertEqual(errors_with('US05', lines), [])
        print(f"[PASS] {msg}")

    def test_both_spouses_alive_not_flagged(self):
        msg = "US05: Family where both spouses are alive should not be flagged"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M", "15 MAR 1960") + \
                indi("@I2@", "Jane /Doe/", "F", "20 APR 1962") + \
                fam("@F1@", "10 JUN 1995", husb="@I1@", wife="@I2@")
        self.assertEqual(errors_with('US05', lines), [])
        print(f"[PASS] {msg}")


class TestUS06BirthAfterParentsMarriage(unittest.TestCase):
    def parents_and_child(self, child_birth, marr, div=None):
        return indi("@I1@", "John /Doe/", "M", "15 MAR 1960") + \
               indi("@I2@", "Jane /Doe/", "F", "20 APR 1962") + \
               indi("@I3@", "Jack /Doe/", "M", child_birth) + \
               fam("@F1@", marr, husb="@I1@", wife="@I2@", children=["@I3@"], div=div)

    def test_born_before_marriage_is_flagged(self):
        msg = "US06: Child born before parents' marriage should be flagged at the child's line"
        print(f"[TEST] {msg}")
        errs = errors_with('US06', self.parents_and_child("1 JAN 1990", "10 JUN 1995"))
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs[0].line_no, 11)  # child starts on line 11
        print(f"[PASS] {msg}")

    def test_born_after_marriage_not_flagged(self):
        msg = "US06: Child born after parents' marriage should not be flagged"
        print(f"[TEST] {msg}")
        errs = errors_with('US06', self.parents_and_child("1 JAN 1998", "10 JUN 1995"))
        self.assertEqual(errs, [])
        print(f"[PASS] {msg}")

    def test_born_on_wedding_day_not_flagged(self):
        msg = "US06: Child born on the wedding day should not be flagged"
        print(f"[TEST] {msg}")
        errs = errors_with('US06', self.parents_and_child("10 JUN 1995", "10 JUN 1995"))
        self.assertEqual(errs, [])
        print(f"[PASS] {msg}")

    def test_born_more_than_9_months_after_divorce_is_flagged(self):
        msg = "US06: Child born more than 9 months after divorce should be flagged"
        print(f"[TEST] {msg}")
        errs = errors_with('US06', self.parents_and_child(
            "16 DEC 2000", "10 JUN 1995", div="15 MAR 2000"))
        self.assertEqual(len(errs), 1)
        self.assertIn('divorce', errs[0].message)
        print(f"[PASS] {msg}")

    def test_born_exactly_9_months_after_divorce_not_flagged(self):
        msg = "US06: Child born exactly 9 months after divorce should not be flagged"
        print(f"[TEST] {msg}")
        errs = errors_with('US06', self.parents_and_child(
            "15 DEC 2000", "10 JUN 1995", div="15 MAR 2000"))
        self.assertEqual(errs, [])
        print(f"[PASS] {msg}")

    def test_born_within_9_months_after_divorce_not_flagged(self):
        msg = "US06: Child born within 9 months after divorce should not be flagged"
        print(f"[TEST] {msg}")
        errs = errors_with('US06', self.parents_and_child(
            "1 JUL 2000", "10 JUN 1995", div="15 MAR 2000"))
        self.assertEqual(errs, [])
        print(f"[PASS] {msg}")

    def test_month_end_divorce_clamps_to_end_of_february(self):
        msg = "US06: Divorce on 31 MAY allows births through 28 FEB, not 1 MAR"
        print(f"[TEST] {msg}")
        ok = errors_with('US06', self.parents_and_child(
            "28 FEB 2001", "10 JUN 1995", div="31 MAY 2000"))
        late = errors_with('US06', self.parents_and_child(
            "1 MAR 2001", "10 JUN 1995", div="31 MAY 2000"))
        self.assertEqual(ok, [])
        self.assertEqual(len(late), 1)
        print(f"[PASS] {msg}")


if __name__ == '__main__':
    unittest.main()
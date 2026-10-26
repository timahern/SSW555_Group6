import unittest
from io import StringIO

from gedcom_parser import validate_gedcom_lines


def indi(id, name, sex, birth="1 JAN 1950"):
    return [f"0 {id} INDI", f"1 NAME {name}", f"1 SEX {sex}", "1 BIRT", f"2 DATE {birth}"]


def fam(id, husb=None, wife=None, children=(), marr="1 JUN 1970"):
    lines = [f"0 {id} FAM"]
    if husb:
        lines.append(f"1 HUSB {husb}")
    if wife:
        lines.append(f"1 WIFE {wife}")
    for c in children:
        lines.append(f"1 CHIL {c}")
    lines += ["1 MARR", f"2 DATE {marr}"]
    return lines


def errors_with(code, lines):
    _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
    return [e for e in errors if e.code == code]


class TestUS13MaleLastNames(unittest.TestCase):
    def test_father_and_son_same_surname_not_flagged(self):
        msg = "US13: Father and son with the same last name should not be flagged"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + indi("@I2@", "Jane /Doe/", "F") + \
                indi("@I3@", "Jack /Doe/", "M") + \
                fam("@F1@", husb="@I1@", wife="@I2@", children=["@I3@"])
        self.assertEqual(errors_with('US13', lines), [])
        print(f"[PASS] {msg}")

    def test_son_with_different_surname_flagged(self):
        msg = "US13: Son with a different last name should be flagged at the son's line"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + indi("@I2@", "Jane /Doe/", "F") + \
                indi("@I3@", "Jack /Smith/", "M") + \
                fam("@F1@", husb="@I1@", wife="@I2@", children=["@I3@"])
        errs = errors_with('US13', lines)
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs[0].line_no, 11)  # son starts on line 11
        self.assertIn('I03', errs[0].message)
        print(f"[PASS] {msg}")

    def test_daughter_with_different_surname_not_flagged(self):
        msg = "US13: Daughter with a different last name should not be flagged"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + indi("@I2@", "Jane /Doe/", "F") + \
                indi("@I3@", "Jill /Smith/", "F") + \
                fam("@F1@", husb="@I1@", wife="@I2@", children=["@I3@"])
        self.assertEqual(errors_with('US13', lines), [])
        print(f"[PASS] {msg}")

    def test_only_mismatched_son_flagged(self):
        msg = "US13: With two sons, only the one with a different last name is flagged"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + indi("@I2@", "Jane /Doe/", "F") + \
                indi("@I3@", "Jack /Doe/", "M") + indi("@I4@", "Jim /Smith/", "M") + \
                fam("@F1@", husb="@I1@", wife="@I2@", children=["@I3@", "@I4@"])
        errs = errors_with('US13', lines)
        self.assertEqual(len(errs), 1)
        self.assertIn('I04', errs[0].message)
        print(f"[PASS] {msg}")

    def test_no_father_compares_sons_to_first_son(self):
        msg = "US13: Without a husband, sons are compared to the first son"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "Jane /Doe/", "F") + indi("@I2@", "Jack /Doe/", "M") + \
                indi("@I3@", "Jim /Smith/", "M") + \
                fam("@F1@", wife="@I1@", children=["@I2@", "@I3@"])
        errs = errors_with('US13', lines)
        self.assertEqual(len(errs), 1)
        self.assertIn('I03', errs[0].message)
        print(f"[PASS] {msg}")

    def test_name_without_surname_is_skipped(self):
        msg = "US13: A name with no /surname/ is skipped rather than flagged"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + indi("@I2@", "Jane /Doe/", "F") + \
                indi("@I3@", "Jack Smith", "M") + \
                fam("@F1@", husb="@I1@", wife="@I2@", children=["@I3@"])
        self.assertEqual(errors_with('US13', lines), [])
        print(f"[PASS] {msg}")


class TestUS14NoMarriageToDescendants(unittest.TestCase):
    def test_unrelated_spouses_not_flagged(self):
        msg = "US14: Unrelated spouses should not be flagged"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + indi("@I2@", "Jane /Roe/", "F") + \
                fam("@F1@", husb="@I1@", wife="@I2@")
        self.assertEqual(errors_with('US14', lines), [])
        print(f"[PASS] {msg}")

    def test_father_marries_daughter_flagged(self):
        msg = "US14: Father marrying his daughter should be flagged"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + indi("@I2@", "Jane /Doe/", "F") + \
                indi("@I3@", "Jill /Doe/", "F") + \
                fam("@F1@", husb="@I1@", wife="@I2@", children=["@I3@"]) + \
                fam("@F2@", husb="@I1@", wife="@I3@")
        errs = errors_with('US14', lines)
        self.assertEqual(len(errs), 1)
        self.assertIn('descendant', errs[0].message)
        print(f"[PASS] {msg}")

    def test_mother_marries_son_flagged(self):
        msg = "US14: Mother marrying her son should be flagged"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + indi("@I2@", "Jane /Doe/", "F") + \
                indi("@I3@", "Jack /Doe/", "M") + \
                fam("@F1@", husb="@I1@", wife="@I2@", children=["@I3@"]) + \
                fam("@F2@", husb="@I3@", wife="@I2@")
        errs = errors_with('US14', lines)
        self.assertEqual(len(errs), 1)
        self.assertIn('wife', errs[0].message)
        print(f"[PASS] {msg}")

    def test_grandfather_marries_granddaughter_flagged(self):
        msg = "US14: Grandfather marrying his granddaughter should be flagged"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + indi("@I2@", "Jane /Doe/", "F") + \
                indi("@I3@", "Jack /Doe/", "M") + indi("@I4@", "Mary /Roe/", "F") + \
                indi("@I5@", "Jill /Doe/", "F") + \
                fam("@F1@", husb="@I1@", wife="@I2@", children=["@I3@"]) + \
                fam("@F2@", husb="@I3@", wife="@I4@", children=["@I5@"]) + \
                fam("@F3@", husb="@I1@", wife="@I5@")
        self.assertEqual(len(errors_with('US14', lines)), 1)
        print(f"[PASS] {msg}")

    def test_uncle_marries_niece_not_flagged(self):
        msg = "US14: Uncle marrying his niece is not a descendant marriage (that's US17)"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + indi("@I2@", "Jane /Doe/", "F") + \
                indi("@I3@", "Jack /Doe/", "M") + indi("@I4@", "Jim /Doe/", "M") + \
                indi("@I5@", "Mary /Roe/", "F") + indi("@I6@", "Jill /Doe/", "F") + \
                fam("@F1@", husb="@I1@", wife="@I2@", children=["@I3@", "@I4@"]) + \
                fam("@F2@", husb="@I4@", wife="@I5@", children=["@I6@"]) + \
                fam("@F3@", husb="@I3@", wife="@I6@")
        self.assertEqual(errors_with('US14', lines), [])
        print(f"[PASS] {msg}")

    def test_self_referencing_family_does_not_loop(self):
        msg = "US14: A corrupt family listing a spouse as their own child finishes and is flagged"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + indi("@I2@", "Jane /Doe/", "F") + \
                fam("@F1@", husb="@I1@", wife="@I2@", children=["@I1@"])
        self.assertEqual(len(errors_with('US14', lines)), 1)
        print(f"[PASS] {msg}")


if __name__ == '__main__':
    unittest.main()
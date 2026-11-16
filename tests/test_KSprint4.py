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


class TestUS39NoSelfRelationships(unittest.TestCase):
    def test_normal_family_not_flagged(self):
        msg = "US39: A normal family with parents and a child should not be flagged"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + indi("@I2@", "Jane /Doe/", "F") + \
                indi("@I3@", "Jack /Doe/", "M", "1 JAN 1975") + \
                fam("@F1@", husb="@I1@", wife="@I2@", children=["@I3@"])
        self.assertEqual(errors_with('US39', lines), [])
        print(f"[PASS] {msg}")

    def test_own_spouse_flagged(self):
        msg = "US39: An individual listed as both husband and wife is their own spouse"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + fam("@F1@", husb="@I1@", wife="@I1@")
        errs = errors_with('US39', lines)
        self.assertEqual(len(errs), 1)
        self.assertIn('own spouse', errs[0].message)
        print(f"[PASS] {msg}")

    def test_husband_is_own_child_flagged(self):
        msg = "US39: A husband listed as a child of his own family is flagged at the family's line"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + indi("@I2@", "Jane /Doe/", "F") + \
                fam("@F1@", husb="@I1@", wife="@I2@", children=["@I1@"])
        errs = errors_with('US39', lines)
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs[0].line_no, 11)  # family starts on line 11
        self.assertIn('I01', errs[0].message)
        print(f"[PASS] {msg}")

    def test_wife_is_own_child_flagged(self):
        msg = "US39: A wife listed as a child of her own family is flagged"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + indi("@I2@", "Jane /Doe/", "F") + \
                fam("@F1@", husb="@I1@", wife="@I2@", children=["@I2@"])
        errs = errors_with('US39', lines)
        self.assertEqual(len(errs), 1)
        self.assertIn('I02', errs[0].message)
        print(f"[PASS] {msg}")

    def test_own_spouse_and_child_reported_once_each(self):
        msg = "US39: Own spouse and own child in one family produce exactly two errors"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + \
                fam("@F1@", husb="@I1@", wife="@I1@", children=["@I1@"])
        self.assertEqual(len(errors_with('US39', lines)), 2)
        print(f"[PASS] {msg}")

    def test_single_parent_family_not_flagged(self):
        msg = "US39: A family with only one parent listed is not a self relationship"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "Jane /Doe/", "F") + indi("@I2@", "Jack /Doe/", "M", "1 JAN 1975") + \
                fam("@F1@", wife="@I1@", children=["@I2@"])
        self.assertEqual(errors_with('US39', lines), [])
        print(f"[PASS] {msg}")


class TestUS40NoAncestryCycles(unittest.TestCase):
    def test_three_generations_not_flagged(self):
        msg = "US40: A normal grandparent-parent-child line has no cycle"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + indi("@I2@", "Jack /Doe/", "M", "1 JAN 1975") + \
                indi("@I3@", "Jim /Doe/", "M", "1 JAN 2000") + \
                fam("@F1@", husb="@I1@", children=["@I2@"]) + \
                fam("@F2@", husb="@I2@", children=["@I3@"])
        self.assertEqual(errors_with('US40', lines), [])
        print(f"[PASS] {msg}")

    def test_two_person_cycle_flagged(self):
        msg = "US40: Two people who are each other's parent form a cycle"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + indi("@I2@", "Jack /Doe/", "M") + \
                fam("@F1@", husb="@I1@", children=["@I2@"]) + \
                fam("@F2@", husb="@I2@", children=["@I1@"])
        errs = errors_with('US40', lines)
        self.assertEqual(len(errs), 1)
        self.assertIn('I01', errs[0].message)
        self.assertIn('I02', errs[0].message)
        print(f"[PASS] {msg}")

    def test_three_generation_cycle_reported_once(self):
        msg = "US40: A grandchild listed as the grandparent's parent is one cycle, reported once"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + indi("@I2@", "Jack /Doe/", "M") + \
                indi("@I3@", "Jim /Doe/", "M") + \
                fam("@F1@", husb="@I1@", children=["@I2@"]) + \
                fam("@F2@", husb="@I2@", children=["@I3@"]) + \
                fam("@F3@", husb="@I3@", children=["@I1@"])
        errs = errors_with('US40', lines)
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs[0].line_no, 1)  # reported at I1, the first person in the cycle
        print(f"[PASS] {msg}")

    def test_cycle_through_mother_flagged(self):
        msg = "US40: A loop through a mother (WIFE) is detected too"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "Jane /Doe/", "F") + indi("@I2@", "Jill /Doe/", "F") + \
                fam("@F1@", wife="@I1@", children=["@I2@"]) + \
                fam("@F2@", wife="@I2@", children=["@I1@"])
        self.assertEqual(len(errors_with('US40', lines)), 1)
        print(f"[PASS] {msg}")

    def test_self_child_left_to_us39(self):
        msg = "US40: A person who is their own direct child is reported by US39, not US40"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + indi("@I2@", "Jane /Doe/", "F") + \
                fam("@F1@", husb="@I1@", wife="@I2@", children=["@I1@"])
        self.assertEqual(errors_with('US40', lines), [])
        self.assertEqual(len(errors_with('US39', lines)), 1)
        print(f"[PASS] {msg}")

    def test_two_separate_cycles_reported_separately(self):
        msg = "US40: Two unrelated cycles produce two errors"
        print(f"[TEST] {msg}")
        lines = indi("@I1@", "John /Doe/", "M") + indi("@I2@", "Jack /Doe/", "M") + \
                indi("@I3@", "Jim /Roe/", "M") + indi("@I4@", "Joe /Roe/", "M") + \
                fam("@F1@", husb="@I1@", children=["@I2@"]) + \
                fam("@F2@", husb="@I2@", children=["@I1@"]) + \
                fam("@F3@", husb="@I3@", children=["@I4@"]) + \
                fam("@F4@", husb="@I4@", children=["@I3@"])
        self.assertEqual(len(errors_with('US40', lines)), 2)
        print(f"[PASS] {msg}")


if __name__ == '__main__':
    unittest.main()
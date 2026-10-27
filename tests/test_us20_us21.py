import unittest
from io import StringIO

from gedcom_parser import validate_gedcom_lines
from tests import TestLogger


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


class TestUS20UniqueFamiliesBySpouses(unittest.TestCase):
    def test_same_spouses_and_date_is_flagged(self):
        with TestLogger("US20: Same spouse names and marriage date should be flagged at the second family"):
            lines = indi("@I1@", "John /Doe/", "M", "1 JAN 1950") + \
                    indi("@I2@", "Jane /Roe/", "F", "1 JAN 1952") + \
                    indi("@I3@", "John /Doe/", "M", "2 FEB 1951") + \
                    indi("@I4@", "Jane /Roe/", "F", "3 MAR 1953") + \
                    fam("@F1@", "1 JUN 1975", husb="@I1@", wife="@I2@") + \
                    fam("@F2@", "1 JUN 1975", husb="@I3@", wife="@I4@")
            errs = errors_with('US20', lines)
            self.assertEqual(len(errs), 1)
            self.assertEqual(errs[0].line_no, 26)  # second family starts on line 26
            self.assertIn('F02', errs[0].message)
            self.assertIn('F01', errs[0].message)

    def test_same_spouses_different_date_not_flagged(self):
        with TestLogger("US20: Same spouse names with a different marriage date should not be flagged"):
            lines = indi("@I1@", "John /Doe/", "M", "1 JAN 1950") + \
                    indi("@I2@", "Jane /Roe/", "F", "1 JAN 1952") + \
                    indi("@I3@", "John /Doe/", "M", "2 FEB 1951") + \
                    indi("@I4@", "Jane /Roe/", "F", "3 MAR 1953") + \
                    fam("@F1@", "1 JUN 1975", husb="@I1@", wife="@I2@") + \
                    fam("@F2@", "2 JUN 1975", husb="@I3@", wife="@I4@")
            self.assertEqual(errors_with('US20', lines), [])

    def test_different_spouse_name_not_flagged(self):
        with TestLogger("US20: A different spouse name on the same date should not be flagged"):
            lines = indi("@I1@", "John /Doe/", "M", "1 JAN 1950") + \
                    indi("@I2@", "Jane /Roe/", "F", "1 JAN 1952") + \
                    indi("@I3@", "John /Doe/", "M", "2 FEB 1951") + \
                    indi("@I4@", "Janet /Roe/", "F", "3 MAR 1953") + \
                    fam("@F1@", "1 JUN 1975", husb="@I1@", wife="@I2@") + \
                    fam("@F2@", "1 JUN 1975", husb="@I3@", wife="@I4@")
            self.assertEqual(errors_with('US20', lines), [])

    def test_same_people_in_two_families_is_flagged(self):
        with TestLogger("US20: The same couple recorded in two families on the same date should be flagged"):
            lines = indi("@I1@", "John /Doe/", "M", "1 JAN 1950") + \
                    indi("@I2@", "Jane /Roe/", "F", "1 JAN 1952") + \
                    fam("@F1@", "1 JUN 1975", husb="@I1@", wife="@I2@") + \
                    fam("@F2@", "1 JUN 1975", husb="@I1@", wife="@I2@")
            errs = errors_with('US20', lines)
            self.assertEqual(len(errs), 1)
            self.assertEqual(errs[0].line_no, 16)  # second family starts on line 16

    def test_swapped_spouse_roles_is_flagged(self):
        with TestLogger("US20: The same spouse names with husband and wife swapped should be flagged"):
            lines = indi("@I1@", "John /Doe/", "M", "1 JAN 1950") + \
                    indi("@I2@", "Jane /Roe/", "F", "1 JAN 1952") + \
                    indi("@I3@", "Jane /Roe/", "M", "4 APR 1954") + \
                    indi("@I4@", "John /Doe/", "F", "5 MAY 1955") + \
                    fam("@F1@", "1 JUN 1975", husb="@I1@", wife="@I2@") + \
                    fam("@F2@", "1 JUN 1975", husb="@I3@", wife="@I4@")
            errs = errors_with('US20', lines)
            self.assertEqual(len(errs), 1)
            self.assertEqual(errs[0].line_no, 26)

    def test_spouse_name_case_is_flagged(self):
        with TestLogger("US20: Spouse names that differ only by case should be flagged"):
            lines = indi("@I1@", "John /Doe/", "M", "1 JAN 1950") + \
                    indi("@I2@", "Jane /Roe/", "F", "1 JAN 1952") + \
                    indi("@I3@", "john /doe/", "M", "2 FEB 1951") + \
                    indi("@I4@", "jane /roe/", "F", "3 MAR 1953") + \
                    fam("@F1@", "1 JUN 1975", husb="@I1@", wife="@I2@") + \
                    fam("@F2@", "1 JUN 1975", husb="@I3@", wife="@I4@")
            errs = errors_with('US20', lines)
            self.assertEqual(len(errs), 1)
            self.assertIn('F02', errs[0].message)

    def test_missing_spouse_not_flagged(self):
        with TestLogger("US20: Families missing a spouse name should not be flagged"):
            lines = indi("@I1@", "John /Doe/", "M", "1 JAN 1950") + \
                    indi("@I2@", "John /Doe/", "M", "2 FEB 1951") + \
                    fam("@F1@", "1 JUN 1975", husb="@I1@") + \
                    fam("@F2@", "1 JUN 1975", husb="@I2@")
            self.assertEqual(errors_with('US20', lines), [])

    def test_equivalent_marriage_dates_are_flagged(self):
        with TestLogger("US20: Marriage dates that parse to the same day should be flagged"):
            lines = indi("@I1@", "John /Doe/", "M", "1 JAN 1950") + \
                    indi("@I2@", "Jane /Roe/", "F", "1 JAN 1952") + \
                    indi("@I3@", "John /Doe/", "M", "2 FEB 1951") + \
                    indi("@I4@", "Jane /Roe/", "F", "3 MAR 1953") + \
                    fam("@F1@", "1 JUN 1975", husb="@I1@", wife="@I2@") + \
                    fam("@F2@", "01 JUN 1975", husb="@I3@", wife="@I4@")
            errs = errors_with('US20', lines)
            self.assertEqual(len(errs), 1)
            self.assertIn('1975-06-01', errs[0].message)

    def test_three_duplicate_families_flag_the_later_two(self):
        with TestLogger("US20: Each later family with the same spouses and date should be flagged"):
            lines = indi("@I1@", "John /Doe/", "M", "1 JAN 1950") + \
                    indi("@I2@", "Jane /Roe/", "F", "1 JAN 1952") + \
                    indi("@I3@", "John /Doe/", "M", "2 FEB 1951") + \
                    indi("@I4@", "Jane /Roe/", "F", "3 MAR 1953") + \
                    indi("@I5@", "John /Doe/", "M", "4 APR 1954") + \
                    indi("@I6@", "Jane /Roe/", "F", "5 MAY 1955") + \
                    fam("@F1@", "1 JUN 1975", husb="@I1@", wife="@I2@") + \
                    fam("@F2@", "1 JUN 1975", husb="@I3@", wife="@I4@") + \
                    fam("@F3@", "1 JUN 1975", husb="@I5@", wife="@I6@")
            errs = errors_with('US20', lines)
            self.assertEqual(len(errs), 2)
            self.assertEqual([e.line_no for e in errs], [36, 41])
            self.assertTrue(all('F01' in e.message for e in errs))


class TestUS21UniqueFirstNamesInFamilies(unittest.TestCase):
    def test_same_name_and_birth_in_family_is_flagged(self):
        with TestLogger("US21: Two children with the same name and birth date should be flagged"):
            lines = indi("@I1@", "John /Doe/", "M", "1 JAN 1970") + \
                    indi("@I2@", "Jane /Roe/", "F", "1 JAN 1972") + \
                    indi("@I3@", "Mary /Doe/", "F", "1 JAN 2000") + \
                    indi("@I4@", "Mary /Doe/", "F", "1 JAN 2000") + \
                    fam("@F1@", "1 JUN 1995", husb="@I1@", wife="@I2@", children=["@I3@", "@I4@"])
            errs = errors_with('US21', lines)
            self.assertEqual(len(errs), 1)
            self.assertEqual(errs[0].line_no, 16)  # second child starts on line 16
            self.assertIn('I04', errs[0].message)
            self.assertIn('I03', errs[0].message)
            self.assertIn('F01', errs[0].message)

    def test_same_name_different_birth_not_flagged(self):
        with TestLogger("US21: The same child name with a different birth date should not be flagged"):
            lines = indi("@I1@", "John /Doe/", "M", "1 JAN 1970") + \
                    indi("@I2@", "Jane /Roe/", "F", "1 JAN 1972") + \
                    indi("@I3@", "Mary /Doe/", "F", "1 JAN 2000") + \
                    indi("@I4@", "Mary /Doe/", "F", "2 JAN 2000") + \
                    fam("@F1@", "1 JUN 1995", husb="@I1@", wife="@I2@", children=["@I3@", "@I4@"])
            self.assertEqual(errors_with('US21', lines), [])

    def test_different_name_same_birth_not_flagged(self):
        with TestLogger("US21: Different child names on the same birth date should not be flagged"):
            lines = indi("@I1@", "John /Doe/", "M", "1 JAN 1970") + \
                    indi("@I2@", "Jane /Roe/", "F", "1 JAN 1972") + \
                    indi("@I3@", "Mary /Doe/", "F", "1 JAN 2000") + \
                    indi("@I4@", "Martha /Doe/", "F", "1 JAN 2000") + \
                    fam("@F1@", "1 JUN 1995", husb="@I1@", wife="@I2@", children=["@I3@", "@I4@"])
            self.assertEqual(errors_with('US21', lines), [])

    def test_same_name_and_birth_in_another_family_not_flagged(self):
        with TestLogger("US21: The same child name and birth date in another family should not be flagged"):
            lines = indi("@I1@", "John /Doe/", "M", "1 JAN 1970") + \
                    indi("@I2@", "Jane /Roe/", "F", "1 JAN 1972") + \
                    indi("@I3@", "Mary /Doe/", "F", "1 JAN 2000") + \
                    indi("@I4@", "Bob /Smith/", "M", "1 JAN 1971") + \
                    indi("@I5@", "Sue /Smith/", "F", "1 JAN 1973") + \
                    indi("@I6@", "Mary /Doe/", "F", "1 JAN 2000") + \
                    fam("@F1@", "1 JUN 1995", husb="@I1@", wife="@I2@", children=["@I3@"]) + \
                    fam("@F2@", "1 JUN 1998", husb="@I4@", wife="@I5@", children=["@I6@"])
            self.assertEqual(errors_with('US21', lines), [])

    def test_child_name_case_is_flagged(self):
        with TestLogger("US21: Child names that differ only by case should be flagged"):
            lines = indi("@I1@", "John /Doe/", "M", "1 JAN 1970") + \
                    indi("@I2@", "Jane /Roe/", "F", "1 JAN 1972") + \
                    indi("@I3@", "Mary /Doe/", "F", "1 JAN 2000") + \
                    indi("@I4@", "mary /doe/", "F", "1 JAN 2000") + \
                    fam("@F1@", "1 JUN 1995", husb="@I1@", wife="@I2@", children=["@I3@", "@I4@"])
            errs = errors_with('US21', lines)
            self.assertEqual(len(errs), 1)
            self.assertIn('I04', errs[0].message)

    def test_three_children_flag_the_later_two(self):
        with TestLogger("US21: Each later child with the same name and birth date should be flagged"):
            lines = indi("@I1@", "John /Doe/", "M", "1 JAN 1970") + \
                    indi("@I2@", "Jane /Roe/", "F", "1 JAN 1972") + \
                    indi("@I3@", "Mary /Doe/", "F", "1 JAN 2000") + \
                    indi("@I4@", "Mary /Doe/", "F", "1 JAN 2000") + \
                    indi("@I5@", "Mary /Doe/", "M", "1 JAN 2000") + \
                    fam("@F1@", "1 JUN 1995", husb="@I1@", wife="@I2@",
                        children=["@I3@", "@I4@", "@I5@"])
            errs = errors_with('US21', lines)
            self.assertEqual(len(errs), 2)
            self.assertEqual([e.line_no for e in errs], [16, 21])
            self.assertTrue(all('I03' in e.message for e in errs))


if __name__ == '__main__':
    unittest.main()

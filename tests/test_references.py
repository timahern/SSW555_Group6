import unittest

from gedcom_parser import validate_gedcom_lines
from tests import TestLogger


class ReferenceTestBase(unittest.TestCase):
    """Shared helpers for the US38 and US41 reference checks."""

    def run_validation(self, lines):
        _, _, errors = validate_gedcom_lines(lines)
        return errors

    def codes(self, lines, code):
        return [e for e in self.run_validation(lines) if e.code == code]

    def gedcom(self, *extra):
        """One valid family (John, Mary, child Jake) with optional extra lines."""
        return [
            '0 HEAD',
            '0 @I1@ INDI',
            '1 NAME John /Smith/',
            '1 SEX M',
            '1 BIRT',
            '2 DATE 1 JAN 1960',
            '1 FAMS @F1@',
            '0 @I2@ INDI',
            '1 NAME Mary /Smith/',
            '1 SEX F',
            '1 BIRT',
            '2 DATE 1 JAN 1962',
            '1 FAMS @F1@',
            '0 @I3@ INDI',
            '1 NAME Jake /Smith/',
            '1 SEX M',
            '1 BIRT',
            '2 DATE 1 JAN 1990',
            '1 FAMC @F1@',
            '0 @F1@ FAM',
            '1 HUSB @I1@',
            '1 WIFE @I2@',
            '1 CHIL @I3@',
            '1 MARR',
            '2 DATE 1 JUN 1985',
            *extra,
            '0 TRLR',
        ]


class TestUS38ValidReferences(ReferenceTestBase):

    def test_clean_family_passes(self):
        with TestLogger("US38: Clean family should have no REF_MISSING errors"):
            self.assertEqual(self.codes(self.gedcom(), 'REF_MISSING'), [])

    def test_child_pointing_to_nobody(self):
        with TestLogger("US38: CHIL pointing to non-existent individual should report REF_MISSING with @I99@ in message"):
            errs = self.codes(self.gedcom('1 CHIL @I99@'), 'REF_MISSING')
            self.assertEqual(len(errs), 1)
            self.assertIn('@I99@', errs[0].message)

    def test_spouse_pointing_to_nobody(self):
        with TestLogger("US38: WIFE pointing to non-existent individual should report REF_MISSING"):
            lines = self.gedcom(
                '0 @F2@ FAM',
                '1 HUSB @I1@',
                '1 WIFE @I98@',
                '1 MARR',
                '2 DATE 1 JUN 2000',
            )
            errs = self.codes(lines, 'REF_MISSING')
            self.assertEqual(len(errs), 1)
            self.assertIn('WIFE @I98@', errs[0].message)

    def test_individual_pointing_to_missing_family(self):
        with TestLogger("US38: Individual with FAMS to missing family should report REF_MISSING with FAMS @F99@"):
            lines = self.gedcom(
                '0 @I4@ INDI',
                '1 NAME Ann /Lee/',
                '1 SEX F',
                '1 BIRT',
                '2 DATE 1 JAN 1970',
                '1 FAMS @F99@',
            )
            errs = self.codes(lines, 'REF_MISSING')
            self.assertEqual(len(errs), 1)
            self.assertIn('FAMS @F99@', errs[0].message)

    def test_child_pointing_to_a_family_is_wrong_type(self):
        with TestLogger("US38: CHIL referencing a family ID should report REF_MISSING"):
            errs = self.codes(self.gedcom('1 CHIL @F1@'), 'REF_MISSING')
            self.assertEqual(len(errs), 1)


class TestUS41NoDuplicateReferences(ReferenceTestBase):

    def test_clean_family_passes(self):
        with TestLogger("US41: Clean family should have no REF_DUPLICATE errors"):
            self.assertEqual(self.codes(self.gedcom(), 'REF_DUPLICATE'), [])

    def test_child_listed_twice_in_one_family(self):
        with TestLogger("US41: Duplicate CHIL entries in one family should report a single REF_DUPLICATE"):
            errs = self.codes(self.gedcom('1 CHIL @I3@'), 'REF_DUPLICATE')
            self.assertEqual(len(errs), 1)
            self.assertIn('CHIL @I3@', errs[0].message)

    def test_spouse_family_listed_twice_on_individual(self):
        with TestLogger("US41: Duplicate FAMS entries on an individual should report REF_DUPLICATE"):
            lines = self.gedcom(
                '0 @I4@ INDI',
                '1 NAME Ann /Lee/',
                '1 SEX F',
                '1 BIRT',
                '2 DATE 1 JAN 1970',
                '1 FAMS @F1@',
                '1 FAMS @F1@',
            )
            errs = self.codes(lines, 'REF_DUPLICATE')
            self.assertEqual(len(errs), 1)
            self.assertIn('FAMS @F1@', errs[0].message)

    def test_same_child_in_two_families_is_allowed(self):
        with TestLogger("US41: Same child in two different families should not be a duplicate error"):
            lines = self.gedcom(
                '0 @F2@ FAM',
                '1 HUSB @I1@',
                '1 WIFE @I2@',
                '1 CHIL @I3@',
                '1 MARR',
                '2 DATE 1 JUN 2000',
            )
            self.assertEqual(self.codes(lines, 'REF_DUPLICATE'), [])

    def test_child_listed_three_times_reports_each_extra(self):
        with TestLogger("US41: Child listed three times should report two REF_DUPLICATE errors"):
            errs = self.codes(self.gedcom('1 CHIL @I3@', '1 CHIL @I3@'), 'REF_DUPLICATE')
            self.assertEqual(len(errs), 2)


if __name__ == '__main__':
    unittest.main()
import unittest

from gedcom_parser import validate_gedcom_lines
from tests import TestLogger


class TestCorrespondingFamilyEntries(unittest.TestCase):

    def test_famc_must_correspond_to_child(self):
        with TestLogger("FAMC on child must correspond to CHIL in the referenced family"):
            gedcom = [
                "0 I01 INDI",
                "1 NAME Alice /Jones/",
                "1 SEX F",
                "1 BIRT",
                "2 DATE 01 JAN 2000",
                "1 FAMC F01",

                "0 I02 INDI",
                "1 NAME John /Jones/",
                "1 SEX M",
                "1 BIRT",
                "2 DATE 01 JAN 1970",
                "1 FAMS F01",

                "0 I03 INDI",
                "1 NAME Mary /Smith/",
                "1 SEX F",
                "1 BIRT",
                "2 DATE 01 JAN 1972",
                "1 FAMS F01",

                "0 F01 FAM",
                "1 MARR",
                "2 DATE 01 JAN 1999",
                "1 HUSB I02",
                "1 WIFE I03",
                "1 CHIL I01",
            ]

            individuals, families, errors = validate_gedcom_lines(gedcom)

            self.assertEqual(errors, [])

    def test_famc_without_matching_child_is_error(self):
        with TestLogger("FAMC reference without corresponding CHIL in family should be REF_MISMATCH error"):
            gedcom = [
                "0 I01 INDI",
                "1 NAME Alice /Jones/",
                "1 SEX F",
                "1 BIRT",
                "2 DATE 01 JAN 2000",
                "1 FAMC F01",

                "0 I02 INDI",
                "1 NAME John /Jones/",
                "1 SEX M",
                "1 BIRT",
                "2 DATE 01 JAN 1970",
                "1 FAMS F01",

                "0 I03 INDI",
                "1 NAME Mary /Smith/",
                "1 SEX F",
                "1 BIRT",
                "2 DATE 01 JAN 1972",
                "1 FAMS F01",

                "0 F01 FAM",
                "1 MARR",
                "2 DATE 01 JAN 1999",
                "1 HUSB I02",
                "1 WIFE I03",
            ]

            individuals, families, errors = validate_gedcom_lines(gedcom)

            self.assertTrue(any(error.code == 'REF_MISMATCH' for error in errors))


if __name__ == '__main__':
    unittest.main()

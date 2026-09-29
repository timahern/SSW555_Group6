import unittest
from io import StringIO

from gedcom_parser import validate_gedcom_lines
from tests import TestLogger


class TestUS18UniqueIDs(unittest.TestCase):
    def test_duplicate_individual_id_is_flagged(self):
        with TestLogger("US18: Duplicate individual ID should be flagged at the second occurrence line"):
            data = StringIO("\n".join([
                "0 @I1@ INDI",
                "1 NAME John /Doe/",
                "1 SEX M",
                "1 BIRT",
                "2 DATE 15 MAR 1990",
                "0 @I1@ INDI", 
                "1 NAME Jane /Doe/",
                "1 SEX F",
                "1 BIRT",
                "2 DATE 20 APR 1992",
            ]))
            _, _, errors = validate_gedcom_lines(data)
            self.assertTrue(any(e.code == 'US18' and e.line_no == 6 for e in errors))

    def test_duplicate_family_id_is_flagged(self):
        with TestLogger("US18: Duplicate family ID should be flagged at the second occurrence line"):
            data = StringIO("\n".join([
                "0 @F1@ FAM",
                "1 MARR",
                "2 DATE 10 JUN 1985",
                "0 @F1@ FAM", 
                "1 MARR",
                "2 DATE 12 JUL 1995",
            ]))
            _, _, errors = validate_gedcom_lines(data)
            self.assertTrue(any(e.code == 'US18' and e.line_no == 4 for e in errors))

    def test_duplicate_does_not_overwrite_original(self):
        with TestLogger("US18: Original individual data should be preserved when duplicate ID appears later"):
            data = StringIO("\n".join([
                "0 @I1@ INDI",
                "1 NAME John /Doe/",
                "1 SEX M",
                "1 BIRT",
                "2 DATE 15 MAR 1990",
                "0 @I1@ INDI",
                "1 NAME Jane /Doe/",
                "1 SEX F",
                "1 BIRT",
                "2 DATE 20 APR 1992",
            ]))
            individuals, _, _ = validate_gedcom_lines(data)
            self.assertEqual(individuals['@I1@']['name'], 'John /Doe/')

    def test_unique_ids_not_flagged(self):
        with TestLogger("US18: Unique individual and family IDs should not produce US18 errors"):
            data = StringIO("\n".join([
                "0 @I1@ INDI",
                "1 NAME John /Doe/",
                "1 SEX M",
                "1 BIRT",
                "2 DATE 15 MAR 1990",
                "0 @I2@ INDI",       
                "1 NAME Jane /Doe/",
                "1 SEX F",
                "1 BIRT",
                "2 DATE 20 APR 1992",
                "0 @F1@ FAM",
                "1 MARR",
                "2 DATE 10 JUN 2015",
            ]))
            _, _, errors = validate_gedcom_lines(data)
            self.assertFalse(any(e.code == 'US18' for e in errors))


class TestUS19UniqueNameAndBirth(unittest.TestCase):
    def test_same_name_and_birth_is_flagged(self):
        with TestLogger("US19: Two individuals with same NAME and BIRT should be flagged at second individual's line"):
            data = StringIO("\n".join([
                "0 @I1@ INDI",
                "1 NAME John /Doe/",
                "1 SEX M",
                "1 BIRT",
                "2 DATE 15 MAR 1990",
                "0 @I2@ INDI",      
                "1 NAME John /Doe/",
                "1 SEX M",
                "1 BIRT",
                "2 DATE 15 MAR 1990",
            ]))
            _, _, errors = validate_gedcom_lines(data)
            self.assertTrue(any(e.code == 'US19' and e.line_no == 6 for e in errors))

    def test_same_name_different_birth_not_flagged(self):
        with TestLogger("US19: Same NAME but different BIRT should not be flagged"):
            data = StringIO("\n".join([
                "0 @I1@ INDI",
                "1 NAME John /Doe/",
                "1 SEX M",
                "1 BIRT",
                "2 DATE 15 MAR 1990",
                "0 @I2@ INDI",
                "1 NAME John /Doe/",
                "1 SEX M",
                "1 BIRT",
                "2 DATE 15 MAR 2015", 
            ]))
            _, _, errors = validate_gedcom_lines(data)
            self.assertFalse(any(e.code == 'US19' for e in errors))

    def test_different_name_same_birth_not_flagged(self):
        with TestLogger("US19: Different NAME with same BIRT should not be flagged"):
            data = StringIO("\n".join([
                "0 @I1@ INDI",
                "1 NAME John /Doe/",
                "1 SEX M",
                "1 BIRT",
                "2 DATE 15 MAR 1990",
                "0 @I2@ INDI",
                "1 NAME Jack /Doe/",  
                "1 SEX M",
                "1 BIRT",
                "2 DATE 15 MAR 1990",
            ]))
            _, _, errors = validate_gedcom_lines(data)
            self.assertFalse(any(e.code == 'US19' for e in errors))


if __name__ == '__main__':
    unittest.main()
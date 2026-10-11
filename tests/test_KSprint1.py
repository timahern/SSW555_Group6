import unittest
from io import StringIO

from gedcom_parser import validate_gedcom_lines


class TestUS18UniqueIDs(unittest.TestCase):
    def test_duplicate_individual_id_is_flagged(self):
        data = StringIO("\n".join([
            "0 @I1@ INDI",
            "1 NAME John /Doe/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 15 MAR 1990",
            "0 @I1@ INDI",        # Invalid: reuses ID @I1@
            "1 NAME Jane /Doe/",
            "1 SEX F",
            "1 BIRT",
            "2 DATE 20 APR 1992",
        ]))
        _, _, errors = validate_gedcom_lines(data)
        self.assertTrue(any(e.code == 'US18' and e.line_no == 6 for e in errors))

    def test_duplicate_family_id_is_flagged(self):
        data = StringIO("\n".join([
            "0 @F1@ FAM",
            "1 MARR",
            "2 DATE 10 JUN 1985",
            "0 @F1@ FAM",         # Invalid: reuses ID @F1@
            "1 MARR",
            "2 DATE 12 JUL 1995",
        ]))
        _, _, errors = validate_gedcom_lines(data)
        self.assertTrue(any(e.code == 'US18' and e.line_no == 4 for e in errors))

    def test_duplicate_does_not_overwrite_original(self):
        data = StringIO("\n".join([
            "0 @I1@ INDI",
            "1 NAME John /Doe/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 15 MAR 1990",
            "0 @I1@ INDI",        # Duplicate should not replace John
            "1 NAME Jane /Doe/",
            "1 SEX F",
            "1 BIRT",
            "2 DATE 20 APR 1992",
        ]))
        individuals, _, _ = validate_gedcom_lines(data)
        self.assertEqual(individuals['@I1@']['name'], 'John /Doe/')

    def test_unique_ids_not_flagged(self):
        data = StringIO("\n".join([
            "0 @I1@ INDI",
            "1 NAME John /Doe/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 15 MAR 1990",
            "0 @I2@ INDI",        # Different ID: valid
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

    def test_three_records_same_id_flagged_twice(self):
        data = StringIO("\n".join([
            "0 @I1@ INDI",
            "1 NAME John /Doe/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 15 MAR 1990",
            "0 @I1@ INDI",        # Invalid: first duplicate
            "1 NAME Jane /Doe/",
            "1 SEX F",
            "1 BIRT",
            "2 DATE 20 APR 1992",
            "0 @I1@ INDI",        # Invalid: second duplicate
            "1 NAME Jack /Doe/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 5 JAN 1995",
        ]))
        _, _, errors = validate_gedcom_lines(data)
        us18 = [e for e in errors if e.code == 'US18']
        self.assertEqual(len(us18), 2)

    def test_error_message_names_duplicate_id(self):
        data = StringIO("\n".join([
            "0 @F7@ FAM",
            "1 MARR",
            "2 DATE 10 JUN 1985",
            "0 @F7@ FAM",         # Invalid: reuses ID @F7@
            "1 MARR",
            "2 DATE 12 JUL 1995",
        ]))
        _, _, errors = validate_gedcom_lines(data)
        us18 = [e for e in errors if e.code == 'US18']
        self.assertIn('@F7@', us18[0].message)


class TestUS19UniqueNameAndBirth(unittest.TestCase):
    def test_same_name_and_birth_is_flagged(self):
        data = StringIO("\n".join([
            "0 @I1@ INDI",
            "1 NAME John /Doe/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 15 MAR 1990",
            "0 @I2@ INDI",        # Invalid: same name and birth date as @I1@
            "1 NAME John /Doe/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 15 MAR 1990",
        ]))
        _, _, errors = validate_gedcom_lines(data)
        self.assertTrue(any(e.code == 'US19' and e.line_no == 6 for e in errors))

    def test_same_name_different_birth_not_flagged(self):
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
            "2 DATE 15 MAR 2015",  # Different birth date: valid
        ]))
        _, _, errors = validate_gedcom_lines(data)
        self.assertFalse(any(e.code == 'US19' for e in errors))

    def test_different_name_same_birth_not_flagged(self):
        data = StringIO("\n".join([
            "0 @I1@ INDI",
            "1 NAME John /Doe/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 15 MAR 1990",
            "0 @I2@ INDI",
            "1 NAME Jack /Doe/",   # Different name: valid (e.g. twins)
            "1 SEX M",
            "1 BIRT",
            "2 DATE 15 MAR 1990",
        ]))
        _, _, errors = validate_gedcom_lines(data)
        self.assertFalse(any(e.code == 'US19' for e in errors))


if __name__ == '__main__':
    unittest.main()
import unittest
from io import StringIO

from gedcom_parser import validate_gedcom_lines


class TestGedcomValidation(unittest.TestCase):
    def test_date_without_parent_event_is_flagged(self):
        data = StringIO("\n".join([
            "0 @I1@ INDI",
            "1 NAME John /Doe/",
            "2 DATE 15 MAR 1990",  # Invalid: level-2 DATE without BIRT/DEAT parent
        ]))
        _, _, errors = validate_gedcom_lines(data)
        self.assertTrue(any(e.code == 'DATE_PARENT' and e.line_no == 3 for e in errors))

    def test_individual_missing_birth_date(self):
        data = StringIO("\n".join([
            "0 @I1@ INDI",
            "1 NAME John /Doe/",
            "1 SEX M",
            "1 BIRT",              # Missing following 2 DATE
            "0 @F1@ FAM",          # Triggers close of INDI and post-checks
        ]))
        _, _, errors = validate_gedcom_lines(data)
        self.assertTrue(any(e.code == 'INDI_BIRT' for e in errors))

    def test_invalid_sex_value(self):
        data = StringIO("\n".join([
            "0 @I1@ INDI",
            "1 NAME Jane /Doe/",
            "1 SEX X",            # Invalid value
            "1 BIRT",
            "2 DATE 1990",        # Allow year-only per updated rules
        ]))
        _, _, errors = validate_gedcom_lines(data)
        self.assertTrue(any(e.code == 'INDI_SEX' for e in errors))

    def test_name_without_surname_slashes(self):
        data = StringIO("\n".join([
            "0 @I1@ INDI",
            "1 NAME Jane Doe",    # Missing /surname/
            "1 SEX F",
            "1 BIRT",
            "2 DATE 15 MAR 1990",
        ]))
        _, _, errors = validate_gedcom_lines(data)
        self.assertTrue(any(e.code == 'INDI_NAME' for e in errors))

    def test_family_missing_marr_date(self):
        data = StringIO("\n".join([
            "0 @F1@ FAM",
            "1 HUSB @I1@",
            "1 WIFE @I2@",
            "1 MARR",             # Missing 2 DATE
            "0 @I1@ INDI",        # Close FAM; check should trigger
            "1 NAME John /Doe/",
            "1 SEX M",
            "1 BIRT",
            "2 DATE 1990",
        ]))
        _, _, errors = validate_gedcom_lines(data)
        self.assertTrue(any(e.code == 'FAM_MARR' for e in errors))


if __name__ == '__main__':
    unittest.main()

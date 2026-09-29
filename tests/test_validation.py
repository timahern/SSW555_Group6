import unittest
from io import StringIO

from gedcom_parser import validate_gedcom_lines
from tests import TestLogger


class TestGedcomValidation(unittest.TestCase):
    def test_date_without_parent_event_is_flagged(self):
        with TestLogger("Level-2 DATE without parent event (BIRT/DEAT/MARR/DIV) is flagged as DATE_PARENT at correct line"):
            data = StringIO("\n".join([
                "0 @I1@ INDI",
                "1 NAME John /Doe/",
                "2 DATE 15 MAR 1990",  # Invalid: level-2 DATE without BIRT/DEAT parent
            ]))
            _, _, errors = validate_gedcom_lines(data)
            self.assertTrue(any(e.code == 'DATE_PARENT' and e.line_no == 3 for e in errors))

    def test_individual_missing_birth_date(self):
        with TestLogger("Individual missing birth date after BIRT is flagged as INDI_BIRT"):
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
        with TestLogger("Invalid SEX value is flagged as INDI_SEX"):
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
        with TestLogger("NAME without /surname/ delimiters is flagged as INDI_NAME"):
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
        with TestLogger("FAM with MARR but missing DATE is flagged as FAM_MARR"):
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

    def test_invalid_calendar_date(self):
        with TestLogger("Invalid calendar date is flagged as DATE_FORMAT"):
            data = StringIO("\n".join([
                "0 @I1@ INDI",
                "1 NAME John /Doe/",
                "1 SEX M",
                "1 BIRT",
                "2 DATE 30 FEB 2015",
            ]))
            _, _, errors = validate_gedcom_lines(data)
            self.assertTrue(any(e.code == 'DATE_FORMAT' for e in errors))

    def test_future_event_dates(self):
        cases = [
            [
                "0 @I1@ INDI",
                "1 NAME John /Doe/",
                "1 SEX M",
                "1 BIRT",
                "2 DATE 1 JAN 2099",
            ],
            [
                "0 @I1@ INDI",
                "1 NAME John /Doe/",
                "1 SEX M",
                "1 BIRT",
                "2 DATE 1 JAN 2000",
                "1 DEAT",
                "2 DATE 1 JAN 2099",
            ],
            [
                "0 @F1@ FAM",
                "1 MARR",
                "2 DATE 1 JAN 2099",
                "1 HUSB @I1@",
                "1 WIFE @I2@",
            ],
            [
                "0 @F1@ FAM",
                "1 MARR",
                "2 DATE 1 JAN 2000",
                "1 DIV",
                "2 DATE 1 JAN 2099",
                "1 HUSB @I1@",
                "1 WIFE @I2@",
            ],
        ]
        for idx, lines in enumerate(cases, start=1):
            with self.subTest(case=idx):
                with TestLogger(f"Future-dated events are flagged as DATE_FUTURE (case {idx})"):
                    _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
                    self.assertTrue(any(e.code == 'DATE_FUTURE' for e in errors))

    def test_lifespan(self):
        with TestLogger("Individual with DEAT before BIRT is flagged as INDI_LIFESPAN"):
            data = StringIO("\n".join([
                "0 @I1@ INDI",
                "1 NAME John /Doe/",
                "1 SEX M",
                "1 BIRT",
                "2 DATE 1 JAN 2000",
                "1 DEAT",
                "2 DATE 1 JAN 1990",
            ]))
            _, _, errors = validate_gedcom_lines(data)
            self.assertTrue(any(e.code == 'INDI_LIFESPAN' for e in errors))


if __name__ == '__main__':
    unittest.main()

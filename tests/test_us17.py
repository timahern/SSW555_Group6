import unittest
from io import StringIO

from gedcom_parser import validate_gedcom_lines
from tests import TestLogger


class TestUS17AuntUncleMarriages(unittest.TestCase):
    def test_uncle_marries_niece_is_flagged(self):
        # Build tree:
        #   GP family -> children: P1 (parent) and U1 (uncle)
        #   P1 marries P2 -> child N1 (niece)
        #   U1 marries N1 -> should trigger US17
        lines = [
            # Individuals
            "0 @P1@ INDI", "1 NAME ParentOne /Doe/", "1 SEX M", "1 BIRT", "2 DATE 1 JAN 1960",
            "0 @P2@ INDI", "1 NAME ParentTwo /Doe/", "1 SEX F", "1 BIRT", "2 DATE 1 JAN 1962",
            "0 @U1@ INDI", "1 NAME UncleOne /Doe/", "1 SEX M", "1 BIRT", "2 DATE 1 JAN 1965",
            "0 @N1@ INDI", "1 NAME NieceOne /Doe/", "1 SEX F", "1 BIRT", "2 DATE 1 JAN 1990",
            # Grandparent family with siblings P1 and U1
            "0 @FGP@ FAM",
            "1 HUSB @IGF@",  # grandparents (not defined further; not needed for rule)
            "1 WIFE @IGM@",
            "1 MARR", "2 DATE 1 JAN 1955",
            "1 CHIL @P1@",
            "1 CHIL @U1@",
            # P1 and P2 marry and have child N1
            "0 @F1@ FAM",
            "1 HUSB @P1@",
            "1 WIFE @P2@",
            "1 MARR", "2 DATE 1 JAN 1985",
            "1 CHIL @N1@",
            # U1 marries N1 (niece) -> invalid
            "0 @FM@ FAM",
            "1 HUSB @U1@",
            "1 WIFE @N1@",
            "1 MARR", "2 DATE 1 JAN 2010",
        ]
        with TestLogger("US17: uncle marrying niece should be flagged"):
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            self.assertTrue(any(e.code == 'US17' for e in errors), f"Expected US17 error, got: {errors}")

    def test_cousins_marrying_is_allowed(self):
        # Cousins marriage should NOT be flagged by US17.
        # Build tree:
        #   GP family -> children: A and B (siblings)
        #   A marries X -> child C1
        #   B marries Y -> child C2
        #   C1 marries C2 (cousins) -> allowed for US17
        lines = [
            # Individuals
            "0 @A@ INDI", "1 NAME Alice /Doe/", "1 SEX F", "1 BIRT", "2 DATE 1 JAN 1970",
            "0 @B@ INDI", "1 NAME Bob /Doe/", "1 SEX M", "1 BIRT", "2 DATE 1 JAN 1972",
            "0 @X@ INDI", "1 NAME Xavier /Roe/", "1 SEX M", "1 BIRT", "2 DATE 1 JAN 1969",
            "0 @Y@ INDI", "1 NAME Yara /Moe/", "1 SEX F", "1 BIRT", "2 DATE 1 JAN 1971",
            "0 @C1@ INDI", "1 NAME Charlie /Doe/", "1 SEX M", "1 BIRT", "2 DATE 1 JAN 1995",
            "0 @C2@ INDI", "1 NAME Clara /Doe/", "1 SEX F", "1 BIRT", "2 DATE 1 JAN 1996",
            # Grandparent family with siblings A and B
            "0 @FGP@ FAM",
            "1 HUSB @IGF@",
            "1 WIFE @IGM@",
            "1 MARR", "2 DATE 1 JAN 1965",
            "1 CHIL @A@",
            "1 CHIL @B@",
            # A and X -> child C1
            "0 @F1@ FAM",
            "1 HUSB @X@",
            "1 WIFE @A@",
            "1 MARR", "2 DATE 1 JAN 1990",
            "1 CHIL @C1@",
            # B and Y -> child C2
            "0 @F2@ FAM",
            "1 HUSB @B@",
            "1 WIFE @Y@",
            "1 MARR", "2 DATE 1 JAN 1991",
            "1 CHIL @C2@",
            # C1 and C2 marry (cousins) -> should not trigger US17
            "0 @FC@ FAM",
            "1 HUSB @C1@",
            "1 WIFE @C2@",
            "1 MARR", "2 DATE 1 JAN 2020",
        ]
        with TestLogger("US17: cousins marrying should not be flagged"):
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            self.assertFalse(any(e.code == 'US17' for e in errors), f"Unexpected US17 errors: {errors}")

    def test_missing_parent_info_does_not_flag(self):
        # If there is no parental information to infer aunt/uncle relationships, do not flag.
        lines = [
            "0 @I1@ INDI", "1 NAME John /Smith/", "1 SEX M", "1 BIRT", "2 DATE 1 JAN 1980",
            "0 @I2@ INDI", "1 NAME Jane /Smith/", "1 SEX F", "1 BIRT", "2 DATE 1 JAN 1982",
            "0 @F1@ FAM",
            "1 HUSB @I1@",
            "1 WIFE @I2@",
            "1 MARR", "2 DATE 1 JAN 2005",
        ]
        with TestLogger("US17: lack of parents info should not create false positives"):
            _, _, errors = validate_gedcom_lines(StringIO("\n".join(lines)))
            self.assertFalse(any(e.code == 'US17' for e in errors), f"Unexpected US17 errors: {errors}")


if __name__ == '__main__':
    unittest.main()

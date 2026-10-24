import unittest
from io import StringIO

from gedcom_parser import validate_gedcom_lines, compute_siblings_by_age
from tests import TestLogger


class TestUS24SiblingsOrderedByAge(unittest.TestCase):
    def _parse(self, lines):
        return validate_gedcom_lines(StringIO("\n".join(lines)))

    def test_siblings_ordered_oldest_first(self):
        # Family F1 with three children, ensure oldest (earliest birth) first
        lines = [
            # Parents (to satisfy validations)
            "0 @H@ INDI", "1 NAME Hank /Doe/", "1 SEX M", "1 BIRT", "2 DATE 1 JAN 1970",
            "0 @W@ INDI", "1 NAME Wendy /Doe/", "1 SEX F", "1 BIRT", "2 DATE 1 JAN 1972",
            # Children
            "0 @C1@ INDI", "1 NAME ChildOne /Doe/", "1 SEX F", "1 BIRT", "2 DATE 1 JAN 2000",
            "0 @C2@ INDI", "1 NAME ChildTwo /Doe/", "1 SEX M", "1 BIRT", "2 DATE 1 JAN 1998",
            "0 @C3@ INDI", "1 NAME ChildThree /Doe/", "1 SEX F", "1 BIRT", "2 DATE 15 JUN 1999",
            # Family with children
            "0 @F1@ FAM",
            "1 HUSB @H@",
            "1 WIFE @W@",
            "1 MARR", "2 DATE 1 JAN 1995",
            "1 CHIL @C1@",
            "1 CHIL @C2@",
            "1 CHIL @C3@",
        ]
        with TestLogger("US24: siblings ordered oldest first"):
            individuals, families, errors = self._parse(lines)
            ordered = compute_siblings_by_age(individuals, families)
            self.assertEqual(ordered.get('@F1@'), ['@C2@', '@C3@', '@C1@'])

    def test_unknown_birth_dates_go_last(self):
        # One child missing birth date should appear after those with known dates
        lines = [
            "0 @H@ INDI", "1 NAME Hank /Doe/", "1 SEX M", "1 BIRT", "2 DATE 1 JAN 1970",
            "0 @W@ INDI", "1 NAME Wendy /Doe/", "1 SEX F", "1 BIRT", "2 DATE 1 JAN 1972",
            "0 @C1@ INDI", "1 NAME ChildOne /Doe/", "1 SEX F", "1 BIRT", "2 DATE 1 JAN 2001",
            "0 @C2@ INDI", "1 NAME ChildTwo /Doe/", "1 SEX M", "1 BIRT", "2 DATE 1 JAN 1999",
            # C3 has no BIRT date
            "0 @C3@ INDI", "1 NAME ChildThree /Doe/", "1 SEX F",
            "0 @F1@ FAM",
            "1 HUSB @H@",
            "1 WIFE @W@",
            "1 MARR", "2 DATE 1 JAN 1995",
            "1 CHIL @C1@",
            "1 CHIL @C2@",
            "1 CHIL @C3@",
        ]
        with TestLogger("US24: unknown birth dates go last"):
            individuals, families, errors = self._parse(lines)
            ordered = compute_siblings_by_age(individuals, families)
            self.assertEqual(ordered.get('@F1@'), ['@C2@', '@C1@', '@C3@'])

    def test_tie_breaker_same_birth_date_by_id(self):
        # Children with the same birth date should be ordered deterministically by displayId
        # We'll use IDs C1, C2, C10 with the same date; expected order: C01, C02, C10 -> @C1@, @C2@, @C10@
        lines = [
            "0 @H@ INDI", "1 NAME Hank /Doe/", "1 SEX M", "1 BIRT", "2 DATE 1 JAN 1970",
            "0 @W@ INDI", "1 NAME Wendy /Doe/", "1 SEX F", "1 BIRT", "2 DATE 1 JAN 1972",
            "0 @C1@ INDI", "1 NAME ChildOne /Doe/", "1 SEX F", "1 BIRT", "2 DATE 1 JAN 2000",
            "0 @C2@ INDI", "1 NAME ChildTwo /Doe/", "1 SEX M", "1 BIRT", "2 DATE 1 JAN 2000",
            "0 @C10@ INDI", "1 NAME ChildTen /Doe/", "1 SEX M", "1 BIRT", "2 DATE 1 JAN 2000",
            "0 @F1@ FAM",
            "1 HUSB @H@",
            "1 WIFE @W@",
            "1 MARR", "2 DATE 1 JAN 1995",
            "1 CHIL @C1@",
            "1 CHIL @C2@",
            "1 CHIL @C10@",
        ]
        with TestLogger("US24: tie-breaker by displayId for same birth date"):
            individuals, families, errors = self._parse(lines)
            ordered = compute_siblings_by_age(individuals, families)
            self.assertEqual(ordered.get('@F1@'), ['@C1@', '@C2@', '@C10@'])


if __name__ == '__main__':
    unittest.main()

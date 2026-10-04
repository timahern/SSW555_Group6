import unittest
from us09 import parents_not_too_old

#CODED VIA PAIR PROGRAMMING WITH KENT BERRY AND TIMOTHY AHERN



def indi(birth):
    return {'birth': birth, 'name': None, 'sex': None, 'death': None,
            'famc': [], 'fams': []}


def fam(husband, wife, children):
    return {'husband': husband, 'wife': wife, 'children': children,
            'married': None, 'divorced': None}


class TestUS09(unittest.TestCase):

    def test_normal_family_no_errors(self):
        individuals = {
            '@I1@': indi('1 JAN 1960'),
            '@I2@': indi('1 JAN 1962'),
            '@I3@': indi('1 JAN 1990'),
        }
        families = {'@F1@': fam('@I1@', '@I2@', ['@I3@'])}
        self.assertEqual(parents_not_too_old(individuals, families), [])

    def test_mother_too_old(self):
        individuals = {
            '@I1@': indi('1 JAN 1950'),
            '@I2@': indi('1 JAN 1900'),
            '@I3@': indi('1 JAN 1965'),
        }
        families = {'@F1@': fam('@I1@', '@I2@', ['@I3@'])}
        errors = parents_not_too_old(individuals, families)
        self.assertEqual(len(errors), 1)
        self.assertIn('Mother', errors[0])

    def test_father_too_old(self):
        individuals = {
            '@I1@': indi('1 JAN 1900'),
            '@I2@': indi('1 JAN 1950'),
            '@I3@': indi('1 JAN 1985'),
        }
        families = {'@F1@': fam('@I1@', '@I2@', ['@I3@'])}
        errors = parents_not_too_old(individuals, families)
        self.assertEqual(len(errors), 1)
        self.assertIn('Father', errors[0])

    def test_mother_exactly_60_is_error(self):
        individuals = {
            '@I1@': indi('1 JAN 1950'),
            '@I2@': indi('5 MAY 1900'),
            '@I3@': indi('5 MAY 1960'),
        }
        families = {'@F1@': fam('@I1@', '@I2@', ['@I3@'])}
        self.assertEqual(len(parents_not_too_old(individuals, families)), 1)

    def test_mother_one_day_under_60_is_ok(self):
        individuals = {
            '@I1@': indi('1 JAN 1950'),
            '@I2@': indi('5 MAY 1900'),
            '@I3@': indi('4 MAY 1960'),
        }
        families = {'@F1@': fam('@I1@', '@I2@', ['@I3@'])}
        self.assertEqual(parents_not_too_old(individuals, families), [])

    def test_father_79_is_ok(self):
        individuals = {
            '@I1@': indi('1 JAN 1900'),
            '@I2@': indi('1 JAN 1950'),
            '@I3@': indi('1 JAN 1979'),
        }
        families = {'@F1@': fam('@I1@', '@I2@', ['@I3@'])}
        self.assertEqual(parents_not_too_old(individuals, families), [])

    def test_both_parents_too_old(self):
        individuals = {
            '@I1@': indi('1 JAN 1900'),
            '@I2@': indi('1 JAN 1900'),
            '@I3@': indi('1 JAN 1985'),
        }
        families = {'@F1@': fam('@I1@', '@I2@', ['@I3@'])}
        self.assertEqual(len(parents_not_too_old(individuals, families)), 2)

    def test_missing_birth_dates_skipped(self):
        individuals = {
            '@I1@': indi(None),
            '@I2@': indi('1 JAN 1900'),
            '@I3@': indi(None),
        }
        families = {'@F1@': fam('@I1@', '@I2@', ['@I3@'])}
        self.assertEqual(parents_not_too_old(individuals, families), [])

    def test_missing_spouse_skipped(self):
        individuals = {
            '@I2@': indi('1 JAN 1900'),
            '@I3@': indi('1 JAN 1985'),
        }
        families = {'@F1@': fam(None, '@I2@', ['@I3@'])}
        errors = parents_not_too_old(individuals, families)
        self.assertEqual(len(errors), 1)
        self.assertIn('Mother', errors[0])

    def test_no_children(self):
        individuals = {
            '@I1@': indi('1 JAN 1900'),
            '@I2@': indi('1 JAN 1900'),
        }
        families = {'@F1@': fam('@I1@', '@I2@', [])}
        self.assertEqual(parents_not_too_old(individuals, families), [])


if __name__ == '__main__':
    unittest.main()
import unittest
from us10 import siblings_spacing
 
 
def indi(birth):
    return {'birth': birth, 'name': None, 'sex': None, 'death': None,
            'famc': [], 'fams': []}
 
 
def fam(children):
    return {'husband': None, 'wife': None, 'children': children,
            'married': None, 'divorced': None}
 
 
class TestUS10(unittest.TestCase):
 
    def test_siblings_more_than_8_months_apart(self):
        individuals = {
            '@I1@': indi('1 JAN 1990'),
            '@I2@': indi('1 OCT 1991'),
        }
        families = {'@F1@': fam(['@I1@', '@I2@'])}
        self.assertEqual(siblings_spacing(individuals, families), [])
 
    def test_twins_same_day(self):
        individuals = {
            '@I1@': indi('1 JAN 1990'),
            '@I2@': indi('1 JAN 1990'),
        }
        families = {'@F1@': fam(['@I1@', '@I2@'])}
        self.assertEqual(siblings_spacing(individuals, families), [])
 
    def test_twins_one_day_apart(self):
        individuals = {
            '@I1@': indi('1 JAN 1990'),
            '@I2@': indi('2 JAN 1990'),
        }
        families = {'@F1@': fam(['@I1@', '@I2@'])}
        self.assertEqual(siblings_spacing(individuals, families), [])
 
    def test_siblings_2_days_apart_is_error(self):
        individuals = {
            '@I1@': indi('1 JAN 1990'),
            '@I2@': indi('3 JAN 1990'),
        }
        families = {'@F1@': fam(['@I1@', '@I2@'])}
        errors = siblings_spacing(individuals, families)
        self.assertEqual(len(errors), 1)
 
    def test_siblings_5_months_apart_is_error(self):
        individuals = {
            '@I1@': indi('1 JAN 1990'),
            '@I2@': indi('1 JUN 1990'),
        }
        families = {'@F1@': fam(['@I1@', '@I2@'])}
        errors = siblings_spacing(individuals, families)
        self.assertEqual(len(errors), 1)
 
    def test_siblings_exactly_8_months_apart_is_error(self):
        individuals = {
            '@I1@': indi('1 JAN 1990'),
            '@I2@': indi('1 SEP 1990'),
        }
        families = {'@F1@': fam(['@I1@', '@I2@'])}
        self.assertEqual(len(siblings_spacing(individuals, families)), 1)
 
    def test_siblings_just_under_8_months_is_error(self):
        individuals = {
            '@I1@': indi('1 JAN 1990'),
            '@I2@': indi('31 AUG 1990'),
        }
        families = {'@F1@': fam(['@I1@', '@I2@'])}
        errors = siblings_spacing(individuals, families)
        self.assertEqual(len(errors), 1)
 
    def test_missing_birth_date_skipped(self):
        individuals = {
            '@I1@': indi('1 JAN 1990'),
            '@I2@': indi(None),
        }
        families = {'@F1@': fam(['@I1@', '@I2@'])}
        self.assertEqual(siblings_spacing(individuals, families), [])
 
    def test_three_siblings_multiple_errors(self):
        individuals = {
            '@I1@': indi('1 JAN 1990'),
            '@I2@': indi('1 MAR 1990'),
            '@I3@': indi('1 MAY 1990'),
        }
        families = {'@F1@': fam(['@I1@', '@I2@', '@I3@'])}
        errors = siblings_spacing(individuals, families)
        self.assertEqual(len(errors), 3)
 
    def test_no_children(self):
        families = {'@F1@': fam([])}
        self.assertEqual(siblings_spacing({}, families), [])
 
    def test_single_child(self):
        individuals = {'@I1@': indi('1 JAN 1990')}
        families = {'@F1@': fam(['@I1@'])}
        self.assertEqual(siblings_spacing(individuals, families), [])
 
 
if __name__ == '__main__':
    unittest.main()
import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from gedcom_parser import (
    list_deceased, list_living_married, displayId, parseGedDate
)


def _build_individuals():
    """Small dataset with a mix of living and deceased, married and single."""
    return {
        '@I1@': {'id': '@I1@', 'name': 'Alice /Smith/', 'sex': 'F',
                 'birth': '1 JAN 1950', 'death': '15 MAR 2020',
                 'famc': [], 'fams': ['@F1@']},
        '@I2@': {'id': '@I2@', 'name': 'Bob /Smith/', 'sex': 'M',
                 'birth': '5 JUN 1948', 'death': None,
                 'famc': [], 'fams': ['@F1@']},
        '@I3@': {'id': '@I3@', 'name': 'Carol /Doe/', 'sex': 'F',
                 'birth': '12 DEC 1970', 'death': None,
                 'famc': ['@F1@'], 'fams': ['@F2@']},
        '@I4@': {'id': '@I4@', 'name': 'Dave /Doe/', 'sex': 'M',
                 'birth': '3 FEB 1968', 'death': None,
                 'famc': [], 'fams': ['@F2@']},
        '@I5@': {'id': '@I5@', 'name': 'Eve /Brown/', 'sex': 'F',
                 'birth': '20 JUL 1990', 'death': '1 AUG 2023',
                 'famc': [], 'fams': []},
    }


def _build_families():
    return {
        '@F1@': {'id': '@F1@', 'married': '10 SEP 1970', 'divorced': None,
                 'husband': '@I2@', 'wife': '@I1@', 'children': ['@I3@']},
        '@F2@': {'id': '@F2@', 'married': '5 MAY 1995', 'divorced': None,
                 'husband': '@I4@', 'wife': '@I3@', 'children': []},
    }


class TestUS25ListDeceased(unittest.TestCase):
   

    def test_returns_only_deceased(self):
        individuals = _build_individuals()
        result = list_deceased(individuals)
        ids = [r[0] for r in result]
       
        self.assertIn('@I1@', ids)
        self.assertIn('@I5@', ids)
        self.assertEqual(len(result), 2)

    def test_living_not_included(self):
        individuals = _build_individuals()
        result = list_deceased(individuals)
        ids = [r[0] for r in result]
        self.assertNotIn('@I2@', ids)
        self.assertNotIn('@I3@', ids)
        self.assertNotIn('@I4@', ids)

    def test_empty_when_no_deaths(self):
        individuals = {
            '@I1@': {'id': '@I1@', 'name': 'Alive /Person/', 'sex': 'M',
                     'birth': '1 JAN 2000', 'death': None,
                     'famc': [], 'fams': []},
        }
        result = list_deceased(individuals)
        self.assertEqual(result, [])

    def test_includes_name_and_death_date(self):
        individuals = _build_individuals()
        result = list_deceased(individuals)
        alice = [r for r in result if r[0] == '@I1@'][0]
        self.assertEqual(alice[1], 'Alice /Smith/')
        self.assertEqual(alice[2], '15 MAR 2020')


class TestUS26ListLivingMarried(unittest.TestCase):
    

    def test_returns_living_married(self):
        individuals = _build_individuals()
        families = _build_families()
        result = list_living_married(individuals, families)
        ids = [r[0] for r in result]
        
        self.assertIn('@I2@', ids)
        self.assertIn('@I3@', ids)
        self.assertIn('@I4@', ids)
        self.assertNotIn('@I1@', ids)

    def test_deceased_spouse_excluded(self):
        individuals = _build_individuals()
        families = _build_families()
        result = list_living_married(individuals, families)
        ids = [r[0] for r in result]
        self.assertNotIn('@I1@', ids)  

    def test_divorced_excluded(self):
        individuals = _build_individuals()
        families = _build_families()
       
        families['@F2@']['divorced'] = '1 JAN 2020'
        result = list_living_married(individuals, families)
        ids = [r[0] for r in result]
       
        self.assertNotIn('@I3@', ids)
        self.assertNotIn('@I4@', ids)

    def test_unmarried_excluded(self):
        individuals = _build_individuals()
        families = _build_families()
        result = list_living_married(individuals, families)
        ids = [r[0] for r in result]
       
        self.assertNotIn('@I5@', ids)

    def test_empty_when_all_dead(self):
        individuals = {
            '@I1@': {'id': '@I1@', 'name': 'A /X/', 'sex': 'M',
                     'birth': '1 JAN 1940', 'death': '1 JAN 2020',
                     'famc': [], 'fams': ['@F1@']},
            '@I2@': {'id': '@I2@', 'name': 'B /X/', 'sex': 'F',
                     'birth': '1 JAN 1942', 'death': '1 JAN 2021',
                     'famc': [], 'fams': ['@F1@']},
        }
        families = {
            '@F1@': {'id': '@F1@', 'married': '1 JUN 1965', 'divorced': None,
                     'husband': '@I1@', 'wife': '@I2@', 'children': []},
        }
        result = list_living_married(individuals, families)
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()
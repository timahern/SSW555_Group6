import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from gedcom_parser import list_living_single, list_multiple_births


class TestUS27ListLivingSingle(unittest.TestCase):

    def _make_person(self, pid, name, birth, death=None, fams=None):
        return {
            'id': pid, 'name': name, 'sex': 'M',
            'birth': birth, 'death': death,
            'famc': [], 'fams': fams or [],
        }

    def test_living_single_over_30_included(self):
        individuals = {
            '@I1@': self._make_person('@I1@', 'Solo /Guy/', '1 JAN 1980'),
        }
        result = list_living_single(individuals)
        ids = [r[0] for r in result]
        self.assertIn('@I1@', ids)

    def test_married_person_excluded(self):
        individuals = {
            '@I1@': self._make_person('@I1@', 'Married /Guy/', '1 JAN 1980',
                                      fams=['@F1@']),
        }
        result = list_living_single(individuals)
        ids = [r[0] for r in result]
        self.assertNotIn('@I1@', ids)

    def test_deceased_person_excluded(self):
        individuals = {
            '@I1@': self._make_person('@I1@', 'Dead /Guy/', '1 JAN 1980',
                                      death='1 JAN 2020'),
        }
        result = list_living_single(individuals)
        self.assertEqual(result, [])

    def test_young_person_excluded(self):
        individuals = {
            '@I1@': self._make_person('@I1@', 'Young /Guy/', '1 JAN 2000'),
        }
        result = list_living_single(individuals)
        self.assertEqual(result, [])

    def test_mixed_population(self):
        individuals = {
            '@I1@': self._make_person('@I1@', 'Old Single /A/', '1 JAN 1980'),
            '@I2@': self._make_person('@I2@', 'Old Married /B/', '1 JAN 1980',
                                      fams=['@F1@']),
            '@I3@': self._make_person('@I3@', 'Young Single /C/', '1 JAN 2005'),
            '@I4@': self._make_person('@I4@', 'Dead Single /D/', '1 JAN 1970',
                                      death='1 JAN 2020'),
        }
        result = list_living_single(individuals)
        ids = [r[0] for r in result]
        self.assertEqual(ids, ['@I1@'])


class TestUS28ListMultipleBirths(unittest.TestCase):

    def test_twins_listed(self):
        individuals = {
            '@I1@': {'id': '@I1@', 'name': 'Twin /A/', 'sex': 'M',
                     'birth': '1 JAN 2000', 'death': None, 'famc': ['@F1@'], 'fams': []},
            '@I2@': {'id': '@I2@', 'name': 'Twin /B/', 'sex': 'F',
                     'birth': '1 JAN 2000', 'death': None, 'famc': ['@F1@'], 'fams': []},
        }
        families = {
            '@F1@': {'id': '@F1@', 'married': '1 JUN 1995', 'divorced': None,
                     'husband': '@I10@', 'wife': '@I11@', 'children': ['@I1@', '@I2@']},
        }
        result = list_multiple_births(individuals, families)
        self.assertEqual(len(result), 1)
        fam_id, birth_raw, child_ids = result[0]
        self.assertEqual(fam_id, '@F1@')
        self.assertIn('@I1@', child_ids)
        self.assertIn('@I2@', child_ids)

    def test_no_multiple_births(self):
        individuals = {
            '@I1@': {'id': '@I1@', 'name': 'Child /A/', 'sex': 'M',
                     'birth': '1 JAN 2000', 'death': None, 'famc': ['@F1@'], 'fams': []},
            '@I2@': {'id': '@I2@', 'name': 'Child /B/', 'sex': 'F',
                     'birth': '15 MAR 2002', 'death': None, 'famc': ['@F1@'], 'fams': []},
        }
        families = {
            '@F1@': {'id': '@F1@', 'married': '1 JUN 1995', 'divorced': None,
                     'husband': '@I10@', 'wife': '@I11@', 'children': ['@I1@', '@I2@']},
        }
        result = list_multiple_births(individuals, families)
        self.assertEqual(result, [])

    def test_triplets_listed(self):
        individuals = {
            '@I1@': {'id': '@I1@', 'name': 'Trip /A/', 'sex': 'M',
                     'birth': '5 MAY 2010', 'death': None, 'famc': ['@F1@'], 'fams': []},
            '@I2@': {'id': '@I2@', 'name': 'Trip /B/', 'sex': 'F',
                     'birth': '5 MAY 2010', 'death': None, 'famc': ['@F1@'], 'fams': []},
            '@I3@': {'id': '@I3@', 'name': 'Trip /C/', 'sex': 'M',
                     'birth': '5 MAY 2010', 'death': None, 'famc': ['@F1@'], 'fams': []},
        }
        families = {
            '@F1@': {'id': '@F1@', 'married': '1 JUN 2005', 'divorced': None,
                     'husband': '@I10@', 'wife': '@I11@', 'children': ['@I1@', '@I2@', '@I3@']},
        }
        result = list_multiple_births(individuals, families)
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0][2]), 3)

    def test_single_child_not_listed(self):
        individuals = {
            '@I1@': {'id': '@I1@', 'name': 'Only /Child/', 'sex': 'M',
                     'birth': '1 JAN 2000', 'death': None, 'famc': ['@F1@'], 'fams': []},
        }
        families = {
            '@F1@': {'id': '@F1@', 'married': '1 JUN 1995', 'divorced': None,
                     'husband': '@I10@', 'wife': '@I11@', 'children': ['@I1@']},
        }
        result = list_multiple_births(individuals, families)
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()
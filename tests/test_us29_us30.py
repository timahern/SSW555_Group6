import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from gedcom_parser import list_orphans, list_large_age_differences


class TestUS29ListOrphans(unittest.TestCase):

    def _make_person(self, pid, name, birth, death=None):
        return {
            'id': pid, 'name': name, 'sex': 'M',
            'birth': birth, 'death': death,
            'famc': [], 'fams': [],
        }

    def _make_family(self, fid, husband, wife, children, married='1 JUN 2000'):
        return {
            'id': fid, 'married': married, 'divorced': None,
            'husband': husband, 'wife': wife, 'children': children,
        }

    def test_young_child_with_dead_parents_included(self):
        individuals = {
            '@I1@': self._make_person('@I1@', 'Dead /Dad/', '1 JAN 1970', death='1 JAN 2020'),
            '@I2@': self._make_person('@I2@', 'Dead /Mom/', '1 JAN 1972', death='1 JAN 2021'),
            '@I3@': self._make_person('@I3@', 'Young /Kid/', '1 JAN 2015'),
        }
        families = {
            '@F1@': self._make_family('@F1@', '@I1@', '@I2@', ['@I3@']),
        }
        result = list_orphans(individuals, families)
        ids = [r[0] for r in result]
        self.assertEqual(ids, ['@I3@'])
        self.assertEqual(result[0][1], 'Young /Kid/')

    def test_one_living_parent_excluded(self):
        individuals = {
            '@I1@': self._make_person('@I1@', 'Dead /Dad/', '1 JAN 1970', death='1 JAN 2020'),
            '@I2@': self._make_person('@I2@', 'Live /Mom/', '1 JAN 1972'),
            '@I3@': self._make_person('@I3@', 'Young /Kid/', '1 JAN 2015'),
        }
        families = {
            '@F1@': self._make_family('@F1@', '@I1@', '@I2@', ['@I3@']),
        }
        result = list_orphans(individuals, families)
        self.assertEqual(result, [])

    def test_child_18_or_older_excluded(self):
        individuals = {
            '@I1@': self._make_person('@I1@', 'Dead /Dad/', '1 JAN 1950', death='1 JAN 2010'),
            '@I2@': self._make_person('@I2@', 'Dead /Mom/', '1 JAN 1952', death='1 JAN 2011'),
            '@I3@': self._make_person('@I3@', 'Adult /Kid/', '1 JAN 2000'),
            '@I4@': self._make_person('@I4@', 'Just18 /Kid/', '1 JAN 2008'),
        }
        families = {
            '@F1@': self._make_family('@F1@', '@I1@', '@I2@', ['@I3@', '@I4@']),
        }
        result = list_orphans(individuals, families)
        self.assertEqual(result, [])

    def test_dead_child_excluded(self):
        individuals = {
            '@I1@': self._make_person('@I1@', 'Dead /Dad/', '1 JAN 1970', death='1 JAN 2020'),
            '@I2@': self._make_person('@I2@', 'Dead /Mom/', '1 JAN 1972', death='1 JAN 2021'),
            '@I3@': self._make_person('@I3@', 'Dead /Kid/', '1 JAN 2015', death='1 JUN 2020'),
        }
        families = {
            '@F1@': self._make_family('@F1@', '@I1@', '@I2@', ['@I3@']),
        }
        result = list_orphans(individuals, families)
        self.assertEqual(result, [])

    def test_missing_parent_excluded(self):
        individuals = {
            '@I1@': self._make_person('@I1@', 'Dead /Dad/', '1 JAN 1970', death='1 JAN 2020'),
            '@I3@': self._make_person('@I3@', 'Young /Kid/', '1 JAN 2015'),
        }
        families = {
            '@F1@': self._make_family('@F1@', '@I1@', None, ['@I3@']),
        }
        result = list_orphans(individuals, families)
        self.assertEqual(result, [])

    def test_child_listed_once(self):
        individuals = {
            '@I1@': self._make_person('@I1@', 'Dead /Dad/', '1 JAN 1970', death='1 JAN 2020'),
            '@I2@': self._make_person('@I2@', 'Dead /Mom/', '1 JAN 1972', death='1 JAN 2021'),
            '@I3@': self._make_person('@I3@', 'Young /Kid/', '1 JAN 2015'),
        }
        families = {
            '@F1@': self._make_family('@F1@', '@I1@', '@I2@', ['@I3@']),
            '@F2@': self._make_family('@F2@', '@I1@', '@I2@', ['@I3@']),
        }
        result = list_orphans(individuals, families)
        ids = [r[0] for r in result]
        self.assertEqual(ids, ['@I3@'])

    def test_mixed_children(self):
        individuals = {
            '@I1@': self._make_person('@I1@', 'Dead /Dad/', '1 JAN 1970', death='1 JAN 2020'),
            '@I2@': self._make_person('@I2@', 'Dead /Mom/', '1 JAN 1972', death='1 JAN 2021'),
            '@I3@': self._make_person('@I3@', 'Older /Kid/', '1 JAN 2000'),
            '@I4@': self._make_person('@I4@', 'Young /Kid/', '1 JAN 2015'),
            '@I5@': self._make_person('@I5@', 'Live /Dad/', '1 JAN 1980'),
            '@I6@': self._make_person('@I6@', 'Live /Mom/', '1 JAN 1982'),
            '@I7@': self._make_person('@I7@', 'Other /Kid/', '1 JAN 2016'),
        }
        families = {
            '@F1@': self._make_family('@F1@', '@I1@', '@I2@', ['@I3@', '@I4@']),
            '@F2@': self._make_family('@F2@', '@I5@', '@I6@', ['@I7@']),
        }
        result = list_orphans(individuals, families)
        ids = [r[0] for r in result]
        self.assertEqual(ids, ['@I4@'])


class TestUS30ListLargeAgeDifferences(unittest.TestCase):

    def _make_person(self, pid, name, birth):
        return {
            'id': pid, 'name': name, 'sex': 'M',
            'birth': birth, 'death': None,
            'famc': [], 'fams': [],
        }

    def _make_family(self, fid, husband, wife, married='1 JAN 2000'):
        return {
            'id': fid, 'married': married, 'divorced': None,
            'husband': husband, 'wife': wife, 'children': [],
        }

    def test_older_more_than_twice_as_old(self):
        individuals = {
            '@I1@': self._make_person('@I1@', 'Old /Husband/', '1 JAN 1950'),
            '@I2@': self._make_person('@I2@', 'Young /Wife/', '1 JAN 1980'),
        }
        families = {
            '@F1@': self._make_family('@F1@', '@I1@', '@I2@'),
        }
        result = list_large_age_differences(individuals, families)
        self.assertEqual(len(result), 1)
        fam_id, husb_id, husb_name, husb_age, wife_id, wife_name, wife_age = result[0]
        self.assertEqual(fam_id, '@F1@')
        self.assertEqual(husb_id, '@I1@')
        self.assertEqual(husb_name, 'Old /Husband/')
        self.assertEqual(husb_age, 50)
        self.assertEqual(wife_id, '@I2@')
        self.assertEqual(wife_name, 'Young /Wife/')
        self.assertEqual(wife_age, 20)

    def test_exactly_twice_as_old_excluded(self):
        individuals = {
            '@I1@': self._make_person('@I1@', 'Old /Husband/', '1 JAN 1960'),
            '@I2@': self._make_person('@I2@', 'Young /Wife/', '1 JAN 1980'),
        }
        families = {
            '@F1@': self._make_family('@F1@', '@I1@', '@I2@'),
        }
        result = list_large_age_differences(individuals, families)
        self.assertEqual(result, [])

    def test_wife_is_the_older_spouse(self):
        individuals = {
            '@I1@': self._make_person('@I1@', 'Young /Husband/', '1 JAN 1980'),
            '@I2@': self._make_person('@I2@', 'Old /Wife/', '1 JAN 1950'),
        }
        families = {
            '@F1@': self._make_family('@F1@', '@I1@', '@I2@'),
        }
        result = list_large_age_differences(individuals, families)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][3], 20)
        self.assertEqual(result[0][6], 50)

    def test_less_than_twice_excluded(self):
        individuals = {
            '@I1@': self._make_person('@I1@', 'Old /Husband/', '1 JAN 1961'),
            '@I2@': self._make_person('@I2@', 'Young /Wife/', '1 JAN 1980'),
        }
        families = {
            '@F1@': self._make_family('@F1@', '@I1@', '@I2@'),
        }
        result = list_large_age_differences(individuals, families)
        self.assertEqual(result, [])

    def test_missing_dates_excluded(self):
        individuals = {
            '@I1@': self._make_person('@I1@', 'Old /Husband/', None),
            '@I2@': self._make_person('@I2@', 'Young /Wife/', '1 JAN 1980'),
            '@I3@': self._make_person('@I3@', 'Other /Husband/', '1 JAN 1950'),
            '@I4@': self._make_person('@I4@', 'Other /Wife/', '1 JAN 1980'),
        }
        families = {
            '@F1@': self._make_family('@F1@', '@I1@', '@I2@'),
            '@F2@': self._make_family('@F2@', '@I3@', '@I4@', married=None),
        }
        result = list_large_age_differences(individuals, families)
        self.assertEqual(result, [])

    def test_divorced_couple_still_listed(self):
        individuals = {
            '@I1@': self._make_person('@I1@', 'Old /Husband/', '1 JAN 1950'),
            '@I2@': self._make_person('@I2@', 'Young /Wife/', '1 JAN 1980'),
        }
        families = {
            '@F1@': self._make_family('@F1@', '@I1@', '@I2@'),
        }
        families['@F1@']['divorced'] = '1 JAN 2010'
        result = list_large_age_differences(individuals, families)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], '@F1@')

    def test_missing_spouse_excluded(self):
        individuals = {
            '@I1@': self._make_person('@I1@', 'Old /Husband/', '1 JAN 1950'),
        }
        families = {
            '@F1@': self._make_family('@F1@', '@I1@', None),
        }
        result = list_large_age_differences(individuals, families)
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()

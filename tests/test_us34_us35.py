
import unittest
from datetime import date

from gedcom_parser import (
    list_upcoming_birthdays,
    list_upcoming_anniversaries,
)


class TestUS34UpcomingBirthdays(unittest.TestCase):

    def setUp(self):
        self.today = date(2026, 11, 16)
        self.individuals = {
            '@I1@': {
                'name': 'Alice /Smith/',
                'birth': '20 NOV 1995',
                'death': None
            },
            '@I2@': {
                'name': 'Bob /Jones/',
                'birth': '25 DEC 1990',
                'death': None
            },
            '@I3@': {
                'name': 'Carol /White/',
                'birth': '1 DEC 1985',
                'death': '10 JAN 2020'
            },
            '@I4@': {
                'name': 'David /Brown/',
                'birth': '10 DEC 2000',
                'death': None
            },
            '@I5@': {
                'name': 'Eva /Green/',
                'birth': None,
                'death': None
            }
        }

    def test_upcoming_birthdays(self):
        result = list_upcoming_birthdays(
            self.individuals, self.today
        )
        ids = [person[0] for person in result]

        self.assertIn('@I1@', ids)
        self.assertIn('@I4@', ids)
        self.assertNotIn('@I2@', ids)

    def test_excludes_deceased(self):
        result = list_upcoming_birthdays(
            self.individuals, self.today
        )
        ids = [person[0] for person in result]

        self.assertNotIn('@I3@', ids)

    def test_missing_birth_date(self):
        result = list_upcoming_birthdays(
            self.individuals, self.today
        )
        ids = [person[0] for person in result]

        self.assertNotIn('@I5@', ids)

    def test_birthday_today(self):
        self.individuals['@I1@']['birth'] = '16 NOV 1995'

        result = list_upcoming_birthdays(
            self.individuals, self.today
        )

        ids = [person[0] for person in result]
        self.assertIn('@I1@', ids)

    def test_birthday_across_new_year(self):
        today = date(2026, 12, 20)
        self.individuals['@I1@']['birth'] = '5 JAN 1995'

        result = list_upcoming_birthdays(
            self.individuals, today
        )

        self.assertIn(
            ('@I1@', 'Alice /Smith/', date(2027, 1, 5)),
            result
        )


class TestUS35UpcomingAnniversaries(unittest.TestCase):

    def setUp(self):
        self.today = date(2026, 11, 16)

        self.individuals = {
            '@I1@': {'name': 'John /Smith/', 'death': None},
            '@I2@': {'name': 'Jane /Smith/', 'death': None},
            '@I3@': {'name': 'Bob /Jones/', 'death': None},
            '@I4@': {'name': 'Mary /Jones/', 'death': None},
            '@I5@': {'name': 'Tom /White/', 'death': '1 JAN 2020'},
            '@I6@': {'name': 'Sue /White/', 'death': None}
        }

        self.families = {
            '@F1@': {
                'husband': '@I1@',
                'wife': '@I2@',
                'married': '25 NOV 2010',
                'divorced': None
            },
            '@F2@': {
                'husband': '@I3@',
                'wife': '@I4@',
                'married': '25 DEC 2015',
                'divorced': None
            },
            '@F3@': {
                'husband': '@I5@',
                'wife': '@I6@',
                'married': '1 DEC 2000',
                'divorced': None
            }
        }

    def test_upcoming_anniversaries(self):
        result = list_upcoming_anniversaries(
            self.individuals, self.families, self.today
        )

        ids = [family[0] for family in result]

        self.assertIn('@F1@', ids)
        self.assertNotIn('@F2@', ids)

    def test_excludes_deceased_spouse(self):
        result = list_upcoming_anniversaries(
            self.individuals, self.families, self.today
        )

        ids = [family[0] for family in result]
        self.assertNotIn('@F3@', ids)

    def test_excludes_divorced(self):
        self.families['@F1@']['divorced'] = '1 JAN 2020'

        result = list_upcoming_anniversaries(
            self.individuals, self.families, self.today
        )

        ids = [family[0] for family in result]
        self.assertNotIn('@F1@', ids)

    def test_anniversary_today(self):
        self.families['@F1@']['married'] = '16 NOV 2010'

        result = list_upcoming_anniversaries(
            self.individuals, self.families, self.today
        )

        ids = [family[0] for family in result]
        self.assertIn('@F1@', ids)

    def test_anniversary_across_new_year(self):
        today = date(2026, 12, 20)
        self.families['@F1@']['married'] = '5 JAN 2010'

        result = list_upcoming_anniversaries(
            self.individuals, self.families, today
        )

        self.assertIn(
            ('@F1@', 'John /Smith/', 'Jane /Smith/', date(2027, 1, 5)),
            result
         )


if __name__ == '__main__':
    unittest.main()

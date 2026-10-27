import unittest
from gedcom_parser import (
    check_siblings_should_not_marry,
    check_first_cousins_should_not_marry
)


class TestUS15(unittest.TestCase):

    def test_siblings_married(self):
        # Two siblings are married - should produce an error
        individuals = {
            '@I1@': {},
            '@I2@': {}
        }

        families = {
            '@F1@': {
                'husband': '@I3@',
                'wife': '@I4@',
                'children': ['@I1@', '@I2@'],
                'line': 1
            },
            '@F2@': {
                'husband': '@I1@',
                'wife': '@I2@',
                'children': [],
                'line': 10
            }
        }

        errors = check_siblings_should_not_marry(individuals, families)

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, 'US15')

    def test_unrelated_people_married(self):
        # Unrelated individuals are married - no error
        individuals = {
            '@I1@': {},
            '@I2@': {}
        }

        families = {
            '@F1@': {
                'husband': '@I1@',
                'wife': '@I2@',
                'children': [],
                'line': 1
            }
        }

        errors = check_siblings_should_not_marry(individuals, families)

        self.assertEqual(len(errors), 0)

class TestUS16(unittest.TestCase):

    def test_first_cousins_married(self):
        # I1 and I2 are siblings.
        # Their children I3 and I4 are first cousins.
        # I3 and I4 are married, so an error is expected.

        individuals = {
            '@I1@': {}, '@I2@': {},
            '@I3@': {}, '@I4@': {}
        }

        families = {
            '@F1@': {
                'husband': '@I5@',
                'wife': '@I6@',
                'children': ['@I1@', '@I2@']
            },
            '@F2@': {
                'husband': '@I1@',
                'wife': '@I7@',
                'children': ['@I3@']
            },
            '@F3@': {
                'husband': '@I8@',
                'wife': '@I2@',
                'children': ['@I4@']
            },
            '@F4@': {
                'husband': '@I3@',
                'wife': '@I4@',
                'children': [],
                'line': 20
            }
        }

        errors = check_first_cousins_should_not_marry(
            individuals, families
        )

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, 'US16')

    def test_unrelated_people_married(self):
        # Unrelated individuals can marry without a US16 error.

        individuals = {
            '@I1@': {},
            '@I2@': {}
        }

        families = {
            '@F1@': {
                'husband': '@I1@',
                'wife': '@I2@',
                'children': [],
                'line': 1
            }
        }

        errors = check_first_cousins_should_not_marry(
            individuals, families
        )

        self.assertEqual(len(errors), 0)

if __name__ == '__main__':
    unittest.main()
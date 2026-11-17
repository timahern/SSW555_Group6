import io
import unittest
from contextlib import redirect_stdout
from datetime import date

from gedcom_parser import (list_recent_births, list_recent_deaths,
                           list_recent_survivors, print_recent_births,
                           print_recent_deaths, print_recent_survivors)

TODAY = date(2026, 11, 15)


def indi(i, birth, death=None, fams=None):
    return {'id': i, 'name': f'N{i} /X/', 'sex': 'M', 'birth': birth,
            'death': death, 'famc': [], 'fams': fams or []}


class RecentTests(unittest.TestCase):
    def setUp(self):
        self.inds = {
            '@I1@': indi('@I1@', '1 JAN 1950', '10 NOV 2026', ['@F1@']),  # recent death
            '@I2@': indi('@I2@', '1 JAN 1952', None, ['@F1@']),           # living spouse
            '@I3@': indi('@I3@', '1 JAN 1975', None, ['@F2@']),           # living child
            '@I4@': indi('@I4@', '1 JAN 2000', None),                     # living grandchild
            '@I5@': indi('@I5@', '1 JAN 1977', '1 JAN 2020'),             # dead child
            '@I6@': indi('@I6@', '1 NOV 2026'),                           # recent birth
            '@I7@': indi('@I7@', '1 JAN 1930', '1 JAN 2026'),             # old death
            '@I8@': indi('@I8@', '16 OCT 2026'),                          # exactly 30 days
            '@I9@': indi('@I9@', '15 OCT 2026'),                          # 31 days
            '@I10@': indi('@I10@', '20 NOV 2026'),                        # future
        }
        self.fams = {
            '@F1@': {'id': '@F1@', 'husband': '@I1@', 'wife': '@I2@',
                     'children': ['@I3@', '@I5@']},
            '@F2@': {'id': '@F2@', 'husband': '@I3@', 'wife': None,
                     'children': ['@I4@']},
        }

    def test_recent_births(self):
        ids = [r[0] for r in list_recent_births(self.inds, TODAY)]
        self.assertEqual(ids, ['@I6@', '@I8@'])

    def test_recent_deaths(self):
        ids = [r[0] for r in list_recent_deaths(self.inds, TODAY)]
        self.assertEqual(ids, ['@I1@'])

    def test_recent_survivors(self):
        rows = list_recent_survivors(self.inds, self.fams, TODAY)
        self.assertEqual([(r[1], r[3]) for r in rows],
                         [('@I2@', 'Spouse'), ('@I3@', 'Descendant'),
                          ('@I4@', 'Descendant')])

    def test_no_survivors_when_no_recent_deaths(self):
        self.inds['@I1@']['death'] = '1 JAN 2020'
        self.assertEqual(list_recent_survivors(self.inds, self.fams, TODAY), [])

    def test_print_functions_output(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_recent_births({})
            print_recent_deaths({})
            print_recent_survivors({}, {})
        out = buf.getvalue()
        self.assertIn('Recent Births (US31)', out)
        self.assertIn('Recent Deaths (US32)', out)
        self.assertIn('Recent Survivors (US33)', out)


if __name__ == '__main__':
    unittest.main()

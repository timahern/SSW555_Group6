import unittest
from gedcom_parser import validate_gedcom_lines


class TestMultipleBirthsAndSiblings(unittest.TestCase):

    def make_family(self, number_of_children, same_birthday=False):
        lines = [
            "0 @F1@ FAM\n",
            "1 HUSB @I100@\n",
            "1 WIFE @I101@\n",
        ]

        for i in range(number_of_children):
            lines.append(f"1 CHIL @I{i+1}@\n")

        for i in range(number_of_children):
            lines.append(f"0 @I{i+1}@ INDI\n")
            lines.append(f"1 NAME Child{i+1} /Smith/\n")
            lines.append("1 BIRT\n")

            if same_birthday:
                lines.append("2 DATE 1 JAN 2020\n")
            else:
                lines.append(f"2 DATE {i+1} JAN 2020\n")

            lines.append("1 FAMC @F1@\n")

        return lines

    def test_us11_five_births_allowed(self):
        lines = self.make_family(5, same_birthday=True)
        _, _, errors = validate_gedcom_lines(lines)
        self.assertFalse(any(e.code == "US11" for e in errors))

    def test_us11_six_births_rejected(self):
        lines = self.make_family(6, same_birthday=True)
        _, _, errors = validate_gedcom_lines(lines)
        self.assertTrue(any(e.code == "US11" for e in errors))

    def test_us12_fourteen_children_allowed(self):
        lines = self.make_family(14)
        _, _, errors = validate_gedcom_lines(lines)
        self.assertFalse(any(e.code == "US12" for e in errors))

    def test_us12_fifteen_children_rejected(self):
        lines = self.make_family(15)
        _, _, errors = validate_gedcom_lines(lines)
        self.assertTrue(any(e.code == "US12" for e in errors))

    def test_us12_sixteen_children_rejected(self):
        lines = self.make_family(16)
        _, _, errors = validate_gedcom_lines(lines)
        self.assertTrue(any(e.code == "US12" for e in errors))


if __name__ == "__main__":
    unittest.main()

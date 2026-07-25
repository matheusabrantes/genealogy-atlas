import unittest

from mygenealogy.gedcom import parse_lines
from mygenealogy.validation import parse_date, validate


GEDCOM = """0 HEAD
1 GEDC
2 VERS 5.5.1
0 @I1@ INDI
1 NAME Ana /Silva/
1 BIRT
2 DATE 1900
2 PLAC Minas Gerais, Brasil
1 DEAT
2 DATE 1980
0 @I2@ INDI
1 NAME Bia /Silva/
1 BIRT
2 DATE 1910
1 DEAT
2 DATE 1909
0 @I3@ INDI
1 NAME Ana /Silva/
1 BIRT
2 DATE ABT 1900
0 @F1@ FAM
1 WIFE @I1@
1 CHIL @I2@
1 MARR
2 DATE 1911
0 TRLR
"""


class ValidationTests(unittest.TestCase):
    def test_partial_dates_are_intervals(self):
        span = parse_date("FEB 1900")
        self.assertEqual((span.earliest.day, span.latest.day), (1, 28))

    def test_brazilian_and_localized_dates(self):
        self.assertEqual(parse_date("14/10/1966").earliest.isoformat(), "1966-10-14")
        self.assertEqual(parse_date("2 de fevereiro de 1926").earliest.isoformat(), "1926-02-02")
        self.assertEqual(parse_date("24 November 1938").earliest.isoformat(), "1938-11-24")
        self.assertEqual(parse_date("aproximadamente 1795").earliest.year, 1794)
        self.assertEqual(parse_date("antes 1835").latest.year, 1835)

    def test_core_checks(self):
        issues, summary = validate(parse_lines(GEDCOM.splitlines()), root="@I2@")
        codes = {issue.code for issue in issues}
        self.assertIn("PARENT_UNDER_13", codes)
        self.assertIn("DEATH_BEFORE_BIRTH", codes)
        self.assertIn("POSSIBLE_DUPLICATE", codes)
        self.assertEqual(summary["people"], 3)
        self.assertEqual(summary["families"], 1)

    def test_cycle_and_duplicate_xref(self):
        data = """0 @I1@ INDI
1 NAME Um /Teste/
0 @I1@ INDI
1 NAME Outro /Teste/
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I1@
1 CHIL @I1@
0 TRLR
"""
        issues, _ = validate(parse_lines(data.splitlines()))
        codes = {issue.code for issue in issues}
        self.assertIn("DUPLICATE_XREF", codes)
        self.assertIn("SELF_RELATIONSHIP", codes)
        self.assertIn("ANCESTRY_LOOP", codes)

    def test_multiple_parents_event_before_birth_and_living_death_gaps(self):
        data = """0 @I1@ INDI
1 NAME Joana /Teste/
1 BIRT
2 DATE 1869
1 CHR
2 DATE 30 JUL 1865
0 @I2@ INDI
1 NAME Pai /Um/
1 SEX F
0 @I3@ INDI
1 NAME Mae /Um/
0 @I4@ INDI
1 NAME Pai /Dois/
0 @I5@ INDI
1 NAME Mae /Dois/
0 @F1@ FAM
1 HUSB @I2@
1 WIFE @I3@
1 CHIL @I1@
0 @F2@ FAM
1 HUSB @I4@
1 WIFE @I5@
1 CHIL @I1@
0 TRLR
"""
        issues, _ = validate(parse_lines(data.splitlines()), root="@I1@")
        codes = {issue.code for issue in issues}
        self.assertIn("MULTIPLE_PARENT_FAMILIES", codes)
        self.assertIn("EVENT_BEFORE_BIRTH", codes)
        self.assertIn("SEX_ROLE_CONFLICT", codes)
        root_gap = next(issue for issue in issues if issue.code == "MISSING_CRITICAL_DATA" and issue.subjects[0].startswith("@I1@"))
        self.assertNotIn("death date", root_gap.message)
        self.assertNotIn("death place", root_gap.message)


if __name__ == "__main__":
    unittest.main()

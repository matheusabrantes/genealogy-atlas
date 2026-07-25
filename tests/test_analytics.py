import unittest

from mygenealogy.analytics import build_analytics
from mygenealogy.gedcom import parse_lines


GEDCOM = """0 HEAD
0 @I1@ INDI
1 NAME Root /Person/
1 _FSFTID TEST-ROOT
1 BIRT
2 DATE 2000
1 FAMC @F1@
0 @I2@ INDI
1 NAME Pai /Privado/
1 _FSFTID PAI1-TEST
1 FAMC @F2@
0 @I3@ INDI
1 NAME Avô /Falecido/
1 _FSFTID AVO1-TEST
1 BIRT
2 DATE 1940
2 PLAC Icó, Ceará, Brasil
1 DEAT
2 DATE 2024
0 @F1@ FAM
1 HUSB @I2@
1 CHIL @I1@
0 @F2@ FAM
1 HUSB @I3@
1 CHIL @I2@
0 @S1@ SOUR
0 TRLR
"""


class AnalyticsTests(unittest.TestCase):
    def test_generations_graph_and_conservative_privacy(self):
        summary, graph = build_analytics(parse_lines(GEDCOM.splitlines()), "TEST-ROOT")
        nodes = {node["id"]: node for node in graph["nodes"]}

        self.assertEqual(summary["reachableAncestors"], 3)
        self.assertEqual(summary["maxGeneration"], 2)
        self.assertEqual(summary["countries"][0], {"country": "Brasil", "events": 1})
        private_nodes = [node for node in graph["nodes"] if node["private"]]
        self.assertEqual({node["name"] for node in private_nodes}, {"Pessoa privada"})
        self.assertNotIn("TEST-ROOT", nodes)
        self.assertNotIn("PAI1-TEST", nodes)
        self.assertEqual(nodes["AVO1-TEST"]["name"], "Avô Falecido")
        self.assertEqual(len(graph["edges"]), 2)
        self.assertTrue(all("TEST-ROOT" not in edge.values() for edge in graph["edges"]))


if __name__ == "__main__":
    unittest.main()

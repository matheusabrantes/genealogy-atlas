import unittest

from mygenealogy.analytics import (
    build_analytics,
    build_places_explorer,
    build_roles_explorer,
)
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
1 OCCU Ferreiro
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

    def test_can_publish_only_the_root_name(self):
        _, graph = build_analytics(
            parse_lines(GEDCOM.splitlines()),
            "TEST-ROOT",
            "Matheus Abrantes",
        )

        root = next(node for node in graph["nodes"] if node["generation"] == 0)
        other_private = [
            node
            for node in graph["nodes"]
            if node["private"] and node["generation"] != 0
        ]

        self.assertEqual(root["name"], "Matheus Abrantes")
        self.assertTrue(root["private"])
        self.assertEqual({node["name"] for node in other_private}, {"Pessoa privada"})

    def test_builds_generation_aware_places_explorer(self):
        summary, graph = build_analytics(
            parse_lines(GEDCOM.splitlines()),
            "TEST-ROOT",
        )
        places = build_places_explorer(summary, graph)

        self.assertEqual(places["maxGeneration"], 2)
        self.assertEqual(places["generationOptions"], [2, 4, 8, 12, 16, 24])
        self.assertEqual(len(places["countries"]), 1)
        self.assertEqual(places["countries"][0]["country"], "Brasil")
        self.assertEqual(places["countries"][0]["people"], 1)
        self.assertEqual(
            places["countries"][0]["views"][0]["representatives"][0]["name"],
            "Avô Falecido",
        )

    def test_builds_normalized_roles_explorer(self):
        records = parse_lines(GEDCOM.splitlines())
        summary, graph = build_analytics(records, "TEST-ROOT")
        roles = build_roles_explorer(records, summary, graph)

        self.assertEqual(roles["roleStats"]["peopleWithRecordedRoles"], 1)
        self.assertEqual(roles["roleStats"]["peopleClassified"], 1)
        trades = next(
            item
            for item in roles["roleCategories"]
            if item["slug"] == "trades"
        )
        blacksmith = next(
            item
            for item in roles["roleTerms"]
            if item["slug"] == "blacksmith"
        )
        self.assertEqual(trades["people"], 1)
        self.assertEqual(blacksmith["people"], 1)
        self.assertEqual(
            blacksmith["views"][0]["representatives"][0]["roleTexts"],
            ["Ferreiro"],
        )


if __name__ == "__main__":
    unittest.main()

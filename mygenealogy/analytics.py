"""Build privacy-aware analytics and graph data from a FamilySearch GEDCOM."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, deque
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from .gedcom import Node, read_gedcom


YEAR_RE = re.compile(r"(?<!\d)(\d{3,4})(?!\d)")

COUNTRY_ALIASES = {
    "brasil": "Brasil",
    "brazil": "Brasil",
    "portugal": "Portugal",
    "portuguesa": "Portugal",
    "france": "França",
    "frança": "França",
    "francia": "França",
    "kingdom of france": "França",
    "kingdom of france)": "França",
    "españa": "Espanha",
    "espanha": "Espanha",
    "spain": "Espanha",
    "england": "Inglaterra",
    "united kingdom": "Reino Unido",
    "scotland": "Escócia",
    "wales": "País de Gales",
    "ireland": "Irlanda",
    "nederland": "Países Baixos",
    "netherlands": "Países Baixos",
    "germany": "Alemanha",
    "deutschland": "Alemanha",
    "allemagne": "Alemanha",
    "italy": "Itália",
    "italia": "Itália",
    "itália": "Itália",
    "belgium": "Bélgica",
    "belgië": "Bélgica",
    "belgique": "Bélgica",
    "israel": "Israel",
    "palestine": "Palestina",
    "hungary": "Hungria",
    "poland": "Polônia",
    "austria": "Áustria",
    "turkey": "Turquia",
    "cyprus": "Chipre",
    "holy roman empire": "Sacro Império Romano-Germânico",
    "byzantine empire": "Império Bizantino",
}

FEATURED = {
    "9H17-VTZ": {
        "rank": 1,
        "label": "Guilherme, o Conquistador",
        "description": "Duque da Normandia que conquistou a Inglaterra em 1066 e se tornou seu primeiro rei normando.",
    },
    "9C8T-V1R": {
        "rank": 2,
        "label": "Leonor da Aquitânia",
        "description": "Duquesa da Aquitânia, rainha da França e depois da Inglaterra; uma das mulheres mais influentes da Europa medieval.",
    },
    "LYD7-TB9": {
        "rank": 3,
        "label": "Henrique II da Inglaterra",
        "description": "Primeiro rei Plantageneta da Inglaterra, conhecido por reformas jurídicas e por governar um vasto domínio europeu.",
    },
    "93RN-C7J": {
        "rank": 4,
        "label": "Eduardo III da Inglaterra",
        "description": "Rei inglês por cinco décadas, figura central no início da Guerra dos Cem Anos e fundador da Ordem da Jarreteira.",
    },
    "GWZX-F4D": {
        "rank": 5,
        "label": "John of Gaunt",
        "description": "Filho de Eduardo III, 1º duque de Lancaster e ancestral da dinastia lancastriana da Inglaterra.",
    },
    "9Z8W-FY1": {
        "rank": 6,
        "label": "Philippa de Hainaut",
        "description": "Rainha consorte da Inglaterra, esposa de Eduardo III e mãe de uma geração decisiva para as dinastias inglesas.",
    },
    "9HKC-FP8": {
        "rank": 7,
        "label": "Dom João I de Portugal",
        "description": "Rei que consolidou a independência portuguesa e fundou a dinastia de Avis após a crise de 1383–1385.",
    },
    "LTKD-XJF": {
        "rank": 8,
        "label": "Afonso IV de Portugal",
        "description": "Sétimo rei de Portugal, associado à Batalha do Salado e ao episódio histórico de Inês de Castro.",
    },
    "GWSV-FP7": {
        "rank": 9,
        "label": "Lopo de Almeida",
        "description": "Conselheiro da Coroa e 1º conde de Abrantes, título concedido por Afonso V de Portugal.",
    },
    "KK1Y-QLM": {
        "rank": 10,
        "label": "João de Almeida",
        "description": "2º conde de Abrantes, responsável por dar continuidade à Casa de Abrantes no final do século XV.",
    },
}


def _year(value: str) -> Optional[int]:
    match = YEAR_RE.search(value or "")
    return int(match.group(1)) if match else None


def _clean_name(value: str) -> str:
    return " ".join(value.replace("/", "").split()).strip(" ,")


def _country(place: str) -> Optional[str]:
    if not place:
        return None
    tail = place.split(",")[-1].strip().lower()
    return COUNTRY_ALIASES.get(tail)


def _event_places(person: Node) -> Iterable[str]:
    for child in person.children:
        place = child.child("PLAC")
        if place and place.value:
            yield place.value.strip()


def _event_year(person: Node, tag: str) -> Optional[int]:
    event = person.child(tag)
    return _year(event.text("DATE")) if event else None


def _is_private(person: Node, generation: int) -> bool:
    birth = _event_year(person, "BIRT")
    death = person.child("DEAT")
    has_specific_death = bool(death and (_year(death.text("DATE")) or death.text("PLAC")))
    if has_specific_death:
        return False
    return bool((birth and birth >= 1920) or (generation <= 4 and not birth))


def _ancestral_generations(
    people: Dict[str, Node], families: Dict[str, Node], root: str
) -> Dict[str, int]:
    generations = {root: 0}
    queue = deque([root])
    while queue:
        person_id = queue.popleft()
        next_generation = generations[person_id] + 1
        for family_ref in people[person_id].children_named("FAMC"):
            family = families.get(family_ref.value)
            if not family:
                continue
            for role in ("HUSB", "WIFE"):
                parent_id = family.text(role)
                if not parent_id:
                    continue
                if parent_id not in generations or next_generation < generations[parent_id]:
                    generations[parent_id] = next_generation
                    queue.append(parent_id)
    return generations


def build_analytics(
    records: List[Node],
    root_fsid: str,
    published_root_name: Optional[str] = None,
) -> Tuple[dict, dict]:
    people = {record.xref: record for record in records if record.tag == "INDI" and record.xref}
    families = {record.xref: record for record in records if record.tag == "FAM" and record.xref}
    root = next(
        (xref for xref, person in people.items() if person.text("_FSFTID") == root_fsid),
        None,
    )
    if not root:
        raise ValueError(f"FamilySearch ID {root_fsid!r} was not found in the GEDCOM")

    generations = _ancestral_generations(people, families, root)
    reachable: Set[str] = set(generations)
    generation_counts = Counter(generations.values())
    countries: Counter[str] = Counter()
    places: Counter[str] = Counter()
    birth_years: List[int] = []
    graph_nodes = []
    public_ids: Dict[str, str] = {}

    fsid_to_xref = {
        person.text("_FSFTID"): xref
        for xref, person in people.items()
        if person.text("_FSFTID")
    }

    ordered_reachable = sorted(reachable, key=lambda item: (generations[item], item))
    for private_index, xref in enumerate(ordered_reachable, 1):
        person = people[xref]
        birth_year = _event_year(person, "BIRT")
        death_year = _event_year(person, "DEAT")
        if birth_year:
            birth_years.append(birth_year)
        person_countries = set()
        for place in _event_places(person):
            places[place] += 1
            normalized = _country(place)
            if normalized:
                countries[normalized] += 1
                person_countries.add(normalized)

        private = _is_private(person, generations[xref])
        fsid = person.text("_FSFTID") or xref.strip("@")
        public_id = f"private-{private_index}" if private else fsid
        public_ids[xref] = public_id
        public_name = (
            published_root_name
            if private and xref == root and published_root_name
            else "Pessoa privada"
            if private
            else (_clean_name(person.text("NAME")) or "Nome desconhecido")
        )
        graph_nodes.append(
            {
                "id": public_id,
                "name": public_name,
                "generation": generations[xref],
                "birthYear": birth_year,
                "deathYear": death_year,
                "countries": sorted(person_countries),
                "sourceCount": len(person.children_named("SOUR")),
                "private": private,
            }
        )

    edge_keys: Set[Tuple[str, str]] = set()
    graph_edges = []
    for family in families.values():
        parents = [family.text(role) for role in ("HUSB", "WIFE") if family.text(role)]
        children = [child.value for child in family.children_named("CHIL") if child.value]
        for parent in parents:
            for child in children:
                if parent not in reachable or child not in reachable:
                    continue
                source = public_ids[parent]
                target = public_ids[child]
                key = (source, target)
                if key in edge_keys:
                    continue
                edge_keys.add(key)
                graph_edges.append({"source": source, "target": target})

    featured = []
    for fsid, copy in FEATURED.items():
        xref = fsid_to_xref.get(fsid)
        if not xref or xref not in reachable:
            continue
        person = people[xref]
        featured.append(
            {
                "id": fsid,
                **copy,
                "generation": generations[xref],
                "birthYear": _event_year(person, "BIRT"),
                "deathYear": _event_year(person, "DEAT"),
                "sourceCount": len(person.children_named("SOUR")),
                "status": "Registrada na árvore do FamilySearch",
            }
        )

    featured.sort(key=lambda item: item["rank"])
    summary = {
        "snapshotRoot": "private",
        "people": len(people),
        "reachableAncestors": len(reachable),
        "families": len(families),
        "sources": sum(1 for record in records if record.tag == "SOUR"),
        "notes": sum(1 for record in records if record.tag == "NOTE"),
        "maxGeneration": max(generations.values()),
        "oldestBirthYear": min(birth_years) if birth_years else None,
        "generationCounts": [
            {"generation": generation, "people": count}
            for generation, count in sorted(generation_counts.items())
        ],
        "countries": [
            {"country": country, "events": count}
            for country, count in countries.most_common(12)
        ],
        "places": [
            {"place": place, "events": count}
            for place, count in places.most_common(12)
        ],
        "featuredPeople": featured,
        "privacy": {
            "livingPeopleRedacted": True,
            "message": "Nomes de pessoas potencialmente vivas são ocultados na saída compartilhável.",
        },
    }
    graph = {"nodes": graph_nodes, "edges": graph_edges}
    return summary, graph


def main() -> int:
    parser = argparse.ArgumentParser(description="Create privacy-aware family-tree analytics")
    parser.add_argument("gedcom", type=Path)
    parser.add_argument("--root-fsid", required=True)
    parser.add_argument(
        "--published-root-name",
        help="Public display name for the root person; other potentially living people remain anonymized.",
    )
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--graph", type=Path, required=True)
    args = parser.parse_args()

    summary, graph = build_analytics(
        read_gedcom(args.gedcom),
        args.root_fsid,
        args.published_root_name,
    )
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.graph.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.graph.write_text(json.dumps(graph, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote summary for {summary['reachableAncestors']} reachable people to {args.summary}")
    print(f"Wrote graph with {len(graph['nodes'])} nodes and {len(graph['edges'])} edges to {args.graph}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

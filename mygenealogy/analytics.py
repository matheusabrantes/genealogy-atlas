"""Build privacy-aware analytics and graph data from a FamilySearch GEDCOM."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
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

ROLE_CATEGORIES = [
    {
        "slug": "royalty-nobility",
        "label": "Realeza e nobreza",
        "description": "Reis, rainhas, príncipes, duques, condes e outros títulos nobiliárquicos.",
    },
    {
        "slug": "military-orders",
        "label": "Exército e ordens militares",
        "description": "Cavaleiros, cruzados, capitães, comandantes e membros de ordens militares.",
    },
    {
        "slug": "government",
        "label": "Governo e administração",
        "description": "Governadores, vereadores, embaixadores e administradores públicos.",
    },
    {
        "slug": "church",
        "label": "Igreja e vida religiosa",
        "description": "Papas, bispos, sacerdotes, religiosos e funções ligadas à Igreja.",
    },
    {
        "slug": "justice-inquisition",
        "label": "Justiça e Inquisição",
        "description": "Juízes, notários, juristas, carcereiros e funções inquisitoriais.",
    },
    {
        "slug": "trades",
        "label": "Comércio e ofícios",
        "description": "Mercadores, ferreiros, carpinteiros, artesãos e outros ofícios.",
    },
    {
        "slug": "land-agriculture",
        "label": "Agricultura e propriedade",
        "description": "Lavradores, fazendeiros, proprietários e senhores de engenho.",
    },
    {
        "slug": "navigation",
        "label": "Navegação e exploração",
        "description": "Navegadores, marinheiros, pilotos, exploradores e conquistadores.",
    },
    {
        "slug": "knowledge-medicine",
        "label": "Artes, ciência e medicina",
        "description": "Médicos, cirurgiões, professores, artistas e estudiosos.",
    },
]

ROLE_DEFINITIONS = [
    ("king-queen", "Rei ou rainha", "royalty-nobility", r"\b(king|queen|rei|rainha|rey|reina|roi|reine|konig|konigin)\b"),
    ("emperor", "Imperador ou imperatriz", "royalty-nobility", r"\b(emperor|empress|imperador|imperatriz|kaiser|imperatore|imperatrice)\b"),
    ("prince", "Príncipe ou princesa", "royalty-nobility", r"\b(prince|princess|principe|princesa|infante|infanta)\b"),
    ("duke", "Duque ou duquesa", "royalty-nobility", r"\b(duke|duchess|duc|duchesse|duque|duquesa|herzog|herzogin)\b"),
    ("count", "Conde ou condessa", "royalty-nobility", r"\b(count|countess|comte|comtesse|conde|condessa|earl|graaf|graf|gravin)\b"),
    ("marquis", "Marquês ou marquesa", "royalty-nobility", r"\b(marquis|marquise|marques|marquesa|marchese|markgraf)\b"),
    ("baron", "Barão ou baronesa", "royalty-nobility", r"\b(baron|baroness|barao|baronesa)\b"),
    ("feudal-lord", "Senhorio e fidalguia", "royalty-nobility", r"\b(seigneur|lord|lady|heer|dame|fidalgo|fidalga|noble|rico homem|senhor feudal)\b"),
    ("knight", "Cavaleiro ou escudeiro", "military-orders", r"\b(knight|chevalier|ridder|cavaleir\w*|caballer\w*|ecuyer|escudeir\w*)\b"),
    ("crusader", "Cruzado", "military-orders", r"\b(crois\w*|crusad\w*)\b"),
    ("military-officer", "Oficial militar", "military-orders", r"\b(capitao|captain|coronel|colonel|general|sargento|sergeant|tenente|lieutenant|marechal|marshal|alferes|comandante|constable)\b"),
    ("soldier", "Militar", "military-orders", r"\b(soldier|militar|guerreiro|warrior|exercito|army)\b"),
    ("governor", "Governador", "government", r"\b(governador|governor|gouverneur)\b"),
    ("public-office", "Administrador público", "government", r"\b(vereador|alcalde|mayor|sheriff|chancel\w*|ambassador|embaixador|regent\w*|senator|senescal|steward|alcaide|camareiro|chamberlain|tesoureiro|treasurer|almoxarife)\b"),
    ("high-clergy", "Alto clero", "church", r"\b(pope|papa|cardinal|bishop|bispo|archbishop|arcebispo|patriarch|patriarca)\b"),
    ("clergy", "Clero e vida religiosa", "church", r"\b(priest|padre|sacerdote|monk|monge|abbot|abade|abbess|abadessa|nun|freira|prior|prioress|prioresa|canon|conego|clerigo|capelao|chaplain)\b"),
    ("inquisition", "Inquisição", "justice-inquisition", r"\b(inquis\w*)\b"),
    ("justice", "Justiça e direito", "justice-inquisition", r"\b(juiz|judge|magistrat\w*|justice|notar\w*|tabeliao|lawyer|advogado|jurist\w*|carcereiro|jailer)\b"),
    ("blacksmith", "Ferreiro", "trades", r"\b(ferreiro|blacksmith|ferrador|smith)\b"),
    ("merchant", "Mercador ou comerciante", "trades", r"\b(mercador|merchant|comerciante|trader)\b"),
    ("artisan", "Artesão", "trades", r"\b(carpinteiro|carpenter|alfaiate|tailor|weaver|tecel\w*|goldsmith|silversmith|ourives|artesao|sapateiro|pedreiro|mason)\b"),
    ("agriculture", "Agricultor ou proprietário rural", "land-agriculture", r"\b(farmer|lavrador|fazendeiro|agricultor|planter|landowner|senhor de engenho|proprietario rural)\b"),
    ("navigator", "Navegador ou marinheiro", "navigation", r"\b(navigator|navegador|sailor|marinheiro|almirante|admiral|piloto|pilot)\b"),
    ("explorer", "Explorador ou conquistador", "navigation", r"\b(explorer|explorador|conquistador|bandeirante)\b"),
    ("medicine", "Medicina", "knowledge-medicine", r"\b(doctor|medico|cirurgiao|surgeon|physician|boticario|apothecary)\b"),
    ("arts-knowledge", "Artes e conhecimento", "knowledge-medicine", r"\b(professor|teacher|poet|poeta|escritor|writer|painter|pintor|musician|musico|artist|artista|scientist|cientista|astronom\w*|mathematic\w*)\b"),
]


def _year(value: str) -> Optional[int]:
    match = YEAR_RE.search(value or "")
    return int(match.group(1)) if match else None


def _clean_name(value: str) -> str:
    return " ".join(value.replace("/", "").split()).strip(" ,")


def _normalize_role_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.casefold())
    return " ".join(
        "".join(character for character in normalized if not unicodedata.combining(character)).split()
    )


def _role_texts(person: Node) -> List[str]:
    values = []
    for tag in ("OCCU", "TITL", "RELI"):
        values.extend(
            node.value.strip()
            for node in person.children_named(tag)
            if node.value.strip()
        )
    return values


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


def build_places_explorer(summary: dict, graph: dict) -> dict:
    featured = {person["id"]: person for person in summary["featuredPeople"]}
    max_generation = summary["maxGeneration"]
    generation_options = [4, 8, 12, 16, 24, max_generation]
    generation_options = sorted(set(generation_options))
    countries = sorted(
        {
            country
            for node in graph["nodes"]
            for country in node["countries"]
        }
    )

    def representative(node: dict) -> dict:
        featured_person = featured.get(node["id"])
        return {
            "id": node["id"],
            "name": featured_person["label"] if featured_person else node["name"],
            "generation": node["generation"],
            "birthYear": node["birthYear"],
            "deathYear": node["deathYear"],
            "sourceCount": node["sourceCount"],
            "description": featured_person["description"] if featured_person else None,
            "featured": bool(featured_person),
            "private": node["private"],
        }

    country_entries = []
    for country in countries:
        country_nodes = [
            node
            for node in graph["nodes"]
            if country in node["countries"] and not node["private"]
        ]
        views = []
        for limit in generation_options:
            visible = [node for node in country_nodes if node["generation"] <= limit]
            visible.sort(
                key=lambda node: (
                    0 if node["id"] in featured else 1,
                    featured.get(node["id"], {}).get("rank", 999),
                    -node["sourceCount"],
                    node["generation"],
                    node["name"],
                )
            )
            views.append(
                {
                    "maxGeneration": limit,
                    "people": len(visible),
                    "representatives": [
                        representative(node) for node in visible[:5]
                    ],
                }
            )
        country_entries.append(
            {
                "country": country,
                "people": len(country_nodes),
                "views": views,
            }
        )

    country_entries.sort(key=lambda item: (-item["people"], item["country"]))
    return {
        "maxGeneration": max_generation,
        "generationOptions": generation_options,
        "countries": country_entries,
    }


def build_roles_explorer(records: List[Node], summary: dict, graph: dict) -> dict:
    featured = {person["id"]: person for person in summary["featuredPeople"]}
    generation_options = sorted(
        set([4, 8, 12, 16, 24, summary["maxGeneration"]])
    )
    people_by_id = {
        person.text("_FSFTID") or person.xref.strip("@"): person
        for person in records
        if person.tag == "INDI" and person.xref
    }
    category_copy = {item["slug"]: item for item in ROLE_CATEGORIES}
    role_copy = {
        slug: {"slug": slug, "label": label, "category": category}
        for slug, label, category, _ in ROLE_DEFINITIONS
    }

    profiles = []
    recorded_people = 0
    for node in graph["nodes"]:
        if node["private"]:
            continue
        person = people_by_id.get(node["id"])
        if not person:
            continue
        raw_values = _role_texts(person)
        if not raw_values:
            continue
        recorded_people += 1
        normalized = " | ".join(_normalize_role_text(value) for value in raw_values)
        matched_roles = {
            slug
            for slug, _, _, pattern in ROLE_DEFINITIONS
            if re.search(pattern, normalized)
        }
        if not matched_roles:
            continue
        profiles.append(
            {
                "node": node,
                "roles": matched_roles,
                "categories": {
                    role_copy[role]["category"] for role in matched_roles
                },
                "roleTexts": raw_values[:3],
            }
        )

    def representative(profile: dict) -> dict:
        node = profile["node"]
        featured_person = featured.get(node["id"])
        return {
            "id": node["id"],
            "name": featured_person["label"] if featured_person else node["name"],
            "generation": node["generation"],
            "birthYear": node["birthYear"],
            "deathYear": node["deathYear"],
            "sourceCount": node["sourceCount"],
            "description": featured_person["description"] if featured_person else None,
            "featured": bool(featured_person),
            "private": node["private"],
            "roleTexts": profile["roleTexts"],
        }

    def views_for(selected_profiles: List[dict]) -> List[dict]:
        views = []
        for limit in generation_options:
            visible = [
                profile
                for profile in selected_profiles
                if profile["node"]["generation"] <= limit
            ]
            visible.sort(
                key=lambda profile: (
                    0 if profile["node"]["id"] in featured else 1,
                    featured.get(profile["node"]["id"], {}).get("rank", 999),
                    -profile["node"]["sourceCount"],
                    profile["node"]["generation"],
                    profile["node"]["name"],
                )
            )
            views.append(
                {
                    "maxGeneration": limit,
                    "people": len(visible),
                    "representatives": [
                        representative(profile) for profile in visible[:5]
                    ],
                }
            )
        return views

    categories = []
    for category in ROLE_CATEGORIES:
        selected = [
            profile
            for profile in profiles
            if category["slug"] in profile["categories"]
        ]
        categories.append(
            {
                **category,
                "people": len(selected),
                "views": views_for(selected),
            }
        )
    categories.sort(key=lambda item: (-item["people"], item["label"]))

    terms = []
    for slug, copy in role_copy.items():
        selected = [profile for profile in profiles if slug in profile["roles"]]
        terms.append(
            {
                **copy,
                "categoryLabel": category_copy[copy["category"]]["label"],
                "people": len(selected),
                "views": views_for(selected),
            }
        )
    terms.sort(key=lambda item: (-item["people"], item["label"]))

    return {
        "roleStats": {
            "peopleWithRecordedRoles": recorded_people,
            "peopleClassified": len(profiles),
        },
        "roleCategories": categories,
        "roleTerms": terms,
    }


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
    parser.add_argument(
        "--places",
        type=Path,
        help="Optional compact dataset for the public country and generation explorer.",
    )
    args = parser.parse_args()

    records = read_gedcom(args.gedcom)
    summary, graph = build_analytics(
        records,
        args.root_fsid,
        args.published_root_name,
    )
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.graph.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.graph.write_text(json.dumps(graph, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    if args.places:
        places = build_places_explorer(summary, graph)
        places.update(build_roles_explorer(records, summary, graph))
        args.places.parent.mkdir(parents=True, exist_ok=True)
        args.places.write_text(
            json.dumps(places, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        print(
            f"Wrote places explorer with {len(places['countries'])} countries "
            f"to {args.places}"
        )
    print(f"Wrote summary for {summary['reachableAncestors']} reachable people to {args.summary}")
    print(f"Wrote graph with {len(graph['nodes'])} nodes and {len(graph['edges'])} edges to {args.graph}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

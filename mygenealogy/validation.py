"""Sanity checks for GEDCOM individuals and family relationships."""

import calendar
import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from .gedcom import Node, event


MONTHS = {
    **{name.upper(): index for index, name in enumerate(calendar.month_abbr) if name},
    **{name.upper(): index for index, name in enumerate(calendar.month_name) if name},
    "JANEIRO": 1, "JAN": 1,
    "FEVEREIRO": 2, "FEV": 2,
    "MARCO": 3, "MAR": 3,
    "ABRIL": 4, "ABR": 4,
    "MAIO": 5, "MAI": 5,
    "JUNHO": 6, "JUN": 6,
    "JULHO": 7, "JUL": 7,
    "AGOSTO": 8, "AGO": 8,
    "SETEMBRO": 9, "SET": 9,
    "OUTUBRO": 10, "OUT": 10,
    "NOVEMBRO": 11, "NOV": 11,
    "DEZEMBRO": 12, "DEZ": 12,
}


@dataclass(frozen=True)
class DateSpan:
    earliest: date
    latest: date
    original: str


@dataclass
class Issue:
    severity: str
    code: str
    subjects: List[str]
    message: str
    why: str
    next_step: str


@dataclass
class PlacePeriod:
    name: str
    valid_from: Optional[int] = None
    valid_to: Optional[int] = None


def parse_date(value: str) -> Optional[DateSpan]:
    """Parse common GEDCOM dates into a conservative possible-date interval."""
    plain = unicodedata.normalize("NFKD", value)
    text = "".join(c for c in plain if not unicodedata.combining(c)).strip().upper()
    if not text:
        return None
    # Brazilian FamilySearch exports can contain localized dates rather than
    # canonical GEDCOM dates (for example, "2 de fevereiro de 1926").
    text = re.sub(r"\bDE\b", " ", text)
    text = " ".join(text.split())
    numeric = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if numeric:
        try:
            exact = date(int(numeric.group(3)), int(numeric.group(2)), int(numeric.group(1)))
            return DateSpan(exact, exact, value)
        except (ValueError, OverflowError):
            return None
    if text.startswith("BET ") and " AND " in text:
        left, right = text[4:].split(" AND ", 1)
        a, b = parse_date(left), parse_date(right)
        return DateSpan(a.earliest, b.latest, value) if a and b else None
    if text.startswith("FROM ") and " TO " in text:
        left, right = text[5:].split(" TO ", 1)
        a, b = parse_date(left), parse_date(right)
        return DateSpan(a.earliest, b.latest, value) if a and b else None
    qualifier = ""
    localized_prefixes = {
        "APROXIMADAMENTE ": "ABT", "APROX ": "ABT", "CERCA ": "ABT",
        "ANTES ": "BEF", "DEPOIS ": "AFT", "APOS ": "AFT",
    }
    for prefix, canonical in localized_prefixes.items():
        if text.startswith(prefix):
            qualifier, text = canonical, text[len(prefix):]
            break
    for prefix in ("ABT ", "CAL ", "EST ", "BEF ", "AFT "):
        if text.startswith(prefix):
            qualifier, text = prefix.strip(), text[len(prefix):]
            break
    parts = text.split()
    try:
        if len(parts) == 3 and parts[1] in MONTHS:
            day, month, year = int(parts[0]), MONTHS[parts[1]], int(parts[2])
            exact = date(year, month, day)
            earliest = latest = exact
        elif len(parts) == 2 and parts[0] in MONTHS:
            month, year = MONTHS[parts[0]], int(parts[1])
            earliest = date(year, month, 1)
            latest = date(year, month, calendar.monthrange(year, month)[1])
        elif len(parts) == 1 and parts[0].isdigit():
            year = int(parts[0])
            earliest, latest = date(year, 1, 1), date(year, 12, 31)
        else:
            return None
    except (ValueError, OverflowError):
        return None
    if qualifier in {"ABT", "CAL", "EST"}:
        earliest, latest = date(max(1, earliest.year - 1), 1, 1), date(min(9999, latest.year + 1), 12, 31)
    elif qualifier == "BEF":
        earliest, latest = date(1, 1, 1), earliest
    elif qualifier == "AFT":
        earliest, latest = latest, date(9999, 12, 31)
    return DateSpan(earliest, latest, value)


def years_between(older: date, newer: date) -> float:
    return (newer - older).days / 365.2425


def _norm(value: str) -> str:
    plain = unicodedata.normalize("NFKD", value.replace("/", " "))
    return " ".join("".join(c for c in plain if not unicodedata.combining(c)).casefold().split())


def _label(person: Node) -> str:
    return f"{person.xref or '?'} ({person.text('NAME', 'unnamed').replace('/', '')})"


def _has_given_name(person: Node) -> bool:
    name = person.text("NAME")
    return bool(name.split("/", 1)[0].strip()) if "/" in name else bool(name.strip())


def _source_count(record: Node) -> int:
    return sum(1 for node in record.walk() if node.tag == "SOUR")


def _direct_ancestors(root: Optional[str], parents: Dict[str, Set[str]]) -> Set[str]:
    if not root:
        return set()
    seen, pending = set(), [root]
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        pending.extend(parents.get(current, ()))
    return seen


def load_place_periods(path: Optional[Path]) -> List[PlacePeriod]:
    if not path:
        return []
    import csv
    result = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            result.append(PlacePeriod(row["name"], int(row["valid_from"]) if row.get("valid_from") else None, int(row["valid_to"]) if row.get("valid_to") else None))
    return result


def validate(records: Iterable[Node], root: Optional[str] = None, place_periods: Optional[List[PlacePeriod]] = None) -> Tuple[List[Issue], dict]:
    records = list(records)
    person_records = [r for r in records if r.tag == "INDI" and r.xref]
    people = {r.xref: r for r in person_records}
    families = [r for r in records if r.tag == "FAM"]
    issues: List[Issue] = []
    parents: Dict[str, Set[str]] = {}
    parent_families: Dict[str, List[Tuple[str, str, str]]] = {}

    def add(severity: str, code: str, subjects: List[str], message: str, why: str, next_step: str) -> None:
        issues.append(Issue(severity, code, subjects, message, why, next_step))

    xref_counts: Dict[str, int] = {}
    for record in [r for r in records if r.xref]:
        xref_counts[record.xref] = xref_counts.get(record.xref, 0) + 1
    for xref, count in xref_counts.items():
        if count > 1:
            add("critical", "DUPLICATE_XREF", [xref], f"The GEDCOM defines {count} top-level records with the same identifier.", "References to this identifier are ambiguous and one record silently replacing another would corrupt validation.", "Re-export from the source application and inspect the duplicate identifier before trusting other results.")

    for family in families:
        father, mother = family.text("HUSB"), family.text("WIFE")
        child_ids = [n.value for n in family.children_named("CHIL")]
        if father and father == mother:
            add("critical", "SELF_RELATIONSHIP", [father], "The same person is listed as both spouses in one family.", "A person cannot be their own spouse in a genealogical family relationship.", "Inspect the family record and replace the unsupported spouse link with the correct individual.")
        if len(child_ids) != len(set(child_ids)):
            add("warning", "DUPLICATE_CHILD_LINK", child_ids, "A child is linked more than once in the same family.", "Repeated relationship links can produce misleading descendants and duplicate events.", "Inspect the family record and retain one supported parent-child relationship.")
        for child_id in child_ids:
            parents.setdefault(child_id, set()).update(x for x in (father, mother) if x)
            parent_families.setdefault(child_id, []).append((family.xref or "?", father, mother))
        for role, person_id in (("spouse", father), ("spouse", mother)):
            if person_id and person_id not in people:
                add("critical", "BROKEN_REFERENCE", [person_id], f"Family references a missing {role} record.", "The relationship cannot be verified and may indicate a truncated or corrupt export.", "Re-export the GEDCOM and inspect the family in the source application.")
        for role, person_id, expected in (("husband", father, "M"), ("wife", mother, "F")):
            person = people.get(person_id)
            recorded = person.text("SEX").upper() if person else ""
            if recorded and recorded != expected:
                add(
                    "warning", "SEX_ROLE_CONFLICT", [_label(person)],
                    f"The family lists this person as {role}, but the profile sex is {recorded!r}.",
                    "The spouse role and recorded sex disagree; this can indicate a profile data error, swapped spouses, or an incorrect relationship.",
                    "Inspect the original record naming the couple and correct only the unsupported sex or spouse role in FamilySearch.",
                )
        for child_id in child_ids:
            if child_id not in people:
                add("critical", "BROKEN_REFERENCE", [child_id], "Family references a missing child record.", "The relationship cannot be verified and may indicate a truncated or corrupt export.", "Re-export the GEDCOM and inspect the family in the source application.")

        marriage_date, _ = event(family, "MARR")
        marriage = parse_date(marriage_date)
        if marriage:
            for spouse_id in (father, mother):
                spouse = people.get(spouse_id)
                birth = parse_date(event(spouse, "BIRT")[0]) if spouse else None
                if birth and years_between(birth.latest, marriage.earliest) < 12:
                    add("critical", "MARRIAGE_UNDER_12", [_label(spouse)], f"Marriage {marriage_date!r} can place this spouse under age 12.", "This is biologically/socially exceptional and often signals a wrong person, date, or relationship.", "Check the original marriage entry and baptism/birth record; verify parents and witnesses before editing.")
                elif birth and years_between(birth.earliest, marriage.latest) > 90:
                    add("warning", "MARRIAGE_AGE_HIGH", [_label(spouse)], f"Marriage {marriage_date!r} can place this spouse over age 90.", "A very late marriage is possible but uncommon and may indicate a namesake or date error.", "Inspect the marriage image, marital status, prior spouse, parents, and residence.")

        dated_children = []
        for child_id in child_ids:
            child = people.get(child_id)
            child_birth = parse_date(event(child, "BIRT")[0]) if child else None
            if child_birth:
                dated_children.append((child_id, child_birth))
            for parent_id in (father, mother):
                parent = people.get(parent_id)
                if not parent or not child or not child_birth:
                    continue
                parent_birth = parse_date(event(parent, "BIRT")[0])
                parent_death = parse_date(event(parent, "DEAT")[0])
                if parent_birth:
                    min_age = years_between(parent_birth.latest, child_birth.earliest)
                    max_age = years_between(parent_birth.earliest, child_birth.latest)
                    if max_age < 0:
                        add("critical", "PARENT_YOUNGER_THAN_CHILD", [_label(parent), _label(child)], "The parent is born after the child.", "This relationship or one of the dates is impossible.", "Compare original birth/baptism and marriage records; distinguish same-name individuals.")
                    elif min_age < 13:
                        add("critical", "PARENT_UNDER_13", [_label(parent), _label(child)], f"The parent-child dates allow a parental age below 13 ({min_age:.1f} years at the strictest endpoints).", "This is a strong red flag for a wrong date, person, or relationship.", "Verify the child's birth/baptism, parents' marriage, and the parent's own birth/baptism images.")
                    elif max_age > 60:
                        add("warning", "PARENT_OVER_60", [_label(parent), _label(child)], f"The parent-child dates allow a parental age above 60 ({max_age:.1f} years).", "This is possible for fathers but uncommon, and generally implausible for biological mothers.", "Check whether generations were skipped or two namesakes were merged; inspect the child's record and grandparents.")
                if parent_death and child_birth.earliest > parent_death.latest:
                    delta = (child_birth.earliest - parent_death.latest).days
                    severity = "warning" if delta <= 300 else "critical"
                    add(severity, "CHILD_AFTER_PARENT_DEATH", [_label(parent), _label(child)], f"The child is born at least {delta} days after the parent's latest possible death date.", "A short interval can be a posthumous birth; a long interval usually means a bad date or relationship.", "Check the parent's burial/death image and the child's birth/baptism image, including legitimacy and named parents.")
        if len(dated_children) > 1:
            listed = [x[0] for x in dated_children]
            chronological = [x[0] for x in sorted(dated_children, key=lambda x: x[1].earliest)]
            if listed != chronological:
                add("minor", "SIBLING_ORDER", listed, "Children are not listed in chronological birth order in this family record.", "GEDCOM order is not always meaningful, but an unexpected order can reveal a mistyped date.", "Compare each child's birth/baptism image; reorder only if the source application treats order as significant.")

    for child_id, links in parent_families.items():
        distinct = {(father, mother) for _, father, mother in links}
        if len(distinct) > 1:
            child = people.get(child_id)
            descriptions = [
                f"{family_id}: {people.get(father).text('NAME').replace('/', '') if people.get(father) else father or '?'} + "
                f"{people.get(mother).text('NAME').replace('/', '') if people.get(mother) else mother or '?'}"
                for family_id, father, mother in links
            ]
            add(
                "warning", "MULTIPLE_PARENT_FAMILIES", [_label(child)] if child else [child_id],
                "The person is linked as a child to multiple parent couples: " + "; ".join(descriptions) + ".",
                "Two biological parent couples cannot both be correct. Adoption or step-parent links are possible, but this GEDCOM export does not preserve enough relationship detail to prove that.",
                "Open the person's FamilySearch parent relationships, inspect the reason statements and attached birth/baptism records, then keep or label each relationship according to the evidence.",
            )

    for person in people.values():
        birth_text, birth_place = event(person, "BIRT")
        death_text, death_place = event(person, "DEAT")
        birth, death = parse_date(birth_text), parse_date(death_text)
        if birth and death:
            if death.latest < birth.earliest:
                add("critical", "DEATH_BEFORE_BIRTH", [_label(person)], f"Death {death_text!r} occurs before birth {birth_text!r}.", "The chronology is impossible.", "Inspect the original birth/baptism and death/burial records and check for a same-name merge.")
            elif years_between(birth.earliest, death.latest) > 110:
                add("warning", "LIFESPAN_OVER_110", [_label(person)], f"The dates allow a lifespan over 110 years ({years_between(birth.earliest, death.latest):.1f}).", "Such lifespans are exceptionally rare and commonly reflect conflated people or an incorrect century.", "Verify both endpoint records and compare parents, spouse, occupation, and residence.")
        if birth:
            for tag, label in (("CHR", "christening"), ("BAPM", "baptism")):
                event_text, _ = event(person, tag)
                event_date = parse_date(event_text)
                if event_date and event_date.latest < birth.earliest:
                    add(
                        "critical", "EVENT_BEFORE_BIRTH", [_label(person)],
                        f"The recorded {label} {event_text!r} occurs before the birth {birth_text!r}.",
                        "A christening or baptism cannot precede the person's birth; one of the dates or the identity is wrong.",
                        "Compare the baptism image with the birth/death evidence, especially the parents, parish, residence, and age; check whether two same-name people were merged.",
                    )

    # Detect ancestor cycles with a path-aware DFS.
    visiting: Set[str] = set()
    visited: Set[str] = set()
    def dfs(person_id: str, path: List[str]) -> None:
        if person_id in visiting:
            start = path.index(person_id) if person_id in path else 0
            cycle = path[start:] + [person_id]
            add("critical", "ANCESTRY_LOOP", cycle, "A person appears in their own ancestry path.", "A biological ancestor graph must be acyclic.", "Inspect every parent-child link in the reported cycle and remove only the unsupported relationship.")
            return
        if person_id in visited:
            return
        visiting.add(person_id)
        for parent_id in parents.get(person_id, ()):
            dfs(parent_id, path + [person_id])
        visiting.remove(person_id)
        visited.add(person_id)
    for person_id in people:
        dfs(person_id, [])

    # Conservative duplicate candidates: same normalized name plus overlapping birth dates.
    groups: Dict[str, List[Node]] = {}
    for person in people.values():
        name = _norm(person.text("NAME"))
        if name and _has_given_name(person):
            groups.setdefault(name, []).append(person)
    for same_name in groups.values():
        for i, left in enumerate(same_name):
            for right in same_name[i + 1:]:
                lb, rb = parse_date(event(left, "BIRT")[0]), parse_date(event(right, "BIRT")[0])
                overlap = not lb or not rb or (lb.earliest <= rb.latest and rb.earliest <= lb.latest)
                if overlap:
                    add("warning", "POSSIBLE_DUPLICATE", [_label(left), _label(right)], "Two records have the same normalized name and compatible or missing birth dates.", "They may be duplicates, but Brazilian names often repeat across generations and families.", "Compare parents, spouses, residences, occupations, sources, and record images before merging.")

    direct = _direct_ancestors(root, parents)
    for person_id, person in people.items():
        missing = []
        birth_text, birth_place = event(person, "BIRT")
        death_text, death_place = event(person, "DEAT")
        deceased = person.child("DEAT") is not None
        if not birth_text: missing.append("birth date")
        if not birth_place: missing.append("birth place")
        if deceased and not death_text: missing.append("death date")
        if deceased and not death_place: missing.append("death place")
        if _source_count(person) == 0: missing.append("sources")
        if missing:
            severity = "gap" if person_id in direct and deceased else "minor"
            add(severity, "MISSING_CRITICAL_DATA", [_label(person)], f"Missing: {', '.join(missing)}.", "Missing vital facts and sources weaken identity and relationship conclusions.", "Prioritize a birth/baptism or marriage record naming parents; then add death/burial and corroborating sources.")
        if not _has_given_name(person):
            add(
                "gap" if person_id in direct else "minor", "MISSING_GIVEN_NAME", [_label(person)],
                "The profile contains only a surname and no given name.",
                "A surname-only identity is too weak to distinguish the person from relatives with the same family name.",
                "Search the child's baptism or marriage record and the spouse's records for the person's full name; preserve the spelling shown in the image.",
            )

    for period in place_periods or []:
        target = _norm(period.name)
        for person in people.values():
            for tag in ("BIRT", "DEAT", "BURI"):
                date_text, place = event(person, tag)
                span = parse_date(date_text)
                if not span or target not in _norm(place):
                    continue
                if period.valid_from and span.latest.year < period.valid_from or period.valid_to and span.earliest.year > period.valid_to:
                    add("warning", "PLACE_PERIOD_MISMATCH", [_label(person)], f"{tag} place {place!r} conflicts with the configured validity period for {period.name}.", "The place name or jurisdiction may be anachronistic, or the event date may be wrong.", "Use IBGE historical municipalities, parish/diocese histories, maps, and the original record's contemporary place wording.")

    order = {"critical": 0, "warning": 1, "gap": 2, "minor": 3}
    issues.sort(key=lambda issue: (order.get(issue.severity, 9), issue.code, issue.subjects))
    summary = {"people": len(people), "families": len(families), "issues": len(issues), "by_severity": {key: sum(i.severity == key for i in issues) for key in order}, "root": root}
    return issues, summary


def report_json(issues: List[Issue], summary: dict) -> str:
    return json.dumps({"summary": summary, "issues": [asdict(issue) for issue in issues]}, ensure_ascii=False, indent=2)

"""A deliberately small GEDCOM 5.5/5.5.1 reader.

The reader preserves record order and the fields needed by the validator. It is
not intended to replace a full genealogy application or to round-trip every
vendor extension.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Tuple


@dataclass
class Node:
    level: int
    tag: str
    value: str = ""
    xref: Optional[str] = None
    children: List["Node"] = field(default_factory=list)
    line_number: int = 0

    def child(self, tag: str) -> Optional["Node"]:
        return next((node for node in self.children if node.tag == tag), None)

    def children_named(self, tag: str) -> List["Node"]:
        return [node for node in self.children if node.tag == tag]

    def text(self, tag: str, default: str = "") -> str:
        node = self.child(tag)
        return node.value if node else default

    def walk(self) -> Iterator["Node"]:
        yield self
        for child in self.children:
            yield from child.walk()


def _parse_line(raw: str, number: int) -> Node:
    parts = raw.rstrip("\r\n").split(" ", 2)
    if len(parts) < 2:
        raise ValueError(f"line {number}: invalid GEDCOM line")
    try:
        level = int(parts[0])
    except ValueError as exc:
        raise ValueError(f"line {number}: invalid level {parts[0]!r}") from exc

    second = parts[1]
    third = parts[2] if len(parts) == 3 else ""
    if second.startswith("@") and second.endswith("@"):
        tag_parts = third.split(" ", 1)
        if not tag_parts or not tag_parts[0]:
            raise ValueError(f"line {number}: missing tag after xref")
        return Node(level, tag_parts[0], tag_parts[1] if len(tag_parts) > 1 else "", second, line_number=number)
    return Node(level, second, third, line_number=number)


def parse_lines(lines: Iterable[str]) -> List[Node]:
    roots: List[Node] = []
    stack: List[Node] = []
    for number, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        node = _parse_line(raw, number)
        while stack and stack[-1].level >= node.level:
            stack.pop()
        if stack:
            if node.level != stack[-1].level + 1:
                raise ValueError(f"line {number}: level jumps from {stack[-1].level} to {node.level}")
            stack[-1].children.append(node)
        else:
            if node.level != 0:
                raise ValueError(f"line {number}: top-level record must have level 0")
            roots.append(node)
        stack.append(node)
    return roots


def read_gedcom(path: Path) -> List[Node]:
    raw = path.read_bytes()
    # GEDCOM 5.5.1 commonly uses UTF-8, ASCII, or ANSEL. Latin-1 is a
    # conservative fallback that preserves bytes for inspection.
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return parse_lines(raw.decode(encoding).splitlines())
        except UnicodeDecodeError:
            continue
    raise ValueError(f"unable to decode {path}")


def event(record: Node, tag: str) -> Tuple[str, str]:
    node = record.child(tag)
    if not node:
        return "", ""
    return node.text("DATE"), node.text("PLAC")


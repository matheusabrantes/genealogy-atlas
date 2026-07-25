"""Command-line interface for local GEDCOM validation."""

import argparse
from pathlib import Path

from .gedcom import read_gedcom
from .validation import load_place_periods, report_json, validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mygenealogy", description="Validate a GEDCOM tree without modifying it")
    parser.add_argument("gedcom", type=Path, help="path to a .ged file")
    parser.add_argument("--root", help="GEDCOM xref of the home person, for example @I1@")
    parser.add_argument("--places", type=Path, help="optional CSV with name,valid_from,valid_to columns")
    parser.add_argument("--output", type=Path, help="write JSON report to this path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    records = read_gedcom(args.gedcom)
    issues, summary = validate(records, root=args.root, place_periods=load_place_periods(args.places))
    rendered = report_json(issues, summary)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote {summary['issues']} issues to {args.output}")
    else:
        print(rendered)
    return 1 if summary["by_severity"]["critical"] else 0


if __name__ == "__main__":
    raise SystemExit(main())


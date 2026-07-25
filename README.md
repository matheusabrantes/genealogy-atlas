# Kinship Atlas

Kinship Atlas is an open-source toolkit and public, privacy-aware web experience
for exploring, validating, and documenting a family tree exported from
FamilySearch.

The current dataset follows one Brazilian family from Icó, Ceará, and the
Paraíba backlands into historical branches across Europe. The public interface
is written in Brazilian Portuguese so it can be shared with the family.

**Live website:** [kinship-atlas.matheus-abrantes.chatgpt.site](https://kinship-atlas.matheus-abrantes.chatgpt.site)

## What it does

- imports a read-only GEDCOM snapshot from FamilySearch through an optional,
  separately installed tool;
- validates age, marriage, chronology, lifespan, duplicate, loop, missing-data,
  source, and geographic consistency;
- generates a sanitized graph that redacts both names and FamilySearch IDs for
  people who may still be living;
- presents headline statistics, historical people, countries, generations, and
  current research questions;
- provides an interactive graph with search, generation filters, zoom, and
  person details;
- records hypotheses separately from documented relationships.

## Project structure

```text
mygenealogy/   GEDCOM parser, validation rules, and public-data generator
scripts/       controlled FamilySearch import workflow
tests/         Python validation and privacy tests
research/      structured research questions and evidence status
web/           Vinext/React public website and graph explorer
data/          private local GEDCOM files, ignored by Git
reports/       private generated validation reports, ignored by Git
```

## Validate a GEDCOM

Python 3.9 or newer is sufficient:

```bash
python3 -m mygenealogy.cli path/to/tree.ged \
  --root '@I1@' \
  --output reports/tree.json
```

An optional historical-place CSV can be supplied with `--places`.

## Import a private FamilySearch snapshot

The importer is an optional external GPL-3.0 dependency pinned in
`requirements-familysearch.txt`. Credentials are entered interactively and are
never persisted by the wrapper.

```bash
./scripts/import_familysearch.zsh ABCD-123 5
```

The resulting GEDCOM and validation report remain local and are ignored by Git.

## Generate public graph data

```bash
python3 -m mygenealogy.analytics \
  data/familysearch-snapshot.ged \
  --root-fsid ABCD-123 \
  --summary web/public/data/tree-summary.json \
  --graph web/public/data/tree-graph.json
```

The generated files contain deceased historical people and anonymized nodes for
people who may be alive. Automated living-status inference is conservative but
must still be reviewed before each public release.

## Run the website

Requires Node.js 22.13 or newer:

```bash
cd web
npm install
npm run dev
```

Then open `http://localhost:3000`.

## Tests

```bash
python3 -m unittest discover -s tests -v
npm test --prefix web
npm audit --omit=dev --prefix web
```

## Data provenance

Historical relationships shown by Kinship Atlas come from the imported
FamilySearch tree. Open research questions, such as an unconnected candidate
relative, remain structurally separate until they are added to that tree.

## Privacy

Never commit raw GEDCOM files, credentials, restricted record images, addresses,
or unredacted data about living people. The public graph deliberately replaces
living names and external identifiers with anonymous local nodes.

## License

No license has been selected yet. Until one is added, the source is publicly
visible but normal copyright restrictions apply.

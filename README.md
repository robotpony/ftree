# Family tree viewer

Read and convert GEDCOM (genealogy) files to Markdown. Generates interlinked markdown files for use in Obsidian, as well as CSV.

`ftree` reads a .GED file into an internal object graph, and is able to write out files based on that internal representation. 

## Motivation

I created `ftree` to dump  .GED files, after I used a web service to build a family tree, so I could continue to view my files after the paid service expired.

## Installation

Requires Rust toolchain. Build with:

```bash
cargo build --release
```

The binary will be at `target/release/ftree`.

## Usage

The ftree tool provides several commands for working with GEDCOM genealogy files:

```bash
# Check file validity and statistics
ftree check <filename>

# Export to Markdown (one file per person)
ftree export <filename> [options]
```

### Commands

#### `ftree check <filename>`

Check a GEDCOM file for validity and missing data. Reports individual/family counts, missing fields, and parser warnings.

```bash
ftree check myfile.ged
```

#### `ftree export <filename>`

Export family tree to Markdown or CSV.

**Options:**

- `--format md|csv` — Output format (default: md)
- `--output`, `-o` — Output path (directory for md, file for csv)

```bash
# Export to Markdown (one file per person)
ftree export myfile.ged
ftree export myfile.ged --output ~/obsidian-vault/family

# Export to CSV
ftree export myfile.ged --format csv
ftree export myfile.ged --format csv --output family.csv
```

#### `ftree list <filename> <field>`

Extract specific field values from a GEDCOM file. Useful for quick lookups and piping to other tools.

**Fields:** names, surnames, places, dates

**Options:**

- `--unique` — Deduplicate and sort output

```bash
# List all names
ftree list myfile.ged names

# List unique surnames
ftree list myfile.ged surnames --unique

# List all places mentioned (birth, death, marriage)
ftree list myfile.ged places --unique
```

#### Planned commands

- `ftree view <filename>` — ASCII tree view (Phase 4)

## Formats

**Input:**

- GEDCOM 5.5 / 5.5.1 (.ged) — the standard text format for genealogy data
- .inftree — Family Historian binary format (planned)

**Output:**

- Markdown (Obsidian/Hugo compatible, with front-matter)
- CSV
- ASCII tree view
- SVG (planned)
- HTML (planned)

## Architecture

- GEDCOM reader library
- .inftree reader library (planned)
- LINT checker for in-memory representation
- ASCII output renderer
- SVG output renderer (planned)
- HTML output renderer (planned)

## GEDCOM Support

For the full GEDCOM format specification, including all record types, date formats, and ftree's implementation status per tag, see [docs/GEDCOM.md](docs/GEDCOM.md).

**Currently supported:** HEAD, INDI, FAM, SUBM, TRLR, NAME (with GIVN/SURN), SEX, BIRT, DEAT, FAMS, FAMC, MARR, HUSB, WIFE, CHIL, DATE, PLAC, FILE, OBJE.

**Planned:** SOUR, NOTE, REPO, BURI, CHR, ADOP, DIV, OCCU, RESI, TITL, and more. See the specification for the full list.

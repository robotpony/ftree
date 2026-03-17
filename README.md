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

Check a GEDCOM file for validity and data quality. Reports individual/family counts, missing fields, lint issues (dangling cross-references, date inconsistencies), and parser warnings.

```bash
ftree check myfile.ged
```

#### `ftree export <filename>`

Export family tree to Markdown, CSV, SVG, or HTML.

**Options:**

- `--format md|csv|svg|html` — Output format (default: md)
- `--output`, `-o` — Output path (directory for md, file for all others)
- `--embed-svg` — (HTML only) Embed the SVG family tree diagram at the top of the page

```bash
# Export to Markdown (one file per person)
ftree export myfile.ged
ftree export myfile.ged --output ~/obsidian-vault/family

# Export to CSV
ftree export myfile.ged --format csv
ftree export myfile.ged --format csv --output family.csv

# Export to SVG (family tree diagram)
ftree export myfile.ged --format svg

# Export to HTML (standalone viewer with search and dark mode)
ftree export myfile.ged --format html

# Export to HTML with embedded SVG diagram
ftree export myfile.ged --format html --embed-svg
```

#### `ftree list <filename> <field>`

Extract specific field values from a GEDCOM file. Useful for quick lookups and piping to other tools.

**Fields:** names, surnames, places, dates, sources

**Options:**

- `--unique` — Deduplicate and sort output

```bash
# List all names
ftree list myfile.ged names

# List unique surnames
ftree list myfile.ged surnames --unique

# List all places mentioned (birth, death, marriage)
ftree list myfile.ged places --unique

# List cited sources
ftree list myfile.ged sources --unique
```

#### `ftree view <filename>`

Display a family tree as ASCII art in the terminal.

**Options:**

- `--layout horizontal|topdown` — Layout orientation (default: horizontal)
- `--output`, `-o` — Write to file instead of stdout

```bash
# Horizontal tree (default)
ftree view myfile.ged

# Top-down box layout
ftree view myfile.ged --layout topdown

# Save to file
ftree view myfile.ged --output tree.txt
```

## Formats

**Input:**

- GEDCOM 5.5 / 5.5.1 (.ged) — the standard text format for genealogy data
- .inftree — Family Historian binary format (planned)

**Output:**

- Markdown (Obsidian/Hugo compatible, with front-matter)
- CSV
- ASCII tree view (horizontal and top-down)
- SVG (family tree diagram with sex-coloured boxes)
- HTML (standalone viewer with search, dark mode, individual detail cards)

## Architecture

- GEDCOM reader library
- .inftree reader library (planned)
- LINT checker for in-memory representation
- ASCII output renderer
- SVG output renderer (planned)
- HTML output renderer (planned)

## GEDCOM Support

For the full GEDCOM format specification, including all record types, date formats, and ftree's implementation status per tag, see [docs/GEDCOM.md](docs/GEDCOM.md).

**Currently supported:** HEAD, INDI, FAM, SUBM, TRLR, NAME (with GIVN/SURN), SEX, BIRT, DEAT, BURI, CHR, ADOP, RESI, FAMS, FAMC, MARR, DIV, ENGA, ANUL, HUSB, WIFE, CHIL, DATE, PLAC, FILE, OBJE (inline and pointer-form, with TITL), SOUR (records and citations with PAGE/QUAY), REPO, NOTE (records and inline, with CONT/CONC), OCCU, EDUC, TITL.

**Planned:** Additional attribute tags, CENS, EMIG, IMMI, and more. See [docs/GEDCOM.md](docs/GEDCOM.md) for the full list.

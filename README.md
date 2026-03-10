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

Export family tree to Markdown. Creates one `.md` file per individual with YAML front-matter and Obsidian wikilinks.

**Options:**

- `--format md` — Output format (default: md)
- `--output`, `-o` — Output directory (default: input filename without extension)

```bash
# Export to ./myfile/ directory
ftree export myfile.ged

# Export to a specific directory
ftree export myfile.ged --output ~/obsidian-vault/family
```

#### Planned commands

- `ftree view <filename>` — ASCII tree view (Phase 4)
- `ftree list <filename> <field>` — Extract field values (Phase 3)

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

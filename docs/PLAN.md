# Implementation Plan

Phased approach to building ftree. Each phase produces a usable tool with incrementally more capability.

## Phase 1: Core Parser + Check Command ✓

**Status:** Complete (v0.1.0)

**Goal:** Parse GEDCOM files and report statistics. Validate the data model works.

**Deliverables:**

1. ✓ Cargo project setup (lib + binary crate, clap skeleton)
2. ✓ Core model types (`FamilyTree`, `Individual`, `Family`, `Name`, `Event`, `Date`, `Place`)
3. ✓ GEDCOM lexer (line tokenizer)
4. ✓ GEDCOM builder (tokens → `FamilyTree`)
5. ✓ UTF-8 encoding support (BOM detection, UTF-16 conversion via `encoding_rs`)
6. ✓ `ftree check <file>` command: parse and print statistics (individual count, family count, missing fields)
7. ✓ Unit tests for lexer and builder (40 unit tests)
8. ✓ Integration tests against all sample .ged files (6 integration tests)

**Supported tags:** HEAD, TRLR, INDI, FAM, SUBM, NAME (GIVN, SURN), SEX, BIRT, DEAT, FAMS, FAMC, HUSB, WIFE, CHIL, MARR, DATE, PLAC, OBJE, FILE

**Exit criteria:** All five sample files parse without errors. `ftree check` reports accurate counts.

## Phase 2: Markdown Export ✓

**Status:** Complete (v0.2.0)

**Goal:** Export to one-Markdown-file-per-person for Obsidian.

**Deliverables:**

1. ✓ Renderer trait definition
2. ✓ Markdown renderer (YAML front-matter + wikilinks)
3. ✓ `ftree export <file> --format md --output <dir>` command
4. ✓ File naming strategy (handle duplicate names, special characters)
5. ✓ Tests verifying front-matter structure and wikilink correctness (9 unit + 7 integration)

**Front-matter fields:** name, sex, birth_date, birth_place, death_date, death_place, tags (person, male/female)

**Exit criteria:** Exported Markdown files open correctly in Obsidian with working inter-file links.

## Phase 3: CSV Export + List Command ✓

**Status:** Complete (v0.3.0)

**Goal:** Tabular data export and field extraction.

**Deliverables:**

1. ✓ CSV renderer (xref, name, given, surname, sex, birth/death date/place, father, mother, spouses)
2. ✓ `ftree export <file> --format csv` command (defaults output to `<file>.csv`)
3. ✓ `ftree list <file> <field>` command (names, surnames, places, dates)
4. ✓ `--unique` flag for deduplicated, sorted output on `list`
5. ✓ Tests: 12 unit tests for CSV, 7 unit tests for list, 8 integration tests

**Exit criteria:** CSV opens correctly in spreadsheet applications. `list` command outputs match expected field values.

## Phase 4: ASCII Tree View ✓

**Status:** Complete (v0.4.0)

**Goal:** Terminal-based tree visualization.

**Deliverables:**

1. ✓ ASCII renderer with top-down box layout (Unicode box-drawing, couples side-by-side)
2. ✓ ASCII renderer with left-to-right horizontal layout (tree-style indentation with connectors)
3. ✓ `ftree view <file> [--layout topdown|horizontal]` command (defaults to horizontal)
4. ✓ Root ancestor detection (individuals with no FAMC, family deduplication)
5. ✓ Multiple disconnected family groups rendered with blank line separation
6. ✓ Optional `--output` flag to write to file instead of stdout
7. ✓ Tests: 9 unit tests for ASCII, 6 integration tests

**Exit criteria:** Trees render correctly for all sample files. Both layouts produce readable output.

## Phase 4.5: Source and Repository Records ✓

**Status:** Complete (v0.5.0)

**Goal:** Parse SOUR and REPO records. MARR and OBJE were already supported from Phase 1.

**Deliverables:**

1. ✓ Source record type (TITL, AUTH, PUBL, ABBR, TEXT, REPO pointer)
2. ✓ Repository record type (NAME)
3. ✓ Inline source citations within INDI records (SOUR @xref@ with PAGE)
4. ✓ `check` command reports source and repository counts
5. ✓ CSV export includes `sources` column
6. ✓ Markdown export includes Sources section per individual
7. ✓ `list` command supports `sources` field
8. ✓ Tests: 12 new unit tests for parsing, 3 for rendering

**Exit criteria:** Source and repository data parsed from sample files. All renderers include source information.

## Phase 5: Lint + Validation

**Goal:** Data quality checking beyond basic statistics.

**Deliverables:**

1. Lint rule framework
2. Rules: dangling xref references, duplicate individuals, missing required fields, date inconsistencies (death before birth, etc.)
3. Enhanced `ftree check` output with categorized warnings
4. Tests for each lint rule

**Exit criteria:** `check` command identifies known issues in sample files.

## Phase 6: Extended GEDCOM Support

**Goal:** Support additional GEDCOM tags from the specification.

**Deliverables:**

1. Source records (SOUR, with PAGE, QUAY, AUTH, PUBL)
2. Note records (NOTE, with CONT/CONC)
3. Additional individual events (BURI, CHR, ADOP, OCCU, RESI, EDUC, TITL)
4. Additional family events (DIV, ENGA, ANUL)
5. Update model, renderers, and tests

**Priority order:** SOUR (appears in sample files) → NOTE → BURI/CHR → OCCU/RESI/TITL → DIV → remaining

## Phase 7: .inftree Binary Format

**Goal:** Parse Family Historian .inftree files.

**Deliverables:**

1. .inftree format reverse-engineering / documentation
2. Binary parser using `nom`
3. Format auto-detection (GEDCOM vs .inftree based on file extension and magic bytes)
4. Tests against .inftree sample files

**Dependency:** Requires access to .inftree file format documentation or sample files for reverse engineering.

## Phase 8: SVG + HTML Output

**Goal:** Visual output formats.

**Deliverables:**

1. SVG renderer (tree layout with configurable styling)
2. HTML renderer (standalone page with embedded CSS, possibly interactive)
3. CSS theme support
4. `ftree export <file> --format svg|html` commands

## Not Planned (Out of Scope)

- GEDCOM 7.0 support (structural incompatibilities require separate parser path; defer until adoption increases)
- Write/export to GEDCOM format (ftree is read-only)
- GUI application
- Web server mode
- LDS-specific records (SUBN, temple ordinances)

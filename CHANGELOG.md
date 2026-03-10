# Changelog

## 0.2.0 — Phase 2: Markdown Export

Export family tree to Obsidian-compatible Markdown files with YAML front-matter and wikilinks.

**Features:**

- `ftree export <file> --format md --output <dir>` command
- One `.md` file per individual with YAML front-matter (name, sex, birth/death dates and places, tags)
- Obsidian-style `[[wikilinks]]` to parents, spouses, and children
- Filename sanitization (strips `/`, `:`, `*`, `?`, etc.)
- Duplicate name handling with numeric suffixes: `John Smith.md`, `John Smith (2).md`
- Media links rendered as markdown links (URLs) or plain text (file paths)
- Renderer trait for future output format plugins

**Tests:** 49 unit tests, 13 integration tests.

## 0.1.0 — Phase 1: Core Parser + Check Command

Initial Rust implementation. Parses GEDCOM 5.5/5.5.1 files into an in-memory model and reports statistics.

**Features:**

- GEDCOM parser with line-level lexer and tree builder
- Encoding detection: UTF-8, ASCII, UTF-16 LE/BE (BOM and heuristic)
- `ftree check <file>` command: individual/family counts, missing data report, parser warnings
- Core model: `FamilyTree`, `Individual`, `Family`, `Name`, `Event`, `Date`, `Place`
- Date parsing with modifiers (ABT, BEF, AFT, BET...AND, FROM...TO, calendar escapes)
- CONT/CONC continuation line merging
- Lenient parsing: unknown tags produce warnings, not errors

**Supported GEDCOM tags:** HEAD, TRLR, INDI, FAM, SUBM, NAME (GIVN, SURN), SEX, BIRT, DEAT, FAMS, FAMC, HUSB, WIFE, CHIL, MARR, DATE, PLAC, OBJE, FILE

**Tests:** 40 unit tests, 6 integration tests against sample files (including UTF-16 LE encoded file).

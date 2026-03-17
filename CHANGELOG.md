# Changelog

## 0.8.4

- **SVG line alignment fix:** child subtree widths and the `children_total` used for centering are now computed from a single consistent measurement pass, preventing connector bars and drop lines from misaligning with boxes in trees with shared individuals.
- **SVG cards are now larger:** box dimensions increased from 164×52 to 200×68, with slightly larger name (13px) and date (11px) text.
- **SVG boxes link to HTML detail cards:** each person box is wrapped in `<a href="#{id}">` so that when the SVG is embedded in an HTML export (`--embed-svg`), clicking a box jumps to that person's detail card.
- **SVG hover highlight:** boxes darken slightly on hover when linked.
- **Fix:** spouse was not being added to the visited set after placement; corrected to prevent potential duplicate box rendering.

## 0.8.3

- SVG export now stacks disconnected family groups vertically instead of horizontally, producing a taller, narrower diagram that fits browser viewports more naturally.

## 0.8.2

- `ftree export --format html --embed-svg` embeds the SVG family tree diagram at the top of the HTML page.
- SVG output now uses `style="max-width: 100%; height: auto;"` instead of fixed pixel dimensions, so it scales correctly in browsers.

## 0.8.1

- `ftree --version` now prints the version string.

## 0.8.0 — Phase 8: SVG + HTML Output

Two new visual export formats.

**SVG (`--format svg`):**

- Recursive family tree layout: couples side-by-side, children below with bar-and-drop connectors
- Sex-coloured boxes: blue (male), pink (female), grey (unknown)
- Birth and death years shown inside each box
- `ftree export <file> --format svg` (defaults to `<file>.svg`)

**HTML (`--format html`):**

- Standalone single-file viewer with all CSS and JavaScript embedded
- Summary table: name, sex, birth, death, father, mother — with live search filter
- Individual detail cards: all vitals (burial, christening, occupation, residence, etc.), family relationships with hyperlinks, sources, notes
- Light and dark themes via `prefers-color-scheme`
- `ftree export <file> --format html` (defaults to `<file>.html`)

**Tests:** 147 unit tests (22 new), 30 integration tests.

## 0.7.0 — Phase 6: Extended GEDCOM Support

Broader tag coverage: notes, burial, christening, occupation, divorce, and more.

**Features:**

- Note records: level-0 NOTE records parsed (text with CONT/CONC merging); inline NOTE in individuals and families (both inline text and pointer-to-NOTE-record forms)
- Individual events: BURI (burial), CHR (christening), ADOP (adoption), RESI (residence) — all with optional DATE and PLAC
- Individual attributes: OCCU (occupation), EDUC (education), TITL (title) — string values
- Family events: DIV (divorce), ENGA (engagement), ANUL (annulment) — with optional DATE and PLAC
- Source citation quality: QUAY field parsed onto `SourceCitation`
- Markdown renderer: new vital events and attributes shown in body; divorce/engagement/annulment in Spouse section; Notes section per individual
- CSV renderer: `burial_date`, `burial_place`, `occupation` columns added

**Tests:** 123 unit tests (13 new), 30 integration tests.

## 0.6.0 — Phase 5: Lint + Validation

Data quality checking beyond basic statistics.

**Features:**

- New `src/lint/` module with a standalone lint pass on a parsed `FamilyTree`
- `LintWarning` with `LintCategory` (`dangling-ref`, `date`) for structured output
- Rules: dangling FAMS/FAMC/HUSB/WIFE/CHIL cross-references, dangling SOUR and OBJE pointers, dangling REPO reference, death before birth, marriage before birth of spouse
- `ftree check` now runs lint after parsing; lint issues appear separately from parse warnings
- "Warnings" section renamed to "Parse warnings" in check output

**Tests:** 109 unit tests (14 new lint tests), 30 integration tests.

## 0.5.1 — OBJE and MARR handling fixes

Quality of life fixes for real-world GEDCOM files.

**Fixes:**

- Top-level OBJE multimedia records now parsed (FILE path and TITL extracted); no longer produce parser warnings
- Pointer-form OBJE in individuals (`1 OBJE @O1@`) now resolved to the top-level OBJE record; titles shown in Markdown export when file path is unavailable
- MARR appearing as an individual attribute (`1 MARR` under INDI) now silently skipped; no longer produces warnings

**Tests:** 95 unit tests, 30 integration tests.

## 0.5.0 — Phase 4.5: Source and Repository Records

Parse and render GEDCOM source (SOUR) and repository (REPO) records.

**Features:**

- Level-0 SOUR records parsed with TITL, AUTH, PUBL, ABBR, TEXT, and REPO pointer
- Level-0 REPO records parsed with NAME
- Inline source citations (SOUR @xref@ with PAGE) parsed within INDI records
- `ftree check` now reports source and repository counts
- CSV export includes a `sources` column (semicolon-separated source titles)
- Markdown export includes a Sources section with titles and page references
- `ftree list <file> sources` extracts cited source titles (supports `--unique`)
- SOUR and REPO level-0 records no longer produce parser warnings

**Tests:** 89 unit tests, 30 integration tests.

## 0.4.0 — Phase 4: ASCII Tree View

Terminal-based family tree visualization with two layout modes.

**Features:**

- `ftree view <file>` command with `--layout horizontal|topdown` (defaults to horizontal)
- Horizontal layout: tree-style indentation with Unicode connectors (├──, └──, │)
- Top-down layout: Unicode box-drawing with couples side-by-side connected by ───
- Root ancestor detection: finds individuals with no FAMC records
- Disconnected family groups rendered separately with blank line separation
- Couples shown together (spouse on same line), children nested below
- Optional `--output` flag to write to file instead of stdout

**Tests:** 77 unit tests, 30 integration tests.

## 0.3.0 — Phase 3: CSV Export + List Command

Tabular data export and field extraction from GEDCOM files.

**Features:**

- `ftree export <file> --format csv` command (outputs to `<file>.csv` by default)
- CSV columns: xref, name, given, surname, sex, birth_date, birth_place, death_date, death_place, father, mother, spouses
- RFC 4180 compliant CSV escaping (quoted fields for commas, quotes, newlines)
- `ftree list <file> <field>` command for extracting field values
- Supported fields: names, surnames, places, dates
- `--unique` flag for deduplicated, sorted output
- Places and dates extracted from individual events (birth, death) and family events (marriage)

**Tests:** 68 unit tests, 24 integration tests.

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

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ftree is a Rust CLI tool and library for reading genealogy files (GEDCOM .ged, .inftree) into an in-memory graph, then rendering to Markdown (Obsidian), CSV, ASCII tree views, and eventually SVG/HTML.

## Build & Test

```bash
cargo build                          # build
cargo test                           # all tests
cargo test --lib                     # unit tests only
cargo test --test integration        # integration tests only
cargo run -- check samples/test_details.ged   # run against sample file
```

## Architecture

Pipeline: **parse → validate → render**. See `docs/ARCHITECTURE.md` for full details and ADRs.

- `src/model/` — Core types: `FamilyTree`, `Individual`, `Family`. Index-based graph using `HashMap<String, T>` keyed by GEDCOM xref IDs.
- `src/parse/` — Input parsers. Hand-written GEDCOM lexer + builder. `nom` for .inftree binary format.
- `src/lint/` — Validation rules. Lenient by default; collect warnings, never fail on valid-ish files.
- `src/render/` — Output renderers implementing `Renderer` trait. One file per person for Markdown.

## Key Design Decisions

- **Index-based graph, not pointer-based.** Individuals and families reference each other by xref string. No `Rc<RefCell<>>`.
- **Lenient parser.** Parse what you can, collect warnings. The `check` command surfaces them.
- **BOM detection + CHAR fallback** for encoding. Some files are UTF-16 LE despite declaring `UNICODE`.
- **Custom Date type, not chrono.** GEDCOM dates have modifiers (ABT, BEF, AFT, BET...AND), partial dates, and date phrases that don't map to standard date types.
- **thiserror for library errors, anyhow for CLI.** Keep structured errors in the library, convenience in `main.rs`.

## Key Documentation

- `docs/ARCHITECTURE.md` — Data flow, module structure, ADRs
- `docs/GEDCOM.md` — GEDCOM 5.5/5.5.1 format specification with ftree support status per tag
- `docs/LIBRARIES.md` — Dependency choices with rationale
- `docs/PLAN.md` — Phased implementation plan

## Sample Files

Test against all files in `samples/`. They cover different GEDCOM producers and edge cases:

- `test_details.ged` — minimal, clean GEDCOM 5.5 (3 individuals, 1 family)
- `555SAMPLE16LE.GED` — UTF-16 LE encoded; sources, adoption, residence
- `Harry Potter.ged` — medium-sized, EVEN tags for custom events
- `Simpsons Cartoon.ged` — descriptive xref IDs (`@Homer_Simpson@`), OBJE with URLs
- `Microsoft Windows DOS OS2.ged` — non-genealogical; stress-tests name parsing

## GEDCOM Parsing Notes

- Lines follow `level [xref] tag [value]` grammar; levels increase by exactly 1
- Cross-references use `@ID@` format; IDs can be numeric or descriptive strings
- Surnames in NAME values are delimited by slashes: `Given /Surname/`
- CONT adds a newline then appends; CONC appends without separator
- Unrecognized tags (including `_`-prefixed extensions) should be silently skipped with their substructures

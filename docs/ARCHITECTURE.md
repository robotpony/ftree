# Architecture

## Overview

ftree is a Rust CLI tool and library for reading genealogy files (GEDCOM, .inftree) into an in-memory graph, then rendering to multiple output formats. The architecture follows a three-stage pipeline: **parse → validate → render**.

```
                    ┌──────────┐
  .ged file ───────▶│  GEDCOM  │──┐
                    │  Parser  │  │    ┌───────────┐    ┌──────────────┐
                    └──────────┘  ├───▶│ FamilyTree│───▶│   Renderer   │───▶ output
                    ┌──────────┐  │    │  (model)  │    │ (md/csv/etc) │
  .inftree file ───▶│ InfTree  │──┘    └─────┬─────┘    └──────────────┘
                    │  Parser  │             │
                    └──────────┘        ┌────▼────┐
                                        │  Lint   │
                                        │ Checker │
                                        └─────────┘
```

## Design Decisions

### ADR-1: Rust as implementation language

**Context:** Previous attempt was Python. Project needs a single distributable binary, binary format parsing (.inftree), and long-term maintainability.

**Decision:** Rust, structured as a library crate (`ftree`) with a thin binary wrapper.

**Trade-offs accepted:** Steeper learning curve. Graph structures require index-based references instead of direct pointers. Compilation is slower than interpreted languages.

### ADR-2: Index-based graph model

**Context:** Family trees are cyclic graphs (parents reference children, children reference parents through families). Rust's ownership model makes pointer-based graphs awkward (`Rc<RefCell<>>`, arenas).

**Decision:** Store individuals and families in `HashMap<String, T>`, keyed by GEDCOM xref IDs (`@I1@`, `@F1@`). Cross-references use string keys, not pointers.

**Rationale:** This mirrors GEDCOM's own reference model. Lookups are O(1). No lifetime complexity. Serialization is trivial.

### ADR-3: Lenient parser with structured warnings

**Context:** Real-world .ged files deviate from the spec. Some use non-standard tags, wrong encodings, or missing required fields.

**Decision:** Parse what we can, collect warnings. Never fail on valid-ish files. The `check` command surfaces warnings. No strict mode initially.

**Rationale:** The primary use case is viewing exported data from commercial genealogy services. These files are "close enough" to valid. Failing on them defeats the purpose.

### ADR-4: BOM detection with CHAR fallback for encoding

**Context:** GEDCOM files declare encoding via the `CHAR` tag in the header, but some files use UTF-16 LE with a BOM despite declaring `UNICODE`. The 555SAMPLE file in our test suite demonstrates this.

**Decision:** Check for BOM first (UTF-8, UTF-16 LE, UTF-16 BE). If no BOM, read enough ASCII-compatible bytes to find the `CHAR` declaration and re-decode accordingly. ANSEL support is deferred.

### ADR-5: thiserror for library errors, anyhow for CLI

**Context:** ftree is both a library and a CLI binary. Library consumers need structured error types. The CLI binary needs convenient error propagation.

**Decision:** Define `ParseError`, `LintWarning`, `RenderError` with `thiserror` in the library. Use `anyhow` in `main.rs` for CLI error handling.

### ADR-6: One Markdown file per person

**Context:** The primary Markdown use case is Obsidian, which works best with interlinked individual files.

**Decision:** Markdown renderer writes one `.md` file per individual to a specified output directory. Files use YAML front-matter with tags, locations, and dates. Body contains wikilinks to related individuals.

### ADR-7: Dual ASCII tree layout

**Context:** Family trees vary in shape. Deep lineages suit top-down. Wide families suit left-to-right.

**Decision:** Support both top-down and left-to-right ASCII layouts, selectable via `--layout` flag (default: top-down).

## Module Structure

```
src/
├── main.rs                  # CLI entry (clap subcommands)
├── lib.rs                   # Public library API
├── model/
│   ├── mod.rs               # Re-exports
│   ├── individual.rs        # Individual, Name, Event structs
│   ├── family.rs            # Family struct
│   ├── tree.rs              # FamilyTree container + query methods
│   └── types.rs             # Shared types (Date, Place, Sex, etc.)
├── parse/
│   ├── mod.rs               # Parser trait + format detection
│   ├── gedcom/
│   │   ├── mod.rs           # GEDCOM parser entry point
│   │   ├── lexer.rs         # Line-level tokenizer
│   │   ├── builder.rs       # Builds FamilyTree from tokens
│   │   └── encoding.rs      # BOM detection + encoding conversion
│   └── inftree.rs           # .inftree binary parser (future)
├── lint/
│   ├── mod.rs               # Lint runner
│   └── rules.rs             # Individual lint rules
└── render/
    ├── mod.rs                # Renderer trait
    ├── markdown.rs           # Obsidian-compatible MD (one file per person)
    ├── csv.rs                # CSV export
    ├── ascii/
    │   ├── mod.rs            # ASCII renderer entry
    │   ├── topdown.rs        # Top-down tree layout
    │   └── horizontal.rs     # Left-to-right tree layout
    ├── svg.rs                # SVG renderer (future)
    └── html.rs               # HTML renderer (future)
```

## Core Types

### FamilyTree

The central data structure. All parsers produce one, all renderers consume one.

```rust
pub struct FamilyTree {
    pub header: Header,
    pub individuals: HashMap<String, Individual>,
    pub families: HashMap<String, Family>,
    pub warnings: Vec<LintWarning>,
}
```

### Individual

```rust
pub struct Individual {
    pub xref: String,           // "@I1@"
    pub name: Option<Name>,
    pub sex: Option<Sex>,
    pub birth: Option<Event>,
    pub death: Option<Event>,
    pub family_as_spouse: Vec<String>,  // xrefs to FAM records
    pub family_as_child: Vec<String>,   // xrefs to FAM records
    pub media: Vec<MediaRef>,
}
```

### Family

```rust
pub struct Family {
    pub xref: String,           // "@F1@"
    pub husband: Option<String>, // xref to INDI
    pub wife: Option<String>,    // xref to INDI
    pub children: Vec<String>,   // xrefs to INDI
    pub marriage: Option<Event>,
}
```

### Traits

```rust
pub trait Parser {
    fn parse(input: &[u8]) -> Result<FamilyTree, ParseError>;
}

pub trait Renderer {
    fn render(&self, tree: &FamilyTree, output: &Path) -> Result<(), RenderError>;
}
```

## Data Flow

### Parse

1. Read file as bytes
2. Detect encoding (BOM → CHAR fallback → assume UTF-8)
3. Decode to UTF-8 string
4. Lex into `(level, Option<xref>, tag, Option<value>)` tuples
5. Build `FamilyTree` from token stream, collecting warnings for unrecognized or malformed data

### Validate (Lint)

1. Check for missing names, dates, dangling xref references
2. Detect duplicate records
3. Report statistics (individual count, family count, completeness)

### Render

1. Accept `&FamilyTree` and output path
2. Format-specific rendering:
   - **Markdown:** iterate individuals, write one `.md` per person with YAML front-matter and wikilinks
   - **CSV:** flatten individuals to rows with columns for name, birth date/place, death date/place, etc.
   - **ASCII:** walk the tree from root ancestors, render with box-drawing characters
   - **SVG/HTML:** (future) generate styled visual output

## Dependencies

See `docs/LIBRARIES.md` for the full dependency list with rationale.

## Testing Strategy

- **Unit tests:** Per-module tests for parser (lexer, builder), model (tree queries), and each renderer
- **Integration tests:** Parse each sample .ged file in `samples/`, verify model population, and spot-check rendered output
- **Test data:** `samples/` contains public .ged files covering different producers, encodings, and edge cases

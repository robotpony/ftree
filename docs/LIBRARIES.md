# Libraries

Dependency choices for the ftree project, with rationale.

## Core Dependencies

| Crate | Purpose | Why this one |
|-------|---------|-------------|
| `clap` (derive) | CLI argument parsing | Standard for Rust CLIs. Derive macros make subcommand definitions clean. Handles `view`, `check`, `export`, `list` naturally. |
| `thiserror` | Library error types | Derive `Error` implementations for `ParseError`, `LintWarning`, `RenderError`. No boilerplate. |
| `anyhow` | CLI error handling | Used only in `main.rs`. Wraps library errors for clean CLI output with context. |
| `encoding_rs` | Character encoding | Handles UTF-16 LE/BE decoding and ANSEL (future). Needed for the 555SAMPLE16LE.GED and similar files. |

## Output Dependencies

| Crate | Purpose | Why this one |
|-------|---------|-------------|
| `serde` + `serde_yaml` | YAML front-matter | Serialize Individual metadata to YAML for Markdown front-matter. serde is the standard. |
| `csv` | CSV export | The standard Rust CSV writer. Handles quoting and escaping. |

## Future / Optional

| Crate | Purpose | When |
|-------|---------|------|
| `svg` | SVG generation | When SVG renderer is implemented. Clean builder API for SVG elements. |
| `nom` | Binary parsing | For the .inftree binary format parser. Combinator-based parsing is well-suited to binary formats. |
| `tera` or `askama` | HTML templating | When HTML renderer is implemented. `askama` for compile-time templates, `tera` for runtime flexibility. |

## Rejected Alternatives

| Crate | Reason for rejection |
|-------|---------------------|
| `structopt` | Merged into clap 3+. Use clap directly. |
| `pest` / `nom` for GEDCOM | GEDCOM's line-based format is simple enough for a hand-written lexer. A parser combinator adds complexity without benefit here. `nom` is reserved for the binary .inftree format where it adds real value. |
| `petgraph` | The family tree graph is simple (two node types, three edge types). A general-purpose graph library adds abstraction without solving real problems. Index-based HashMaps are sufficient. |
| `chrono` | GEDCOM dates don't map cleanly to standard date types (partial dates, ranges, modifiers like ABT/BEF/AFT). A custom Date enum is more appropriate. |

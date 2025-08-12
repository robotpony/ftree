# Family tree viewer

Plot and lint GEDCOM files for genealogy. Generates PNG, Markdown, and SVG family trees from standard inputs. Lint-tests family tree files showing missing data, errors, etc.

## Usage

```
$ ftree view <filemame>

Name LastName (1980-)
├── Name LastName (1950-1999)
├────┴── Name LastName (1900-1980)
├── Name LastName (1950-1999)
...
```

### Actions

- `view` View a family tree in a brief ASCII format for the terminal
- `check` Check a file for validity
- `export [--format=svg|html]` 

## Formats

- GEDCOM files are an open text format for genealogy
- .inftree files are Family Historian binary format
- output to SVG, Markdown, and PNGs (optionally)
- output in outline view or left-to-right tree view
- simple command line tool
- use standard formats and tools
- output quality should high, and customizable with CSS themes

## Architecture

- GEDCOM reader library
- .inftree reader library
- LINT checker for in-memory representation
- ASCII output renderer
- SVG output renderer
- HTML output renderer

## Phases

1. (P0) Command-line GEDCOM viewing, in outline mode (plain text markdown)
1. (P1) Add details and improve data presentation
2. (P2) GEDCOM to SVG and PNG trees (simple)
3. (P3) Basic themes for SVG and PNG rendering
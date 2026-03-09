# Family tree viewer

Read and convert GEDCOM (genealogy) files to Markdown. Generates interlinked markdown files for use in Obsidian, as well as CSV.

`ftree` reads a .GED file into an internal object graph, and is able to write out files based on that internal representation. 

## Motivation

I created `ftree` to dump  .GED files, after I used a web service to build a family tree, so I could continue to view my files after the paid service expired.

## Installation

To run the tool, use the executable in the `bin/` directory:

```bash
./bin/ftree <command> [options]
```

Or add the bin directory to your PATH for system-wide access:

```bash
export PATH="$PATH:/path/to/ftree/bin"
ftree <command> [options]
```

## Usage

The ftree tool provides several commands for working with GEDCOM genealogy files:

```bash
# View family tree in ASCII format
ftree view <filename> [options]

# Check file validity and statistics  
ftree check <filename>

# Export markdown or CSV
ftree export <filename> [options]
```

### Commands

#### `ftree view <filename>`

View a family tree in Markdown format for the terminal. The markdown is formatted for Obsidian or Hugo, with front-matter containing tags, locations, and other metadata, and the body containing lists of links to resources, full descriptions, and links to parents/children.

**Example:**
```bash
ftree view myfile.ged
```

#### `ftree check <filename>`

Check a GEDCOM file for validity and missing data.

Displays file statistics including:
- Number of individuals and families
- Missing names, birth dates, and death dates
- Validation warnings and errors

**Example:**
```bash
ftree check myfile.ged
```

#### `ftree export <filename>`

Export family tree to various formats.

**Options:**
- `--format {md,csv}` - Output format (default: md)
- `--output`, `-o` - Specify output file path (default: input filename with new extension)

**Examples:**
```bash
# Export with default settings
ftree export myfile.ged

# Export twith custom output path
ftree export myfile.ged --output ~/tmp
```

#### `ftree list <filename> [field_alias]`

Extract and analyze field values from GEDCOM files. Useful for data analysis and quality checking.

**Field Aliases:**
- `cities` or `places` - All birth/death places
- `names` - All individual names
- `surnames` - All surnames
- `dates` - All dates (birth, death, marriage)
- `birth_dates` - Birth dates only
- `death_dates` - Death dates only  
- `birth_places` - Birth places only
- `death_places` - Death places only
- `marriage_dates` - Marriage dates only
- `marriage_places` - Marriage places only

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

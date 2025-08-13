# Family tree viewer

Plot and lint GEDCOM files for genealogy. Generates PNG, Markdown, and SVG family trees from standard inputs. Lint-tests family tree files showing missing data, errors, etc.

## Motivation

I created `ftree` to dump  .GED files, after I used a service to build a family tree, so I could continue to view my files after the service expired.

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

# Export to HTML/SVG formats
ftree export <filename> [options]

# Extract and analyze field data
ftree list <filename> [field_alias] [options]
```

**Example output:**
```
$ ftree view myfile.ged

Name LastName (1980-)
├── Name LastName (1950-1999)
├────┴── Name LastName (1900-1980)
├── Name LastName (1950-1999)
...
```

### Commands

#### `ftree view <filename>`

View a family tree in ASCII format for the terminal.

**Options:**
- `--places` - Include birth/death places in the output
- `--marriage` - Include marriage dates in the output  
- `--grouped` - Group families together with sorted children

**Example:**
```bash
ftree view myfile.ged --places --marriage
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
- `--format {svg,html}` - Output format (default: html)
- `--output`, `-o` - Specify output file path (default: input filename with new extension)
- `--theme` - CSS theme for HTML output (default: default)
- `--no-places` - Exclude birth/death places from HTML output
- `--no-photos` - Exclude photos from HTML output

**Examples:**
```bash
# Export to HTML with default settings
ftree export myfile.ged

# Export to HTML with custom output path
ftree export myfile.ged --output my_tree.html

# Export without places and photos
ftree export myfile.ged --no-places --no-photos

# Export to SVG (not yet implemented)
ftree export myfile.ged --format=svg
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

**Options:**
- `--field`, `-f` - Specify exact field name instead of alias
- `--count`, `-c` - Show count for each value
- `--group`, `-g` - Group individuals by field value
- `--all`, `-a` - Show all occurrences (not just unique values)
- `--stats`, `-s` - Show summary statistics

**Examples:**
```bash
# List all unique places
ftree list myfile.ged places

# Count occurrences of each surname
ftree list myfile.ged surnames --count

# Group people by birth place
ftree list myfile.ged birth_places --group

# Show all dates with statistics
ftree list myfile.ged dates --all --stats

# List using exact field name
ftree list myfile.ged --field birth_date
```

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

## GEDCOM Support

### Supported Keywords

The parser currently handles the following GEDCOM tags:

**Level 0 Records:**
- `HEAD` - Header record (file metadata)
- `INDI` - Individual person record
- `FAM` - Family record
- `SUBM` - Submitter record
- `TRLR` - Trailer record (end of file)

**Individual Records (Level 1):**
- `NAME` - Full name (parsed into given/surname)
- `SEX` - Gender
- `BIRT` - Birth event
- `DEAT` - Death event
- `FAMS` - Family as spouse reference
- `FAMC` - Family as child reference
- `OBJE` - Multimedia object

**Family Records (Level 1):**
- `HUSB` - Husband reference
- `WIFE` - Wife reference
- `CHIL` - Child reference
- `MARR` - Marriage event

**Event Details (Level 2):**
- `DATE` - Date of event
- `PLAC` - Place of event
- `FILE` - Multimedia file path
- `GIVN` - Given name
- `SURN` - Surname

### Unsupported Keywords

The following standard GEDCOM tags are not yet implemented:

**Core Records:**
- `SOUR` - Source citations
- `NOTE` - General notes
- `REPO` - Repository records

**Individual Events:**
- `BAPM`/`CHR` - Baptism/Christening
- `BURI` - Burial
- `CREM` - Cremation
- `ADOP` - Adoption
- `OCCU` - Occupation
- `RESI` - Residence
- `EDUC` - Education

**Family Events:**
- `ENGA` - Engagement
- `DIV` - Divorce
- `ANUL` - Annulment

**Attributes:**
- `RELI` - Religion
- `NATI` - Nationality
- `CAST` - Caste
- `TITL` - Title

**Source/Citation Tags:**
- `PAGE` - Source page reference
- `QUAY` - Quality of evidence
- `DATA` - Source data
- `AUTH` - Author
- `PUBL` - Publication

## Phases

1. (P0) Command-line GEDCOM viewing, in outline mode (plain text markdown)
1. (P1) Add details and improve data presentation
2. (P2) GEDCOM to SVG and PNG trees (simple)
3. (P3) Basic themes for SVG and PNG rendering
# Family tree viewer

Plot and lint GEDCOM files for genealogy. Generates PNG, Markdown, and SVG family trees from standard inputs. Lint-tests family tree files showing missing data, errors, etc.

## Motiation

I created this utility to dump the .GED files I exported after using a family tree builder, so I could view the files I created.

## Usage

```
$ ftree view <filemame>

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

Export family tree to various formats (not yet implemented).

**Options:**
- `--format {svg,html}` - Output format (default: svg)

**Example:**
```bash
ftree export myfile.ged --format=svg
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
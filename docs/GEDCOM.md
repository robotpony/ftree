# GEDCOM 5.5 Format Specification

**Status:** Reference specification for ftree
**Version:** 1.0
**Date:** 2026-03-08

## Abstract

This document specifies the GEDCOM 5.5 and 5.5.1 data format as it applies to the ftree project. GEDCOM (GEnealogical Data COMmunication) is a text-based format for exchanging genealogical data between software systems. This specification serves as both a reference for implementors and a tracking document for ftree's parser coverage.

Each section notes ftree's current implementation status using RFC 2119 requirement levels and support markers:

- **Supported** — ftree parses and uses this structure
- **Planned** — ftree will support this in a future release
- **Ignored** — ftree silently skips this structure
- **Not applicable** — structure is irrelevant to ftree's purpose

## Motivation

GEDCOM is the de facto standard for genealogical data interchange. Most genealogy applications export GEDCOM 5.5 or 5.5.1. The ftree tool MUST parse these files reliably, even when they contain structures ftree does not fully interpret. This document defines what ftree MUST handle, what it SHOULD handle, and what it MAY safely ignore.

The official specification is maintained by FamilySearch. This document references GEDCOM 5.5 (1996) and GEDCOM 5.5.1 (1999), with notes on 7.0 for future planning.

## 1. Line Format

Every GEDCOM file is a sequence of lines (records). Each line follows this grammar:

```
gedcom_line := level + delim + [xref_id + delim] + tag + [delim + line_value] + terminator
```

### Components

| Component | Required | Description |
|-----------|----------|-------------|
| `level` | Yes | Integer 0–99. No leading zeroes. |
| `delim` | Yes | Single space (U+0020). |
| `xref_id` | No | Cross-reference identifier in `@ID@` format. Only on level 0 records. |
| `tag` | Yes | 3–4 character alphanumeric tag. |
| `line_value` | No | Data value or pointer (`@XREF@`). |
| `terminator` | Yes | CR, LF, or CR+LF. |

### Level Rules

- Level 0 marks top-level records (HEAD, INDI, FAM, TRLR, etc.)
- A subordinate line MUST have level = parent level + 1
- A line at level L belongs to the nearest preceding line at level L-1
- Level increases MUST NOT skip values (jumping from level 1 to level 3 is invalid)

### Maximum Line Length

255 characters total, including level, delimiters, tag, value, and terminator. Values exceeding this limit MUST be split using CONC or CONT.

### Cross-Reference Identifiers

Cross-references link records to each other. Format: `@ID@`

- First character after opening `@` MUST be alphanumeric or underscore
- Remaining characters: alphanumeric, underscore, `#`, `-`
- Maximum 22 characters between the `@` delimiters (5.5.1)
- MUST be unique within a file
- Conventional prefixes: `I` (Individual), `F` (Family), `S` (Source), `R` (Repository), `N` (Note), `O` or `M` (Object/Media)

Some producers use descriptive IDs (e.g., `@Homer_Simpson@` in the GRAMPS sample files) rather than numeric ones. Parsers MUST accept any valid identifier format.

### Continuation Lines

**CONT** — appends value after inserting a newline:

```
1 NOTE First line of text
2 CONT Second line of text
```

Result: `First line of text\nSecond line of text`

**CONC** — appends value with no separator (for splitting long values):

```
1 NOTE This is a very long note that must be spl
2 CONC it across multiple lines
```

Result: `This is a very long note that must be split across multiple lines`

Parsers SHOULD handle trailing whitespace carefully with CONC, as some producers strip trailing spaces before the split point.

**ftree status:** Supported (CONT, CONC)

### Cardinality Notation

This document uses the following notation for occurrence constraints:

| Notation | Meaning |
|----------|---------|
| `{1:1}` | Required, exactly once |
| `{0:1}` | Optional, at most once |
| `{0:M}` | Optional, multiple allowed |
| `{1:M}` | Required, multiple allowed |

## 2. File Structure

A GEDCOM file MUST begin with a HEAD record and end with a TRLR record. All other records appear between them.

```
0 HEAD
  ...header substructures...
0 @XREF@ INDI
  ...
0 @XREF@ FAM
  ...
0 @XREF@ SOUR
  ...
0 TRLR
```

### Level 0 Record Types

| Tag | Name | Cardinality | Has XREF | Description |
|-----|------|-------------|----------|-------------|
| `HEAD` | Header | `{1:1}` | No | File metadata. MUST be first record. |
| `TRLR` | Trailer | `{1:1}` | No | End-of-file marker. MUST be last. No substructures. |
| `INDI` | Individual | `{0:M}` | Yes | Person record. |
| `FAM` | Family | `{0:M}` | Yes | Family group linking spouses and children. |
| `SOUR` | Source | `{0:M}` | Yes | Bibliographic source record. |
| `NOTE` | Note | `{0:M}` | Yes | Shared note record. |
| `REPO` | Repository | `{0:M}` | Yes | Archive or library holding sources. |
| `SUBM` | Submitter | `{0:M}` | Yes | Person or organization that contributed data. |
| `SUBN` | Submission | `{0:1}` | Yes | Submission control (LDS-specific). |
| `OBJE` | Object | `{0:M}` | Yes | Multimedia object record. |

**ftree status:**

| Tag | Status |
|-----|--------|
| HEAD | Supported |
| TRLR | Supported |
| INDI | Supported |
| FAM | Supported |
| SUBM | Supported |
| SOUR | Planned |
| NOTE | Planned |
| REPO | Planned |
| OBJE | Supported (partial) |
| SUBN | Not applicable |

## 3. Header Record (HEAD)

```
0 HEAD                                           {1:1}
  1 SOUR <APPROVED_SYSTEM_ID>                    {1:1}
    2 VERS <VERSION_NUMBER>                      {0:1}
    2 NAME <NAME_OF_PRODUCT>                     {0:1}
    2 CORP <NAME_OF_BUSINESS>                    {0:1}
      3 <<ADDRESS_STRUCTURE>>                    {0:1}
    2 DATA <NAME_OF_SOURCE_DATA>                 {0:1}
      3 DATE <PUBLICATION_DATE>                  {0:1}
      3 COPR <COPYRIGHT_SOURCE_DATA>             {0:1}
  1 DEST <RECEIVING_SYSTEM_NAME>                 {0:1}
  1 DATE <TRANSMISSION_DATE>                     {0:1}
    2 TIME <TIME_VALUE>                          {0:1}
  1 SUBM @XREF:SUBM@                            {1:1}
  1 SUBN @XREF:SUBN@                            {0:1}
  1 FILE <FILE_NAME>                             {0:1}
  1 COPR <COPYRIGHT_GEDCOM_FILE>                 {0:1}
  1 GEDC                                         {1:1}
    2 VERS <VERSION_NUMBER>                      {1:1}
    2 FORM <GEDCOM_FORM>                         {1:1}
  1 CHAR <CHARACTER_SET>                         {1:1}
    2 VERS <VERSION_NUMBER>                      {0:1}
  1 LANG <LANGUAGE_OF_TEXT>                      {0:1}
  1 PLAC                                         {0:1}
    2 FORM <PLACE_HIERARCHY>                     {1:1}
  1 NOTE <CONTENT_DESCRIPTION>                   {0:1}
    2 [CONT|CONC] <TEXT>                         {0:M}
```

- `GEDC.VERS` — version string, typically `5.5` or `5.5.1`
- `GEDC.FORM` — always `LINEAGE-LINKED` for genealogical data
- `CHAR` — character encoding for the file (see Section 10)
- `PLAC.FORM` — defines the default place hierarchy (e.g., `City, County, State, Country`)
- `SUBM` — pointer to the submitter record; required in 5.5 and 5.5.1

**ftree status:** Supported. ftree reads GEDC, CHAR, and SOUR for validation. Other header fields are parsed but not displayed.

## 4. Individual Record (INDI)

```
0 @XREF:INDI@ INDI
  1 RESN <RESTRICTION_NOTICE>                    {0:1}
  1 <<PERSONAL_NAME_STRUCTURE>>                  {0:M}
  1 SEX <SEX_VALUE>                              {0:1}
  1 <<INDIVIDUAL_EVENT_STRUCTURE>>               {0:M}
  1 <<INDIVIDUAL_ATTRIBUTE_STRUCTURE>>           {0:M}
  1 <<CHILD_TO_FAMILY_LINK>>                     {0:M}
  1 <<SPOUSE_TO_FAMILY_LINK>>                    {0:M}
  1 SUBM @XREF:SUBM@                            {0:M}
  1 <<ASSOCIATION_STRUCTURE>>                    {0:M}
  1 ALIA @XREF:INDI@                             {0:M}
  1 ANCI @XREF:SUBM@                             {0:M}
  1 DESI @XREF:SUBM@                             {0:M}
  1 <<SOURCE_CITATION>>                          {0:M}
  1 <<MULTIMEDIA_LINK>>                          {0:M}
  1 <<NOTE_STRUCTURE>>                           {0:M}
  1 RFN <PERMANENT_RECORD_FILE_NUMBER>           {0:1}
  1 AFN <ANCESTRAL_FILE_NUMBER>                  {0:1}
  1 REFN <USER_REFERENCE_NUMBER>                 {0:M}
    2 TYPE <USER_REFERENCE_TYPE>                 {0:1}
  1 RIN <AUTOMATED_RECORD_ID>                    {0:1}
  1 <<CHANGE_DATE>>                              {0:1}
```

### 4.1 Personal Name Structure

The NAME value uses slashes to delimit the surname: `Given Names /Surname/`

```
  1 NAME <NAME_PERSONAL>                         {0:M}
    2 TYPE <NAME_TYPE>                           {0:1}
    2 NPFX <NAME_PREFIX>                         {0:1}
    2 GIVN <GIVEN_NAME>                          {0:1}
    2 NICK <NICKNAME>                            {0:1}
    2 SPFX <SURNAME_PREFIX>                      {0:1}
    2 SURN <SURNAME>                             {0:1}
    2 NSFX <NAME_SUFFIX>                         {0:1}
    2 <<SOURCE_CITATION>>                        {0:M}
    2 <<NOTE_STRUCTURE>>                         {0:M}
    2 FONE <PHONETIC_VARIATION>                  {0:M}
      3 TYPE <PHONETIC_TYPE>                     {1:1}
    2 ROMN <ROMANIZED_VARIATION>                 {0:M}
      3 TYPE <ROMANIZED_TYPE>                    {1:1}
```

Name pieces:

| Tag | Description | Example |
|-----|-------------|---------|
| `NPFX` | Prefix (title) | Dr., Rev. |
| `GIVN` | Given/first name | Robert Eugene |
| `NICK` | Nickname | Bob |
| `SPFX` | Surname prefix | de, von, van |
| `SURN` | Surname | Williams |
| `NSFX` | Suffix | Jr., Sr., III |

`TYPE` values (5.5.1): `aka`, `birth`, `immigrant`, `maiden`, `married`, etc.

`FONE` and `ROMN` are 5.5.1 additions for phonetic and romanized name variations.

**ftree status:** Supported (NAME, GIVN, SURN). Other name pieces are planned.

### 4.2 Individual Events

All individual events accept the `[Y|<NULL>]` value. When `Y` is present without a DATE or PLAC, it asserts the event occurred but details are unknown. Each event accepts the Event Detail substructure (Section 7).

| Tag | Name | Description | ftree |
|-----|------|-------------|-------|
| `BIRT` | Birth | Entering into life. Accepts FAMC substructure. | Supported |
| `CHR` | Christening | Baptism/naming of a child. Accepts FAMC. | Planned |
| `DEAT` | Death | End of mortal life. | Supported |
| `BURI` | Burial | Disposal of mortal remains. | Planned |
| `CREM` | Cremation | Disposal of remains by fire. | Planned |
| `ADOP` | Adoption | Legal parent-child relationship. Accepts FAMC with ADOP detail. | Planned |
| `BAPM` | Baptism | Religious baptism (not LDS). | Planned |
| `BARM` | Bar Mitzvah | Jewish coming of age (male). | Ignored |
| `BASM` | Bas Mitzvah | Jewish coming of age (female). | Ignored |
| `BLES` | Blessing | Bestowing divine care. | Ignored |
| `CHRA` | Adult Christening | Baptism/naming of an adult. | Ignored |
| `CONF` | Confirmation | Religious confirmation. | Ignored |
| `FCOM` | First Communion | First sharing in the Lord's supper. | Ignored |
| `ORDN` | Ordination | Receiving religious authority. | Ignored |
| `NATU` | Naturalization | Obtaining citizenship. | Ignored |
| `EMIG` | Emigration | Leaving homeland. | Ignored |
| `IMMI` | Immigration | Entering a new locality. | Ignored |
| `CENS` | Census | Periodic population count. | Ignored |
| `PROB` | Probate | Judicial determination of will validity. | Ignored |
| `WILL` | Will | Document for estate distribution. | Ignored |
| `GRAD` | Graduation | Awarding diplomas/degrees. | Ignored |
| `RETI` | Retirement | Exiting occupational life. | Ignored |
| `EVEN` | Event | Generic event (requires TYPE substructure). | Ignored |

### 4.3 Individual Attributes

Attributes describe characteristics rather than events. Each accepts the Event Detail substructure.

| Tag | Name | Value | ftree |
|-----|------|-------|-------|
| `CAST` | Caste | `<CASTE_NAME>` | Planned |
| `DSCR` | Description | `<PHYSICAL_DESCRIPTION>` | Ignored |
| `EDUC` | Education | `<SCHOLASTIC_ACHIEVEMENT>` | Planned |
| `IDNO` | ID Number | `<ID_NUMBER>` (requires TYPE) | Ignored |
| `NATI` | Nationality | `<NATIONAL_ORIGIN>` | Planned |
| `NCHI` | Children Count | `<COUNT>` | Ignored |
| `NMR` | Marriage Count | `<COUNT>` | Ignored |
| `OCCU` | Occupation | `<OCCUPATION>` | Planned |
| `PROP` | Property | `<POSSESSIONS>` | Ignored |
| `RELI` | Religion | `<RELIGIOUS_AFFILIATION>` | Planned |
| `RESI` | Residence | (no value; uses event detail) | Planned |
| `SSN` | Social Security | `<SSN>` | Ignored |
| `TITL` | Title | `<TITLE>` | Planned |
| `FACT` | Fact | `<TEXT>` (5.5.1; requires TYPE) | Ignored |

### 4.4 Family Links

```
  1 FAMC @XREF:FAM@                             {0:M}
    2 PEDI <PEDIGREE_LINKAGE_TYPE>               {0:1}
    2 STAT <CHILD_LINKAGE_STATUS>                {0:1}
    2 <<NOTE_STRUCTURE>>                         {0:M}
  1 FAMS @XREF:FAM@                             {0:M}
    2 <<NOTE_STRUCTURE>>                         {0:M}
```

PEDI values: `adopted`, `birth`, `foster`, `sealing`

STAT values (5.5.1): `challenged`, `disproven`, `proven`

**ftree status:** Supported (FAMC, FAMS pointers). PEDI and STAT are planned.

## 5. Family Record (FAM)

```
0 @XREF:FAM@ FAM
  1 RESN <RESTRICTION_NOTICE>                    {0:1}
  1 <<FAMILY_EVENT_STRUCTURE>>                   {0:M}
  1 HUSB @XREF:INDI@                             {0:1}
  1 WIFE @XREF:INDI@                             {0:1}
  1 CHIL @XREF:INDI@                             {0:M}
  1 NCHI <COUNT_OF_CHILDREN>                     {0:1}
  1 SUBM @XREF:SUBM@                            {0:M}
  1 <<SOURCE_CITATION>>                          {0:M}
  1 <<MULTIMEDIA_LINK>>                          {0:M}
  1 <<NOTE_STRUCTURE>>                           {0:M}
  1 REFN <USER_REFERENCE_NUMBER>                 {0:M}
    2 TYPE <USER_REFERENCE_TYPE>                 {0:1}
  1 RIN <AUTOMATED_RECORD_ID>                    {0:1}
  1 <<CHANGE_DATE>>                              {0:1}
```

Maximum one HUSB and one WIFE per FAM record.

### 5.1 Family Events

All family events accept `[Y|<NULL>]` and support HUSB/WIFE AGE substructures:

```
  1 MARR [Y|<NULL>]
    2 HUSB
      3 AGE <AGE_AT_EVENT>
    2 WIFE
      3 AGE <AGE_AT_EVENT>
    2 <<EVENT_DETAIL>>
```

| Tag | Name | Description | ftree |
|-----|------|-------------|-------|
| `ANUL` | Annulment | Declaring marriage void. | Planned |
| `CENS` | Census | Census record for the family. | Ignored |
| `DIV` | Divorce | Dissolving marriage. | Planned |
| `DIVF` | Divorce Filed | Filing for divorce. | Ignored |
| `ENGA` | Engagement | Agreement to marry. | Planned |
| `MARB` | Marriage Bann | Public notice of intent to marry. | Ignored |
| `MARC` | Marriage Contract | Formal marriage agreement. | Ignored |
| `MARL` | Marriage License | Obtaining legal license. | Ignored |
| `MARR` | Marriage | Creating a family unit. | Supported |
| `MARS` | Marriage Settlement | Pre-marriage property agreement. | Ignored |
| `RESI` | Residence | Family residence (5.5.1). | Ignored |
| `EVEN` | Event | Generic family event (requires TYPE). | Ignored |

**ftree status:** Supported (HUSB, WIFE, CHIL, MARR). Other family events are planned or ignored as noted.

## 6. Source Record (SOUR)

### 6.1 Source Record (Level 0)

```
0 @XREF:SOUR@ SOUR
  1 DATA                                         {0:1}
    2 EVEN <EVENTS_RECORDED>                     {0:M}
      3 DATE <DATE_PERIOD>                       {0:1}
      3 PLAC <SOURCE_JURISDICTION_PLACE>         {0:1}
    2 AGNC <RESPONSIBLE_AGENCY>                  {0:1}
    2 <<NOTE_STRUCTURE>>                         {0:M}
  1 AUTH <SOURCE_ORIGINATOR>                     {0:1}
    2 [CONT|CONC] <TEXT>                         {0:M}
  1 TITL <SOURCE_DESCRIPTIVE_TITLE>              {0:1}
    2 [CONT|CONC] <TEXT>                         {0:M}
  1 ABBR <SOURCE_FILED_BY_ENTRY>                 {0:1}
  1 PUBL <SOURCE_PUBLICATION_FACTS>              {0:1}
    2 [CONT|CONC] <TEXT>                         {0:M}
  1 TEXT <TEXT_FROM_SOURCE>                       {0:1}
    2 [CONT|CONC] <TEXT>                         {0:M}
  1 <<SOURCE_REPOSITORY_CITATION>>               {0:M}
  1 REFN <USER_REFERENCE_NUMBER>                 {0:M}
    2 TYPE <USER_REFERENCE_TYPE>                 {0:1}
  1 RIN <AUTOMATED_RECORD_ID>                    {0:1}
  1 <<CHANGE_DATE>>                              {0:1}
  1 <<NOTE_STRUCTURE>>                           {0:M}
  1 <<MULTIMEDIA_LINK>>                          {0:M}
```

### 6.2 Source Citation (Pointer Form)

Used inline under events, attributes, and other structures to reference a level 0 source record:

```
  n SOUR @XREF:SOUR@
    +1 PAGE <WHERE_WITHIN_SOURCE>                {0:1}
    +1 EVEN <EVENT_TYPE_CITED_FROM>              {0:1}
      +2 ROLE <ROLE_IN_EVENT>                    {0:1}
    +1 DATA                                      {0:1}
      +2 DATE <ENTRY_RECORDING_DATE>             {0:1}
      +2 TEXT <TEXT_FROM_SOURCE>                  {0:M}
        +3 [CONT|CONC] <TEXT>                    {0:M}
    +1 QUAY <CERTAINTY_ASSESSMENT>               {0:1}
    +1 <<MULTIMEDIA_LINK>>                       {0:M}
    +1 <<NOTE_STRUCTURE>>                        {0:M}
```

### 6.3 Source Citation (Non-Pointer Form)

Inline source description without a separate record:

```
  n SOUR <SOURCE_DESCRIPTION>
    +1 [CONT|CONC] <TEXT>                        {0:M}
    +1 TEXT <TEXT_FROM_SOURCE>                    {0:M}
      +2 [CONT|CONC] <TEXT>                      {0:M}
    +1 QUAY <CERTAINTY_ASSESSMENT>               {0:1}
    +1 <<MULTIMEDIA_LINK>>                       {0:M}
    +1 <<NOTE_STRUCTURE>>                        {0:M}
```

### 6.4 Certainty Assessment (QUAY)

| Value | Meaning |
|-------|---------|
| `0` | Unreliable evidence or estimated data |
| `1` | Questionable reliability (interviews, census, oral genealogies) |
| `2` | Secondary evidence, officially recorded after the event |
| `3` | Direct and primary evidence, or by dominance of evidence |

### 6.5 Source Repository Citation

```
  n REPO @XREF:REPO@
    +1 CALN <SOURCE_CALL_NUMBER>                 {0:M}
      +2 MEDI <SOURCE_MEDIA_TYPE>                {0:1}
    +1 <<NOTE_STRUCTURE>>                        {0:M}
```

**ftree status:** Planned. Source citations appear in real-world files (the 555SAMPLE file references `@S1@` with PAGE details) and SHOULD be supported for completeness.

## 7. Event Detail Substructure

This substructure appears under every event and attribute tag. It provides the date, place, and supporting evidence for an event.

```
  n <EVENT_TAG> [Y|value]
    +1 TYPE <EVENT_CLASSIFICATION>               {0:1}
    +1 DATE <DATE_VALUE>                         {0:1}
    +1 <<PLACE_STRUCTURE>>                       {0:1}
    +1 <<ADDRESS_STRUCTURE>>                     {0:1}
    +1 AGNC <RESPONSIBLE_AGENCY>                 {0:1}
    +1 RELI <RELIGIOUS_AFFILIATION>              {0:1}
    +1 CAUS <CAUSE_OF_EVENT>                     {0:1}
    +1 RESN <RESTRICTION_NOTICE>                 {0:1}
    +1 <<NOTE_STRUCTURE>>                        {0:M}
    +1 <<SOURCE_CITATION>>                       {0:M}
    +1 <<MULTIMEDIA_LINK>>                       {0:M}
```

Individual events add:

```
    +1 AGE <AGE_AT_EVENT>                        {0:1}
```

Family events add spouse ages:

```
    +1 HUSB
      +2 AGE <AGE_AT_EVENT>
    +1 WIFE
      +2 AGE <AGE_AT_EVENT>
```

**ftree status:** Supported (DATE, PLAC). Other event detail fields (CAUS, AGNC, AGE) are planned.

## 8. Date Formats

### 8.1 Date Grammar

```
DATE_VALUE :=
    <DATE>
  | <DATE_PERIOD>
  | <DATE_RANGE>
  | <DATE_APPROXIMATED>
  | INT <DATE> (<DATE_PHRASE>)
  | (<DATE_PHRASE>)
```

### 8.2 Exact and Partial Dates

Format: `DD MMM YYYY`

Partial dates are valid: `MMM YYYY` (month and year), `YYYY` (year only).

Day is a 1- or 2-digit number (no leading zero required). Year is typically 3–4 digits.

### 8.3 Month Abbreviations (Gregorian)

| Abbr | Month | Abbr | Month |
|------|-------|------|-------|
| `JAN` | January | `JUL` | July |
| `FEB` | February | `AUG` | August |
| `MAR` | March | `SEP` | September |
| `APR` | April | `OCT` | October |
| `MAY` | May | `NOV` | November |
| `JUN` | June | `DEC` | December |

### 8.4 Date Modifiers

| Modifier | Syntax | Meaning |
|----------|--------|---------|
| `ABT` | `ABT <DATE>` | About/approximately |
| `CAL` | `CAL <DATE>` | Calculated from other data |
| `EST` | `EST <DATE>` | Estimated |
| `BEF` | `BEF <DATE>` | Before this date |
| `AFT` | `AFT <DATE>` | After this date |
| `BET...AND` | `BET <DATE> AND <DATE>` | Between two dates (range) |
| `FROM` | `FROM <DATE>` | Period starting on this date |
| `TO` | `TO <DATE>` | Period ending on this date |
| `FROM...TO` | `FROM <DATE> TO <DATE>` | Period spanning two dates |
| `INT` | `INT <DATE> (<PHRASE>)` | Interpreted from freeform text |

### 8.5 Date Phrase

Freeform text enclosed in parentheses, used when no standard date form applies:

```
2 DATE (2 days after Easter 1790)
```

Parsers MUST preserve date phrases verbatim and SHOULD NOT attempt to parse their contents.

### 8.6 Calendar Escape Sequences

Non-Gregorian dates use escape prefixes before the date value:

| Escape | Calendar |
|--------|----------|
| `@#DGREGORIAN@` | Gregorian (default; escape is optional) |
| `@#DJULIAN@` | Julian |
| `@#DHEBREW@` | Hebrew |
| `@#DFRENCH R@` | French Republican |
| `@#DROMAN@` | Roman (not defined in detail) |
| `@#DUNKNOWN@` | Unknown calendar |

Hebrew month abbreviations: `TSH`, `CSH`, `KSL`, `TVT`, `SHV`, `ADR`, `ADS`, `NSN`, `IYR`, `SVN`, `TMZ`, `AAV`, `ELL`

French Republican month abbreviations: `VEND`, `BRUM`, `FRIM`, `NIVO`, `PLUV`, `VENT`, `GERM`, `FLOR`, `PRAI`, `MESS`, `THER`, `FRUC`, `COMP`

### 8.7 Special Date Forms

**Dual dating** (calendar transitions): `15 DEC 1752/53`

**B.C. dates**: Year followed by `B.C.`: `600 B.C.`

### 8.8 Examples

```
2 DATE 12 MAY 1920
2 DATE ABT 1850
2 DATE BEF 15 JUN 1900
2 DATE AFT 1776
2 DATE BET 1 JAN 1820 AND 31 DEC 1825
2 DATE FROM 1 MAR 1900 TO 15 APR 1900
2 DATE CAL 1845
2 DATE EST 1700
2 DATE INT 15 JAN 1950 (about the middle of January 1950)
2 DATE @#DJULIAN@ 25 DEC 1066
2 DATE (Christmas Day)
```

**ftree status:** Supported (exact dates, ABT, BEF, AFT, BET...AND, FROM...TO). Calendar escapes and date phrases are planned.

## 9. Place Format

### 9.1 Convention

Places use comma-separated jurisdictions, ordered from smallest to largest:

```
City, County, State/Province, Country
```

Example: `Weston, Madison, Connecticut, United States of America`

Missing intermediate jurisdictions use adjacent commas: `Springfield,,Illinois,USA`

### 9.2 Place Structure

```
  n PLAC <PLACE_NAME>                            {0:1}
    +1 FORM <PLACE_HIERARCHY>                    {0:1}
    +1 <<SOURCE_CITATION>>                       {0:M}
    +1 <<NOTE_STRUCTURE>>                        {0:M}
    +1 FONE <PHONETIC_VARIATION>                 {0:M}
      +2 TYPE <PHONETIC_TYPE>                    {1:1}
    +1 ROMN <ROMANIZED_VARIATION>                {0:M}
      +2 TYPE <ROMANIZED_TYPE>                   {1:1}
    +1 MAP                                       {0:1}
      +2 LATI <LATITUDE>                         {1:1}
      +2 LONG <LONGITUDE>                        {1:1}
```

`MAP`, `LATI`, `LONG`, `FONE`, and `ROMN` are 5.5.1 additions.

### 9.3 Coordinate Format

```
LATI: N|S + degrees.decimal    (e.g., N50.9414, S33.8667)
LONG: E|W + degrees.decimal    (e.g., W1.4311, E151.2)
```

### 9.4 Default Place Hierarchy

Defined in the header:

```
1 PLAC
  2 FORM City, County, State, Country
```

When present, this declares the default jurisdiction order for all PLAC values in the file.

**ftree status:** Supported (PLAC values). MAP coordinates and FONE/ROMN are ignored.

## 10. Character Encodings

### 10.1 GEDCOM 5.5

| Value | Description |
|-------|-------------|
| `ANSEL` | Default. 8-bit ANSEL (Z39.47). Codes 0–127 are ASCII. Codes 128–255 provide extended Latin with diacriticals. Combining characters precede the character they modify. |
| `ASCII` | 7-bit ASCII only. No extended characters. |
| `UNICODE` | 16-bit Unicode (UCS-2). |

### 10.2 GEDCOM 5.5.1

Added `UTF-8` as a valid encoding alongside ANSEL, ASCII, and UNICODE.

### 10.3 Practical Considerations

Most modern GEDCOM files use UTF-8. The 555SAMPLE16LE.GED sample demonstrates that some files use UTF-16 Little Endian encoding, despite declaring `UNICODE` in the header. Parsers SHOULD detect byte-order marks (BOM) and handle common encoding mismatches gracefully.

| BOM Bytes | Encoding |
|-----------|----------|
| `EF BB BF` | UTF-8 |
| `FF FE` | UTF-16 LE |
| `FE FF` | UTF-16 BE |
| (none) | Check CHAR declaration; default to ANSEL for 5.5, UTF-8 for 5.5.1+ |

**ftree status:** Supported (UTF-8, ASCII). ANSEL and UTF-16 handling is planned.

## 11. Multimedia (OBJE)

### 11.1 Multimedia Record (5.5.1)

GEDCOM 5.5 used `BLOB` for embedded binary data (now obsolete). GEDCOM 5.5.1 replaced this with external file references:

```
0 @XREF:OBJE@ OBJE
  1 FILE <MULTIMEDIA_FILE_REFERENCE>             {1:M}
    2 FORM <MULTIMEDIA_FORMAT>                   {1:1}
      3 TYPE <SOURCE_MEDIA_TYPE>                 {0:1}
    2 TITL <DESCRIPTIVE_TITLE>                   {0:1}
  1 REFN <USER_REFERENCE_NUMBER>                 {0:M}
  1 RIN <AUTOMATED_RECORD_ID>                    {0:1}
  1 <<NOTE_STRUCTURE>>                           {0:M}
  1 <<SOURCE_CITATION>>                          {0:M}
  1 <<CHANGE_DATE>>                              {0:1}
```

### 11.2 Multimedia Link (Inline)

Pointer form:

```
  n OBJE @XREF:OBJE@
```

Embedded form (5.5.1):

```
  n OBJE
    +1 FILE <MULTIMEDIA_FILE_REFERENCE>          {1:M}
      +2 FORM <MULTIMEDIA_FORMAT>                {1:1}
        +3 MEDI <SOURCE_MEDIA_TYPE>              {0:1}
      +2 TITL <DESCRIPTIVE_TITLE>                {0:1}
```

### 11.3 Format Values

Common FORM values: `bmp`, `gif`, `jpg`, `ole`, `pcx`, `tif`, `wav`

TYPE/MEDI values: `audio`, `book`, `card`, `electronic`, `fiche`, `film`, `magazine`, `manuscript`, `map`, `newspaper`, `photo`, `tombstone`, `video`

### 11.4 URL References

Some producers (notably GRAMPS) use URL values in OBJE.FILE:

```
1 OBJE
  2 FORM URL
  2 FILE http://en.wikipedia.org/wiki/Bart_Simpson
```

This is a common extension, not part of the official specification.

**ftree status:** Supported (FILE path extraction). Format and type metadata are ignored.

## 12. Other Record Types

### 12.1 Repository Record (REPO)

```
0 @XREF:REPO@ REPO
  1 NAME <NAME_OF_REPOSITORY>                    {1:1}
  1 <<ADDRESS_STRUCTURE>>                        {0:1}
  1 <<NOTE_STRUCTURE>>                           {0:M}
  1 REFN <USER_REFERENCE_NUMBER>                 {0:M}
  1 RIN <AUTOMATED_RECORD_ID>                    {0:1}
  1 <<CHANGE_DATE>>                              {0:1}
```

**ftree status:** Planned.

### 12.2 Submitter Record (SUBM)

```
0 @XREF:SUBM@ SUBM
  1 NAME <SUBMITTER_NAME>                        {1:1}
  1 <<ADDRESS_STRUCTURE>>                        {0:1}
  1 <<MULTIMEDIA_LINK>>                          {0:M}
  1 LANG <LANGUAGE_PREFERENCE>                   {0:3}
  1 RFN <SUBMITTER_REGISTERED_RFN>               {0:1}
  1 RIN <AUTOMATED_RECORD_ID>                    {0:1}
  1 <<NOTE_STRUCTURE>>                           {0:M}
  1 <<CHANGE_DATE>>                              {0:1}
```

**ftree status:** Supported (NAME). Other fields are ignored.

### 12.3 Note Record (NOTE)

```
0 @XREF:NOTE@ NOTE <SUBMITTER_TEXT>
  1 [CONT|CONC] <SUBMITTER_TEXT>                 {0:M}
  1 <<SOURCE_CITATION>>                          {0:M}
  1 REFN <USER_REFERENCE_NUMBER>                 {0:M}
  1 RIN <AUTOMATED_RECORD_ID>                    {0:1}
  1 <<CHANGE_DATE>>                              {0:1}
```

Note records carry their text as the value of the level 0 line, continued with CONT/CONC.

**ftree status:** Planned.

### 12.4 Note Structure (Inline)

Notes can appear inline (without a separate record) or as pointers:

Inline form:

```
  n NOTE <TEXT>
    +1 [CONT|CONC] <TEXT>                        {0:M}
    +1 <<SOURCE_CITATION>>                       {0:M}
```

Pointer form:

```
  n NOTE @XREF:NOTE@
```

### 12.5 Change Date Structure

```
  n CHAN
    +1 DATE <CHANGE_DATE>                        {1:1}
      +2 TIME <TIME_VALUE>                       {0:1}
    +1 <<NOTE_STRUCTURE>>                        {0:M}
```

**ftree status:** Ignored.

### 12.6 Address Structure

```
  n ADDR <ADDRESS_LINE>                          {0:1}
    +1 CONT <ADDRESS_LINE>                       {0:M}
    +1 ADR1 <ADDRESS_LINE_1>                     {0:1}
    +1 ADR2 <ADDRESS_LINE_2>                     {0:1}
    +1 ADR3 <ADDRESS_LINE_3>                     {0:1}
    +1 CITY <ADDRESS_CITY>                       {0:1}
    +1 STAE <ADDRESS_STATE>                      {0:1}
    +1 POST <ADDRESS_POSTAL_CODE>                {0:1}
    +1 CTRY <ADDRESS_COUNTRY>                    {0:1}
  n PHON <PHONE_NUMBER>                          {0:3}
  n EMAIL <ADDRESS_EMAIL>                        {0:3}
  n FAX <ADDRESS_FAX>                            {0:3}
  n WWW <ADDRESS_WEB_PAGE>                       {0:3}
```

EMAIL, FAX, and WWW are 5.5.1 additions.

**ftree status:** Ignored.

## 13. Version Differences

### 13.1 GEDCOM 5.5 vs 5.5.1

| Feature | 5.5 | 5.5.1 |
|---------|-----|-------|
| Character encoding | ANSEL, ASCII, UNICODE | Added UTF-8 |
| Multimedia | BLOB (embedded binary) | External FILE references; BLOB removed |
| OBJE hierarchy | FORM, TITL at same level | FORM, TITL subordinate to FILE |
| Place structure | Basic PLAC only | Added MAP (LATI/LONG), FONE, ROMN |
| Name structure | Basic name pieces | Added TYPE, FONE, ROMN |
| FAM record | No RESN | Added RESN (restriction notice) |
| Event detail | No RELI, no RESN | Added RELI, RESN |
| Individual attributes | No FACT tag | Added FACT (generic attribute) |
| Source repo citation | `{0:1}` (single) | `{0:M}` (multiple allowed) |
| REPO.NAME | Optional | Required |
| Address structure | No EMAIL, FAX, WWW | Added EMAIL, FAX, WWW |
| FAMC.PEDI | `{0:M}` | `{0:1}` |
| Child linkage | No STAT | Added STAT |

### 13.2 GEDCOM 7.0 (Future Reference)

GEDCOM 7.0 (released 2021) is a major revision with breaking changes. Files from 5.5.1 and 7.0 are not cross-compatible.

Key changes relevant to ftree:

- **Encoding**: Exclusively UTF-8
- **CONC removed**: Only CONT remains; the 255-character line limit is removed
- **NOTE becomes SNOTE**: Shared notes use `SNOTE` at level 0; inline `NOTE` remains
- **Extensions formalized**: `SCHMA` in the header maps `_`-prefixed extension tags to URIs
- **SEX expanded**: Supports `M`, `F`, `X` (intersex), `U` (unknown)
- **Non-pointer SOUR/OBJE removed**: All citations and media links MUST use pointers
- **Multimedia**: IANA media types replace format enumerations (`image/jpeg` instead of `jpg`)
- **Date phrases**: Moved from parenthetical syntax to dedicated `PHRASE` substructure

ftree MAY add GEDCOM 7.0 support in a future release. The structural differences are significant enough that a separate parser path would be needed.

## 14. Extension Tags

Many genealogy applications define custom tags prefixed with an underscore (`_`). These are not part of the specification but are common in real-world files.

Examples:

```
1 _MILT    (military service)
1 _DNA     (DNA test results)
1 _PHOTO   (photo reference)
1 _STAT    (custom status)
```

Parsers SHOULD silently skip unrecognized tags (including extension tags) and their substructures, rather than treating them as errors.

**ftree status:** Unrecognized tags are silently ignored.

## References

- GEDCOM 5.5.1 Specification (PDF): https://gedcom.io/specifications/ged551.pdf
- GEDCOM 5.5.2 Specification (HTML): https://jfcardinal.github.io/GEDCOM-5.5.2/gedcom-5.5.2.html
- FamilySearch GEDCOM 7.0 Specification: https://gedcom.io/specifications/FamilySearchGEDCOMv7.html
- GEDCOM Specifications Portal: https://gedcom.io/specs/

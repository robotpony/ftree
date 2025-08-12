# ftree Development Plan

## Unsupported GEDCOM Keywords

The following standard GEDCOM tags are not yet implemented and could be added in future versions:

### Core Records
- `SOUR` - Source citations
- `NOTE` - General notes
- `REPO` - Repository records

### Individual Events
- `BAPM`/`CHR` - Baptism/Christening
- `BURI` - Burial
- `CREM` - Cremation
- `ADOP` - Adoption
- `OCCU` - Occupation
- `RESI` - Residence
- `EDUC` - Education

### Family Events
- `ENGA` - Engagement
- `DIV` - Divorce
- `ANUL` - Annulment

### Attributes
- `RELI` - Religion
- `NATI` - Nationality
- `CAST` - Caste
- `TITL` - Title

### Source/Citation Tags
- `PAGE` - Source page reference
- `QUAY` - Quality of evidence
- `DATA` - Source data
- `AUTH` - Author
- `PUBL` - Publication

## Implementation Priority

1. **P1**: Source citations (`SOUR`, `PAGE`, `QUAY`) - Essential for genealogy validation
2. **P2**: Notes (`NOTE`) - Important for additional context
3. **P3**: Additional life events (`BAPM`, `BURI`, `OCCU`, `RESI`)
4. **P4**: Repository and publication data (`REPO`, `AUTH`, `PUBL`)
5. **P5**: Attributes and less common events (`RELI`, `TITL`, `ENGA`, `DIV`)
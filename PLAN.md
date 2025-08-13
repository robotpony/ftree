# ftree Development Plan

## HTML Rendering Improvements

### Priority 1 - Core Fixes (Immediate) ✅ COMPLETED
- ✅ **Fix HTML formatting**: Add proper indentation and line breaks for readability
- ✅ **Add tree connectors**: CSS/SVG lines between family members for visual relationships
- ✅ **Improve person cards**: Show more metadata (occupation, education, notes already in data model)
- ✅ **Fix search functionality**: Current search input doesn't connect to Alpine.js properly
- ✅ **Generation counters**: Add generation numbers to help navigate large trees

**Completed 2025-08-13**: All Priority 1 items have been implemented and tested. Key improvements include:
- Proper HTML indentation and formatting throughout the renderer
- Enhanced tree connectors with gradients, marriage lines, and junction dots
- Rich person cards with icons for occupation (📋), education (🎓), religion (⛪), and notes (📝)
- Comprehensive search across all fields (names, dates, occupation, education, religion, notes)
- Generation badges and filtering functionality
- All changes validated with unit tests and sample GEDCOM files

### Priority 2 - Enhanced Navigation (Short-term) ✅ COMPLETED
- ✅ **Breadcrumb navigation**: Show current position in tree
- ✅ **Jump-to-person**: Quick navigation to any individual
- ✅ **Keyboard shortcuts**: Arrow keys for navigation, / for search
- ✅ **Improved filtering**: By date range, location, living/deceased status
- ✅ **Collapsible sidebar**: List of all families for quick access

**Completed 2025-08-13**: All Priority 2 navigation enhancements have been implemented and tested. Key improvements include:
- Dynamic breadcrumb trail showing current position in family hierarchy
- Jump-to-person dropdown with chronological sorting
- Comprehensive keyboard shortcuts (/, ↑↓, Enter, E, C, Esc) with visual feedback
- Advanced filtering panel with date range, location, living/deceased status, and gender filters
- Collapsible sidebar with family navigator, quick stats, and direct family navigation
- Full Alpine.js reactivity and smooth animations throughout

### Priority 3 - Visual Enhancements (Medium-term) ✅ COMPLETED
- ✅ **Multiple view modes**:
  - Pedigree chart (ancestors only)
  - Descendant chart (descendants only)
  - Hourglass chart (both directions from selected person)
- ✅ **Visual indicators**:
  - Age badges (age at death or current age)
  - Living/deceased status icons
  - Gender-neutral color options
- ✅ **Dark mode theme**: Toggle between light/dark themes
- ✅ **Print optimization**: Better layout for printing

**Completed 2025-08-13**: All Priority 3 visual enhancements have been implemented and tested. Key improvements include:
- Complete view mode system with pedigree, descendant, and hourglass chart filters
- Age badges showing current age for living people or age at death for deceased
- Living/deceased status icons (○ for living, ✝ for deceased) with automatic detection
- Dark mode toggle with localStorage persistence and comprehensive theme switching
- Comprehensive print optimization with print-specific CSS, page breaks, and layout adjustments
- All functionality fully integrated with Alpine.js reactivity and smooth user experience

### Priority 4 - Advanced Features (Long-term)
- **Timeline view**: Show events chronologically
- **Statistics dashboard**: Family size, lifespan, location distribution
- **Export options**: PDF, SVG tree, CSV data export
- **Photo gallery**: View all photos in tree
- **Relationship calculator**: Calculate relationship between any two people

### Priority 5 - Performance & Polish
- **Lazy loading**: For trees with 1000+ individuals
- **Virtual scrolling**: Optimize rendering of long lists
- **Progressive enhancement**: Basic functionality without JavaScript
- **Accessibility**: Full ARIA support, keyboard navigation
- **Responsive design**: Better mobile/tablet experience

## Unsupported GEDCOM Keywords

The following standard GEDCOM tags are not yet fully implemented and could be added in future versions:

### Core Records
- `SOUR` - Source citations
- `NOTE` - General notes (partially implemented)
- `REPO` - Repository records

### Individual Events
- `BAPM`/`CHR` - Baptism/Christening
- `BURI` - Burial
- `CREM` - Cremation
- `ADOP` - Adoption
- `OCCU` - Occupation (implemented in data model, not fully displayed)
- `RESI` - Residence
- `EDUC` - Education (implemented in data model, not fully displayed)

### Family Events
- `ENGA` - Engagement (implemented in data model)
- `DIV` - Divorce (implemented in data model)
- `ANUL` - Annulment

### Attributes
- `RELI` - Religion (implemented in data model, not fully displayed)
- `NATI` - Nationality
- `CAST` - Caste
- `TITL` - Title

### Source/Citation Tags
- `PAGE` - Source page reference
- `QUAY` - Quality of evidence
- `DATA` - Source data
- `AUTH` - Author
- `PUBL` - Publication

## Implementation Priority (GEDCOM)

1. **P1**: Source citations (`SOUR`, `PAGE`, `QUAY`) - Essential for genealogy validation
2. **P2**: Notes (`NOTE`) - Important for additional context
3. **P3**: Additional life events (`BAPM`, `BURI`, `OCCU`, `RESI`)
4. **P4**: Repository and publication data (`REPO`, `AUTH`, `PUBL`)
5. **P5**: Attributes and less common events (`RELI`, `TITL`, `ENGA`, `DIV`)
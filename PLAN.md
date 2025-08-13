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

## HTML Renderer Enhancements

### Mobile/Touch Support (Future Task)
- Touch-friendly controls for expanding/collapsing family branches
- Responsive grid layouts for different screen sizes
- Swipe gestures for navigation
- Optimized touch target sizes for person cards
- Mobile-specific CSS improvements for better readability

### Additional Features to Consider
- Zoom and pan functionality for large family trees
- Export options (PNG, PDF) from HTML view
- Print-friendly styling improvements
- Accessibility features (ARIA labels, keyboard navigation)
- Additional CSS themes (dark mode, high contrast)
- Performance optimizations for very large trees

## Theme System (Future Implementation)

### Design Goals
- Support multiple visual themes for different preferences
- Enable easy theme switching without regenerating HTML
- Maintain readability and accessibility across all themes

### Planned Themes
1. **Default** - Current light theme with blue/gray colors
2. **Dark Mode** - Dark background with light text for low-light viewing
3. **High Contrast** - Black and white with strong borders for accessibility
4. **Vintage** - Sepia tones mimicking old family photos
5. **Modern** - Flat design with bold colors and minimal shadows
6. **Print** - Optimized for black and white printing

### Implementation Strategy
- CSS custom properties (variables) for easy color theming
- Theme switcher in HTML header controls
- Save theme preference in localStorage
- Separate CSS classes for each theme
- Consider user's system preference (prefers-color-scheme)

### Color Customization Options
- Primary color (headers, borders)
- Secondary color (buttons, links)
- Accent colors for gender indicators
- Background colors for cards and containers
- Text colors with proper contrast ratios
- Shadow and border styles per theme

### Technical Approach
- Keep CSS embedded for self-contained files
- Use data attributes to apply theme-specific styles
- Ensure all themes meet WCAG accessibility standards
- Test themes with various genealogy data sizes
"""HTML renderer for family trees."""

import html
from typing import List, Set
from .models import FamilyTree, Individual, Family


class HtmlRenderer:
    """Render family trees as interactive HTML."""
    
    def __init__(self, tree: FamilyTree):
        self.tree = tree
        self.rendered_individuals: Set[str] = set()
        self.include_photos = True  # Default value
        self.include_places = True  # Default value
    
    def render(self, 
               theme: str = "default",
               include_places: bool = True,
               include_photos: bool = True,
               title: str = "Family Tree") -> str:
        """Render the complete family tree as HTML.
        
        Args:
            theme: CSS theme name
            include_places: Include birth/death places in output
            include_photos: Include photos from GEDCOM objects
            title: Page title
        """
        self.include_places = include_places
        self.include_photos = include_photos
        self.rendered_individuals = set()
        
        try:
            # Find root families
            root_families = self._find_root_families()
            
            # Generate HTML structure
            html_content = self._generate_html_document(root_families, theme, title)
            
            return html_content
        except Exception as e:
            # Return a basic error page if rendering fails completely
            error_html = f"""<!DOCTYPE html>
<html><head><title>Error</title></head>
<body><h1>Error Rendering Family Tree</h1>
<p>An error occurred while rendering the family tree: {html.escape(str(e))}</p>
</body></html>"""
            print(f"Critical error rendering tree: {e}")
            return error_html
    
    def _generate_html_document(self, root_families: List[Family], theme: str, title: str) -> str:
        """Generate the complete HTML document."""
        css_content = self._get_embedded_css(theme)
        
        # Build HTML template with proper escaping for curly braces in Alpine.js/CSS
        tree_content = self._generate_tree_content(root_families)
        javascript = self._generate_javascript()
        
        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <style>
        {css_content}
    </style>
</head>
<body x-data="familyTreeApp()" x-init="init()">
    <div class="ftree-container">
        <header class="ftree-header">
            <h1>{html.escape(title)}</h1>
            <div class="ftree-controls">
                <button @click="expandAll()">Expand All</button>
                <button @click="collapseAll()">Collapse All</button>
                <input type="search" x-model="searchQuery" @input="filterPeople()" placeholder="Search names, dates, occupation, education..." id="search-box">
                <select @change="filterByGeneration($event.target.value)">
                    <option value="">All Generations</option>
                    <option value="1">Generation 1</option>
                    <option value="2">Generation 2</option>
                    <option value="3">Generation 3</option>
                    <option value="4">Generation 4+</option>
                </select>
                <div class="jump-to-person">
                    <select @change="jumpToPerson($event.target.value)" x-init="populatePersonList()">
                        <option value="">Jump to person...</option>
                        <template x-for="person in allPeople" :key="person.id">
                            <option :value="person.id" x-text="person.name + ' (' + person.lifespan + ')'"></option>
                        </template>
                    </select>
                </div>
                <div class="view-mode-selector">
                    <label for="view-mode">View Mode:</label>
                    <select id="view-mode" @change="changeViewMode($event.target.value)" x-model="currentViewMode">
                        <option value="full">Full Tree</option>
                        <option value="pedigree">Pedigree Chart</option>
                        <option value="descendant">Descendant Chart</option>
                        <option value="hourglass">Hourglass Chart</option>
                    </select>
                    <input type="text" x-show="currentViewMode !== 'full'" x-model="focusPersonId" @input="updateFocusPerson()" placeholder="Enter person ID or select from list" class="focus-person-input">
                    <select x-show="currentViewMode !== 'full'" @change="setFocusPerson($event.target.value)" class="focus-person-select">
                        <option value="">Select focus person...</option>
                        <template x-for="person in allPeople" :key="person.id">
                            <option :value="person.id" x-text="person.name + ' (' + person.lifespan + ')'"></option>
                        </template>
                    </select>
                </div>
                <div class="keyboard-help">
                    <small>💡 <strong>Keys:</strong> / (search), ↑↓ (navigate), Enter (details), E (expand), C (collapse)</small>
                </div>
                <button @click="toggleDarkMode()" class="theme-toggle" :title="isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'">
                    <span x-show="!isDarkMode">🌙</span>
                    <span x-show="isDarkMode">☀️</span>
                </button>
                <button @click="showAdvancedFilters = !showAdvancedFilters" class="toggle-filters">
                    <span x-text="showAdvancedFilters ? '🔽 Hide Filters' : '🔼 Show Advanced Filters'"></span>
                </button>
            </div>
            
            <div x-show="showAdvancedFilters" x-transition class="advanced-filters">
                <div class="filter-row">
                    <label>Date Range:</label>
                    <input type="number" x-model="filters.yearFrom" placeholder="From year" min="1000" max="2100">
                    <span>to</span>
                    <input type="number" x-model="filters.yearTo" placeholder="To year" min="1000" max="2100">
                </div>
                
                <div class="filter-row">
                    <label>Location:</label>
                    <input type="text" x-model="filters.location" placeholder="Birth or death place...">
                </div>
                
                <div class="filter-row">
                    <label>Status:</label>
                    <select x-model="filters.livingStatus">
                        <option value="">All</option>
                        <option value="living">Living</option>
                        <option value="deceased">Deceased</option>
                    </select>
                    
                    <label>Gender:</label>
                    <select x-model="filters.gender">
                        <option value="">All</option>
                        <option value="M">Male</option>
                        <option value="F">Female</option>
                        <option value="U">Unknown</option>
                    </select>
                </div>
                
                <div class="filter-row">
                    <button @click="applyAdvancedFilters()" class="apply-filters">Apply Filters</button>
                    <button @click="clearAdvancedFilters()" class="clear-filters">Clear Filters</button>
                    <span x-show="activeFilters > 0" class="filter-count" x-text="activeFilters + ' filter(s) active'"></span>
                </div>
            </div>
        </header>
        
        <nav class="ftree-breadcrumb" x-show="breadcrumbs.length > 0" x-transition>
            <span class="breadcrumb-label">Current position:</span>
            <template x-for="(crumb, index) in breadcrumbs" :key="crumb.id">
                <span class="breadcrumb-item">
                    <a href="#" @click.prevent="navigateToPerson(crumb.id)" x-text="crumb.name"></a>
                    <span x-show="index < breadcrumbs.length - 1" class="breadcrumb-separator">→</span>
                </span>
            </template>
        </nav>
        
        <div class="ftree-content-wrapper">
            <aside class="ftree-sidebar" x-show="showSidebar" x-transition:enter="transition transform ease-out duration-300" x-transition:enter-start="-translate-x-full" x-transition:enter-end="translate-x-0" x-transition:leave="transition transform ease-in duration-300" x-transition:leave-start="translate-x-0" x-transition:leave-end="-translate-x-full">
                <div class="sidebar-header">
                    <h3>Family Navigator</h3>
                    <button @click="showSidebar = false" class="close-sidebar">&times;</button>
                </div>
                
                <div class="sidebar-content">
                    <div class="sidebar-section">
                        <h4>Root Families</h4>
                        <ul class="family-list">
                            <template x-for="family in familyList" :key="family.id">
                                <li class="family-item">
                                    <strong x-text="family.parents.join(' & ')"></strong>
                                    <span x-show="family.marriageYear" x-text="'(m. ' + family.marriageYear + ')'"></span>
                                    <div x-show="family.children.length > 0" class="children-count">
                                        <small x-text="family.children.length + ' children'"></small>
                                    </div>
                                    <button @click="navigateToFamily(family.id)" class="goto-family">Go to Family</button>
                                </li>
                            </template>
                        </ul>
                    </div>
                    
                    <div class="sidebar-section">
                        <h4>Quick Stats</h4>
                        <div class="stats-grid">
                            <div class="stat-item">
                                <span class="stat-number" x-text="totalPeople"></span>
                                <span class="stat-label">People</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-number" x-text="totalFamilies"></span>
                                <span class="stat-label">Families</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-number" x-text="generations"></span>
                                <span class="stat-label">Generations</span>
                            </div>
                        </div>
                    </div>
                </div>
            </aside>
            
            <button @click="showSidebar = !showSidebar" class="sidebar-toggle" :class="{{'sidebar-open': showSidebar}}">
                <span x-show="!showSidebar">☰</span>
                <span x-show="showSidebar">✕</span>
            </button>
            
            <main class="ftree-main" :class="{{'sidebar-open': showSidebar}}">
                {tree_content}
            </main>
        </div>
        
        <div x-show="showModal" @click.away="showModal = false" class="modal" style="display: none;" x-transition>
            <div class="modal-content">
                <span class="close" @click="showModal = false">&times;</span>
                <div id="person-details">
                    <h2 x-text="selectedPerson.name"></h2>
                    <div class="person-modal-info">
                        <div x-show="selectedPerson.birth" class="info-row">
                            <strong>Born:</strong> <span x-text="selectedPerson.birth"></span>
                        </div>
                        <div x-show="selectedPerson.death" class="info-row">
                            <strong>Died:</strong> <span x-text="selectedPerson.death"></span>
                        </div>
                        <div x-show="selectedPerson.birthPlace" class="info-row">
                            <strong>Birth Place:</strong> <span x-text="selectedPerson.birthPlace"></span>
                        </div>
                        <div x-show="selectedPerson.deathPlace" class="info-row">
                            <strong>Death Place:</strong> <span x-text="selectedPerson.deathPlace"></span>
                        </div>
                        <div x-show="selectedPerson.occupation" class="info-row">
                            <strong>Occupation:</strong> <span x-text="selectedPerson.occupation"></span>
                        </div>
                        <div x-show="selectedPerson.religion" class="info-row">
                            <strong>Religion:</strong> <span x-text="selectedPerson.religion"></span>
                        </div>
                        <div x-show="selectedPerson.education" class="info-row">
                            <strong>Education:</strong> <span x-text="selectedPerson.education"></span>
                        </div>
                        <div x-show="selectedPerson.notes" class="info-row">
                            <strong>Notes:</strong> <span x-text="selectedPerson.notes"></span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        {javascript}
    </script>
</body>
</html>"""
        return html_doc
    
    def _generate_tree_content(self, root_families: List[Family]) -> str:
        """Generate the tree structure content."""
        content_parts = []
        
        # Render each root family tree
        for family in root_families:
            family_tree = self._render_family_tree(family)
            if family_tree:
                content_parts.append(f'            <div class="family-tree">\n{family_tree}\n            </div>')
        
        # Render any remaining unconnected individuals
        orphans = self._find_orphaned_individuals()
        if orphans:
            orphan_lines = []
            orphan_lines.append('            <div class="orphaned-individuals">')
            orphan_lines.append('                <h2>Unconnected Individuals</h2>')
            orphan_lines.append('                <ul class="orphan-list">')
            for individual in orphans:
                orphan_lines.append(f'                    <li>\n{self._render_person_card(individual, indent=24)}\n                    </li>')
            orphan_lines.append('                </ul>')
            orphan_lines.append('            </div>')
            content_parts.append('\n'.join(orphan_lines))
        
        return '\n'.join(content_parts)
    
    def _render_family_tree(self, family: Family, generation: int = 1, indent: int = 16) -> str:
        """Render a family and their descendants as HTML tree."""
        if not family:
            return ""
        
        ind = ' ' * indent
        lines = []
        lines.append(f'{ind}<div class="family-unit" data-family-id="{html.escape(family.id)}" data-generation="{generation}">')
        
        # Parents section
        parents_html = self._render_parents(family, generation, indent + 4)
        if parents_html:
            lines.append(f'{ind}    <div class="parents">')
            lines.append(parents_html)
            lines.append(f'{ind}    </div>')
        
        # Children section
        children_html = self._render_children(family, generation, indent + 4)
        if children_html:
            lines.append(f'{ind}    <div class="children">')
            lines.append(children_html)
            lines.append(f'{ind}    </div>')
        
        lines.append(f'{ind}</div>')
        
        return '\n'.join(lines)
    
    def _render_parents(self, family: Family, generation: int = 1, indent: int = 20) -> str:
        """Render the parent couple."""
        parents = []
        
        try:
            if family.husband_id:
                husband = self.tree.get_individual(family.husband_id)
                if husband and husband.id not in self.rendered_individuals:
                    parents.append(self._render_person_card(husband, "husband", generation, indent + 8))
                    self.rendered_individuals.add(husband.id)
            
            if family.wife_id:
                wife = self.tree.get_individual(family.wife_id)
                if wife and wife.id not in self.rendered_individuals:
                    parents.append(self._render_person_card(wife, "wife", generation, indent + 8))
                    self.rendered_individuals.add(wife.id)
        except (AttributeError, KeyError) as e:
            # Handle missing or corrupt individual data
            print(f"Warning: Error rendering parents for family {family.id}: {e}")
        
        if not parents:
            return ""
        
        # Check if family has children to determine if connector should be shown
        has_children = bool(family.children_ids)
        couple_class = "couple" if has_children else "couple no-children"
        
        ind = ' ' * indent
        lines = []
        lines.append(f'{ind}<div class="{couple_class}" data-family-id="{html.escape(family.id)}">')
        for parent_html in parents:
            lines.append(parent_html)
        
        # Add marriage info
        if family.marriage_date or family.marriage_place:
            lines.append(f'{ind}    <div class="marriage-info">')
            if family.marriage_date:
                lines.append(f'{ind}        <span class="marriage-date">m. {html.escape(family.marriage_date)}</span>')
            if family.marriage_place:
                lines.append(f'{ind}        <span class="marriage-place">in {html.escape(family.marriage_place)}</span>')
            lines.append(f'{ind}    </div>')
        
        lines.append(f'{ind}</div>')
        return '\n'.join(lines)
    
    def _render_children(self, family: Family, generation: int = 1, indent: int = 20) -> str:
        """Render the children of a family."""
        if not family.children_ids:
            return ""
        
        ind = ' ' * indent
        lines = []
        lines.append(f'{ind}<div class="children-container" data-parent-family="{html.escape(family.id)}">')
        lines.append(f'{ind}    <button class="toggle-children" data-expanded="true" data-family-id="{html.escape(family.id)}">▼ Children</button>')
        lines.append(f'{ind}    <div class="children-list">')
        
        # Sort children by birth year
        children = []
        for child_id in family.children_ids:
            try:
                child = self.tree.get_individual(child_id)
                if child:
                    children.append(child)
            except (AttributeError, KeyError) as e:
                print(f"Warning: Could not find child {child_id}: {e}")
        
        try:
            children.sort(key=lambda c: c.get_birth_year() or 9999)
        except (AttributeError, TypeError) as e:
            print(f"Warning: Error sorting children: {e}")
        
        for child in children:
            if child.id not in self.rendered_individuals:
                lines.append(f'{ind}        <div class="child-branch" data-child-id="{html.escape(child.id)}">')
                lines.append(self._render_person_card(child, "child", generation + 1, indent + 12))
                self.rendered_individuals.add(child.id)
                
                # Render child's own families
                try:
                    for spouse_family_id in child.family_spouse:
                        spouse_family = self.tree.get_family(spouse_family_id)
                        if spouse_family:
                            child_family_tree = self._render_descendant_family(spouse_family, child, generation + 1, indent + 12)
                            if child_family_tree:
                                lines.append(f'{ind}            <div class="descendant-family">')
                                lines.append(child_family_tree)
                                lines.append(f'{ind}            </div>')
                except (AttributeError, KeyError, TypeError) as e:
                    print(f"Warning: Error rendering child's families for {child.id}: {e}")
                
                lines.append(f'{ind}        </div>')
        
        lines.append(f'{ind}    </div>')
        lines.append(f'{ind}</div>')
        return '\n'.join(lines)
    
    def _render_descendant_family(self, family: Family, known_parent: Individual, generation: int = 1, indent: int = 20) -> str:
        """Render a family where we already know one parent."""
        ind = ' ' * indent
        lines = []
        lines.append(f'{ind}<div class="descendant-unit" data-family-id="{html.escape(family.id)}" data-generation="{generation}">')
        
        # Find and render spouse
        spouse_id = None
        if family.husband_id == known_parent.id:
            spouse_id = family.wife_id
        elif family.wife_id == known_parent.id:
            spouse_id = family.husband_id
        
        if spouse_id:
            try:
                spouse = self.tree.get_individual(spouse_id)
                if spouse:
                    spouse_role = "wife" if family.husband_id == known_parent.id else "husband"
                    lines.append(f'{ind}    <div class="spouse">')
                    lines.append(self._render_person_card(spouse, spouse_role, generation, indent + 8))
                    lines.append(f'{ind}    </div>')
                    self.rendered_individuals.add(spouse_id)
            except (AttributeError, KeyError) as e:
                print(f"Warning: Could not find spouse {spouse_id}: {e}")
        
        # Render children
        children_html = self._render_children(family, generation, indent + 4)
        if children_html:
            lines.append(children_html)
        
        lines.append(f'{ind}</div>')
        return '\n'.join(lines)
    
    def _render_person_card(self, individual: Individual, role: str = "", generation: int = 0, indent: int = 0) -> str:
        """Render an individual as an HTML card."""
        if not individual:
            ind = ' ' * indent
            return f'{ind}<div class="person-card error">Missing Individual</div>'
        
        card_classes = f"person-card {role}".strip()
        
        try:
            name = html.escape(individual.name or individual.id or "Unknown")
            birth_year = str(individual.get_birth_year() or "")
            # Extract death year from death_date string if available
            death_year = ""
            if individual.death_date:
                # Try to extract year from date string
                import re
                year_match = re.search(r'\b(\d{4})\b', individual.death_date)
                if year_match:
                    death_year = year_match.group(1)
            gender = individual.sex or "U"
        except (AttributeError, TypeError) as e:
            # Handle corrupt individual data
            print(f"Warning: Error rendering individual {getattr(individual, 'id', 'unknown')}: {e}")
            name = "Unknown"
            birth_year = ""
            death_year = ""
            gender = "U"
        
        # Prepare data for modal
        occupation = getattr(individual, 'occupation', '') or ''
        religion = getattr(individual, 'religion', '') or ''
        education = getattr(individual, 'education', '') or ''
        notes = getattr(individual, 'notes', [])
        notes_text = f"{len(notes)} note{'s' if len(notes) != 1 else ''}" if notes else ''
        notes_preview = notes[0][:50] + "..." if notes and notes[0] and len(notes[0]) > 50 else (notes[0] if notes and notes[0] else '')
        
        ind = ' ' * indent
        lines = []
        lines.append(f'{ind}<div class="{card_classes}"')
        lines.append(f'{ind}    data-person-id="{html.escape(individual.id)}"')
        lines.append(f'{ind}    data-person-name="{name}"')
        lines.append(f'{ind}    data-birth-year="{birth_year}"')
        lines.append(f'{ind}    data-death-year="{death_year}"')
        lines.append(f'{ind}    data-gender="{gender}"')
        lines.append(f'{ind}    data-role="{role}"')
        lines.append(f'{ind}    data-generation="{generation}"')
        lines.append(f'{ind}    data-occupation="{html.escape(occupation)}"')
        lines.append(f'{ind}    data-religion="{html.escape(religion)}"')
        lines.append(f'{ind}    data-education="{html.escape(education)}"')
        lines.append(f'{ind}    data-notes="{html.escape(notes_text)}"')
        lines.append(f'{ind}    @click="showPersonDetails($el)">')
        
        # Photo if available
        photo_html = self._render_person_photo(individual)
        if photo_html:
            lines.append(f'{ind}    {photo_html}')
        
        # Generation badge
        if generation > 0:
            lines.append(f'{ind}    <span class="generation-badge">Gen {generation}</span>')
        
        # Age badge and living/deceased status
        age_info = self._get_age_info(individual)
        if age_info['show_age']:
            lines.append(f'{ind}    <span class="age-badge {age_info["status"]}">{age_info["text"]}</span>')
        
        # Living/deceased status icon
        status_icon = self._get_status_icon(individual)
        if status_icon:
            lines.append(f'{ind}    <span class="status-icon {status_icon["class"]}">{status_icon["icon"]}</span>')
        
        # Name
        lines.append(f'{ind}    <h3 class="person-name">{name}</h3>')
        
        # Dates
        dates_html = self._render_person_dates(individual)
        if dates_html:
            lines.append(f'{ind}    {dates_html}')
        
        # Places (if enabled)
        if self.include_places:
            places_html = self._render_person_places(individual)
            if places_html:
                lines.append(f'{ind}    {places_html}')
        
        # Additional metadata section
        metadata_parts = []
        if occupation:
            metadata_parts.append(f'<strong>📋</strong> {html.escape(occupation)}')
        if education:
            metadata_parts.append(f'<strong>🎓</strong> {html.escape(education)}')
        if religion:
            metadata_parts.append(f'<strong>⛪</strong> {html.escape(religion)}')
        
        if metadata_parts:
            lines.append(f'{ind}    <div class="person-metadata">')
            for part in metadata_parts:
                lines.append(f'{ind}        <div class="metadata-item"><small>{part}</small></div>')
            lines.append(f'{ind}    </div>')
        
        # Notes preview
        if notes_preview:
            lines.append(f'{ind}    <div class="person-notes-preview"><small><strong>📝</strong> {html.escape(notes_preview)}</small></div>')
        elif notes_text:
            lines.append(f'{ind}    <div class="person-notes-indicator"><small><strong>📝</strong> {html.escape(notes_text)}</small></div>')
        
        lines.append(f'{ind}</div>')
        return '\n'.join(lines)
    
    def _get_age_info(self, individual: Individual) -> dict:
        """Calculate age information for display."""
        try:
            birth_year = individual.get_birth_year()
            death_year = None
            if individual.death_date:
                import re
                year_match = re.search(r'\b(\d{4})\b', individual.death_date)
                if year_match:
                    death_year = int(year_match.group(1))
            
            if birth_year:
                if death_year:
                    age = death_year - birth_year
                    return {
                        'show_age': True,
                        'text': f'†{age}',
                        'status': 'deceased'
                    }
                else:
                    # Living person - calculate current age
                    from datetime import datetime
                    current_year = datetime.now().year
                    age = current_year - birth_year
                    # Only show current age if reasonable (not over 120)
                    if age <= 120:
                        return {
                            'show_age': True,
                            'text': f'{age}',
                            'status': 'living'
                        }
            
            return {'show_age': False}
        except (ValueError, TypeError, AttributeError):
            return {'show_age': False}
    
    def _get_status_icon(self, individual: Individual) -> dict:
        """Get living/deceased status icon."""
        try:
            if individual.death_date:
                return {
                    'icon': '✝',
                    'class': 'deceased'
                }
            else:
                # Check if birth date suggests person is likely still living
                birth_year = individual.get_birth_year()
                if birth_year:
                    from datetime import datetime
                    current_year = datetime.now().year
                    age = current_year - birth_year
                    if age <= 120:  # Reasonable age for living person
                        return {
                            'icon': '○',
                            'class': 'living'
                        }
            
            return None
        except (ValueError, TypeError, AttributeError):
            return None
    
    def _render_person_photo(self, individual: Individual) -> str:
        """Render person's photo if available."""
        if not self.include_photos or not individual.objects:
            return ""
        
        # Look for image files in objects
        for obj_ref in individual.objects:
            if any(ext in obj_ref.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                return f'<div class="person-photo"><img src="{html.escape(obj_ref)}" alt="Photo of {html.escape(individual.name)}" loading="lazy"></div>'
        
        return ""
    
    def _render_person_dates(self, individual: Individual) -> str:
        """Render birth and death dates."""
        try:
            if not individual.birth_date and not individual.death_date:
                return ""
            
            dates_html = '<div class="person-dates">'
            
            if individual.birth_date:
                dates_html += f'<span class="birth-date">b. {html.escape(str(individual.birth_date))}</span>'
            
            if individual.death_date:
                if individual.birth_date:
                    dates_html += ' – '
                dates_html += f'<span class="death-date">d. {html.escape(str(individual.death_date))}</span>'
        except (AttributeError, TypeError) as e:
            print(f"Warning: Error rendering dates for {getattr(individual, 'id', 'unknown')}: {e}")
            return ""
        
        dates_html += '</div>'
        return dates_html
    
    def _render_person_places(self, individual: Individual) -> str:
        """Render birth and death places."""
        try:
            if not individual.birth_place and not individual.death_place:
                return ""
            
            places_html = '<div class="person-places">'
            
            if individual.birth_place:
                places_html += f'<span class="birth-place">Born: {html.escape(str(individual.birth_place))}</span>'
            
            if individual.death_place:
                if individual.birth_place:
                    places_html += '<br>'
                places_html += f'<span class="death-place">Died: {html.escape(str(individual.death_place))}</span>'
        except (AttributeError, TypeError) as e:
            print(f"Warning: Error rendering places for {getattr(individual, 'id', 'unknown')}: {e}")
            return ""
        
        places_html += '</div>'
        return places_html
    
    def _find_root_families(self) -> List[Family]:
        """Find families where at least one parent has no parents."""
        root_families = []
        
        for family in self.tree.families.values():
            try:
                is_root = False
                
                # Check if husband has no parents
                if family.husband_id:
                    husband = self.tree.get_individual(family.husband_id)
                    if husband and not husband.family_child:
                        is_root = True
                
                # Check if wife has no parents
                if family.wife_id:
                    wife = self.tree.get_individual(family.wife_id)
                    if wife and not wife.family_child:
                        is_root = True
                
                if is_root:
                    root_families.append(family)
            except (AttributeError, KeyError) as e:
                print(f"Warning: Error processing family {getattr(family, 'id', 'unknown')}: {e}")
        
        return root_families
    
    def _get_embedded_css(self, theme: str = "default") -> str:
        """Get the embedded CSS content for the specified theme."""
        # For now, embed the default theme directly
        # Future: support multiple themes
        return """
        /* Default theme for ftree HTML renderer */
        
        :root {
            --primary-color: #2c3e50;
            --secondary-color: #3498db;
            --accent-color: #e74c3c;
            --background-color: #ffffff;
            --card-background: #f8f9fa;
            --border-color: #dee2e6;
            --text-color: #2c3e50;
            --text-muted: #6c757d;
            --male-color: #3498db;
            --female-color: #e91e63;
            --shadow: rgba(0, 0, 0, 0.1);
        }
        
        [data-theme="dark"] {
            --primary-color: #ecf0f1;
            --secondary-color: #5dade2;
            --accent-color: #e74c3c;
            --background-color: #1a1a1a;
            --card-background: #2c2c2c;
            --border-color: #444444;
            --text-color: #ecf0f1;
            --text-muted: #bdc3c7;
            --male-color: #5dade2;
            --female-color: #f39c12;
            --shadow: rgba(0, 0, 0, 0.3);
        }
        
        * {
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: var(--background-color);
            color: var(--text-color);
            line-height: 1.6;
        }
        
        .ftree-container {
            max-width: 100%;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Header */
        .ftree-header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid var(--border-color);
        }
        
        .ftree-header h1 {
            color: var(--primary-color);
            margin-bottom: 20px;
            font-size: 2.5rem;
            font-weight: 300;
        }
        
        .ftree-controls {
            display: flex;
            justify-content: center;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .ftree-controls button {
            background-color: var(--secondary-color);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.3s ease;
        }
        
        .ftree-controls button:hover {
            background-color: #2980b9;
        }
        
        #search-box {
            padding: 10px;
            border: 2px solid var(--border-color);
            border-radius: 5px;
            font-size: 14px;
            width: 250px;
            transition: border-color 0.3s ease;
        }
        
        #search-box:focus {
            outline: none;
            border-color: var(--secondary-color);
        }
        
        /* Breadcrumb Navigation */
        .ftree-breadcrumb {
            background-color: var(--card-background);
            padding: 10px 20px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid var(--secondary-color);
            box-shadow: 0 2px 5px var(--shadow);
        }
        
        .breadcrumb-label {
            font-weight: 600;
            color: var(--primary-color);
            margin-right: 10px;
        }
        
        .breadcrumb-item {
            display: inline-block;
            margin: 0 5px;
        }
        
        .breadcrumb-item a {
            color: var(--secondary-color);
            text-decoration: none;
            padding: 4px 8px;
            border-radius: 4px;
            transition: background-color 0.3s ease;
        }
        
        .breadcrumb-item a:hover {
            background-color: rgba(52, 152, 219, 0.1);
            text-decoration: underline;
        }
        
        .breadcrumb-separator {
            color: var(--text-muted);
            margin: 0 8px;
            font-weight: bold;
        }

        /* Main content */
        .ftree-main {
            overflow-x: auto;
            padding: 20px 0;
        }
        
        .family-tree {
            margin-bottom: 40px;
            padding: 20px;
            background-color: var(--card-background);
            border-radius: 10px;
            box-shadow: 0 2px 10px var(--shadow);
        }
        
        /* Family units */
        .family-unit {
            margin-bottom: 30px;
            position: relative;
        }
        
        .parents {
            margin-bottom: 20px;
            position: relative;
        }
        
        .couple {
            display: flex;
            justify-content: center;
            align-items: flex-start;
            gap: 20px;
            flex-wrap: wrap;
            margin-bottom: 15px;
            position: relative;
        }
        
        /* Tree connectors */
        .couple::after {
            content: '';
            position: absolute;
            bottom: -15px;
            left: 50%;
            transform: translateX(-50%);
            width: 3px;
            height: 15px;
            background-color: var(--secondary-color);
            border-radius: 2px;
        }
        
        .couple.no-children::after {
            display: none;
        }
        
        /* Marriage connector line between spouses */
        .couple::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 25%;
            right: 25%;
            height: 3px;
            background: linear-gradient(90deg, 
                transparent 0%, 
                var(--secondary-color) 20%, 
                var(--secondary-color) 80%, 
                transparent 100%);
            transform: translateY(-50%);
            z-index: -1;
        }
        
        .marriage-info {
            text-align: center;
            font-style: italic;
            color: var(--text-muted);
            margin-top: 10px;
        }
        
        .marriage-date, .marriage-place {
            display: block;
            font-size: 0.9rem;
        }
        
        /* Person cards */
        .person-card {
            background-color: white;
            border: 2px solid var(--border-color);
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px var(--shadow);
            max-width: 250px;
            min-width: 200px;
        }
        
        .person-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px var(--shadow);
            border-color: var(--secondary-color);
        }
        
        .person-card.husband {
            border-left: 4px solid var(--male-color);
        }
        
        .person-card.wife {
            border-left: 4px solid var(--female-color);
        }
        
        .person-card.child {
            border-left: 4px solid var(--accent-color);
        }
        
        .person-card.keyboard-highlighted {
            border: 3px solid var(--secondary-color);
            box-shadow: 0 0 15px rgba(52, 152, 219, 0.5);
            transform: scale(1.02);
        }
        
        /* Generation badge */
        .generation-badge {
            position: absolute;
            top: 5px;
            right: 5px;
            background-color: var(--secondary-color);
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        /* Age badge */
        .age-badge {
            position: absolute;
            top: 5px;
            left: 5px;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 0.7rem;
            font-weight: 600;
            color: white;
        }
        
        .age-badge.living {
            background-color: #27ae60;
        }
        
        .age-badge.deceased {
            background-color: #7f8c8d;
        }
        
        /* Status icon */
        .status-icon {
            position: absolute;
            bottom: 5px;
            right: 5px;
            font-size: 0.9rem;
        }
        
        .status-icon.living {
            color: #27ae60;
        }
        
        .status-icon.deceased {
            color: #7f8c8d;
        }
        
        .person-photo {
            margin-bottom: 10px;
        }
        
        .person-photo img {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid var(--border-color);
        }
        
        .person-name {
            margin: 10px 0;
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--primary-color);
        }
        
        .person-dates {
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-bottom: 8px;
        }
        
        .birth-date, .death-date {
            display: inline-block;
        }
        
        .person-places {
            color: var(--text-muted);
            font-size: 0.85rem;
            line-height: 1.4;
        }
        
        .birth-place, .death-place {
            display: block;
        }
        
        /* Additional metadata fields */
        .person-metadata {
            margin-top: 8px;
            padding: 6px 0;
            border-top: 1px solid rgba(52, 152, 219, 0.2);
        }
        
        .metadata-item {
            margin: 3px 0;
            color: var(--text-muted);
            font-size: 0.8rem;
            line-height: 1.4;
        }
        
        .metadata-item strong {
            margin-right: 4px;
            font-size: 0.9rem;
        }
        
        .person-notes-preview,
        .person-notes-indicator {
            margin-top: 6px;
            padding: 4px 8px;
            background-color: rgba(52, 152, 219, 0.1);
            border-radius: 4px;
            color: var(--text-muted);
            font-size: 0.75rem;
            line-height: 1.3;
            border-left: 3px solid var(--secondary-color);
        }
        
        .person-notes-preview strong,
        .person-notes-indicator strong {
            margin-right: 4px;
            color: var(--secondary-color);
        }
        
        /* Children sections */
        .children-container {
            margin-top: 20px;
            padding-top: 20px;
            position: relative;
        }
        
        .children-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 80%;
            max-width: 500px;
            height: 3px;
            background: linear-gradient(90deg, 
                transparent 0%, 
                var(--secondary-color) 10%, 
                var(--secondary-color) 90%, 
                transparent 100%);
            border-radius: 2px;
        }
        
        .toggle-children {
            background-color: var(--accent-color);
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            margin-bottom: 15px;
            transition: background-color 0.3s ease;
        }
        
        .toggle-children:hover {
            background-color: #c0392b;
        }
        
        .children-list {
            display: grid;
            gap: 20px;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            position: relative;
        }
        
        .child-branch {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 15px;
            position: relative;
        }
        
        .child-branch::before {
            content: '';
            position: absolute;
            top: -20px;
            left: 50%;
            transform: translateX(-50%);
            width: 3px;
            height: 20px;
            background-color: var(--secondary-color);
            border-radius: 0 0 2px 2px;
        }
        
        /* Add horizontal connector dot at junction points */
        .child-branch::after {
            content: '';
            position: absolute;
            top: -23px;
            left: 50%;
            transform: translateX(-50%);
            width: 8px;
            height: 8px;
            background-color: var(--secondary-color);
            border-radius: 50%;
            border: 2px solid var(--background-color);
        }
        
        .descendant-family {
            margin-top: 15px;
            padding: 15px;
            background-color: rgba(52, 152, 219, 0.05);
            border-radius: 8px;
            border-left: 3px solid var(--secondary-color);
        }
        
        .descendant-unit {
            margin-top: 10px;
        }
        
        .spouse {
            margin-bottom: 15px;
            display: flex;
            justify-content: center;
        }
        
        /* Orphaned individuals */
        .orphaned-individuals {
            margin-top: 40px;
            padding: 20px;
            background-color: var(--card-background);
            border-radius: 10px;
            box-shadow: 0 2px 10px var(--shadow);
        }
        
        .orphaned-individuals h2 {
            color: var(--primary-color);
            text-align: center;
            margin-bottom: 20px;
        }
        
        .orphan-list {
            list-style: none;
            padding: 0;
            display: grid;
            gap: 20px;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        }
        
        .orphan-list li {
            display: flex;
            justify-content: center;
        }
        
        /* Search highlighting */
        mark {
            background-color: #fff3cd;
            padding: 2px 4px;
            border-radius: 3px;
        }
        
        /* Modal */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
        }
        
        .modal-content {
            background-color: white;
            margin: 5% auto;
            padding: 20px;
            border-radius: 10px;
            width: 90%;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            position: relative;
        }
        
        .close {
            color: var(--text-muted);
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            line-height: 1;
        }
        
        .close:hover {
            color: var(--primary-color);
        }
        
        /* Modal person info */
        .person-modal-info {
            margin-top: 20px;
        }
        
        .info-row {
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .info-row:last-child {
            border-bottom: none;
        }
        
        .info-row strong {
            display: inline-block;
            min-width: 120px;
            color: var(--primary-color);
        }
        
        .info-row p {
            margin-top: 10px;
            line-height: 1.6;
            color: var(--text-muted);
        }
        
        /* Generation filter and Jump-to-person */
        select {
            padding: 10px;
            border: 2px solid var(--border-color);
            border-radius: 5px;
            font-size: 14px;
            background-color: white;
            cursor: pointer;
            transition: border-color 0.3s ease;
            min-width: 150px;
        }
        
        select:focus {
            outline: none;
            border-color: var(--secondary-color);
        }
        
        .jump-to-person {
            position: relative;
        }
        
        .jump-to-person select {
            min-width: 200px;
            max-width: 300px;
        }
        
        /* View Mode Selector */
        .view-mode-selector {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
            margin: 10px 0;
        }
        
        .view-mode-selector label {
            font-weight: 600;
            color: var(--primary-color);
        }
        
        .view-mode-selector select {
            min-width: 140px;
        }
        
        .focus-person-input {
            padding: 8px;
            border: 2px solid var(--border-color);
            border-radius: 4px;
            font-size: 14px;
            width: 200px;
            transition: border-color 0.3s ease;
        }
        
        .focus-person-input:focus {
            outline: none;
            border-color: var(--secondary-color);
        }
        
        .focus-person-select {
            min-width: 250px;
            max-width: 350px;
        }
        
        .keyboard-help {
            margin-top: 10px;
            padding: 8px 12px;
            background-color: rgba(52, 152, 219, 0.1);
            border-radius: 5px;
            border-left: 3px solid var(--secondary-color);
            color: var(--text-muted);
            font-size: 0.85rem;
        }
        
        .keyboard-help strong {
            color: var(--secondary-color);
        }
        
        .toggle-filters {
            background-color: var(--accent-color);
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 13px;
            margin-top: 10px;
            transition: background-color 0.3s ease;
        }
        
        .toggle-filters:hover {
            background-color: #c0392b;
        }
        
        /* Theme Toggle Button */
        .theme-toggle {
            background-color: var(--secondary-color);
            color: white;
            border: none;
            padding: 10px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 16px;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background-color 0.3s ease, transform 0.2s ease;
            margin: 5px;
        }
        
        .theme-toggle:hover {
            background-color: #2980b9;
            transform: scale(1.1);
        }
        
        [data-theme="dark"] .theme-toggle {
            background-color: #f39c12;
        }
        
        [data-theme="dark"] .theme-toggle:hover {
            background-color: #e67e22;
        }
        
        /* Advanced Filters */
        .advanced-filters {
            background-color: var(--card-background);
            padding: 20px;
            margin-top: 10px;
            border-radius: 8px;
            border: 2px solid var(--border-color);
            box-shadow: 0 2px 10px var(--shadow);
        }
        
        .filter-row {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        
        .filter-row:last-child {
            margin-bottom: 0;
            justify-content: flex-start;
        }
        
        .filter-row label {
            font-weight: 600;
            color: var(--primary-color);
            min-width: 80px;
        }
        
        .filter-row input[type="number"],
        .filter-row input[type="text"] {
            padding: 8px;
            border: 2px solid var(--border-color);
            border-radius: 4px;
            font-size: 14px;
            transition: border-color 0.3s ease;
            width: 120px;
        }
        
        .filter-row input[type="text"] {
            width: 200px;
        }
        
        .filter-row input:focus {
            outline: none;
            border-color: var(--secondary-color);
        }
        
        .filter-row select {
            padding: 8px;
            border: 2px solid var(--border-color);
            border-radius: 4px;
            font-size: 14px;
            min-width: 100px;
        }
        
        .apply-filters, .clear-filters {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.3s ease;
            margin-right: 10px;
        }
        
        .apply-filters {
            background-color: var(--secondary-color);
            color: white;
        }
        
        .apply-filters:hover {
            background-color: #2980b9;
        }
        
        .clear-filters {
            background-color: var(--text-muted);
            color: white;
        }
        
        .clear-filters:hover {
            background-color: #5a6268;
        }
        
        .filter-count {
            color: var(--secondary-color);
            font-weight: 600;
            font-size: 13px;
        }
        
        /* Sidebar */
        .ftree-content-wrapper {
            position: relative;
            display: flex;
        }
        
        .ftree-sidebar {
            position: fixed;
            top: 0;
            left: 0;
            width: 320px;
            height: 100vh;
            background-color: var(--card-background);
            border-right: 3px solid var(--secondary-color);
            box-shadow: 2px 0 10px var(--shadow);
            z-index: 900;
            overflow-y: auto;
        }
        
        .sidebar-header {
            background-color: var(--primary-color);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .sidebar-header h3 {
            margin: 0;
            font-size: 1.2rem;
        }
        
        .close-sidebar {
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            padding: 0;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: background-color 0.3s ease;
        }
        
        .close-sidebar:hover {
            background-color: rgba(255, 255, 255, 0.2);
        }
        
        .sidebar-content {
            padding: 20px;
        }
        
        .sidebar-section {
            margin-bottom: 30px;
        }
        
        .sidebar-section h4 {
            color: var(--primary-color);
            margin: 0 0 15px 0;
            font-size: 1.1rem;
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 5px;
        }
        
        .family-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .family-item {
            background-color: white;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            transition: box-shadow 0.3s ease;
        }
        
        .family-item:hover {
            box-shadow: 0 4px 12px var(--shadow);
        }
        
        .children-count {
            margin: 5px 0;
            color: var(--text-muted);
        }
        
        .goto-family {
            background-color: var(--secondary-color);
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin-top: 8px;
            transition: background-color 0.3s ease;
        }
        
        .goto-family:hover {
            background-color: #2980b9;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
            gap: 15px;
        }
        
        .stat-item {
            text-align: center;
            background-color: white;
            padding: 15px 10px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        
        .stat-number {
            display: block;
            font-size: 1.8rem;
            font-weight: bold;
            color: var(--secondary-color);
        }
        
        .stat-label {
            display: block;
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-top: 5px;
        }
        
        .sidebar-toggle {
            position: fixed;
            top: 20px;
            left: 20px;
            z-index: 1000;
            background-color: var(--secondary-color);
            color: white;
            border: none;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 4px 12px var(--shadow);
            font-size: 18px;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .sidebar-toggle:hover {
            background-color: #2980b9;
            transform: scale(1.1);
        }
        
        .sidebar-toggle.sidebar-open {
            left: 340px;
        }
        
        .ftree-main.sidebar-open {
            margin-left: 320px;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .ftree-container {
                padding: 10px;
            }
            
            .ftree-header h1 {
                font-size: 2rem;
            }
            
            .ftree-controls {
                flex-direction: column;
                gap: 10px;
            }
            
            #search-box {
                width: 100%;
                max-width: 300px;
            }
            
            .couple {
                flex-direction: column;
                align-items: center;
            }
            
            .children-list {
                grid-template-columns: 1fr;
            }
            
            .person-card {
                min-width: auto;
                width: 100%;
                max-width: 300px;
            }
            
            .modal-content {
                margin: 10% auto;
                width: 95%;
            }
            
            /* Mobile sidebar adjustments */
            .ftree-sidebar {
                width: 280px;
            }
            
            .sidebar-toggle.sidebar-open {
                left: 300px;
            }
            
            .ftree-main.sidebar-open {
                margin-left: 280px;
            }
            
            .filter-row {
                flex-direction: column;
                align-items: stretch;
            }
            
            .filter-row input, .filter-row select {
                width: 100%;
                margin-bottom: 10px;
            }
        }
        
        /* Print styles */
        @media print {
            /* Hide interactive elements */
            .ftree-controls,
            .ftree-breadcrumb,
            .ftree-sidebar,
            .sidebar-toggle,
            .toggle-children,
            .keyboard-help,
            .theme-toggle,
            .toggle-filters,
            .advanced-filters,
            .modal {
                display: none !important;
            }
            
            /* Reset body and container for print */
            body {
                background: white !important;
                color: black !important;
                font-size: 12pt;
                line-height: 1.4;
            }
            
            .ftree-container {
                max-width: none;
                margin: 0;
                padding: 10pt;
            }
            
            .ftree-header {
                text-align: center;
                margin-bottom: 20pt;
                padding-bottom: 10pt;
                border-bottom: 2pt solid #333;
            }
            
            .ftree-header h1 {
                font-size: 18pt;
                margin: 0 0 10pt 0;
                color: black !important;
            }
            
            .ftree-main {
                margin-left: 0 !important;
            }
            
            /* Optimize tree layout for print */
            .family-tree {
                break-inside: avoid;
                margin-bottom: 30pt;
                padding: 15pt;
                background: transparent !important;
                border: 1pt solid #666;
                box-shadow: none !important;
                border-radius: 0;
            }
            
            .family-unit,
            .descendant-unit {
                break-inside: avoid;
                margin-bottom: 15pt;
            }
            
            .couple {
                justify-content: flex-start;
                gap: 15pt;
                margin-bottom: 10pt;
            }
            
            /* Person cards optimized for print */
            .person-card {
                break-inside: avoid;
                background: white !important;
                border: 1pt solid #333 !important;
                border-radius: 4pt;
                padding: 8pt;
                margin: 5pt;
                box-shadow: none !important;
                font-size: 10pt;
                max-width: none;
                min-width: 120pt;
                width: auto;
            }
            
            .person-card.husband {
                border-left: 3pt solid #333 !important;
            }
            
            .person-card.wife {
                border-left: 3pt solid #666 !important;
            }
            
            .person-card.child {
                border-left: 3pt solid #999 !important;
            }
            
            .person-name {
                font-size: 11pt;
                font-weight: bold;
                margin: 2pt 0;
                color: black !important;
            }
            
            .person-dates,
            .person-places {
                font-size: 9pt;
                color: #333 !important;
                margin: 2pt 0;
            }
            
            .person-metadata {
                font-size: 8pt;
                color: #444 !important;
                margin-top: 5pt;
                padding-top: 3pt;
                border-top: 0.5pt solid #ccc;
            }
            
            /* Hide visual indicators not needed in print */
            .person-photo,
            .generation-badge,
            .age-badge,
            .status-icon {
                display: none !important;
            }
            
            /* Show all children expanded */
            .children-list {
                display: grid !important;
                grid-template-columns: repeat(auto-fit, minmax(120pt, 1fr));
                gap: 10pt;
            }
            
            .child-branch {
                break-inside: avoid;
                align-items: flex-start;
            }
            
            /* Marriage info */
            .marriage-info {
                font-size: 9pt;
                color: #555 !important;
                text-align: left;
                margin: 5pt 0;
            }
            
            /* Tree connectors - simplified for print */
            .couple::before,
            .couple::after,
            .children-container::before,
            .child-branch::before,
            .child-branch::after {
                display: none !important;
            }
            
            /* Orphaned individuals */
            .orphaned-individuals {
                break-before: page;
                background: transparent !important;
                border: 1pt solid #666;
                padding: 15pt;
                margin-top: 20pt;
            }
            
            .orphaned-individuals h2 {
                font-size: 14pt;
                color: black !important;
                margin: 0 0 15pt 0;
                border-bottom: 1pt solid #333;
                padding-bottom: 5pt;
            }
            
            .orphan-list {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(140pt, 1fr));
                gap: 10pt;
            }
            
            /* Page break helpers */
            .family-unit:first-child {
                break-before: avoid;
            }
            
            /* Print-friendly colors */
            * {
                -webkit-print-color-adjust: exact !important;
                color-adjust: exact !important;
            }
        }
        """
    
    def _find_orphaned_individuals(self) -> List[Individual]:
        """Find individuals not connected to any family."""
        connected_ids = set()
        
        # Collect all individuals in families
        for family in self.tree.families.values():
            if family.husband_id:
                connected_ids.add(family.husband_id)
            if family.wife_id:
                connected_ids.add(family.wife_id)
            connected_ids.update(family.children_ids)
        
        # Find unconnected individuals
        orphans = []
        for individual in self.tree.individuals.values():
            if individual.id not in connected_ids:
                orphans.append(individual)
        
        orphans.sort(key=lambda i: i.name or i.id)
        return orphans
    
    def _generate_javascript(self) -> str:
        """Generate JavaScript for interactivity using Alpine.js."""
        return """
function familyTreeApp() {
    return {
        searchQuery: '',
        showModal: false,
        selectedPerson: {},
        expandedFamilies: new Set(),
        generationFilter: '',
        breadcrumbs: [],
        allPeople: [],
        showAdvancedFilters: false,
        currentViewMode: 'full',
        focusPersonId: '',
        focusPerson: null,
        isDarkMode: false,
        filters: {
            yearFrom: '',
            yearTo: '',
            location: '',
            livingStatus: '',
            gender: ''
        },
        activeFilters: 0,
        showSidebar: false,
        familyList: [],
        totalPeople: 0,
        totalFamilies: 0,
        generations: 0,
        
        init() {
            // Initialize all families as expanded
            document.querySelectorAll('.toggle-children').forEach(button => {
                const familyId = button.dataset.familyId;
                this.expandedFamilies.add(familyId);
            });
            
            // Initialize dark mode from localStorage
            this.isDarkMode = localStorage.getItem('ftree-dark-mode') === 'true';
            this.applyTheme();
            
            // Set up toggle buttons
            this.setupToggleButtons();
            
            // Set up keyboard shortcuts
            this.setupKeyboardShortcuts();
            
            // Initialize sidebar data
            this.initializeSidebarData();
            
            // Initialize view mode
            this.applyViewMode();
        },
        
        setupToggleButtons() {
            document.querySelectorAll('.toggle-children').forEach(button => {
                button.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.toggleFamily(button);
                });
            });
        },
        
        toggleFamily(button) {
            const familyId = button.dataset.familyId;
            const childrenList = button.nextElementSibling;
            const isExpanded = this.expandedFamilies.has(familyId);
            
            if (isExpanded) {
                this.expandedFamilies.delete(familyId);
                childrenList.style.display = 'none';
                button.textContent = '▶ Children';
                button.dataset.expanded = 'false';
            } else {
                this.expandedFamilies.add(familyId);
                childrenList.style.display = 'block';
                button.textContent = '▼ Children';
                button.dataset.expanded = 'true';
            }
        },
        
        expandAll() {
            document.querySelectorAll('.toggle-children').forEach(button => {
                const familyId = button.dataset.familyId;
                const childrenList = button.nextElementSibling;
                this.expandedFamilies.add(familyId);
                childrenList.style.display = 'block';
                button.textContent = '▼ Children';
                button.dataset.expanded = 'true';
            });
        },
        
        collapseAll() {
            document.querySelectorAll('.toggle-children').forEach(button => {
                const familyId = button.dataset.familyId;
                const childrenList = button.nextElementSibling;
                this.expandedFamilies.delete(familyId);
                childrenList.style.display = 'none';
                button.textContent = '▶ Children';
                button.dataset.expanded = 'false';
            });
        },
        
        filterPeople() {
            const query = this.searchQuery.toLowerCase().trim();
            
            if (query === '') {
                // Show all cards and clear highlights
                document.querySelectorAll('.person-card').forEach(card => {
                    card.style.display = '';
                    const nameElement = card.querySelector('.person-name');
                    if (nameElement) {
                        nameElement.innerHTML = nameElement.textContent;
                    }
                });
                return;
            }
            
            document.querySelectorAll('.person-card').forEach(card => {
                const name = (card.dataset.personName || '').toLowerCase();
                const birthYear = (card.dataset.birthYear || '').toLowerCase();
                const deathYear = (card.dataset.deathYear || '').toLowerCase();
                const occupation = (card.dataset.occupation || '').toLowerCase();
                const education = (card.dataset.education || '').toLowerCase();
                const religion = (card.dataset.religion || '').toLowerCase();
                const notes = (card.dataset.notes || '').toLowerCase();
                
                // Search in all available fields
                const match = name.includes(query) || 
                             birthYear.includes(query) || 
                             deathYear.includes(query) ||
                             occupation.includes(query) ||
                             education.includes(query) ||
                             religion.includes(query) ||
                             notes.includes(query);
                
                // Show/hide card and its parent containers
                const cardContainer = card.closest('.child-branch') || card.closest('.spouse') || card.parentElement;
                if (match) {
                    card.style.display = '';
                    if (cardContainer) cardContainer.style.display = '';
                    
                    // Show parent family containers
                    const familyUnit = card.closest('.family-unit, .descendant-unit');
                    if (familyUnit) familyUnit.style.display = '';
                    
                    const familyTree = card.closest('.family-tree');
                    if (familyTree) familyTree.style.display = '';
                } else {
                    card.style.display = 'none';
                }
                
                // Highlight matches in name
                const nameElement = card.querySelector('.person-name');
                if (nameElement) {
                    if (match && name.includes(query)) {
                        const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
                        const originalText = nameElement.textContent;
                        nameElement.innerHTML = originalText.replace(regex, '<mark>$1</mark>');
                    } else {
                        nameElement.innerHTML = nameElement.textContent;
                    }
                }
            });
        },
        
        escapeRegex(string) {
            return string.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
        },
        
        filterByGeneration(generation) {
            this.generationFilter = generation;
            
            document.querySelectorAll('.person-card').forEach(card => {
                const cardGeneration = card.dataset.generation;
                
                if (generation === '' || cardGeneration === generation) {
                    card.style.display = '';
                    // Show parent containers
                    const cardContainer = card.closest('.child-branch') || card.closest('.spouse') || card.parentElement;
                    if (cardContainer) cardContainer.style.display = '';
                    
                    const familyUnit = card.closest('.family-unit, .descendant-unit');
                    if (familyUnit) familyUnit.style.display = '';
                    
                    const familyTree = card.closest('.family-tree');
                    if (familyTree) familyTree.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
            
            // Also apply current search filter if active
            if (this.searchQuery.trim() !== '') {
                this.filterPeople();
            }
        },
        
        showPersonDetails(element) {
            // Extract person data from the clicked element
            const personData = {
                id: element.dataset.personId,
                name: element.dataset.personName,
                birth: element.querySelector('.birth-date')?.textContent || '',
                death: element.querySelector('.death-date')?.textContent || '',
                birthPlace: element.querySelector('.birth-place')?.textContent.replace('Born: ', '') || '',
                deathPlace: element.querySelector('.death-place')?.textContent.replace('Died: ', '') || '',
                occupation: element.dataset.occupation || '',
                religion: element.dataset.religion || '',
                education: element.dataset.education || '',
                notes: element.dataset.notes || '',
                gender: element.dataset.gender || 'U',
                role: element.dataset.role || ''
            };
            
            // Get additional family relationships
            const relationships = this.getPersonRelationships(personData.id);
            personData.relationships = relationships;
            
            this.selectedPerson = personData;
            this.showModal = true;
        },
        
        getPersonRelationships(personId) {
            const relationships = {
                parents: [],
                spouses: [],
                children: [],
                siblings: []
            };
            
            // Find family relationships based on data attributes
            // This is a simplified version - could be enhanced
            document.querySelectorAll(`[data-person-id="${personId}"]`).forEach(card => {
                const role = card.dataset.role;
                const parentElement = card.closest('.family-unit, .descendant-unit');
                
                if (parentElement) {
                    // Find related people in the same family unit
                    const familyId = parentElement.dataset.familyId;
                    
                    // Find spouse
                    if (role === 'husband' || role === 'wife') {
                        const spouseRole = role === 'husband' ? 'wife' : 'husband';
                        const spouse = parentElement.querySelector(`.person-card.${spouseRole}`);
                        if (spouse) {
                            relationships.spouses.push({
                                id: spouse.dataset.personId,
                                name: spouse.dataset.personName
                            });
                        }
                    }
                    
                    // Find children
                    const childrenContainer = parentElement.querySelector('.children-container');
                    if (childrenContainer) {
                        childrenContainer.querySelectorAll('.person-card.child').forEach(child => {
                            relationships.children.push({
                                id: child.dataset.personId,
                                name: child.dataset.personName
                            });
                        });
                    }
                }
            });
            
            return relationships;
        },
        
        navigateToPerson(personId) {
            // Close modal
            this.showModal = false;
            
            // Find and scroll to person
            const personCard = document.querySelector(`[data-person-id="${personId}"]`);
            if (personCard) {
                personCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                // Update breadcrumbs
                this.updateBreadcrumbs(personCard);
                
                // Highlight the person temporarily
                personCard.style.transition = 'all 0.3s';
                personCard.style.boxShadow = '0 0 20px rgba(52, 152, 219, 0.8)';
                setTimeout(() => {
                    personCard.style.boxShadow = '';
                }, 2000);
            }
        },
        
        updateBreadcrumbs(personCard) {
            const breadcrumbs = [];
            let currentElement = personCard;
            
            // Walk up the family tree to build breadcrumb trail
            while (currentElement) {
                const personId = currentElement.dataset?.personId;
                const personName = currentElement.dataset?.personName;
                const generation = currentElement.dataset?.generation;
                
                if (personId && personName) {
                    breadcrumbs.unshift({
                        id: personId,
                        name: personName,
                        generation: generation
                    });
                }
                
                // Move up to parent family unit
                const familyUnit = currentElement.closest('.family-unit, .descendant-unit');
                if (familyUnit) {
                    // Find parent in the family hierarchy
                    const parentFamily = familyUnit.parentElement?.closest('.family-unit, .descendant-unit');
                    if (parentFamily) {
                        const parentCard = parentFamily.querySelector('.person-card.husband, .person-card.wife');
                        currentElement = parentCard;
                    } else {
                        break;
                    }
                } else {
                    break;
                }
            }
            
            // Limit breadcrumbs to reasonable length
            this.breadcrumbs = breadcrumbs.slice(-5);
        },
        
        populatePersonList() {
            // Collect all people from person cards
            const people = [];
            document.querySelectorAll('.person-card').forEach(card => {
                const id = card.dataset.personId;
                const name = card.dataset.personName;
                const birthYear = card.dataset.birthYear;
                const deathYear = card.dataset.deathYear;
                
                if (id && name) {
                    let lifespan = '';
                    if (birthYear || deathYear) {
                        lifespan = `${birthYear || '?'}-${deathYear || ''}`;
                    }
                    
                    people.push({
                        id: id,
                        name: name,
                        lifespan: lifespan,
                        birthYear: parseInt(birthYear) || 9999
                    });
                }
            });
            
            // Sort by birth year, then by name
            people.sort((a, b) => {
                if (a.birthYear !== b.birthYear) {
                    return a.birthYear - b.birthYear;
                }
                return a.name.localeCompare(b.name);
            });
            
            this.allPeople = people;
        },
        
        jumpToPerson(personId) {
            if (personId) {
                this.navigateToPerson(personId);
                // Reset the select
                const select = event.target;
                select.value = '';
            }
        },
        
        setupKeyboardShortcuts() {
            let currentPersonIndex = -1;
            const visibleCards = () => Array.from(document.querySelectorAll('.person-card:not([style*="display: none"])'));
            
            document.addEventListener('keydown', (e) => {
                // Don't interfere if user is typing in an input
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
                    return;
                }
                
                const cards = visibleCards();
                
                switch(e.key) {
                    case '/':
                        e.preventDefault();
                        document.getElementById('search-box').focus();
                        break;
                        
                    case 'ArrowRight':
                    case 'ArrowDown':
                        e.preventDefault();
                        if (cards.length > 0) {
                            currentPersonIndex = Math.min(currentPersonIndex + 1, cards.length - 1);
                            this.highlightPerson(cards[currentPersonIndex]);
                        }
                        break;
                        
                    case 'ArrowLeft':
                    case 'ArrowUp':
                        e.preventDefault();
                        if (cards.length > 0) {
                            currentPersonIndex = Math.max(currentPersonIndex - 1, 0);
                            this.highlightPerson(cards[currentPersonIndex]);
                        }
                        break;
                        
                    case 'Enter':
                        e.preventDefault();
                        if (currentPersonIndex >= 0 && cards[currentPersonIndex]) {
                            this.showPersonDetails(cards[currentPersonIndex]);
                        }
                        break;
                        
                    case 'Escape':
                        e.preventDefault();
                        this.showModal = false;
                        this.clearPersonHighlight();
                        currentPersonIndex = -1;
                        break;
                        
                    case 'e':
                        e.preventDefault();
                        this.expandAll();
                        break;
                        
                    case 'c':
                        e.preventDefault();
                        this.collapseAll();
                        break;
                }
            });
        },
        
        highlightPerson(personCard) {
            // Clear previous highlights
            this.clearPersonHighlight();
            
            // Add highlight to current person
            personCard.classList.add('keyboard-highlighted');
            personCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Update breadcrumbs
            this.updateBreadcrumbs(personCard);
        },
        
        clearPersonHighlight() {
            document.querySelectorAll('.keyboard-highlighted').forEach(card => {
                card.classList.remove('keyboard-highlighted');
            });
        },
        
        applyAdvancedFilters() {
            this.countActiveFilters();
            
            document.querySelectorAll('.person-card').forEach(card => {
                let show = true;
                
                const birthYear = parseInt(card.dataset.birthYear) || null;
                const deathYear = parseInt(card.dataset.deathYear) || null;
                const gender = card.dataset.gender || '';
                
                // Get birth and death places from card content
                const birthPlace = card.querySelector('.birth-place')?.textContent.replace('Born: ', '') || '';
                const deathPlace = card.querySelector('.death-place')?.textContent.replace('Died: ', '') || '';
                
                // Year range filter
                if (this.filters.yearFrom && birthYear && birthYear < parseInt(this.filters.yearFrom)) {
                    show = false;
                }
                if (this.filters.yearTo && birthYear && birthYear > parseInt(this.filters.yearTo)) {
                    show = false;
                }
                
                // Location filter
                if (this.filters.location) {
                    const locationQuery = this.filters.location.toLowerCase();
                    const hasLocationMatch = birthPlace.toLowerCase().includes(locationQuery) || 
                                           deathPlace.toLowerCase().includes(locationQuery);
                    if (!hasLocationMatch) {
                        show = false;
                    }
                }
                
                // Living/deceased status filter
                if (this.filters.livingStatus) {
                    const isDeceased = deathYear || card.dataset.deathYear;
                    if (this.filters.livingStatus === 'living' && isDeceased) {
                        show = false;
                    } else if (this.filters.livingStatus === 'deceased' && !isDeceased) {
                        show = false;
                    }
                }
                
                // Gender filter
                if (this.filters.gender && gender !== this.filters.gender) {
                    show = false;
                }
                
                // Show/hide card and containers
                const cardContainer = card.closest('.child-branch') || card.closest('.spouse') || card.parentElement;
                if (show) {
                    card.style.display = '';
                    if (cardContainer) cardContainer.style.display = '';
                    
                    const familyUnit = card.closest('.family-unit, .descendant-unit');
                    if (familyUnit) familyUnit.style.display = '';
                    
                    const familyTree = card.closest('.family-tree');
                    if (familyTree) familyTree.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
            
            // Also apply current search if active
            if (this.searchQuery.trim() !== '') {
                this.filterPeople();
            }
        },
        
        clearAdvancedFilters() {
            this.filters = {
                yearFrom: '',
                yearTo: '',
                location: '',
                livingStatus: '',
                gender: ''
            };
            this.activeFilters = 0;
            
            // Show all cards
            document.querySelectorAll('.person-card').forEach(card => {
                card.style.display = '';
                const cardContainer = card.closest('.child-branch') || card.closest('.spouse') || card.parentElement;
                if (cardContainer) cardContainer.style.display = '';
                
                const familyUnit = card.closest('.family-unit, .descendant-unit');
                if (familyUnit) familyUnit.style.display = '';
                
                const familyTree = card.closest('.family-tree');
                if (familyTree) familyTree.style.display = '';
            });
            
            // Reapply search if active
            if (this.searchQuery.trim() !== '') {
                this.filterPeople();
            }
        },
        
        countActiveFilters() {
            this.activeFilters = Object.values(this.filters).filter(value => value !== '').length;
        },
        
        initializeSidebarData() {
            // Calculate stats
            this.totalPeople = document.querySelectorAll('.person-card').length;
            this.totalFamilies = document.querySelectorAll('.family-unit').length;
            
            // Calculate generations
            const generationElements = document.querySelectorAll('[data-generation]');
            const generationNumbers = Array.from(generationElements).map(el => parseInt(el.dataset.generation) || 0);
            this.generations = generationNumbers.length > 0 ? Math.max(...generationNumbers) : 0;
            
            // Build family list
            this.familyList = [];
            document.querySelectorAll('.family-unit').forEach(familyUnit => {
                const familyId = familyUnit.dataset.familyId;
                const parents = [];
                const children = [];
                
                // Get parents
                const husbandCard = familyUnit.querySelector('.person-card.husband');
                const wifeCard = familyUnit.querySelector('.person-card.wife');
                
                if (husbandCard) parents.push(husbandCard.dataset.personName);
                if (wifeCard) parents.push(wifeCard.dataset.personName);
                
                // Get children
                const childCards = familyUnit.querySelectorAll('.person-card.child');
                childCards.forEach(child => {
                    children.push(child.dataset.personName);
                });
                
                // Get marriage year
                const marriageInfo = familyUnit.querySelector('.marriage-date');
                const marriageYear = marriageInfo ? marriageInfo.textContent.replace('m. ', '').split(' ').pop() : '';
                
                if (parents.length > 0) {
                    this.familyList.push({
                        id: familyId,
                        parents: parents,
                        children: children,
                        marriageYear: marriageYear
                    });
                }
            });
        },
        
        changeViewMode(mode) {
            this.currentViewMode = mode;
            if (mode === 'full') {
                this.focusPersonId = '';
                this.focusPerson = null;
            }
            this.applyViewMode();
        },
        
        setFocusPerson(personId) {
            this.focusPersonId = personId;
            this.updateFocusPerson();
        },
        
        updateFocusPerson() {
            if (this.focusPersonId) {
                const personCard = document.querySelector(`[data-person-id="${this.focusPersonId}"]`);
                if (personCard) {
                    this.focusPerson = {
                        id: this.focusPersonId,
                        name: personCard.dataset.personName,
                        generation: parseInt(personCard.dataset.generation) || 1
                    };
                } else {
                    this.focusPerson = null;
                }
            } else {
                this.focusPerson = null;
            }
            this.applyViewMode();
        },
        
        applyViewMode() {
            // Reset all visibility first
            document.querySelectorAll('.family-unit, .descendant-unit, .person-card').forEach(el => {
                el.style.display = '';
            });
            
            if (this.currentViewMode === 'full') {
                // Show everything
                return;
            }
            
            if (!this.focusPerson) {
                // Need a focus person for specialized views
                return;
            }
            
            const focusCard = document.querySelector(`[data-person-id="${this.focusPersonId}"]`);
            if (!focusCard) return;
            
            // Hide all elements first
            document.querySelectorAll('.family-unit, .descendant-unit, .person-card').forEach(el => {
                el.style.display = 'none';
            });
            
            switch (this.currentViewMode) {
                case 'pedigree':
                    this.showPedigreeView(focusCard);
                    break;
                case 'descendant':
                    this.showDescendantView(focusCard);
                    break;
                case 'hourglass':
                    this.showHourglassView(focusCard);
                    break;
            }
        },
        
        showPedigreeView(focusCard) {
            // Show the focus person
            this.showPersonAndContainers(focusCard);
            
            // Walk up the family tree to show ancestors
            let currentPerson = focusCard;
            const visited = new Set();
            
            while (currentPerson && !visited.has(currentPerson.dataset.personId)) {
                visited.add(currentPerson.dataset.personId);
                
                // Find the family unit where this person is a child
                const childFamily = this.findFamilyWhereChild(currentPerson.dataset.personId);
                if (childFamily) {
                    this.showElementAndContainers(childFamily);
                    
                    // Show parents in this family
                    const parents = childFamily.querySelectorAll('.person-card.husband, .person-card.wife');
                    parents.forEach(parent => {
                        this.showPersonAndContainers(parent);
                    });
                    
                    // Move up to one of the parents (prefer father, then mother)
                    const father = childFamily.querySelector('.person-card.husband');
                    const mother = childFamily.querySelector('.person-card.wife');
                    currentPerson = father || mother;
                } else {
                    break;
                }
            }
        },
        
        showDescendantView(focusCard) {
            // Show the focus person
            this.showPersonAndContainers(focusCard);
            
            // Show all descendants
            this.showDescendantsRecursive(focusCard.dataset.personId, new Set());
        },
        
        showHourglassView(focusCard) {
            // Show both ancestors (pedigree) and descendants
            this.showPedigreeView(focusCard);
            this.showDescendantsRecursive(focusCard.dataset.personId, new Set());
        },
        
        showDescendantsRecursive(personId, visited) {
            if (visited.has(personId)) return;
            visited.add(personId);
            
            // Find families where this person is a spouse
            const spouseFamilies = this.findFamiliesWhereSpouse(personId);
            
            spouseFamilies.forEach(family => {
                this.showElementAndContainers(family);
                
                // Show spouse
                const spouse = this.findSpouseInFamily(family, personId);
                if (spouse) {
                    this.showPersonAndContainers(spouse);
                }
                
                // Show and recurse through children
                const children = family.querySelectorAll('.person-card.child');
                children.forEach(child => {
                    this.showPersonAndContainers(child);
                    this.showDescendantsRecursive(child.dataset.personId, visited);
                });
            });
        },
        
        findFamilyWhereChild(personId) {
            // Find family unit where this person appears as a child
            const childCards = document.querySelectorAll(`.person-card.child[data-person-id="${personId}"]`);
            for (let card of childCards) {
                const familyUnit = card.closest('.family-unit');
                if (familyUnit) return familyUnit;
            }
            return null;
        },
        
        findFamiliesWhereSpouse(personId) {
            // Find all family units where this person is husband or wife
            const families = [];
            const spouseCards = document.querySelectorAll(`.person-card.husband[data-person-id="${personId}"], .person-card.wife[data-person-id="${personId}"]`);
            
            spouseCards.forEach(card => {
                const familyUnit = card.closest('.family-unit, .descendant-unit');
                if (familyUnit && !families.includes(familyUnit)) {
                    families.push(familyUnit);
                }
            });
            
            return families;
        },
        
        findSpouseInFamily(familyUnit, personId) {
            // Find the spouse of the given person in this family
            const husband = familyUnit.querySelector('.person-card.husband');
            const wife = familyUnit.querySelector('.person-card.wife');
            
            if (husband && husband.dataset.personId === personId) {
                return wife;
            } else if (wife && wife.dataset.personId === personId) {
                return husband;
            }
            return null;
        },
        
        showPersonAndContainers(personCard) {
            if (!personCard) return;
            
            personCard.style.display = '';
            
            // Show containing elements
            const containers = ['child-branch', 'spouse', 'parents', 'children-container', 'children-list'];
            containers.forEach(className => {
                const container = personCard.closest(`.${className}`);
                if (container) container.style.display = '';
            });
        },
        
        showElementAndContainers(element) {
            if (!element) return;
            
            element.style.display = '';
            
            // Show parent containers
            const familyTree = element.closest('.family-tree');
            if (familyTree) familyTree.style.display = '';
            
            const orphanedContainer = element.closest('.orphaned-individuals');
            if (orphanedContainer) orphanedContainer.style.display = '';
        },
        
        navigateToFamily(familyId) {
            const familyUnit = document.querySelector(`[data-family-id="${familyId}"]`);
            if (familyUnit) {
                familyUnit.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                // Highlight family temporarily
                familyUnit.style.transition = 'all 0.3s';
                familyUnit.style.boxShadow = '0 0 20px rgba(231, 76, 60, 0.6)';
                familyUnit.style.borderRadius = '10px';
                setTimeout(() => {
                    familyUnit.style.boxShadow = '';
                    familyUnit.style.borderRadius = '';
                }, 3000);
            }
        },
        
        toggleDarkMode() {
            this.isDarkMode = !this.isDarkMode;
            localStorage.setItem('ftree-dark-mode', this.isDarkMode.toString());
            this.applyTheme();
        },
        
        applyTheme() {
            const html = document.documentElement;
            if (this.isDarkMode) {
                html.setAttribute('data-theme', 'dark');
            } else {
                html.removeAttribute('data-theme');
            }
        }
    }
}
"""
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
            </div>
        </header>
        
        <main class="ftree-main">
            {self._generate_tree_content(root_families)}
        </main>
        
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
        {self._generate_javascript()}
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
        
        /* Generation filter */
        select {
            padding: 10px;
            border: 2px solid var(--border-color);
            border-radius: 5px;
            font-size: 14px;
            background-color: white;
            cursor: pointer;
            transition: border-color 0.3s ease;
        }
        
        select:focus {
            outline: none;
            border-color: var(--secondary-color);
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
        }
        
        /* Print styles */
        @media print {
            .ftree-controls {
                display: none;
            }
            
            .person-card {
                break-inside: avoid;
                box-shadow: none;
                border: 1px solid #000;
            }
            
            .family-tree {
                break-inside: avoid;
                box-shadow: none;
                border: 1px solid #ccc;
            }
            
            .toggle-children {
                display: none;
            }
            
            .children-list {
                display: block !important;
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
        
        init() {
            // Initialize all families as expanded
            document.querySelectorAll('.toggle-children').forEach(button => {
                const familyId = button.dataset.familyId;
                this.expandedFamilies.add(familyId);
            });
            
            // Set up toggle buttons
            this.setupToggleButtons();
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
                
                // Highlight the person temporarily
                personCard.style.transition = 'all 0.3s';
                personCard.style.boxShadow = '0 0 20px rgba(52, 152, 219, 0.8)';
                setTimeout(() => {
                    personCard.style.boxShadow = '';
                }, 2000);
            }
        }
    }
}
"""
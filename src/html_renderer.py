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
                <input type="search" x-model="searchQuery" @input="filterPeople()" placeholder="Search names...">
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
                        <div x-show="selectedPerson.notes" class="info-row">
                            <strong>Notes:</strong> <p x-text="selectedPerson.notes"></p>
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
                content_parts.append(f'<div class="family-tree">{family_tree}</div>')
        
        # Render any remaining unconnected individuals
        orphans = self._find_orphaned_individuals()
        if orphans:
            orphan_content = '<div class="orphaned-individuals">'
            orphan_content += '<h2>Unconnected Individuals</h2>'
            orphan_content += '<ul class="orphan-list">'
            for individual in orphans:
                orphan_content += f'<li>{self._render_person_card(individual)}</li>'
            orphan_content += '</ul></div>'
            content_parts.append(orphan_content)
        
        return '\n'.join(content_parts)
    
    def _render_family_tree(self, family: Family) -> str:
        """Render a family and their descendants as HTML tree."""
        if not family:
            return ""
        
        family_html = f'<div class="family-unit" data-family-id="{html.escape(family.id)}">'
        
        # Parents section
        parents_html = self._render_parents(family)
        if parents_html:
            family_html += f'<div class="parents">{parents_html}</div>'
        
        # Children section
        children_html = self._render_children(family)
        if children_html:
            family_html += f'<div class="children">{children_html}</div>'
        
        family_html += '</div>'
        
        return family_html
    
    def _render_parents(self, family: Family) -> str:
        """Render the parent couple."""
        parents = []
        
        try:
            if family.husband_id:
                husband = self.tree.get_individual(family.husband_id)
                if husband and husband.id not in self.rendered_individuals:
                    parents.append(self._render_person_card(husband, "husband"))
                    self.rendered_individuals.add(husband.id)
            
            if family.wife_id:
                wife = self.tree.get_individual(family.wife_id)
                if wife and wife.id not in self.rendered_individuals:
                    parents.append(self._render_person_card(wife, "wife"))
                    self.rendered_individuals.add(wife.id)
        except (AttributeError, KeyError) as e:
            # Handle missing or corrupt individual data
            print(f"Warning: Error rendering parents for family {family.id}: {e}")
        
        if not parents:
            return ""
        
        parents_html = f'<div class="couple" data-family-id="{html.escape(family.id)}">'
        parents_html += '\n'.join(parents)
        
        # Add marriage info
        if family.marriage_date or family.marriage_place:
            marriage_info = '<div class="marriage-info">'
            if family.marriage_date:
                marriage_info += f'<span class="marriage-date">m. {html.escape(family.marriage_date)}</span>'
            if family.marriage_place:
                marriage_info += f'<span class="marriage-place">in {html.escape(family.marriage_place)}</span>'
            marriage_info += '</div>'
            parents_html += marriage_info
        
        parents_html += '</div>'
        return parents_html
    
    def _render_children(self, family: Family) -> str:
        """Render the children of a family."""
        if not family.children_ids:
            return ""
        
        children_html = f'<div class="children-container" data-parent-family="{html.escape(family.id)}">'
        children_html += f'<button class="toggle-children" data-expanded="true" data-family-id="{html.escape(family.id)}">▼ Children</button>'
        children_html += '<div class="children-list">'
        
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
                child_html = f'<div class="child-branch" data-child-id="{html.escape(child.id)}">{self._render_person_card(child, "child")}'
                self.rendered_individuals.add(child.id)
                
                # Render child's own families
                try:
                    for spouse_family_id in child.family_spouse:
                        spouse_family = self.tree.get_family(spouse_family_id)
                        if spouse_family:
                            child_family_tree = self._render_descendant_family(spouse_family, child)
                            if child_family_tree:
                                child_html += f'<div class="descendant-family">{child_family_tree}</div>'
                except (AttributeError, KeyError, TypeError) as e:
                    print(f"Warning: Error rendering child's families for {child.id}: {e}")
                
                child_html += '</div>'
                children_html += child_html
        
        children_html += '</div></div>'
        return children_html
    
    def _render_descendant_family(self, family: Family, known_parent: Individual) -> str:
        """Render a family where we already know one parent."""
        family_html = f'<div class="descendant-unit" data-family-id="{html.escape(family.id)}">'
        
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
                    family_html += f'<div class="spouse">{self._render_person_card(spouse, spouse_role)}</div>'
                    self.rendered_individuals.add(spouse_id)
            except (AttributeError, KeyError) as e:
                print(f"Warning: Could not find spouse {spouse_id}: {e}")
        
        # Render children
        children_html = self._render_children(family)
        if children_html:
            family_html += children_html
        
        family_html += '</div>'
        return family_html
    
    def _render_person_card(self, individual: Individual, role: str = "") -> str:
        """Render an individual as an HTML card."""
        if not individual:
            return '<div class="person-card error">Missing Individual</div>'
        
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
        notes = getattr(individual, 'notes', '') or ''
        
        card_html = f'''<div class="{card_classes}" 
            data-person-id="{html.escape(individual.id)}"
            data-person-name="{name}"
            data-birth-year="{birth_year}"
            data-death-year="{death_year}"
            data-gender="{gender}"
            data-role="{role}"
            data-occupation="{html.escape(occupation)}"
            data-notes="{html.escape(notes)}"
            @click="showPersonDetails($el)">'''
        
        # Photo if available
        photo_html = self._render_person_photo(individual)
        if photo_html:
            card_html += photo_html
        
        # Name
        card_html += f'<h3 class="person-name">{name}</h3>'
        
        # Dates
        dates_html = self._render_person_dates(individual)
        if dates_html:
            card_html += dates_html
        
        # Places (if enabled)
        if self.include_places:
            places_html = self._render_person_places(individual)
            if places_html:
                card_html += places_html
        
        card_html += '</div>'
        return card_html
    
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
        }
        
        .parents {
            margin-bottom: 20px;
        }
        
        .couple {
            display: flex;
            justify-content: center;
            align-items: flex-start;
            gap: 20px;
            flex-wrap: wrap;
            margin-bottom: 15px;
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
        
        /* Children sections */
        .children-container {
            margin-top: 20px;
            border-top: 2px dashed var(--border-color);
            padding-top: 20px;
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
        }
        
        .child-branch {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 15px;
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
            const query = this.searchQuery.toLowerCase();
            document.querySelectorAll('.person-card').forEach(card => {
                const name = card.dataset.personName.toLowerCase();
                const birthYear = card.dataset.birthYear;
                const deathYear = card.dataset.deathYear;
                
                // Search in name and years
                const match = name.includes(query) || 
                             birthYear.includes(query) || 
                             deathYear.includes(query);
                
                // Show/hide card
                card.style.display = match || query === '' ? '' : 'none';
                
                // Highlight matches in name
                const nameElement = card.querySelector('.person-name');
                if (query && match && name.includes(query)) {
                    const regex = new RegExp(`(${query})`, 'gi');
                    const originalText = nameElement.textContent;
                    nameElement.innerHTML = originalText.replace(regex, '<mark>$1</mark>');
                } else {
                    nameElement.innerHTML = nameElement.textContent;
                }
            });
        },
        
        filterByGeneration(generation) {
            this.generationFilter = generation;
            // This would require generation data in the cards
            // For now, it's a placeholder for future enhancement
            console.log('Filter by generation:', generation);
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
"""HTML renderer for family trees."""

import html
from typing import List, Set, Optional, Dict
from .models import FamilyTree, Individual, Family


class HtmlRenderer:
    """Render family trees as interactive HTML."""
    
    def __init__(self, tree: FamilyTree):
        self.tree = tree
        self.rendered_individuals: Set[str] = set()
    
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
        
        # Find root families
        root_families = self._find_root_families()
        
        # Generate HTML structure
        html_content = self._generate_html_document(root_families, theme, title)
        
        return html_content
    
    def _generate_html_document(self, root_families: List[Family], theme: str, title: str) -> str:
        """Generate the complete HTML document."""
        css_link = f'<link rel="stylesheet" href="ftree-{theme}.css">'
        
        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    {css_link}
</head>
<body>
    <div class="ftree-container">
        <header class="ftree-header">
            <h1>{html.escape(title)}</h1>
            <div class="ftree-controls">
                <button id="expand-all">Expand All</button>
                <button id="collapse-all">Collapse All</button>
                <input type="search" id="search-box" placeholder="Search names...">
            </div>
        </header>
        
        <main class="ftree-main">
            {self._generate_tree_content(root_families)}
        </main>
        
        <div id="person-modal" class="modal">
            <div class="modal-content">
                <span class="close">&times;</span>
                <div id="person-details"></div>
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
        
        family_html = '<div class="family-unit">'
        
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
        
        if not parents:
            return ""
        
        parents_html = '<div class="couple">'
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
        
        children_html = '<div class="children-container">'
        children_html += '<button class="toggle-children" data-expanded="true">▼ Children</button>'
        children_html += '<div class="children-list">'
        
        # Sort children by birth year
        children = []
        for child_id in family.children_ids:
            child = self.tree.get_individual(child_id)
            if child:
                children.append(child)
        
        children.sort(key=lambda c: c.get_birth_year() or 9999)
        
        for child in children:
            if child.id not in self.rendered_individuals:
                child_html = f'<div class="child-branch">{self._render_person_card(child, "child")}'
                self.rendered_individuals.add(child.id)
                
                # Render child's own families
                for spouse_family_id in child.family_spouse:
                    spouse_family = self.tree.get_family(spouse_family_id)
                    if spouse_family:
                        child_family_tree = self._render_descendant_family(spouse_family, child)
                        if child_family_tree:
                            child_html += f'<div class="descendant-family">{child_family_tree}</div>'
                
                child_html += '</div>'
                children_html += child_html
        
        children_html += '</div></div>'
        return children_html
    
    def _render_descendant_family(self, family: Family, known_parent: Individual) -> str:
        """Render a family where we already know one parent."""
        family_html = '<div class="descendant-unit">'
        
        # Find and render spouse
        spouse_id = None
        if family.husband_id == known_parent.id:
            spouse_id = family.wife_id
        elif family.wife_id == known_parent.id:
            spouse_id = family.husband_id
        
        if spouse_id:
            spouse = self.tree.get_individual(spouse_id)
            if spouse:
                spouse_role = "wife" if family.husband_id == known_parent.id else "husband"
                family_html += f'<div class="spouse">{self._render_person_card(spouse, spouse_role)}</div>'
                self.rendered_individuals.add(spouse_id)
        
        # Render children
        children_html = self._render_children(family)
        if children_html:
            family_html += children_html
        
        family_html += '</div>'
        return family_html
    
    def _render_person_card(self, individual: Individual, role: str = "") -> str:
        """Render an individual as an HTML card."""
        card_classes = f"person-card {role}".strip()
        
        name = html.escape(individual.name or individual.id)
        card_html = f'<div class="{card_classes}" data-person-id="{html.escape(individual.id)}">'
        
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
        if not individual.birth_date and not individual.death_date:
            return ""
        
        dates_html = '<div class="person-dates">'
        
        if individual.birth_date:
            dates_html += f'<span class="birth-date">b. {html.escape(individual.birth_date)}</span>'
        
        if individual.death_date:
            if individual.birth_date:
                dates_html += ' – '
            dates_html += f'<span class="death-date">d. {html.escape(individual.death_date)}</span>'
        
        dates_html += '</div>'
        return dates_html
    
    def _render_person_places(self, individual: Individual) -> str:
        """Render birth and death places."""
        if not individual.birth_place and not individual.death_place:
            return ""
        
        places_html = '<div class="person-places">'
        
        if individual.birth_place:
            places_html += f'<span class="birth-place">Born: {html.escape(individual.birth_place)}</span>'
        
        if individual.death_place:
            if individual.birth_place:
                places_html += '<br>'
            places_html += f'<span class="death-place">Died: {html.escape(individual.death_place)}</span>'
        
        places_html += '</div>'
        return places_html
    
    def _find_root_families(self) -> List[Family]:
        """Find families where at least one parent has no parents."""
        root_families = []
        
        for family in self.tree.families.values():
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
        
        return root_families
    
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
        """Generate JavaScript for interactivity."""
        return """
// Family tree interactivity
document.addEventListener('DOMContentLoaded', function() {
    // Toggle children visibility
    document.querySelectorAll('.toggle-children').forEach(button => {
        button.addEventListener('click', function() {
            const isExpanded = this.dataset.expanded === 'true';
            const childrenList = this.nextElementSibling;
            
            if (isExpanded) {
                childrenList.style.display = 'none';
                this.textContent = '▶ Children';
                this.dataset.expanded = 'false';
            } else {
                childrenList.style.display = 'block';
                this.textContent = '▼ Children';
                this.dataset.expanded = 'true';
            }
        });
    });
    
    // Expand/Collapse all controls
    document.getElementById('expand-all')?.addEventListener('click', function() {
        document.querySelectorAll('.toggle-children').forEach(button => {
            const childrenList = button.nextElementSibling;
            childrenList.style.display = 'block';
            button.textContent = '▼ Children';
            button.dataset.expanded = 'true';
        });
    });
    
    document.getElementById('collapse-all')?.addEventListener('click', function() {
        document.querySelectorAll('.toggle-children').forEach(button => {
            const childrenList = button.nextElementSibling;
            childrenList.style.display = 'none';
            button.textContent = '▶ Children';
            button.dataset.expanded = 'false';
        });
    });
    
    // Search functionality
    const searchBox = document.getElementById('search-box');
    if (searchBox) {
        searchBox.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            document.querySelectorAll('.person-card').forEach(card => {
                const name = card.querySelector('.person-name').textContent.toLowerCase();
                const match = name.includes(query);
                card.style.display = match || query === '' ? 'block' : 'none';
                
                // Highlight matches
                const nameElement = card.querySelector('.person-name');
                if (query && match) {
                    const regex = new RegExp(`(${query})`, 'gi');
                    nameElement.innerHTML = nameElement.textContent.replace(regex, '<mark>$1</mark>');
                } else {
                    nameElement.innerHTML = nameElement.textContent;
                }
            });
        });
    }
    
    // Person card click for detailed view
    document.querySelectorAll('.person-card').forEach(card => {
        card.addEventListener('click', function() {
            const personId = this.dataset.personId;
            showPersonDetails(personId);
        });
    });
    
    // Modal functionality
    const modal = document.getElementById('person-modal');
    const closeBtn = document.querySelector('.close');
    
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            modal.style.display = 'none';
        });
    }
    
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});

function showPersonDetails(personId) {
    // This would be populated with detailed person information
    const modal = document.getElementById('person-modal');
    const detailsDiv = document.getElementById('person-details');
    
    // For now, just show basic info
    const personCard = document.querySelector(`[data-person-id="${personId}"]`);
    if (personCard) {
        detailsDiv.innerHTML = '<h2>Person Details</h2>' + personCard.innerHTML;
        modal.style.display = 'block';
    }
}
"""
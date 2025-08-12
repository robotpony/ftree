"""ASCII tree renderer for family trees."""

from typing import List, Set, Optional
from .models import FamilyTree, Individual, Family


class AsciiRenderer:
    """Render family trees in ASCII format."""
    
    def __init__(self, tree: FamilyTree):
        self.tree = tree
        self.rendered_individuals: Set[str] = set()
    
    def render(self, show_places: bool = False, show_marriage: bool = False) -> str:
        """Render the complete family tree.
        
        Args:
            show_places: Include birth/death places in output
            show_marriage: Include marriage dates in output
        """
        self.show_places = show_places
        self.show_marriage = show_marriage
        self.rendered_individuals = set()  # Reset for each render
        output = []
        
        # Find root families (where at least one parent has no parents)
        root_families = self._find_root_families()
        
        # Render each root family
        for family in root_families:
            family_output = self._render_family_tree(family, "", True)
            if family_output:
                output.append(family_output)
        
        # Render any remaining unconnected individuals
        for individual in self.tree.individuals.values():
            if individual.id not in self.rendered_individuals:
                output.append(self._format_individual(individual))
                self.rendered_individuals.add(individual.id)
        
        return "\n".join(output)
    
    def _find_root_families(self) -> List[Family]:
        """Find root families (where parents have no parents)."""
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
    
    def _render_family_tree(self, family: Family, prefix: str, is_root: bool) -> str:
        """Render a family and their descendants."""
        lines = []
        
        # Format parents line
        parent_parts = []
        if family.husband_id:
            husband = self.tree.get_individual(family.husband_id)
            if husband and husband.id not in self.rendered_individuals:
                parent_parts.append(self._format_individual(husband))
                self.rendered_individuals.add(husband.id)
        
        if family.wife_id:
            wife = self.tree.get_individual(family.wife_id)
            if wife and wife.id not in self.rendered_individuals:
                if parent_parts:
                    parent_parts.append("+")
                parent_parts.append(self._format_individual(wife))
                self.rendered_individuals.add(wife.id)
        
        if parent_parts:
            parent_line = " ".join(parent_parts)
            if self.show_marriage and family.marriage_date:
                parent_line += f" (m. {family.marriage_date})"
            lines.append(prefix + parent_line)
        
        # Render children
        if family.children_ids:
            for i, child_id in enumerate(family.children_ids):
                child = self.tree.get_individual(child_id)
                if not child or child.id in self.rendered_individuals:
                    continue
                
                is_last_child = (i == len(family.children_ids) - 1)
                child_prefix = prefix + ("└── " if is_last_child else "├── ")
                continuation = prefix + ("    " if is_last_child else "│   ")
                
                # Show the child
                lines.append(child_prefix + self._format_individual(child))
                self.rendered_individuals.add(child_id)
                
                # Render child's families
                for child_family_id in child.family_spouse:
                    child_family = self.tree.get_family(child_family_id)
                    if child_family:
                        family_lines = self._render_descendant_family(child_family, child, continuation)
                        lines.extend(family_lines)
        
        return "\n".join(lines) if lines else ""
    
    def _render_descendant_family(self, family: Family, known_parent: Individual, prefix: str) -> List[str]:
        """Render a family where we already know one parent."""
        lines = []
        
        # Find the spouse
        spouse_id = None
        if family.husband_id == known_parent.id:
            spouse_id = family.wife_id
        elif family.wife_id == known_parent.id:
            spouse_id = family.husband_id
        
        if spouse_id:
            spouse = self.tree.get_individual(spouse_id)
            if spouse:
                spouse_line = prefix + "+ " + self._format_individual(spouse)
                if self.show_marriage and family.marriage_date:
                    spouse_line += f" (m. {family.marriage_date})"
                lines.append(spouse_line)
                self.rendered_individuals.add(spouse_id)
        
        # Render children of this family
        for i, child_id in enumerate(family.children_ids):
            child = self.tree.get_individual(child_id)
            if not child:
                continue
            
            is_last = (i == len(family.children_ids) - 1)
            if is_last:
                child_prefix = prefix + "    └── "
            else:
                child_prefix = prefix + "    ├── "
            
            lines.append(child_prefix + self._format_individual(child))
            self.rendered_individuals.add(child_id)
        
        return lines
    
    
    def _format_individual(self, individual: Individual) -> str:
        """Format an individual's display string."""
        name = individual.name or individual.id
        
        # Build date string
        date_parts = []
        if individual.birth_date or individual.death_date:
            if individual.birth_date and individual.death_date:
                # Both birth and death
                date_parts.append(f"({individual.birth_date} - {individual.death_date})")
            elif individual.birth_date:
                # Only birth date
                date_parts.append(f"(b. {individual.birth_date})")
            elif individual.death_date:
                # Only death date  
                date_parts.append(f"(d. {individual.death_date})")
        
        # Add places if requested
        place_parts = []
        if self.show_places:
            if individual.birth_place:
                place_parts.append(f"born: {individual.birth_place}")
            if individual.death_place:
                place_parts.append(f"died: {individual.death_place}")
        
        # Combine all parts
        result = name
        if date_parts:
            result += " " + date_parts[0]
        if place_parts:
            result += " [" + "; ".join(place_parts) + "]"
        
        return result
    
    def _extract_year(self, date_str: Optional[str]) -> Optional[str]:
        """Extract year from a date string."""
        if not date_str:
            return None
        
        # Handle various date formats
        parts = date_str.split()
        for part in reversed(parts):
            if part.isdigit() and len(part) == 4:
                return part
        
        return None
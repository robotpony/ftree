"""Family-grouped output formatter for GEDCOM data."""

from typing import List, Dict
from .models import FamilyTree, Individual, Family


class FamilyFormatter:
    """Format family tree data with families grouped together."""
    
    def __init__(self, tree: FamilyTree):
        self.tree = tree
    
    def format_grouped_families(self) -> str:
        """Format all families as grouped units with sorted children."""
        output = []
        
        family_groups = self.tree.get_all_family_groups()
        
        for group in family_groups:
            family_text = self._format_family_group(group)
            if family_text:
                output.append(family_text)
        
        # Add orphaned individuals (not in any family)
        orphans = self._find_orphaned_individuals(family_groups)
        if orphans:
            output.append("\n## Individuals not in families:")
            for individual in orphans:
                output.append(f"- {self._format_individual(individual)}")
        
        return "\n\n".join(output)
    
    def _format_family_group(self, group: Dict) -> str:
        """Format a single family group."""
        family = group['family']
        husband = group['husband']
        wife = group['wife']
        children = group['children']
        
        lines = []
        
        # Family header
        parents = []
        if husband:
            parents.append(self._format_individual(husband))
        if wife:
            parents.append(self._format_individual(wife))
        
        if parents:
            parent_line = " + ".join(parents)
            if family.marriage_date:
                parent_line += f" (married {family.marriage_date})"
            lines.append(f"## Family {family.id}: {parent_line}")
        else:
            lines.append(f"## Family {family.id}")
        
        # Marriage info
        if family.marriage_place:
            lines.append(f"**Marriage place:** {family.marriage_place}")
        
        # Engagement info
        if family.engagement_date:
            lines.append(f"**Engagement date:** {family.engagement_date}")
        
        # Divorce info
        if family.divorce_date:
            lines.append(f"**Divorce date:** {family.divorce_date}")
        
        # Children (already sorted by birth year)
        if children:
            lines.append("**Children:**")
            for i, child in enumerate(children, 1):
                lines.append(f"{i}. {self._format_individual(child)}")
        else:
            lines.append("**Children:** None")
        
        return "\n".join(lines)
    
    def _format_individual(self, individual: Individual) -> str:
        """Format an individual's information."""
        name = individual.name or individual.id
        
        details = []
        if individual.birth_date:
            birth_info = f"b. {individual.birth_date}"
            if individual.birth_place:
                birth_info += f" in {individual.birth_place}"
            details.append(birth_info)
        
        if individual.death_date:
            death_info = f"d. {individual.death_date}"
            if individual.death_place:
                death_info += f" in {individual.death_place}"
            details.append(death_info)
        
        # Add occupation if available
        if individual.occupation:
            details.append(f"occupation: {individual.occupation}")
        
        # Add notes count if available
        if individual.notes:
            details.append(f"{len(individual.notes)} note(s)")
        
        if details:
            return f"{name} ({'; '.join(details)})"
        else:
            return name
    
    def _find_orphaned_individuals(self, family_groups: List[Dict]) -> List[Individual]:
        """Find individuals not referenced in any family."""
        referenced_ids = set()
        
        # Collect all individuals referenced in families
        for group in family_groups:
            if group['husband']:
                referenced_ids.add(group['husband'].id)
            if group['wife']:
                referenced_ids.add(group['wife'].id)
            for child in group['children']:
                referenced_ids.add(child.id)
        
        # Find unreferenced individuals
        orphans = []
        for individual in self.tree.individuals.values():
            if individual.id not in referenced_ids:
                orphans.append(individual)
        
        # Sort orphans by name
        orphans.sort(key=lambda i: i.name)
        
        return orphans
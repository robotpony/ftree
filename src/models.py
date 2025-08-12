"""Data models for family tree representation."""

from typing import Optional, List, Dict


class Individual:
    """Represents a person in the family tree."""
    
    def __init__(self, id: str):
        self.id = id
        self.given_name: Optional[str] = None
        self.surname: Optional[str] = None
        self.sex: Optional[str] = None
        self.birth_date: Optional[str] = None
        self.birth_place: Optional[str] = None
        self.death_date: Optional[str] = None
        self.death_place: Optional[str] = None
        self.family_spouse: List[str] = []  # FAMS - families where spouse
        self.family_child: List[str] = []   # FAMC - families where child
        self.objects: List[str] = []  # URLs or other objects
    
    @property
    def name(self) -> str:
        """Get full name."""
        parts = []
        if self.given_name:
            parts.append(self.given_name)
        if self.surname:
            parts.append(self.surname)
        return " ".join(parts) if parts else self.id
    
    @property
    def lifespan(self) -> str:
        """Get birth-death date string."""
        if self.birth_date or self.death_date:
            birth = self._format_date(self.birth_date) if self.birth_date else "?"
            death = self._format_date(self.death_date) if self.death_date else ""
            if birth == "?" and death == "":
                return ""
            return f"({birth}-{death})"
        return ""
    
    def _format_date(self, date_str: str) -> str:
        """Format a date string for display."""
        if not date_str:
            return ""
        # For now, return the full date as-is
        # Can be customized later for different formats
        return date_str
    
    def __repr__(self) -> str:
        return f"Individual({self.id}, {self.name})"


class Family:
    """Represents a family unit."""
    
    def __init__(self, id: str):
        self.id = id
        self.husband_id: Optional[str] = None
        self.wife_id: Optional[str] = None
        self.children_ids: List[str] = []
        self.marriage_date: Optional[str] = None
        self.marriage_place: Optional[str] = None
    
    def __repr__(self) -> str:
        return f"Family({self.id}, H={self.husband_id}, W={self.wife_id}, C={len(self.children_ids)})"


class FamilyTree:
    """Container for all individuals and families."""
    
    def __init__(self):
        self.individuals: Dict[str, Individual] = {}
        self.families: Dict[str, Family] = {}
        self.submitter: Optional[Dict] = None
        self.header: Optional[Dict] = None
    
    def add_individual(self, individual: Individual):
        """Add an individual to the tree."""
        self.individuals[individual.id] = individual
    
    def add_family(self, family: Family):
        """Add a family to the tree."""
        self.families[family.id] = family
    
    def get_individual(self, id: str) -> Optional[Individual]:
        """Get individual by ID."""
        return self.individuals.get(id)
    
    def get_family(self, id: str) -> Optional[Family]:
        """Get family by ID."""
        return self.families.get(id)
    
    def get_roots(self) -> List[Individual]:
        """Find individuals with no parents (tree roots)."""
        roots = []
        for individual in self.individuals.values():
            if not individual.family_child:
                roots.append(individual)
        return roots
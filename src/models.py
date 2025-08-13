"""Data models for family tree representation."""

from typing import Optional, List, Dict
from datetime import datetime
import re


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
        self.occupation: Optional[str] = None  # OCCU
        self.religion: Optional[str] = None    # RELI
        self.education: Optional[str] = None   # EDUC
        self.notes: List[str] = []            # NOTE references
    
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
        # Extract year from common GEDCOM date formats
        year_match = re.search(r'\b(\d{4})\b', date_str)
        if year_match:
            return year_match.group(1)
        return date_str
    
    def get_birth_year(self) -> Optional[int]:
        """Extract birth year as integer for sorting."""
        if not self.birth_date:
            return None
        year_match = re.search(r'\b(\d{4})\b', self.birth_date)
        return int(year_match.group(1)) if year_match else None
    
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
        self.engagement_date: Optional[str] = None  # ENGA
        self.divorce_date: Optional[str] = None     # DIV
    
    def __repr__(self) -> str:
        return f"Family({self.id}, H={self.husband_id}, W={self.wife_id}, C={len(self.children_ids)})"


class Note:
    """Represents a note record in GEDCOM."""
    
    def __init__(self, id: str):
        self.id = id
        self.text: str = ""
        self.continuation: List[str] = []  # CONT/CONC lines
    
    @property
    def full_text(self) -> str:
        """Get the complete note text including continuations."""
        if not self.continuation:
            return self.text
        return self.text + " " + " ".join(self.continuation)
    
    def __repr__(self) -> str:
        return f"Note({self.id}, {len(self.full_text)} chars)"


class Source:
    """Represents a source record in GEDCOM."""
    
    def __init__(self, id: str):
        self.id = id
        self.title: Optional[str] = None      # TITL
        self.author: Optional[str] = None     # AUTH
        self.publication: Optional[str] = None # PUBL
        self.abbreviation: Optional[str] = None # ABBR
        self.text: Optional[str] = None       # TEXT
    
    def __repr__(self) -> str:
        return f"Source({self.id}, {self.title or 'No title'})"


class FamilyTree:
    """Container for all individuals and families."""
    
    def __init__(self):
        self.individuals: Dict[str, Individual] = {}
        self.families: Dict[str, Family] = {}
        self.notes: Dict[str, Note] = {}
        self.sources: Dict[str, Source] = {}
        self.submitter: Optional[Dict] = None
        self.header: Optional[Dict] = None
    
    def add_individual(self, individual: Individual):
        """Add an individual to the tree."""
        self.individuals[individual.id] = individual
    
    def add_family(self, family: Family):
        """Add a family to the tree."""
        self.families[family.id] = family
    
    def add_note(self, note: Note):
        """Add a note to the tree."""
        self.notes[note.id] = note
    
    def add_source(self, source: Source):
        """Add a source to the tree."""
        self.sources[source.id] = source
    
    def get_individual(self, id: str) -> Optional[Individual]:
        """Get individual by ID."""
        return self.individuals.get(id)
    
    def get_family(self, id: str) -> Optional[Family]:
        """Get family by ID."""
        return self.families.get(id)
    
    def get_note(self, id: str) -> Optional[Note]:
        """Get note by ID."""
        return self.notes.get(id)
    
    def get_source(self, id: str) -> Optional[Source]:
        """Get source by ID."""
        return self.sources.get(id)
    
    def get_roots(self) -> List[Individual]:
        """Find individuals with no parents (tree roots)."""
        roots = []
        for individual in self.individuals.values():
            if not individual.family_child:
                roots.append(individual)
        return roots
    
    def get_family_group(self, family_id: str) -> Dict:
        """Get a complete family group with all members."""
        family = self.get_family(family_id)
        if not family:
            return {}
        
        husband = self.get_individual(family.husband_id) if family.husband_id else None
        wife = self.get_individual(family.wife_id) if family.wife_id else None
        
        children = []
        for child_id in family.children_ids:
            child = self.get_individual(child_id)
            if child:
                children.append(child)
        
        # Sort children by birth year
        children.sort(key=lambda c: c.get_birth_year() or 9999)
        
        return {
            'family': family,
            'husband': husband,
            'wife': wife,
            'children': children
        }
    
    def get_all_family_groups(self) -> List[Dict]:
        """Get all families as grouped units."""
        groups = []
        for family_id in self.families.keys():
            group = self.get_family_group(family_id)
            if group:
                groups.append(group)
        return groups
    
    def get_field_values(self, field_name: str, unique: bool = True) -> List[str]:
        """Extract values for a specific field from all individuals and families."""
        values = []
        
        # Individual fields
        if field_name in ['given_name', 'surname', 'sex', 'birth_date', 'birth_place', 
                          'death_date', 'death_place']:
            for individual in self.individuals.values():
                value = getattr(individual, field_name, None)
                if value:
                    values.append(value)
        
        # Family fields
        elif field_name in ['marriage_date', 'marriage_place']:
            for family in self.families.values():
                value = getattr(family, field_name, None)
                if value:
                    values.append(value)
        
        # Special field: full names
        elif field_name == 'name':
            for individual in self.individuals.values():
                if individual.name and individual.name != individual.id:
                    values.append(individual.name)
        
        if unique:
            return sorted(list(set(values)))
        return values
    
    def get_all_places(self, unique: bool = True) -> List[str]:
        """Get all places (birth, death, marriage) from the tree."""
        places = []
        
        for individual in self.individuals.values():
            if individual.birth_place:
                places.append(individual.birth_place)
            if individual.death_place:
                places.append(individual.death_place)
        
        for family in self.families.values():
            if family.marriage_place:
                places.append(family.marriage_place)
        
        if unique:
            return sorted(list(set(places)))
        return places
    
    def get_all_dates(self, unique: bool = True) -> List[str]:
        """Get all dates (birth, death, marriage) from the tree."""
        dates = []
        
        for individual in self.individuals.values():
            if individual.birth_date:
                dates.append(individual.birth_date)
            if individual.death_date:
                dates.append(individual.death_date)
        
        for family in self.families.values():
            if family.marriage_date:
                dates.append(family.marriage_date)
        
        if unique:
            return sorted(list(set(dates)))
        return dates
    
    def get_field_with_individuals(self, field_name: str) -> Dict[str, List[Individual]]:
        """Get field values grouped with the individuals who have them."""
        grouped = {}
        
        for individual in self.individuals.values():
            value = None
            
            if field_name in ['given_name', 'surname', 'sex', 'birth_date', 'birth_place',
                             'death_date', 'death_place']:
                value = getattr(individual, field_name, None)
            elif field_name == 'name':
                value = individual.name if individual.name != individual.id else None
            elif field_name == 'places':
                # Add individual to all their associated places
                for place in [individual.birth_place, individual.death_place]:
                    if place:
                        if place not in grouped:
                            grouped[place] = []
                        grouped[place].append(individual)
                continue
            
            if value:
                if value not in grouped:
                    grouped[value] = []
                grouped[value].append(individual)
        
        # Handle family fields
        if field_name == 'marriage_place':
            for family in self.families.values():
                if family.marriage_place:
                    if family.marriage_place not in grouped:
                        grouped[family.marriage_place] = []
                    # Add both spouses to the marriage place
                    if family.husband_id:
                        husband = self.get_individual(family.husband_id)
                        if husband:
                            grouped[family.marriage_place].append(husband)
                    if family.wife_id:
                        wife = self.get_individual(family.wife_id)
                        if wife:
                            grouped[family.marriage_place].append(wife)
        
        return grouped
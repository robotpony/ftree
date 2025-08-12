"""GEDCOM file parser."""

import codecs
from typing import Optional, Tuple, List
from pathlib import Path
from .models import Individual, Family, FamilyTree


class GedcomParser:
    """Parse GEDCOM genealogy files."""
    
    def __init__(self):
        self.tree = FamilyTree()
        self.current_record = None
        self.current_type = None
    
    def parse_file(self, filepath: str) -> FamilyTree:
        """Parse a GEDCOM file and return a FamilyTree."""
        path = Path(filepath)
        
        # Detect encoding
        encoding = self._detect_encoding(path)
        
        # Read and parse lines
        with open(path, 'r', encoding=encoding) as f:
            lines = f.readlines()
        
        self._parse_lines(lines)
        
        # Save final record
        self._save_current_record()
        
        return self.tree
    
    def _detect_encoding(self, path: Path) -> str:
        """Detect file encoding (UTF-8 or UTF-16LE)."""
        with open(path, 'rb') as f:
            raw = f.read(2)
            if raw == b'\xff\xfe':  # UTF-16LE BOM
                return 'utf-16-le'
            return 'utf-8'
    
    def _parse_lines(self, lines: List[str]):
        """Parse all lines in the GEDCOM file."""
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            level, tag, value = self._parse_line(line)
            
            if level == 0:
                self._process_level0(tag, value)
            elif level == 1:
                self._process_level1(tag, value)
            elif level == 2:
                self._process_level2(tag, value)
    
    def _parse_line(self, line: str) -> Tuple[int, str, Optional[str]]:
        """Parse a GEDCOM line into level, tag, and value."""
        # Remove BOM if present
        line = line.lstrip('\ufeff')
        
        parts = line.split(None, 2)
        
        if not parts:
            return 0, "", None
        
        level = int(parts[0])
        
        if len(parts) == 1:
            return level, "", None
        
        # Check if second part is an ID (starts with @)
        if parts[1].startswith('@'):
            if len(parts) == 3:
                return level, parts[2], parts[1]
            return level, "", parts[1]
        
        tag = parts[1]
        value = parts[2] if len(parts) == 3 else None
        
        return level, tag, value
    
    def _process_level0(self, tag: str, value: Optional[str]):
        """Process level 0 records (new record starts)."""
        # Save previous record if exists
        self._save_current_record()
        
        if tag == 'INDI':
            self.current_type = 'INDI'
            self.current_record = Individual(value)
        elif tag == 'FAM':
            self.current_type = 'FAM'
            self.current_record = Family(value)
        elif tag == 'HEAD':
            self.current_type = 'HEAD'
            self.current_record = {}
        elif tag == 'SUBM':
            self.current_type = 'SUBM'
            self.current_record = {'id': value}
        elif tag == 'TRLR':
            self.current_type = None
            self.current_record = None
        else:
            self.current_type = None
            self.current_record = None
    
    def _process_level1(self, tag: str, value: Optional[str]):
        """Process level 1 tags."""
        if not self.current_record:
            return
        
        # Reset event flags whenever we see a new level 1 tag
        self.current_birth = False
        self.current_death = False
        self.current_marriage = False
        self.current_object = False
        
        if self.current_type == 'INDI':
            if tag == 'NAME':
                self._parse_name(value)
            elif tag == 'SEX':
                self.current_record.sex = value
            elif tag == 'BIRT':
                self.current_birth = True
            elif tag == 'DEAT':
                self.current_death = True
            elif tag == 'FAMS':
                self.current_record.family_spouse.append(value)
            elif tag == 'FAMC':
                self.current_record.family_child.append(value)
            elif tag == 'OBJE':
                self.current_object = True
        
        elif self.current_type == 'FAM':
            if tag == 'HUSB':
                self.current_record.husband_id = value
            elif tag == 'WIFE':
                self.current_record.wife_id = value
            elif tag == 'CHIL':
                self.current_record.children_ids.append(value)
            elif tag == 'MARR':
                self.current_marriage = True
    
    def _process_level2(self, tag: str, value: Optional[str]):
        """Process level 2 tags."""
        if not self.current_record:
            return
        
        if self.current_type == 'INDI':
            if hasattr(self, 'current_birth') and self.current_birth:
                if tag == 'DATE':
                    self.current_record.birth_date = value
                elif tag == 'PLAC':
                    self.current_record.birth_place = value
            elif hasattr(self, 'current_death') and self.current_death:
                if tag == 'DATE':
                    self.current_record.death_date = value
                elif tag == 'PLAC':
                    self.current_record.death_place = value
            elif hasattr(self, 'current_object') and self.current_object:
                if tag == 'FILE':
                    self.current_record.objects.append(value)
                    self.current_object = False
            elif tag == 'GIVN':
                self.current_record.given_name = value
            elif tag == 'SURN':
                self.current_record.surname = value
        
        elif self.current_type == 'FAM':
            if hasattr(self, 'current_marriage') and self.current_marriage:
                if tag == 'DATE':
                    self.current_record.marriage_date = value
                elif tag == 'PLAC':
                    self.current_record.marriage_place = value
    
    def _parse_name(self, name_str: Optional[str]):
        """Parse a NAME field into given name and surname."""
        if not name_str:
            return
        
        # Format is typically: Given /Surname/
        if '/' in name_str:
            parts = name_str.split('/')
            if len(parts) >= 2:
                self.current_record.given_name = parts[0].strip()
                self.current_record.surname = parts[1].strip()
        else:
            # No surname markers, treat as given name
            self.current_record.given_name = name_str.strip()
    
    def _save_current_record(self):
        """Save the current record to the tree."""
        if self.current_type == 'INDI' and self.current_record:
            self.tree.add_individual(self.current_record)
        elif self.current_type == 'FAM' and self.current_record:
            self.tree.add_family(self.current_record)
        elif self.current_type == 'HEAD' and self.current_record:
            self.tree.header = self.current_record
        elif self.current_type == 'SUBM' and self.current_record:
            self.tree.submitter = self.current_record
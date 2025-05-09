"""
Club Parser Module

This module contains functions for parsing club data from different file formats.
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def parse_club_json(file_path: str, team_mapper: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Parse a JSON file containing club data.
    
    Args:
        file_path: Path to the JSON file
        team_mapper: Dictionary mapping variant names to canonical names
        
    Returns:
        List of club dictionaries
    """
    clubs = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # openfootball club JSON is usually a list of dicts
        if isinstance(data, list):
            for club in data:
                if isinstance(club, dict) and 'name' in club:
                    # Apply team mapping if available
                    name = team_mapper.get(club.get('name'), club.get('name'))
                    
                    # Extract alternative names
                    alt_names = club.get('alt_names', [])
                    if alt_names and not isinstance(alt_names, list):
                        if isinstance(alt_names, str):
                            alt_names = [alt_names]
                        else:
                            alt_names = []
                    
                    # Convert to string for storage
                    alt_names_str = ','.join(alt_names) if alt_names else None
                    
                    clubs.append({
                        'name': name,
                        'founded_year': club.get('founded'),
                        'stadium_name': club.get('stadium'),
                        'city': club.get('city'),
                        'country': club.get('country'),
                        'alternative_names': alt_names_str
                    })
        else:
            logging.warning(f"Unexpected JSON structure in {file_path}")
    except Exception as e:
        logging.error(f"Error parsing club JSON file {file_path}: {e}")
    
    return clubs

def parse_club_txt(file_path: str, country: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Parse a TXT file containing club data in OpenFootball format.
    
    Args:
        file_path: Path to the club file
        country: Country of the clubs, if known
        
    Returns:
        List of club dictionaries
    """
    clubs = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines, comments, or header lines
            if not line or line.startswith('=') or line.startswith('#'):
                i += 1
                continue
            
            # Main club line: Club Name, 1886, @ Stadium, City (Region)
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 1:
                i += 1
                continue
            
            name = parts[0]
            founded_year = None
            stadium_name = None
            city = None
            alt_names = []
            
            # Try to extract founded year
            if len(parts) > 1 and parts[1].isdigit():
                founded_year = int(parts[1])
            
            # Try to extract stadium and city
            for p in parts[2:]:
                if p.startswith('@'):
                    stadium_name = p[1:].strip()
                elif '(' in p and ')' in p:
                    city = p.split('(')[0].strip()
                elif p:
                    city = p.strip()
            
            # Look ahead for alternative names (lines starting with '|')
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith('|'):
                alt_line = lines[j].strip()[1:].strip()
                # Remove comments after '#'
                alt_line = alt_line.split('#')[0].strip()
                if alt_line:
                    # Alternative names are separated by '|'
                    alt_names.extend([a.strip() for a in alt_line.split('|') if a.strip()])
                j += 1
            
            # Create club entry
            clubs.append({
                'name': name,
                'founded_year': founded_year,
                'stadium_name': stadium_name,
                'city': city,
                'country': country,
                'alternative_names': ','.join(alt_names) if alt_names else None
            })
            
            # Move to the next club
            i = j if j > i else i + 1
    
    except Exception as e:
        logging.error(f"Error parsing club TXT file {file_path}: {e}")
    
    return clubs

def bulk_upsert_clubs(db, clubs):
    """
    Bulk upsert clubs to the database.
    
    Args:
        db: Database session
        clubs: List of club dictionaries
        
    Returns:
        Tuple of (added_count, updated_count)
    """
    from app.models.models import Club
    
    if not clubs:
        return 0, 0
    
    # Fetch all existing clubs by name
    names = [club['name'] for club in clubs if club.get('name')]
    existing = {c.name: c for c in db.query(Club).filter(Club.name.in_(names)).all()}
    
    to_insert = []
    to_update = []
    
    for club in clubs:
        if not club.get('name'):
            continue
        
        if club['name'] in existing:
            db_club = existing[club['name']]
            changed = False
            
            # Update fields if changed
            for field in ['founded_year', 'stadium_name', 'city', 'country', 'alternative_names']:
                if club.get(field) is not None and getattr(db_club, field) != club[field]:
                    setattr(db_club, field, club[field])
                    changed = True
            
            if changed:
                to_update.append(db_club)
        else:
            to_insert.append(Club(**club))
    
    # Perform bulk operations
    if to_insert:
        db.bulk_save_objects(to_insert)
    
    db.commit()
    
    return len(to_insert), len(to_update) 
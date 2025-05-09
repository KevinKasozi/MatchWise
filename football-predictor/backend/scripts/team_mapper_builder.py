#!/usr/bin/env python3
"""
Team Mapper Builder

This script scans all football data directories to build a comprehensive team name mapping.
It extracts alternative team names from club files and creates a mapping to normalize team names
across different sources.
"""

import os
import json
import re
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from sqlalchemy.orm import Session

# Import from project
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import Club

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def normalize_team_name(name: str) -> str:
    """
    Normalize team name by removing common suffixes, spaces, and special characters.
    """
    if not name:
        return ""
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove common suffixes
    suffixes = [
        'fc', 'f.c.', 'f.c', 'afc', 'a.f.c', 'a.f.c.', 'united', 'utd', 'city', 
        'football club', 'association football club', '1899', '1900', '1901', '1902', 
        '1903', '1904', '1905', '1906', '1907', '1908', '1909', '1910',
        '1911', '1912', '1913', '1914', '1915', '04', '05', '06', '07', '08', '09'
    ]
    
    # Replace apostrophes and other special characters
    name = re.sub(r'[\'\.&\-]', ' ', name)
    
    # Remove common suffixes
    for suffix in suffixes:
        name = re.sub(r'\b{}\b'.format(suffix), '', name)
    
    # Remove extra spaces and strip
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name

def extract_alternative_names_from_club_file(file_path: str) -> Tuple[str, List[str]]:
    """
    Extract main club name and alternative names from a club file.
    """
    main_name = os.path.splitext(os.path.basename(file_path))[0].replace('_', ' ').title()
    alt_names = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines or header lines
            if not line or line.startswith('=') or line.startswith('#'):
                continue
                
            # Main club line: Club Name, 1886, @ Stadium, City (Region)
            if i == 0 or not line.startswith('|'):
                parts = [p.strip() for p in line.split(',')]
                if parts and len(parts) > 0:
                    # First part is the club name
                    main_name = parts[0]
                    
            # Alternative names (lines starting with '|')
            elif line.startswith('|'):
                alt_line = line.strip()[1:].strip()
                # Remove comments after '#'
                alt_line = alt_line.split('#')[0].strip()
                if alt_line:
                    alt_names.extend([a.strip() for a in alt_line.split('|') if a.strip()])
    except Exception as e:
        logging.warning(f"Error parsing club file {file_path}: {e}")
    
    return main_name, alt_names

def extract_alternative_names_from_json(file_path: str) -> List[Tuple[str, List[str]]]:
    """
    Extract club names and alternative names from a JSON file.
    """
    results = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if isinstance(data, list):
            for club in data:
                if isinstance(club, dict) and 'name' in club:
                    name = club.get('name')
                    alt_names = club.get('alt_names', [])
                    if alt_names and not isinstance(alt_names, list):
                        alt_names = [alt_names]
                    results.append((name, alt_names))
    except Exception as e:
        logging.warning(f"Error parsing JSON file {file_path}: {e}")
    
    return results

def extract_teams_from_fixture_file(file_path: str) -> Set[str]:
    """
    Extract team names from fixture files.
    """
    teams = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        current_date = None
        for line in lines:
            line = line.strip()
            
            # Skip empty lines or header lines
            if not line or line.startswith('=') or line.startswith('#') or line.startswith('Matchday'):
                continue
                
            # Date header
            date_match = re.match(r'\[(.+)\]', line)
            if date_match:
                current_date = date_match.group(1)
                continue
                
            # Match line: time  home_team  score (ht)  away_team
            match = re.match(r'(\d{1,2}\.\d{2})?\s*([\w &\'\-\.]+?)\s+(\d+)-(\d+)(?: \([^)]+\))?\s+([\w &\'\-\.]+)', line)
            if match:
                time, home_team, home_score, away_score, away_team = match.groups()
                if home_team:
                    teams.add(home_team.strip())
                if away_team:
                    teams.add(away_team.strip())
            
            # Alternative formats: Home Team vs Away Team
            alt_match = re.match(r'([\w &\'\-\.]+)\s+(?:v|vs|[-])\s+([\w &\'\-\.]+)', line)
            if alt_match and not match:
                home_team, away_team = alt_match.groups()
                if home_team:
                    teams.add(home_team.strip())
                if away_team:
                    teams.add(away_team.strip())
    except Exception as e:
        logging.warning(f"Error parsing fixture file {file_path}: {e}")
    
    return teams

def extract_from_database(db: Session) -> Dict[str, List[str]]:
    """
    Extract team names and alternative names from the database.
    """
    club_map = {}
    
    try:
        clubs = db.query(Club).all()
        for club in clubs:
            if club.name:
                alt_names = []
                if club.alternative_names:
                    try:
                        # Alternative names could be stored as comma-separated strings or JSON
                        if ',' in club.alternative_names:
                            alt_names = [n.strip() for n in club.alternative_names.split(',') if n.strip()]
                        else:
                            try:
                                names = json.loads(club.alternative_names)
                                if isinstance(names, list):
                                    alt_names = names
                                elif isinstance(names, str):
                                    alt_names = [names]
                            except json.JSONDecodeError:
                                alt_names = [club.alternative_names]
                    except Exception as e:
                        logging.warning(f"Error parsing alternative names for club {club.name}: {e}")
                
                club_map[club.name] = alt_names
    except Exception as e:
        logging.error(f"Error querying database for clubs: {e}")
    
    return club_map

def scan_directory_for_team_names(directory: str) -> Dict[str, List[str]]:
    """
    Scan a directory for team names and alternative names.
    """
    team_map = {}
    squad_names = set()
    fixture_teams = set()
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Check if we're in a clubs directory
            in_clubs_dir = any('clubs' in part.lower() for part in root.split(os.sep))
            
            # Check if we're in a squads directory
            in_squads_dir = any('squads' in part.lower() for part in root.split(os.sep))
            
            # Determine file type
            is_club_file = 'club' in file.lower()
            is_fixture_file = file.endswith('.txt') and not in_squads_dir and not in_clubs_dir and not is_club_file
            
            if is_club_file and file.endswith('.txt'):
                main_name, alt_names = extract_alternative_names_from_club_file(file_path)
                if main_name:
                    if main_name in team_map:
                        team_map[main_name].extend(alt_names)
                    else:
                        team_map[main_name] = alt_names
            
            elif is_club_file and file.endswith('.json'):
                results = extract_alternative_names_from_json(file_path)
                for main_name, alt_names in results:
                    if main_name:
                        if main_name in team_map:
                            team_map[main_name].extend(alt_names)
                        else:
                            team_map[main_name] = alt_names
            
            elif in_squads_dir and file.endswith('.txt'):
                # Squad file names are often team names
                squad_name = os.path.splitext(os.path.basename(file))[0].replace('_', ' ').title()
                squad_names.add(squad_name)
            
            elif is_fixture_file:
                # Extract team names from fixture files
                teams = extract_teams_from_fixture_file(file_path)
                fixture_teams.update(teams)
    
    # Add squad names as main names if not already in the map
    for name in squad_names:
        if name not in team_map:
            team_map[name] = []
    
    # Add fixture teams as main names if not already in the map
    for name in fixture_teams:
        if name not in team_map:
            team_map[name] = []
    
    return team_map

def build_normalized_team_map(team_map: Dict[str, List[str]]) -> Dict[str, str]:
    """
    Build a normalized team map where keys are variant names and values are canonical names.
    """
    normalized_map = {}
    
    # First, add all main names to the normalized map
    for main_name, alt_names in team_map.items():
        normalized_main = normalize_team_name(main_name)
        normalized_map[main_name] = main_name  # Identity mapping
        normalized_map[normalized_main] = main_name  # Normalized to main
        
        # Add alt names
        for alt in alt_names:
            normalized_alt = normalize_team_name(alt)
            normalized_map[alt] = main_name
            normalized_map[normalized_alt] = main_name
    
    return normalized_map

def main():
    parser = argparse.ArgumentParser(description='Build team name mapper from football data')
    parser.add_argument('--data-path', default=settings.DATA_PATH, help='Path to football data')
    parser.add_argument('--output', default=settings.TEAM_NAME_NORMALIZATION, help='Output file for team mapper')
    parser.add_argument('--use-db', action='store_true', help='Include team names from database')
    args = parser.parse_args()
    
    logging.info(f"Scanning directory: {args.data_path}")
    
    # Scan directories for team names
    team_map = scan_directory_for_team_names(args.data_path)
    
    # Add database team names if requested
    if args.use_db:
        logging.info("Extracting team names from database")
        db = SessionLocal()
        db_team_map = extract_from_database(db)
        db.close()
        
        # Merge database team map into main team map
        for main_name, alt_names in db_team_map.items():
            if main_name in team_map:
                team_map[main_name].extend(alt_names)
            else:
                team_map[main_name] = alt_names
    
    # Remove duplicates in alternative names
    for main_name in team_map:
        team_map[main_name] = list(set(team_map[main_name]))
    
    # Build normalized team map
    normalized_map = build_normalized_team_map(team_map)
    
    # Save to file
    output_path = args.output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(normalized_map, f, indent=2, sort_keys=True)
    
    logging.info(f"Team mapper saved to {output_path} with {len(normalized_map)} entries")
    
    # Summary
    main_names = len(team_map)
    alt_names = sum(len(alts) for alts in team_map.values())
    
    logging.info(f"Team mapper contains {main_names} main team names and {alt_names} alternative names")
    logging.info(f"Total number of name variations: {len(normalized_map)}")

if __name__ == "__main__":
    main() 
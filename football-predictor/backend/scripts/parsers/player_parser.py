"""
Player Parser Module

This module contains functions for parsing player data from different file formats.
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def parse_squad_txt(file_path: str, club_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Parse a squad TXT file in OpenFootball format.
    
    Args:
        file_path: Path to the squad file
        club_name: Name of the club, if known
        
    Returns:
        List of player dictionaries
    """
    players = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines or header lines
            if not line or line.startswith('=') or line.startswith('#'):
                continue
            
            # Example format:  1,  Aaron Ramsdale,                    GK,   b. 1998,   Sheffield U
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 3:
                continue
            
            # Player number (optional)
            number = None
            if parts[0].isdigit():
                number = int(parts[0])
            
            # Player name
            name = parts[1]
            
            # Position
            position = parts[2] if len(parts) > 2 else None
            
            # Birth year and nationality (optional)
            birth_year = None
            nationality = None
            current_club = None
            
            for p in parts[3:]:
                if p.startswith('b. '):
                    try:
                        birth_year = int(p.replace('b. ', '').strip())
                    except Exception:
                        pass
                elif '(' in p and ')' in p:
                    # e.g. David Raya (ESP)
                    nat = p[p.find('(')+1:p.find(')')]
                    if len(nat) <= 4:  # Country codes are typically 2-3 characters
                        nationality = nat
                elif p:
                    # Last part might be current club
                    current_club = p
            
            players.append({
                'name': name,
                'position': position,
                'birth_year': birth_year,
                'nationality': nationality,
                'club_name': club_name,
                'number': number,
                'current_club': current_club
            })
    
    except Exception as e:
        logging.error(f"Error parsing squad file {file_path}: {e}")
    
    return players

def parse_player_json(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse a player JSON file.
    
    Args:
        file_path: Path to the player JSON file
        
    Returns:
        List of player dictionaries
    """
    import json
    players = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            for player in data:
                if isinstance(player, dict) and 'name' in player:
                    birth_date = None
                    if 'birth' in player:
                        try:
                            birth_date = datetime.strptime(player['birth'], '%Y-%m-%d').date()
                        except Exception:
                            birth_year = None
                    
                    players.append({
                        'name': player.get('name'),
                        'position': player.get('position'),
                        'birth_year': birth_date.year if birth_date else None,
                        'nationality': player.get('nationality'),
                        'club_name': player.get('club'),
                        'number': player.get('number'),
                        'height': player.get('height'),
                        'weight': player.get('weight')
                    })
    
    except Exception as e:
        logging.error(f"Error parsing player JSON file {file_path}: {e}")
    
    return players

def extract_players_from_match_report(file_path: str) -> List[Dict[str, Any]]:
    """
    Extract player information from match reports.
    
    Args:
        file_path: Path to the match report file
        
    Returns:
        List of player dictionaries with partial information
    """
    players = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # This is a simplified approach - match reports have many formats
        # Try to extract line-ups or player lists
        lineup_section = False
        current_team = None
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Look for lineup sections
            if line.lower().startswith('line-up') or line.lower().startswith('lineup') or line.lower().startswith('starting xi'):
                lineup_section = True
                continue
            
            # Detect team headers
            if line.endswith(':') and lineup_section:
                current_team = line.rstrip(':')
                continue
            
            # Parse player entries in lineup section
            if lineup_section and current_team and line:
                # Try to match player entries like:
                # 1-Alisson, 66-Alexander-Arnold, 4-van Dijk, ...
                player_matches = re.finditer(r'(?:(\d+)[.\-)]?\s*)?([A-Za-z\s\'-]+)(?:\s*\(([A-Z]{2,3})\))?', line)
                
                for match in player_matches:
                    number, name, nationality = match.groups()
                    if name:
                        players.append({
                            'name': name.strip(),
                            'nationality': nationality,
                            'number': int(number) if number else None,
                            'club_name': current_team
                        })
    
    except Exception as e:
        logging.error(f"Error extracting players from match report {file_path}: {e}")
    
    return players

def bulk_upsert_players(db, players, club_id=None, team_id=None):
    """
    Bulk upsert players to the database.
    
    Args:
        db: Database session
        players: List of player dictionaries
        club_id: Club ID to associate with the players
        team_id: Team ID to associate with the players
        
    Returns:
        Tuple of (added_count, updated_count)
    """
    from app.models.models import Player
    from datetime import datetime
    
    if not players:
        return 0, 0
    
    # Extract names for existing player lookup
    names = [p['name'] for p in players if p.get('name')]
    existing = {p.name: p for p in db.query(Player).filter(Player.name.in_(names)).all()}
    
    to_insert = []
    to_update = []
    
    for player in players:
        if not player.get('name'):
            continue
        
        if player['name'] in existing:
            # Update existing player
            db_player = existing[player['name']]
            changed = False
            
            # Update fields if provided and different
            for field, val in [
                ('position', player.get('position')),
                ('nationality', player.get('nationality')),
                ('club_id', club_id),
                ('team_id', team_id)
            ]:
                if val is not None and getattr(db_player, field) != val:
                    setattr(db_player, field, val)
                    changed = True
            
            # Update birth date if provided
            if player.get('birth_year') and (
                not db_player.date_of_birth or 
                db_player.date_of_birth.year != player['birth_year']
            ):
                try:
                    db_player.date_of_birth = datetime(player['birth_year'], 1, 1)
                    changed = True
                except Exception:
                    pass
            
            if changed:
                to_update.append(db_player)
        else:
            # Create new player
            date_of_birth = None
            if player.get('birth_year'):
                try:
                    date_of_birth = datetime(player['birth_year'], 1, 1)
                except Exception:
                    pass
            
            to_insert.append(Player(
                name=player['name'],
                position=player.get('position'),
                nationality=player.get('nationality'),
                date_of_birth=date_of_birth,
                club_id=club_id,
                team_id=team_id
            ))
    
    # Perform bulk operations
    if to_insert:
        db.bulk_save_objects(to_insert)
    
    db.commit()
    
    return len(to_insert), len(to_update) 
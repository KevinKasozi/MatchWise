"""
Fixture Parser Module

This module contains functions for parsing fixture data from different file formats.
"""

import csv
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def normalize_date(date_str: str, season_year: Optional[str] = None) -> Optional[str]:
    """
    Normalize various date formats to YYYY-MM-DD.
    
    Args:
        date_str: Date string in various formats
        season_year: Year the season starts, to help with inferring the year
        
    Returns:
        Normalized date string in YYYY-MM-DD format or None if parsing fails
    """
    if not date_str:
        return None
    
    try:
        # Handle 'Fri Aug/11' format
        parts = date_str.split()
        if len(parts) == 2 and '/' in parts[1]:
            # Format: 'Fri Aug/11'
            month, day = parts[1].split('/')
            month_num = datetime.strptime(month, '%b').month
            day = int(day)
        elif len(parts) == 1 and '/' in parts[0]:
            # Format: 'Aug/11'
            month, day = parts[0].split('/')
            month_num = datetime.strptime(month, '%b').month
            day = int(day)
        else:
            # Try other formats
            try:
                # ISO format: YYYY-MM-DD
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                return date_str
            except ValueError:
                logging.warning(f"Could not parse date: {date_str}")
                return None
        
        # Determine year based on season_year and month
        if season_year:
            year = int(season_year)
            # If month is July or later, it's the first year of the season, otherwise it's next year
            if month_num >= 7:
                normalized_year = year
            else:
                normalized_year = year + 1
        else:
            # Default to current year
            normalized_year = datetime.now().year
        
        return f"{normalized_year:04d}-{month_num:02d}-{day:02d}"
    
    except Exception as e:
        logging.warning(f"normalize_date failed: {date_str}, error={e}")
        return None

def parse_fixture_csv(file_path: str, team_mapper: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Parse a CSV file containing fixture data.
    
    Args:
        file_path: Path to the CSV file
        team_mapper: Dictionary mapping variant names to canonical names
        
    Returns:
        List of fixture dictionaries
    """
    fixtures = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Normalize team names using team_mapper
                home_team = team_mapper.get(row.get('home_team', ''), row.get('home_team', ''))
                away_team = team_mapper.get(row.get('away_team', ''), row.get('away_team', ''))
                
                # Parse score if available
                home_score = None
                away_score = None
                if row.get('score'):
                    try:
                        score_parts = row['score'].split('-')
                        home_score = int(score_parts[0].strip())
                        away_score = int(score_parts[1].strip())
                    except (ValueError, IndexError):
                        pass
                
                # Determine if match is completed
                is_completed = True if home_score is not None and away_score is not None else False
                
                # Create fixture entry
                fixtures.append({
                    'season': row.get('season'),
                    'match_date': row.get('date'),
                    'home_team': home_team,
                    'away_team': away_team,
                    'stage': row.get('stage'),
                    'venue': row.get('venue'),
                    'is_completed': is_completed,
                    'home_score': home_score,
                    'away_score': away_score
                })
    except Exception as e:
        logging.error(f"Error parsing fixture CSV file {file_path}: {e}")
    
    return fixtures

def parse_fixture_txt(file_path: str, team_mapper: Dict[str, str], season_year: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Parse a TXT file containing fixture data in OpenFootball format.
    
    Args:
        file_path: Path to the fixture file
        team_mapper: Dictionary mapping variant names to canonical names
        season_year: Year the season starts
        
    Returns:
        List of fixture dictionaries
    """
    fixtures = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_date = None
        current_round = None
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines or comment/header lines
            if not line or line.startswith('=') or line.startswith('#'):
                continue
            
            # Check for round/matchday
            if line.lower().startswith('matchday') or line.lower().startswith('round'):
                current_round = line
                continue
            
            # Check for date header
            date_match = re.match(r'\[(.+)\]', line)
            if date_match:
                current_date = date_match.group(1)
                continue
            
            # Match line: time  home_team  score (ht)  away_team
            match = re.match(r'(\d{1,2}\.\d{2})?\s*([\w &\'\-\.]+?)\s+(\d+)-(\d+)(?: \([^)]+\))?\s+([\w &\'\-\.]+)', line)
            if match:
                time, home_team, home_score, away_score, away_team = match.groups()
                
                # Normalize team names
                home_team = home_team.strip()
                away_team = away_team.strip()
                home_team = team_mapper.get(home_team, home_team)
                away_team = team_mapper.get(away_team, away_team)
                
                # Normalize date
                match_date = normalize_date(current_date, season_year) if current_date else None
                
                # Set is_completed based on match date
                is_completed = True
                if match_date:
                    try:
                        match_date_obj = datetime.strptime(match_date, '%Y-%m-%d').date()
                        today = datetime.today().date()
                        is_completed = match_date_obj <= today
                    except Exception:
                        pass
                
                # Create fixture entry
                fixtures.append({
                    'match_date': match_date,
                    'home_team': home_team,
                    'away_team': away_team,
                    'stage': current_round,
                    'venue': None,  # Venue information not typically included in .txt files
                    'is_completed': is_completed,
                    'home_score': int(home_score),
                    'away_score': int(away_score)
                })
            
            # Alternative format: Home Team vs Away Team
            else:
                alt_match = re.match(r'([\w &\'\-\.]+)\s+(?:v|vs|[-])\s+([\w &\'\-\.]+)', line)
                if alt_match:
                    home_team, away_team = alt_match.groups()
                    home_team = home_team.strip()
                    away_team = away_team.strip()
                    home_team = team_mapper.get(home_team, home_team)
                    away_team = team_mapper.get(away_team, away_team)
                    
                    match_date = normalize_date(current_date, season_year) if current_date else None
                    
                    # For fixtures without scores, mark as not completed
                    fixtures.append({
                        'match_date': match_date,
                        'home_team': home_team,
                        'away_team': away_team,
                        'stage': current_round,
                        'venue': None,
                        'is_completed': False,
                        'home_score': None,
                        'away_score': None
                    })
    
    except Exception as e:
        logging.error(f"Error parsing fixture TXT file {file_path}: {e}")
    
    return fixtures

def validate_fixture(fixture: Dict[str, Any]) -> bool:
    """
    Validate a fixture dictionary.
    
    Args:
        fixture: Fixture dictionary
        
    Returns:
        True if valid, False otherwise
    """
    # Required fields
    if not fixture.get('home_team') or not fixture.get('away_team'):
        logging.warning(f"Fixture missing team: {fixture}")
        return False
    
    # Date validation
    if fixture.get('match_date'):
        try:
            datetime.strptime(fixture['match_date'], '%Y-%m-%d')
        except Exception:
            logging.warning(f"Fixture has invalid date: {fixture}")
            return False
    
    # Score validation
    if fixture.get('is_completed'):
        if fixture.get('home_score') is None or fixture.get('away_score') is None:
            logging.warning(f"Completed fixture missing score: {fixture}")
            return False
        if not (0 <= fixture['home_score'] <= 20 and 0 <= fixture['away_score'] <= 20):
            logging.warning(f"Fixture has extreme score: {fixture}")
            return False
    
    return True

def bulk_upsert_fixtures(db, fixtures, season_id=None):
    """
    Bulk upsert fixtures to the database.
    
    Args:
        db: Database session
        fixtures: List of fixture dictionaries
        season_id: Season ID
        
    Returns:
        Tuple of (added_count, updated_count)
    """
    from app.models.models import Fixture, MatchResult, Team, Club
    
    if not fixtures:
        return 0, 0
    
    # Validate fixtures
    valid_fixtures = [f for f in fixtures if validate_fixture(f)]
    if not valid_fixtures:
        return 0, 0
    
    # Extract all team names
    team_names = set()
    for f in valid_fixtures:
        team_names.add(f['home_team'])
        team_names.add(f['away_team'])
    
    # Map team names to club IDs
    clubs = db.query(Club).filter(Club.name.in_(team_names)).all()
    club_map = {c.name: c.id for c in clubs}
    
    # Map club IDs to team IDs
    teams = db.query(Team).filter(Team.club_id.in_(club_map.values())).all()
    team_map = {}
    for t in teams:
        club = db.query(Club).filter(Club.id == t.club_id).first()
        if club:
            team_map[club.name] = t.id
    
    # Build lookup keys for existing fixtures
    keys = []
    for f in valid_fixtures:
        home_id = team_map.get(f['home_team'])
        away_id = team_map.get(f['away_team'])
        if f['match_date'] and home_id and away_id:
            keys.append((f['match_date'], home_id, away_id))
    
    # Fetch existing fixtures
    existing = {}
    if keys:
        existing_fixtures = db.query(Fixture).filter(
            Fixture.match_date.in_([k[0] for k in keys if k[0]]),
            Fixture.home_team_id.in_([k[1] for k in keys if k[1]]),
            Fixture.away_team_id.in_([k[2] for k in keys if k[2]])
        ).all()
        
        existing = {(fx.match_date, fx.home_team_id, fx.away_team_id): fx for fx in existing_fixtures}
    
    # Process fixtures
    to_insert = []
    updated = 0
    placeholders_created = 0
    
    for fixture in valid_fixtures:
        # Get team IDs, creating placeholders if needed
        home_id = team_map.get(fixture['home_team'])
        away_id = team_map.get(fixture['away_team'])
        
        # Create placeholder for home team if needed
        if not home_id:
            club_id = club_map.get(fixture['home_team'])
            if not club_id:
                placeholder_club = db.query(Club).filter_by(name=fixture['home_team']).first()
                if not placeholder_club:
                    placeholder_club = Club(name=fixture['home_team'], country=None)
                    db.add(placeholder_club)
                    db.commit()
                club_id = placeholder_club.id
                club_map[fixture['home_team']] = club_id
            
            placeholder_team = db.query(Team).filter_by(club_id=club_id, team_type='club').first()
            if not placeholder_team:
                from app.models.models import TeamType
                placeholder_team = Team(club_id=club_id, team_type=TeamType.CLUB)
                db.add(placeholder_team)
                db.commit()
                placeholders_created += 1
            
            home_id = placeholder_team.id
            team_map[fixture['home_team']] = home_id
        
        # Create placeholder for away team if needed
        if not away_id:
            club_id = club_map.get(fixture['away_team'])
            if not club_id:
                placeholder_club = db.query(Club).filter_by(name=fixture['away_team']).first()
                if not placeholder_club:
                    placeholder_club = Club(name=fixture['away_team'], country=None)
                    db.add(placeholder_club)
                    db.commit()
                club_id = placeholder_club.id
                club_map[fixture['away_team']] = club_id
            
            placeholder_team = db.query(Team).filter_by(club_id=club_id, team_type='club').first()
            if not placeholder_team:
                from app.models.models import TeamType
                placeholder_team = Team(club_id=club_id, team_type=TeamType.CLUB)
                db.add(placeholder_team)
                db.commit()
                placeholders_created += 1
            
            away_id = placeholder_team.id
            team_map[fixture['away_team']] = away_id
        
        # Skip if we don't have valid IDs or date
        if not fixture.get('match_date') or not home_id or not away_id:
            continue
        
        # Check if fixture already exists
        key = (fixture['match_date'], home_id, away_id)
        if key in existing:
            # Update existing fixture
            db_fixture = existing[key]
            
            # Update match details if needed
            changed = False
            if db_fixture.stage != fixture.get('stage'):
                db_fixture.stage = fixture.get('stage')
                changed = True
            
            if db_fixture.venue != fixture.get('venue') and fixture.get('venue'):
                db_fixture.venue = fixture.get('venue')
                changed = True
            
            if db_fixture.is_completed != fixture.get('is_completed', False):
                db_fixture.is_completed = fixture.get('is_completed', False)
                changed = True
            
            # Update result if needed
            if fixture.get('is_completed') and fixture.get('home_score') is not None and fixture.get('away_score') is not None:
                if db_fixture.result:
                    if (db_fixture.result.home_score != fixture['home_score'] or 
                        db_fixture.result.away_score != fixture['away_score']):
                        db_fixture.result.home_score = fixture['home_score']
                        db_fixture.result.away_score = fixture['away_score']
                        changed = True
                else:
                    db_fixture.result = MatchResult(
                        home_score=fixture['home_score'],
                        away_score=fixture['away_score']
                    )
                    changed = True
            
            if changed:
                updated += 1
        else:
            # Create new fixture
            db_fixture = Fixture(
                match_date=fixture['match_date'],
                home_team_id=home_id,
                away_team_id=away_id,
                stage=fixture.get('stage'),
                venue=fixture.get('venue'),
                is_completed=fixture.get('is_completed', False),
                season_id=season_id
            )
            
            # Add result if completed
            if fixture.get('is_completed') and fixture.get('home_score') is not None and fixture.get('away_score') is not None:
                db_fixture.result = MatchResult(
                    home_score=fixture['home_score'],
                    away_score=fixture['away_score']
                )
            
            to_insert.append(db_fixture)
    
    # Perform bulk insert
    if to_insert:
        db.bulk_save_objects(to_insert)
    
    db.commit()
    
    return len(to_insert), updated 
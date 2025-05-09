#!/usr/bin/env python3

import os
import sys
import glob
from pathlib import Path
from datetime import datetime, date, timedelta
import logging
import re
from typing import List, Dict, Any, Optional, Set

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from app.models.models import (
    Base, Fixture, Team, Club, Competition, Season, CompetitionType
)

# Get database connection string from environment or use a default for local development
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/football_predictor")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def find_fixture_files(data_dir: str = None, current_season: bool = True) -> List[str]:
    """
    Find fixture files in the data directory.
    
    Args:
        data_dir: Path to the data directory (default: app/data/raw)
        current_season: Only consider current season files if True
    
    Returns:
        List of paths to fixture files
    """
    if not data_dir:
        # Default to the raw data directory in the project
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
    
    # Find all fixture files
    fixture_files = []
    
    # Leagues to include (major leagues)
    leagues = ["eng-england", "es-espana", "de-deutschland", "it-italy", "fr-france", "champions-league", "europa-league"]
    
    # Current season is typically the last numbered directory in each league
    for league in leagues:
        league_path = os.path.join(data_dir, league)
        if not os.path.isdir(league_path):
            continue
        
        # Get all seasons for this league (directories like 2023-24)
        seasons = sorted([d for d in os.listdir(league_path) 
                         if os.path.isdir(os.path.join(league_path, d)) 
                         and re.match(r'\d{4}-\d{2}|\d{4}--', d)])
        
        if not seasons:
            continue
        
        if current_season:
            # Only use the most recent season
            recent_seasons = seasons[-1:]
        else:
            # Use all seasons
            recent_seasons = seasons
        
        for season in recent_seasons:
            season_path = os.path.join(league_path, season)
            
            # Check for txt files in the season directory
            txt_files = glob.glob(os.path.join(season_path, "*.txt"))
            fixture_files.extend(txt_files)
    
    return fixture_files

def parse_txt_fixtures(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse a fixture file in txt format.
    
    Args:
        file_path: Path to the fixture file
    
    Returns:
        List of fixture dictionaries
    """
    fixtures = []
    
    # Extract competition and season info from file path
    # Example: /data/raw/eng-england/2023-24/1-premierleague.txt
    path_parts = file_path.split(os.path.sep)
    
    # Default values
    competition_name = "Unknown"
    country = "Unknown"
    season_name = "2023-24"
    
    # Parse league/country from path
    for part in path_parts:
        if "england" in part.lower():
            country = "England"
        elif "espana" in part.lower() or "spain" in part.lower():
            country = "Spain"
        elif "deutschland" in part.lower() or "germany" in part.lower():
            country = "Germany"
        elif "italy" in part.lower():
            country = "Italy"
        elif "france" in part.lower():
            country = "France"
        elif "champions-league" in part.lower():
            country = "Europe"
            competition_name = "Champions League"
        elif "europa-league" in part.lower():
            country = "Europe"
            competition_name = "Europa League"
    
    # Parse season from path
    for part in path_parts:
        if re.match(r'\d{4}-\d{2}', part):
            season_name = part
    
    # Parse competition from filename if not already set
    filename = os.path.basename(file_path)
    if competition_name == "Unknown":
        if "premier" in filename.lower():
            competition_name = "Premier League"
        elif "bundesliga" in filename.lower():
            competition_name = "Bundesliga"
        elif "laliga" in filename.lower() or "liga" in filename.lower():
            competition_name = "La Liga"
        elif "serie" in filename.lower():
            competition_name = "Serie A"
        elif "ligue1" in filename.lower() or "ligue" in filename.lower():
            competition_name = "Ligue 1"
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_date = None
    current_matchday = None
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
        
        # Check for matchday/round
        if line.lower().startswith('matchday') or line.lower().startswith('round'):
            current_matchday = line
            continue
        
        # Check for date
        date_match = re.match(r'\[([^\]]+)\]', line)
        if date_match:
            date_str = date_match.group(1)
            # Parse date in various formats
            for fmt in ['%a %b/%d/%Y', '%a %b/%d', '%b/%d/%Y', '%b/%d', '%Y-%m-%d']:
                try:
                    parsed_date = datetime.strptime(date_str, fmt).date()
                    # For dates without year, use current year
                    if fmt in ['%a %b/%d', '%b/%d']:
                        current_year = date.today().year
                        parsed_date = parsed_date.replace(year=current_year)
                        # If date is in past, use next year
                        if parsed_date < date.today():
                            parsed_date = parsed_date.replace(year=current_year + 1)
                    current_date = parsed_date
                    break
                except ValueError:
                    continue
            continue
        
        # Try to match a fixture line
        # Format: Time Team1 vs Team2 or Team1 vs Team2
        # Time could be HH.MM or HH:MM
        fixture_match = re.match(r'(?:(\d{1,2}[:\.]\d{2})\s+)?([^0-9][^0-9-].*?)\s+(?:v|vs|[-])\s+([^0-9].*?)$', line)
        
        if fixture_match:
            time_str, home_team, away_team = fixture_match.groups()
            
            # Clean team names
            home_team = home_team.strip()
            away_team = away_team.strip()
            
            # Default time if not provided
            if not time_str:
                time_str = "15:00"
            
            # Convert time format to HH:MM
            if "." in time_str:
                time_str = time_str.replace(".", ":")
            
            # Create fixture entry
            if current_date:
                fixtures.append({
                    'date': current_date,
                    'time': time_str,
                    'home_team': home_team,
                    'away_team': away_team,
                    'competition': competition_name,
                    'country': country,
                    'season': season_name,
                    'matchday': current_matchday
                })
    
    return fixtures

def get_or_create_club(db_session, club_name: str, country: str = None) -> Club:
    """
    Get or create a club by name.
    
    Args:
        db_session: Database session
        club_name: Name of the club
        country: Country of the club
    
    Returns:
        Club object
    """
    # Try to find an existing club first
    club = db_session.query(Club).filter(func.lower(Club.name) == func.lower(club_name)).first()
    
    if not club:
        # Create a new club
        club = Club(
            name=club_name,
            country=country
        )
        db_session.add(club)
        db_session.flush()
    
    return club

def get_or_create_team(db_session, club_id: int) -> Team:
    """
    Get or create a team for a club.
    
    Args:
        db_session: Database session
        club_id: ID of the club
    
    Returns:
        Team object
    """
    team = db_session.query(Team).filter(Team.club_id == club_id).first()
    
    if not team:
        team = Team(
            club_id=club_id,
            team_type="club"
        )
        db_session.add(team)
        db_session.flush()
    
    return team

def get_or_create_competition(db_session, name: str, country: str) -> Competition:
    """
    Get or create a competition by name.
    
    Args:
        db_session: Database session
        name: Name of the competition
        country: Country of the competition
    
    Returns:
        Competition object
    """
    competition = db_session.query(Competition).filter(func.lower(Competition.name) == func.lower(name)).first()
    
    if not competition:
        # Determine competition type
        competition_type = CompetitionType.LEAGUE
        if "cup" in name.lower():
            competition_type = CompetitionType.CUP
        elif "champions league" in name.lower() or "europa league" in name.lower():
            competition_type = CompetitionType.INTERNATIONAL
        
        competition = Competition(
            name=name,
            country=country,
            competition_type=competition_type
        )
        db_session.add(competition)
        db_session.flush()
    
    return competition

def get_or_create_season(db_session, competition_id: int, season_name: str) -> Season:
    """
    Get or create a season for a competition.
    
    Args:
        db_session: Database session
        competition_id: ID of the competition
        season_name: Name of the season (e.g., "2023-24")
    
    Returns:
        Season object
    """
    # Try to find existing season
    season = db_session.query(Season).filter(
        Season.competition_id == competition_id,
        Season.season_name == season_name
    ).first()
    
    if not season:
        # Parse year_start and year_end from season_name
        year_start = 2023
        year_end = 2024
        
        if '-' in season_name:
            parts = season_name.split('-')
            if len(parts) == 2:
                try:
                    # Handle format like "2023-24"
                    if len(parts[0]) == 2:
                        year_start = int('20' + parts[0])
                        year_end = int('20' + parts[1])
                    else:
                        year_start = int(parts[0])
                        year_end = int(parts[1])
                except ValueError:
                    pass
        
        season = Season(
            competition_id=competition_id,
            season_name=season_name,
            year_start=year_start,
            year_end=year_end
        )
        db_session.add(season)
        db_session.flush()
    
    return season

def populate_fixtures(db_session, fixtures: List[Dict[str, Any]]) -> int:
    """
    Add fixtures to the database.
    
    Args:
        db_session: Database session
        fixtures: List of fixture dictionaries
    
    Returns:
        Number of fixtures added
    """
    fixture_count = 0
    
    for fixture in fixtures:
        try:
            # Ensure fixture date is in the current year or next year
            fixture_date = fixture['date']
            current_year = date.today().year
            
            if fixture_date.year != current_year:
                # Create a new date with the same month/day but current year
                try:
                    new_date = date(current_year, fixture_date.month, fixture_date.day)
                    
                    # If the new date is in the past, use next year
                    if new_date < date.today():
                        new_date = date(current_year + 1, fixture_date.month, fixture_date.day)
                    
                    # Only use dates within next 6 months
                    future_cutoff = date.today() + timedelta(days=180)
                    if new_date > future_cutoff:
                        # Skip this fixture
                        continue
                    
                    fixture['date'] = new_date
                except ValueError:
                    # Skip invalid dates (e.g., Feb 29 in non-leap years)
                    continue
            
            # Get or create clubs
            home_club = get_or_create_club(db_session, fixture['home_team'], fixture['country'])
            away_club = get_or_create_club(db_session, fixture['away_team'], fixture['country'])
            
            # Get or create teams
            home_team = get_or_create_team(db_session, home_club.id)
            away_team = get_or_create_team(db_session, away_club.id)
            
            # Get or create competition
            competition = get_or_create_competition(db_session, fixture['competition'], fixture['country'])
            
            # Get or create season
            season = get_or_create_season(db_session, competition.id, fixture['season'])
            
            # Check if fixture already exists to avoid duplicates
            existing_fixture = db_session.query(Fixture).filter(
                Fixture.match_date == fixture['date'],
                Fixture.home_team_id == home_team.id,
                Fixture.away_team_id == away_team.id
            ).first()
            
            if not existing_fixture:
                # Create the fixture
                stage = fixture['matchday'] if fixture.get('matchday') else "Regular Season"
                
                new_fixture = Fixture(
                    season_id=season.id,
                    match_date=fixture['date'],
                    match_time=fixture['time'],
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    stage=stage,
                    venue=f"{home_club.name} Stadium",
                    is_completed=False,
                    group_id=None  # Not handling groups for now
                )
                db_session.add(new_fixture)
                fixture_count += 1
        
        except Exception as e:
            logging.error(f"Error adding fixture {fixture}: {e}")
            continue
    
    return fixture_count

def main():
    """
    Main function to find fixture files, parse them, and add to database.
    """
    logging.info("Searching for fixture files...")
    fixture_files = find_fixture_files()
    
    if not fixture_files:
        logging.error("No fixture files found!")
        return
    
    logging.info(f"Found {len(fixture_files)} fixture files")
    
    all_fixtures = []
    for file_path in fixture_files:
        logging.info(f"Parsing {file_path}...")
        fixtures = parse_txt_fixtures(file_path)
        all_fixtures.extend(fixtures)
    
    if not all_fixtures:
        logging.error("No fixtures parsed!")
        return
    
    logging.info(f"Parsed {len(all_fixtures)} fixtures")
    
    # Add fixtures to database
    db = SessionLocal()
    try:
        fixture_count = populate_fixtures(db, all_fixtures)
        db.commit()
        logging.info(f"Successfully added {fixture_count} fixtures to the database")
    except Exception as e:
        db.rollback()
        logging.error(f"Error adding fixtures to database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main() 
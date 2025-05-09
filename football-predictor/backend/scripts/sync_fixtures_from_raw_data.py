#!/usr/bin/env python3

import os
import sys
import re
import glob
from datetime import datetime, date, timedelta
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, joinedload

from app.models.models import (
    Base, Fixture, Team, Club, Competition, Season, CompetitionType
)

# Database connection string
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/football_predictor")
logger.info(f"Using database: {DATABASE_URL}")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Raw data paths - adjust these based on where your data is located
RAW_DATA_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")

LEAGUE_MAPPINGS = {
    "eng-england": {
        "country": "England",
        "competitions": {
            "1-premierleague": {"name": "Premier League", "type": "league"},
            "2-championship": {"name": "Championship", "type": "league"},
            "3-league1": {"name": "League One", "type": "league"},
            "4-league2": {"name": "League Two", "type": "league"},
        }
    },
    "es-espana": {
        "country": "Spain",
        "competitions": {
            "1-liga": {"name": "La Liga", "type": "league"},
            "2-liga2": {"name": "La Liga 2", "type": "league"},
        }
    },
    "de-deutschland": {
        "country": "Germany",
        "competitions": {
            "1-bundesliga": {"name": "Bundesliga", "type": "league"},
            "2-bundesliga2": {"name": "2. Bundesliga", "type": "league"},
            "3-liga3": {"name": "3. Liga", "type": "league"},
        }
    },
    "it-italy": {
        "country": "Italy",
        "competitions": {
            "1-seriea": {"name": "Serie A", "type": "league"},
            "2-serieb": {"name": "Serie B", "type": "league"},
        }
    },
    "fr-france": {
        "country": "France",
        "competitions": {
            "1-ligue1": {"name": "Ligue 1", "type": "league"},
            "2-ligue2": {"name": "Ligue 2", "type": "league"},
        }
    },
    "champions-league": {
        "country": "Europe",
        "competitions": {
            "cl": {"name": "Champions League", "type": "cup"},
        }
    },
    "europa-league": {
        "country": "Europe",
        "competitions": {
            "el": {"name": "Europa League", "type": "cup"},
        }
    },
}

MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
}

def find_league_files() -> List[Dict]:
    """Find all league fixture files in the raw data directories"""
    league_files = []
    
    for league_dir, league_info in LEAGUE_MAPPINGS.items():
        league_path = os.path.join(RAW_DATA_ROOT, league_dir)
        if not os.path.exists(league_path):
            logger.warning(f"League directory not found: {league_path}")
            continue
            
        # Find the most recent season directory
        season_dirs = []
        for item in os.listdir(league_path):
            if re.match(r'^\d{4}-\d{2}$', item):
                season_dirs.append(item)
        
        if not season_dirs:
            logger.warning(f"No season directories found for {league_dir}")
            continue
            
        # Sort by season year (most recent first)
        season_dirs.sort(reverse=True)
        latest_season = season_dirs[0]
        
        # Find fixture files in this directory
        for comp_id, comp_info in league_info.get("competitions", {}).items():
            fixture_file = os.path.join(league_path, latest_season, f"{comp_id}.txt")
            
            if os.path.exists(fixture_file):
                league_files.append({
                    "file_path": fixture_file,
                    "league_dir": league_dir,
                    "season": latest_season,
                    "competition_id": comp_id,
                    "competition_name": comp_info.get("name"),
                    "competition_type": comp_info.get("type", "league"),
                    "country": league_info.get("country")
                })
            else:
                logger.warning(f"Fixture file not found: {fixture_file}")
    
    logger.info(f"Found {len(league_files)} league fixture files")
    return league_files

def parse_fixture_file(file_info: Dict) -> List[Dict]:
    """Parse a fixture file and extract match data"""
    fixtures = []
    file_path = file_info["file_path"]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        lines = content.split('\n')
        current_date = None
        current_year = int(file_info["season"].split('-')[0])
        
        # Process line by line
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and match round headers
            if not line or line.startswith('Matchday') or line.startswith('Round') or line.startswith('Group'):
                continue
                
            # Check if line contains a date
            date_match = re.match(r'\s*([A-Za-z]+)\s+([A-Za-z]+)/(\d+)', line)
            if date_match:
                day_of_week, month_name, day = date_match.groups()
                month = MONTH_MAP.get(month_name[:3], 1)  # Default to January if month not recognized
                
                # Handle year rollover (e.g., if May is after August in the same file)
                year = current_year
                if month < 6 and "Aug" in content[:content.find(line)]:
                    year += 1
                
                try:
                    current_date = date(year, month, int(day))
                except ValueError as e:
                    logger.error(f"Invalid date in {file_path}: {line} - {e}")
                    current_date = None
                continue
            
            # Check if line contains match info (time and teams)
            match_info = re.match(r'\s*(\d{1,2}\.\d{2})?\s*([^v]+?)\s+v\s+(.+)', line)
            if match_info and current_date:
                time_str, home_team, away_team = match_info.groups()
                
                # Clean team names
                home_team = home_team.strip()
                away_team = away_team.strip()
                
                # Format time (if available)
                match_time = None
                if time_str:
                    try:
                        hour, minute = map(int, time_str.split('.'))
                        match_time = f"{hour:02d}:{minute:02d}"
                    except (ValueError, AttributeError):
                        logger.warning(f"Invalid time format: {time_str} in {file_path}")
                
                fixtures.append({
                    "competition": file_info["competition_name"],
                    "competition_id": file_info["competition_id"],
                    "competition_type": file_info["competition_type"],
                    "country": file_info["country"],
                    "season": file_info["season"],
                    "match_date": current_date,
                    "match_time": match_time,
                    "home_team": home_team,
                    "away_team": away_team,
                    "venue": None,  # Not available in these files
                    "stage": "Regular Season"
                })
    
    except Exception as e:
        logger.error(f"Error parsing fixture file {file_path}: {e}")
    
    logger.info(f"Extracted {len(fixtures)} fixtures from {file_path}")
    return fixtures

def update_database(fixtures: List[Dict]):
    """Update the database with the parsed fixtures"""
    db = SessionLocal()
    
    try:
        # Maps to keep track of entities
        competitions_map = {}
        clubs_map = {}
        teams_map = {}
        seasons_map = {}
        
        # Create or get competitions
        unique_competitions = {(fixture["competition"], fixture["country"], fixture["competition_type"]) for fixture in fixtures}
        for comp_name, country, comp_type_str in unique_competitions:
            comp = db.query(Competition).filter(
                Competition.name == comp_name,
                Competition.country == country
            ).first()
            
            if not comp:
                # Convert string type to enum
                if comp_type_str == "cup":
                    comp_type = CompetitionType.CUP
                elif comp_type_str == "international":
                    comp_type = CompetitionType.INTERNATIONAL
                else:
                    comp_type = CompetitionType.LEAGUE
                
                comp = Competition(
                    name=comp_name,
                    country=country,
                    competition_type=comp_type
                )
                db.add(comp)
                db.flush()
                logger.info(f"Created new competition: {comp_name} ({country})")
            
            competitions_map[(comp_name, country)] = comp
        
        # Create or get seasons
        unique_seasons = {(fixture["competition"], fixture["country"], fixture["season"]) for fixture in fixtures}
        for comp_name, country, season_name in unique_seasons:
            comp = competitions_map.get((comp_name, country))
            if not comp:
                logger.error(f"Competition not found: {comp_name} ({country})")
                continue
                
            season = db.query(Season).filter(
                Season.season_name == season_name,
                Season.competition_id == comp.id
            ).first()
            
            if not season:
                season_years = season_name.split('-')
                start_year = int(season_years[0])
                end_year = None
                if len(season_years) > 1 and season_years[1]:
                    if len(season_years[1]) == 2:
                        end_year = int(f"20{season_years[1]}")
                    else:
                        end_year = int(season_years[1])
                
                season = Season(
                    season_name=season_name,
                    competition_id=comp.id,
                    year_start=start_year,
                    year_end=end_year
                )
                db.add(season)
                db.flush()
                logger.info(f"Created new season: {season_name} for {comp_name}")
            
            seasons_map[(comp_name, country, season_name)] = season
        
        # Create or get clubs and teams
        unique_clubs = set()
        for fixture in fixtures:
            unique_clubs.add(fixture["home_team"])
            unique_clubs.add(fixture["away_team"])
        
        for club_name in unique_clubs:
            club = db.query(Club).filter(Club.name == club_name).first()
            
            if not club:
                club = Club(
                    name=club_name,
                    founded_year=None,  # Not available
                    stadium_name=None,  # Not available
                    city=None,          # Not available
                    country=None        # Not available
                )
                db.add(club)
                db.flush()
                logger.info(f"Created new club: {club_name}")
            
            # Create team for this club if it doesn't exist
            team = db.query(Team).filter(Team.club_id == club.id).first()
            if not team:
                team = Team(
                    club_id=club.id,
                    team_type="First Team"
                )
                db.add(team)
                db.flush()
                logger.info(f"Created new team for club: {club_name}")
            
            clubs_map[club_name] = club
            teams_map[club_name] = team
        
        # Now create or update fixtures
        fixture_count = 0
        for fixture_data in fixtures:
            comp_name = fixture_data["competition"]
            country = fixture_data["country"]
            season_name = fixture_data["season"]
            
            season = seasons_map.get((comp_name, country, season_name))
            if not season:
                logger.error(f"Season not found: {season_name} for {comp_name}")
                continue
                
            home_team = teams_map.get(fixture_data["home_team"])
            away_team = teams_map.get(fixture_data["away_team"])
            
            if not home_team or not away_team:
                logger.error(f"Team not found: {fixture_data['home_team']} or {fixture_data['away_team']}")
                continue
            
            # Check if fixture already exists
            existing_fixture = db.query(Fixture).filter(
                Fixture.season_id == season.id,
                Fixture.home_team_id == home_team.id,
                Fixture.away_team_id == away_team.id
            ).first()
            
            if existing_fixture:
                # Update existing fixture
                existing_fixture.match_date = fixture_data["match_date"]
                existing_fixture.match_time = fixture_data["match_time"]
                existing_fixture.stage = fixture_data["stage"]
                db.flush()
                logger.info(f"Updated fixture: {fixture_data['home_team']} vs {fixture_data['away_team']} on {fixture_data['match_date']}")
            else:
                # Create new fixture
                new_fixture = Fixture(
                    season_id=season.id,
                    match_date=fixture_data["match_date"],
                    match_time=fixture_data["match_time"],
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    stage=fixture_data["stage"],
                    venue=fixture_data["venue"],
                    is_completed=False  # Assuming all fixtures are upcoming
                )
                db.add(new_fixture)
                db.flush()
                fixture_count += 1
        
        db.commit()
        logger.info(f"Successfully added {fixture_count} new fixtures to the database")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating database: {e}")
        raise
    finally:
        db.close()

def update_fixture_dates():
    """Update fixture dates to ensure they're in the future (for demo purposes)"""
    db = SessionLocal()
    
    try:
        today = date.today()
        year_diff = today.year - 2023  # Assuming most fixtures are from 2023/24 season
        
        # Get all fixtures
        all_fixtures = db.query(Fixture).all()
        updated_count = 0
        
        for fixture in all_fixtures:
            # Skip if already in the future
            if fixture.match_date and fixture.match_date > today:
                continue
                
            # Adjust the year but keep month and day
            if fixture.match_date:
                try:
                    new_date = date(today.year, fixture.match_date.month, fixture.match_date.day)
                    
                    # If the new date is in the past, add 1 year
                    if new_date < today:
                        new_date = date(today.year + 1, fixture.match_date.month, fixture.match_date.day)
                    
                    fixture.match_date = new_date
                    updated_count += 1
                except ValueError:
                    # Handle invalid dates (e.g., Feb 29 in non-leap year)
                    logger.warning(f"Invalid date conversion for fixture ID {fixture.id}: {fixture.match_date}")
        
        db.commit()
        logger.info(f"Updated dates for {updated_count} fixtures")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating fixture dates: {e}")
    finally:
        db.close()

def main():
    """Main function to run the data import process"""
    logger.info("Starting fixture data synchronization")
    
    # Find league fixture files
    league_files = find_league_files()
    
    if not league_files:
        logger.error("No league files found. Check the raw data directories.")
        return
    
    # Parse fixtures from all files
    all_fixtures = []
    for file_info in league_files:
        fixtures = parse_fixture_file(file_info)
        all_fixtures.extend(fixtures)
    
    logger.info(f"Total fixtures parsed: {len(all_fixtures)}")
    
    # Update database with parsed fixtures
    if all_fixtures:
        update_database(all_fixtures)
        
        # Update fixture dates to ensure they're in the future
        update_fixture_dates()
    
    logger.info("Fixture data synchronization completed")

if __name__ == "__main__":
    main() 
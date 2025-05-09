#!/usr/bin/env python3

import os
import sys
import logging
import re
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.models import Fixture, Team, Club, Competition, Season, MatchResult

# Raw data directory
RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")

# Country mappings
COUNTRY_MAPPINGS = {
    "eng-england": "England",
    "es-espana": "Spain",
    "de-deutschland": "Germany",
    "it-italy": "Italy",
    "fr-france": "France",
    "champions-league": "Europe",
    "europa-league": "Europe",
    "world-cup": "World"
}

# Competition mappings
COMPETITION_MAPPINGS = {
    "eng-england": "Premier League",
    "es-espana": "La Liga",
    "de-deutschland": "Bundesliga",
    "it-italy": "Serie A",
    "fr-france": "Ligue 1",
    "champions-league": "Champions League",
    "europa-league": "Europa League",
    "world-cup": "World Cup"
}

def find_league_directories() -> List[Tuple[str, str, str]]:
    """Find all league directories and their latest season folders."""
    leagues = []
    
    for country_dir in os.listdir(RAW_DATA_DIR):
        country_path = os.path.join(RAW_DATA_DIR, country_dir)
        
        if not os.path.isdir(country_path) or country_dir.startswith('.'):
            continue
            
        # Skip directories we don't need
        if country_dir not in COUNTRY_MAPPINGS:
            continue
            
        # Find season directories (like 2023-24, 2022-23, etc.)
        seasons = []
        for item in os.listdir(country_path):
            season_path = os.path.join(country_path, item)
            if os.path.isdir(season_path) and re.match(r'^\d{4}-\d{2}$', item):
                seasons.append(item)
                
        if seasons:
            # Sort seasons and get the latest 3 seasons
            seasons.sort(reverse=True)
            # Look back up to 3 seasons, including current season, to get historical data
            for season in seasons[:3]:  # Take up to 3 most recent seasons
                leagues.append((country_dir, season, os.path.join(country_path, season)))
            
    return leagues

def parse_match_result(result_line: str) -> Tuple[Optional[int], Optional[int]]:
    """Parse the match result from a result line."""
    # Example: "2-1", "1-1", etc.
    if not result_line or result_line == "?-?":
        return None, None
        
    try:
        parts = result_line.strip().split('-')
        if len(parts) == 2:
            return int(parts[0].strip()), int(parts[1].strip())
    except ValueError:
        pass
        
    return None, None

def parse_historical_matches(file_path: str) -> List[Dict]:
    """Parse a league file to extract historical matches."""
    matches = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        current_date = None
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Date line
            if re.match(r'^[A-Z][a-z]{2} \d{1,2}$', line):
                # Handle month/day format like "Aug 19"
                current_date = line
                continue
                
            # Match line
            match_data = re.match(r'^(?:\[\d+\.\]\s+)?([^0-9]+[^\s])\s+(\d+)-(\d+)\s+([^0-9]+[^\s])\s*(?:\[.+\])?$', line)
            if match_data:
                home_team, home_score, away_score, away_team = match_data.groups()
                
                # Clean team names
                home_team = home_team.strip()
                away_team = away_team.strip()
                
                # Create match dict
                match = {
                    "date": current_date,
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_score": int(home_score),
                    "away_score": int(away_score),
                    "completed": True
                }
                
                matches.append(match)
                continue
                
            # Match with time
            match_with_time = re.match(r'^(?:\[\d+\.\]\s+)?([^0-9]+[^\s])\s+(\d+:\d+)\s+([^0-9]+[^\s])$', line)
            if match_with_time:
                # This is a future match, skip it
                continue
                
    except Exception as e:
        logger.error(f"Error parsing file {file_path}: {e}")
        
    return matches

def process_league(league_tuple: Tuple[str, str, str], db: Session) -> int:
    """Process a league directory to import historical match results."""
    country_dir, season_name, league_path = league_tuple
    
    # Get country and competition names
    country = COUNTRY_MAPPINGS.get(country_dir)
    competition_name = COMPETITION_MAPPINGS.get(country_dir)
    
    if not country or not competition_name:
        logger.warning(f"Unknown country/competition: {country_dir}")
        return 0
        
    # Find the competition in database
    competition = db.query(Competition).filter(
        Competition.name == competition_name,
        Competition.country == country
    ).first()
    
    if not competition:
        logger.warning(f"Competition not found in database: {competition_name} ({country})")
        return 0
        
    # Find or create season
    season = db.query(Season).filter(
        Season.competition_id == competition.id,
        Season.season_name == season_name
    ).first()
    
    if not season:
        logger.warning(f"Season not found in database: {season_name} for {competition_name}")
        return 0
        
    # Look for results files
    imported_count = 0
    
    # Main league file (e.g., 1-premierleague.txt)
    main_files = [f for f in os.listdir(league_path) if f.endswith('.txt') and not f.startswith('.')]
    
    for file_name in main_files:
        file_path = os.path.join(league_path, file_name)
        logger.info(f"Processing file: {file_path}")
        
        # Parse historical matches
        matches = parse_historical_matches(file_path)
        logger.info(f"Found {len(matches)} historical matches in {file_path}")
        
        # Add results to database
        for match in matches:
            # Get teams
            home_club = db.query(Club).filter(Club.name == match["home_team"]).first()
            away_club = db.query(Club).filter(Club.name == match["away_team"]).first()
            
            if not home_club or not away_club:
                logger.warning(f"Club not found: {match['home_team']} or {match['away_team']}")
                continue
                
            home_team = db.query(Team).filter(Team.club_id == home_club.id).first()
            away_team = db.query(Team).filter(Team.club_id == away_club.id).first()
            
            if not home_team or not away_team:
                logger.warning(f"Team not found for clubs: {home_club.name} or {away_club.name}")
                continue
                
            # Find fixture in database
            fixture = db.query(Fixture).filter(
                Fixture.season_id == season.id,
                Fixture.home_team_id == home_team.id,
                Fixture.away_team_id == away_team.id
            ).first()
            
            if not fixture:
                # Create fixture if it doesn't exist
                fixture = Fixture(
                    season_id=season.id,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    match_date=date.today(),  # Placeholder date
                    match_time="00:00",
                    is_completed=True
                )
                db.add(fixture)
                db.flush()
                
            # Check if result already exists
            existing_result = db.query(MatchResult).filter(
                MatchResult.fixture_id == fixture.id
            ).first()
            
            if existing_result:
                logger.info(f"Result already exists for fixture {fixture.id}")
                continue
                
            # Create match result
            result = MatchResult(
                fixture_id=fixture.id,
                home_score=match["home_score"],
                away_score=match["away_score"],
                home_xg=None,
                away_xg=None
            )
            
            # Update fixture
            fixture.is_completed = True
            
            db.add(result)
            imported_count += 1
            
            if imported_count % 100 == 0:
                logger.info(f"Imported {imported_count} results so far...")
                
    return imported_count

def import_historical_results():
    """Import historical match results from raw data files."""
    logger.info("Starting import of historical match results")
    
    # Find league directories
    leagues = find_league_directories()
    logger.info(f"Found {len(leagues)} leagues to process")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Process each league
        total_imported = 0
        
        for league in leagues:
            country_dir, season_name, _ = league
            logger.info(f"Processing league: {country_dir}, season: {season_name}")
            
            imported = process_league(league, db)
            total_imported += imported
            
            logger.info(f"Imported {imported} results for {country_dir}")
            
        # Commit changes
        db.commit()
        logger.info(f"Successfully imported {total_imported} historical match results")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error importing historical results: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import_historical_results() 
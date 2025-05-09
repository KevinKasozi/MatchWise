#!/usr/bin/env python3

import os
import sys
import re
import glob
from datetime import datetime, date, timedelta
import logging
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
import time
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, func, or_, and_
from sqlalchemy.orm import sessionmaker, joinedload
from app.models.models import Base, Fixture, Team, Club, Competition, Season, CompetitionType

# Database connection string
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/football_predictor")
logger.info(f"Using database: {DATABASE_URL}")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Raw data paths
RAW_DATA_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")

# Month name to number mapping
MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
}

# League folder to country mapping
COUNTRY_MAP = {
    "eng-england": "England",
    "es-espana": "Spain",
    "de-deutschland": "Germany",
    "it-italy": "Italy",
    "fr-france": "France",
    "champions-league": "Europe",
    "europa-league": "Europe"
}

# Competition file to name mapping
COMPETITION_MAP = {
    # England
    "1-premierleague": {"name": "Premier League", "type": CompetitionType.LEAGUE},
    "2-championship": {"name": "Championship", "type": CompetitionType.LEAGUE},
    "3-league1": {"name": "League One", "type": CompetitionType.LEAGUE},
    "4-league2": {"name": "League Two", "type": CompetitionType.LEAGUE},
    "5-nationalleague": {"name": "National League", "type": CompetitionType.LEAGUE},
    "facup": {"name": "FA Cup", "type": CompetitionType.CUP},
    "eflcup": {"name": "EFL Cup", "type": CompetitionType.CUP},
    
    # Spain
    "1-liga": {"name": "La Liga", "type": CompetitionType.LEAGUE},
    "2-liga2": {"name": "La Liga 2", "type": CompetitionType.LEAGUE},
    "cup": {"name": "Copa del Rey", "type": CompetitionType.CUP},
    
    # Germany
    "1-bundesliga": {"name": "Bundesliga", "type": CompetitionType.LEAGUE},
    "2-bundesliga2": {"name": "2. Bundesliga", "type": CompetitionType.LEAGUE},
    "3-liga3": {"name": "3. Liga", "type": CompetitionType.LEAGUE},
    
    # Italy
    "1-seriea": {"name": "Serie A", "type": CompetitionType.LEAGUE},
    "2-serieb": {"name": "Serie B", "type": CompetitionType.LEAGUE},
    "3-seriec_a": {"name": "Serie C - Group A", "type": CompetitionType.LEAGUE},
    "3-seriec_b": {"name": "Serie C - Group B", "type": CompetitionType.LEAGUE},
    "3-seriec_c": {"name": "Serie C - Group C", "type": CompetitionType.LEAGUE},
    
    # France
    "fr1": {"name": "Ligue 1", "type": CompetitionType.LEAGUE},
    "fr2": {"name": "Ligue 2", "type": CompetitionType.LEAGUE},
    
    # European competitions
    "cl": {"name": "Champions League", "type": CompetitionType.CUP},
    "el": {"name": "Europa League", "type": CompetitionType.CUP}
}

def find_latest_season_dirs() -> List[Dict]:
    """Find the latest season directory for each league folder"""
    league_dirs = []
    
    # Process main leagues
    for league_folder in ["eng-england", "es-espana", "de-deutschland", "it-italy", "champions-league", "europa-league"]:
        league_path = os.path.join(RAW_DATA_ROOT, league_folder)
        if not os.path.exists(league_path):
            logger.warning(f"League directory not found: {league_path}")
            continue
            
        # Find all season directories
        season_dirs = []
        for item in os.listdir(league_path):
            if re.match(r'^\d{4}-\d{2}$', item):
                season_dirs.append(item)
        
        if not season_dirs:
            logger.warning(f"No season directories found for {league_folder}")
            continue
            
        # Sort by season year (most recent first)
        season_dirs.sort(reverse=True)
        latest_season = season_dirs[0]
        
        league_dirs.append({
            "league_folder": league_folder,
            "path": os.path.join(league_path, latest_season),
            "season_name": latest_season,
            "country": COUNTRY_MAP.get(league_folder, "Unknown")
        })
    
    # Process French league which has a different structure
    fr_league_path = os.path.join(RAW_DATA_ROOT, "fr-france", "france")
    if os.path.exists(fr_league_path):
        # Find all season directories
        season_dirs = []
        for item in os.listdir(fr_league_path):
            if re.match(r'^\d{4}-\d{2}$', item):
                season_dirs.append(item)
        
        if season_dirs:
            # Sort by season year (most recent first)
            season_dirs.sort(reverse=True)
            latest_season = season_dirs[0]
            
            league_dirs.append({
                "league_folder": "fr-france",
                "path": os.path.join(fr_league_path, latest_season),
                "season_name": latest_season,
                "country": "France"
            })
    
    logger.info(f"Found {len(league_dirs)} league directories with latest seasons")
    return league_dirs

def find_competition_files(league_dirs: List[Dict]) -> List[Dict]:
    """Find all competition files in the latest season directories"""
    competition_files = []
    
    for league_dir in league_dirs:
        path = league_dir["path"]
        league_folder = league_dir["league_folder"]
        season_name = league_dir["season_name"]
        country = league_dir["country"]
        
        # Find all .txt files in the season directory
        for file_path in glob.glob(os.path.join(path, "*.txt")):
            filename = os.path.basename(file_path)
            
            # Skip README and other non-competition files
            if filename.startswith("README") or filename.startswith("."):
                continue
                
            # Handle French league's different naming
            if league_folder == "fr-france":
                comp_id = filename.split("_")[0]
            else:
                comp_id = os.path.splitext(filename)[0]
                
            # Get competition info
            comp_info = COMPETITION_MAP.get(comp_id)
            if not comp_info:
                # Try to infer from filename
                if "cup" in filename.lower():
                    comp_type = CompetitionType.CUP
                else:
                    comp_type = CompetitionType.LEAGUE
                    
                comp_name = comp_id.replace("-", " ").title()
                comp_info = {"name": comp_name, "type": comp_type}
            
            competition_files.append({
                "file_path": file_path,
                "league_folder": league_folder,
                "season_name": season_name,
                "competition_id": comp_id,
                "competition_name": comp_info["name"],
                "competition_type": comp_info["type"],
                "country": country
            })
    
    logger.info(f"Found {len(competition_files)} competition files")
    return competition_files

def parse_fixture_file(file_info: Dict) -> List[Dict]:
    """Parse a fixture file and extract match data"""
    fixtures = []
    file_path = file_info["file_path"]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        lines = content.split('\n')
        current_date = None
        current_year = int(file_info["season_name"].split('-')[0])
        current_matchday = None
        
        # Process line by line
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Check for matchday
            if line.startswith('Matchday') or line.startswith('Round') or line.startswith('» Matchday') or line.startswith('Group'):
                current_matchday = line.split()[1] if len(line.split()) > 1 else "Unknown"
                continue
                
            # Check if line contains a date
            date_match = re.match(r'\s*(?:[A-Za-z]+\s+)?([A-Za-z]+)/(\d+)(?:\s+\d{4})?', line)
            if date_match:
                month_name, day = date_match.groups()
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
            match_info = re.match(r'\s*(\d{1,2}\.\d{2})?\s*([^v]+?)\s+v\s+(.+?)(?:\s+\d+-\d+.*)?$', line)
            if match_info and current_date:
                time_str, home_team, away_team = match_info.groups()
                
                # Clean team names
                home_team = home_team.strip()
                away_team = away_team.strip()
                
                # Handle score if present (in format like "2-1 (1-0)")
                match_score = re.search(r'(\d+-\d+)(?:\s+\((\d+-\d+)\))?$', line)
                is_completed = bool(match_score)
                
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
                    "season": file_info["season_name"],
                    "match_date": current_date,
                    "match_time": match_time,
                    "home_team": home_team,
                    "away_team": away_team,
                    "venue": None,  # Not available in these files
                    "stage": current_matchday or "Regular Season",
                    "is_completed": is_completed
                })
    
    except Exception as e:
        logger.error(f"Error parsing fixture file {file_path}: {e}")
    
    logger.info(f"Extracted {len(fixtures)} fixtures from {file_path}")
    return fixtures

def validate_team_country(team_name, fixture_data, club_countries):
    """Validate that a team is assigned to the correct country based on raw data"""
    assigned_country = fixture_data["country"]
    
    # If we've seen this club before and know its correct country
    if team_name in club_countries:
        correct_country = club_countries[team_name]
        # If the team is assigned to the wrong country
        if correct_country != assigned_country:
            logger.warning(f"Team {team_name} should be in {correct_country}, not {assigned_country}")
            return correct_country
    
    # Use the assigned country but store it for future reference
    club_countries[team_name] = assigned_country
    return assigned_country

def save_to_database(all_fixtures: List[Dict]) -> None:
    """Save all fixtures to the database"""
    db = SessionLocal()
    
    try:
        start_time = time.time()
        logger.info("Starting database update...")
        
        # Maps to keep track of entities
        competitions_map = {}  # (name, country) -> Competition
        seasons_map = {}       # (competition_id, season_name) -> Season
        clubs_map = {}         # name -> Club
        teams_map = {}         # club_id -> Team
        
        # 1. Process all competitions
        unique_competitions = {(fixture["competition"], fixture["country"], fixture["competition_type"]) 
                             for fixture in all_fixtures}
        logger.info(f"Processing {len(unique_competitions)} unique competitions")
        
        for comp_name, country, comp_type in unique_competitions:
            comp = db.query(Competition).filter(
                Competition.name == comp_name,
                Competition.country == country
            ).first()
            
            if not comp:
                logger.info(f"Creating new competition: {comp_name} ({country})")
                comp = Competition(
                    name=comp_name,
                    country=country,
                    competition_type=comp_type
                )
                db.add(comp)
                db.flush()
            
            competitions_map[(comp_name, country)] = comp
        
        # 2. Process all seasons
        unique_seasons = {(fixture["competition"], fixture["country"], fixture["season"]) 
                         for fixture in all_fixtures}
        logger.info(f"Processing {len(unique_seasons)} unique seasons")
        
        for comp_name, country, season_name in unique_seasons:
            comp = competitions_map.get((comp_name, country))
            if not comp:
                logger.error(f"Competition not found: {comp_name} ({country})")
                continue
                
            season = db.query(Season).filter(
                Season.competition_id == comp.id,
                Season.season_name == season_name
            ).first()
            
            if not season:
                season_years = season_name.split('-')
                year_start = int(season_years[0])
                year_end = None
                if len(season_years) > 1 and season_years[1]:
                    if len(season_years[1]) == 2:
                        year_end = int(f"20{season_years[1]}")
                    else:
                        year_end = int(season_years[1])
                
                logger.info(f"Creating new season: {season_name} for {comp_name}")
                season = Season(
                    competition_id=comp.id,
                    season_name=season_name,
                    year_start=year_start,
                    year_end=year_end
                )
                db.add(season)
                db.flush()
            
            seasons_map[(comp.id, season_name)] = season
        
        # 3. Process all clubs and teams
        unique_clubs = {name for fixture in all_fixtures 
                       for name in (fixture["home_team"], fixture["away_team"])}
        logger.info(f"Processing {len(unique_clubs)} unique clubs")
        
        # Track the correct country for each club
        club_countries = {}
        # Load country assignments from file if available
        country_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "club_countries.json")
        if os.path.exists(country_file):
            try:
                with open(country_file, 'r') as f:
                    club_countries = json.load(f)
                logger.info(f"Loaded {len(club_countries)} club country assignments")
            except Exception as e:
                logger.error(f"Error loading club countries: {e}")
        
        for club_name in unique_clubs:
            club = db.query(Club).filter(Club.name == club_name).first()
            
            if not club:
                logger.info(f"Creating new club: {club_name}")
                club = Club(
                    name=club_name,
                    founded_year=None,  # Not available
                    stadium_name=None,  # Not available
                    city=None,          # Not available
                    country=None        # Not available
                )
                db.add(club)
                db.flush()
            
            clubs_map[club_name] = club
            
            # Create team for this club if it doesn't exist
            team = db.query(Team).filter(Team.club_id == club.id).first()
            if not team:
                logger.info(f"Creating new team for club: {club_name}")
                team = Team(
                    club_id=club.id,
                    team_type="First Team"
                )
                db.add(team)
                db.flush()
            
            teams_map[club.id] = team
        
        # 4. Create or update fixtures
        processed_count = 0
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        # First, prepare upcoming fixture dates for validation
        upcoming_fixture_dates = {}
        for fixture in all_fixtures:
            # Only use future fixtures for date reference
            if fixture["match_date"] and fixture["match_date"] >= date.today():
                key = (fixture["competition"], fixture["country"], fixture["home_team"], fixture["away_team"])
                if key not in upcoming_fixture_dates or fixture["match_date"] < upcoming_fixture_dates[key]:
                    upcoming_fixture_dates[key] = fixture["match_date"]
        
        # Process all fixtures
        for fixture_data in all_fixtures:
            processed_count += 1
            if processed_count % 100 == 0:
                logger.info(f"Processed {processed_count}/{len(all_fixtures)} fixtures")
            
            comp_name = fixture_data["competition"]
            country = fixture_data["country"]
            season_name = fixture_data["season"]
            
            # Validate country for home and away teams
            home_team = fixture_data["home_team"]
            away_team = fixture_data["away_team"]
            
            home_country = validate_team_country(home_team, fixture_data, club_countries)
            away_country = validate_team_country(away_team, fixture_data, club_countries)
            
            # If both teams are from the same country but it's different from the fixture country,
            # change the fixture's country to match the teams
            if home_country == away_country and home_country != country:
                logger.warning(f"Fixing competition country for {home_team} vs {away_team}")
                logger.warning(f"  From: {country} to: {home_country}")
                country = home_country
                
                # Find the correct competition in the home country
                correct_comp = None
                for (c_name, c_country), comp in competitions_map.items():
                    if c_country == country and c_name.lower() == comp_name.lower():
                        correct_comp = comp
                        break
                
                if correct_comp:
                    comp = correct_comp
                    comp_name = comp.name
                else:
                    # Try to find a similar competition type in the correct country
                    for (c_name, c_country), comp in competitions_map.items():
                        if c_country == country and comp.competition_type == fixture_data["competition_type"]:
                            correct_comp = comp
                            comp_name = comp.name
                            logger.warning(f"  Using similar competition: {comp_name}")
                            break
            
            comp = competitions_map.get((comp_name, country))
            if not comp:
                logger.error(f"Competition not found: {comp_name} ({country})")
                skipped_count += 1
                continue
                
            season = seasons_map.get((comp.id, season_name))
            if not season:
                logger.error(f"Season not found: {season_name} for {comp_name}")
                skipped_count += 1
                continue
                
            home_club = clubs_map.get(fixture_data["home_team"])
            away_club = clubs_map.get(fixture_data["away_team"])
            
            if not home_club or not away_club:
                logger.error(f"Club not found: {fixture_data['home_team']} or {fixture_data['away_team']}")
                skipped_count += 1
                continue
                
            home_team = teams_map.get(home_club.id)
            away_team = teams_map.get(away_club.id)
            
            if not home_team or not away_team:
                logger.error(f"Team not found for clubs: {fixture_data['home_team']} or {fixture_data['away_team']}")
                skipped_count += 1
                continue
            
            # Get the correct date for this fixture (use today's year)
            match_date = fixture_data["match_date"]
            if match_date:
                # For upcoming fixtures in the past, adjust to this year or next
                today = date.today()
                if match_date < today:
                    try:
                        # Use the same month and day, but with current year
                        adjusted_date = date(today.year, match_date.month, match_date.day)
                        
                        # If this date is still in the past, try next year
                        if adjusted_date < today:
                            adjusted_date = date(today.year + 1, match_date.month, match_date.day)
                        
                        match_date = adjusted_date
                    except ValueError:
                        # Handle invalid dates (e.g., Feb 29 in non-leap year)
                        logger.warning(f"Invalid date conversion for fixture: {fixture_data['home_team']} vs {fixture_data['away_team']}")
            
            # Check if fixture already exists
            existing_fixture = db.query(Fixture).filter(
                Fixture.season_id == season.id,
                Fixture.home_team_id == home_team.id,
                Fixture.away_team_id == away_team.id
            ).first()
            
            if existing_fixture:
                # Only update if we need to change the date or other details
                needs_update = False
                
                # Check if date needs to be updated
                if match_date and existing_fixture.match_date != match_date:
                    existing_fixture.match_date = match_date
                    needs_update = True
                
                # Update match time if available
                if fixture_data["match_time"] and existing_fixture.match_time != fixture_data["match_time"]:
                    existing_fixture.match_time = fixture_data["match_time"]
                    needs_update = True
                
                # Update completion status if needed
                if existing_fixture.is_completed != fixture_data["is_completed"]:
                    existing_fixture.is_completed = fixture_data["is_completed"]
                    needs_update = True
                
                if needs_update:
                    updated_count += 1
                    logger.debug(f"Updated fixture: {fixture_data['home_team']} vs {fixture_data['away_team']} on {match_date}")
            else:
                # Create new fixture
                new_fixture = Fixture(
                    season_id=season.id,
                    match_date=match_date,
                    match_time=fixture_data["match_time"],
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    stage=fixture_data["stage"],
                    venue=fixture_data["venue"],
                    is_completed=fixture_data["is_completed"]
                )
                
                db.add(new_fixture)
                created_count += 1
                logger.debug(f"Created new fixture: {fixture_data['home_team']} vs {fixture_data['away_team']} on {match_date}")
        
        # Save club country mappings
        country_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "club_countries.json")
        try:
            with open(country_file, 'w') as f:
                json.dump(club_countries, f, indent=2)
            logger.info(f"Saved {len(club_countries)} club country assignments")
        except Exception as e:
            logger.error(f"Error saving club countries: {e}")
        
        # Commit the changes
        db.commit()
        end_time = time.time()
        
        logger.info(f"Database update completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Processed {processed_count} fixtures:")
        logger.info(f"  - Created: {created_count}")
        logger.info(f"  - Updated: {updated_count}")
        logger.info(f"  - Skipped: {skipped_count}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating database: {e}")
        raise
    finally:
        db.close()

def validate_fixtures() -> None:
    """Validate that fixtures in the database match the raw data"""
    db = SessionLocal()
    
    try:
        logger.info("Validating fixtures...")
        
        # Check upcoming fixtures
        tomorrow = date.today() + timedelta(days=1)
        
        # Get Premier League competition
        premier_league = db.query(Competition).filter(
            Competition.name == "Premier League",
            Competition.country == "England"
        ).first()
        
        if premier_league:
            # Check Premier League fixtures for tomorrow
            pl_fixtures = db.query(Fixture).join(Season).filter(
                Season.competition_id == premier_league.id,
                Fixture.match_date == tomorrow
            ).options(
                joinedload(Fixture.home_team).joinedload(Team.club),
                joinedload(Fixture.away_team).joinedload(Team.club)
            ).all()
            
            logger.info(f"Found {len(pl_fixtures)} Premier League fixtures for tomorrow ({tomorrow}):")
            for fixture in pl_fixtures:
                home_team = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else "Unknown"
                away_team = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else "Unknown"
                time = fixture.match_time or "Unknown time"
                logger.info(f"  - {home_team} vs {away_team} at {time}")
        
        # Check La Liga fixtures for tomorrow
        la_liga = db.query(Competition).filter(
            Competition.name == "La Liga",
            Competition.country == "Spain"
        ).first()
        
        if la_liga:
            la_liga_fixtures = db.query(Fixture).join(Season).filter(
                Season.competition_id == la_liga.id,
                Fixture.match_date == tomorrow
            ).options(
                joinedload(Fixture.home_team).joinedload(Team.club),
                joinedload(Fixture.away_team).joinedload(Team.club)
            ).all()
            
            logger.info(f"Found {len(la_liga_fixtures)} La Liga fixtures for tomorrow ({tomorrow}):")
            for fixture in la_liga_fixtures:
                home_team = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else "Unknown"
                away_team = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else "Unknown"
                time = fixture.match_time or "Unknown time"
                logger.info(f"  - {home_team} vs {away_team} at {time}")
        
        # Count total fixtures for tomorrow
        total_fixtures = db.query(Fixture).filter(Fixture.match_date == tomorrow).count()
        logger.info(f"Total fixtures for tomorrow ({tomorrow}): {total_fixtures}")
        
    except Exception as e:
        logger.error(f"Error validating fixtures: {e}")
    finally:
        db.close()

def main():
    """Main function to run the data import process"""
    logger.info("Starting fixture data synchronization")
    
    # 1. Find latest season directories
    league_dirs = find_latest_season_dirs()
    
    # 2. Find all competition files
    competition_files = find_competition_files(league_dirs)
    
    # 3. Parse all fixture files
    all_fixtures = []
    for file_info in competition_files:
        fixtures = parse_fixture_file(file_info)
        all_fixtures.extend(fixtures)
    
    logger.info(f"Total fixtures parsed: {len(all_fixtures)}")
    
    # 4. Save to database
    if all_fixtures:
        save_to_database(all_fixtures)
        
        # 5. Validate the fixtures
        validate_fixtures()
    
    logger.info("Fixture data synchronization completed successfully")

if __name__ == "__main__":
    main() 
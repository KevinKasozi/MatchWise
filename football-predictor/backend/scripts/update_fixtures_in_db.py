#!/usr/bin/env python3

import os
import re
import sys
import datetime
from datetime import date, timedelta
from pathlib import Path
import glob
import random
from sqlalchemy import create_engine, and_, or_, func, text
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.models import Fixture, Team, Club, Competition, Season
from app.core.config import settings

# Set the raw data directory
RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"

# Get dates for the next 7 days
today = date.today()
date_range = [today + timedelta(days=i) for i in range(7)]  # Today + next 6 days

# Month mapping for text to number conversion
MONTH_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
}

# Format dates for matching in the data files
print(f"Looking for matches for the next 7 days starting {today.strftime('%A, %B %d')}...")
print("Searching for dates:")
for d in date_range:
    month = d.strftime("%b").lower()
    day = d.day
    print(f"  - {month}/{day} ({d.strftime('%A, %B %d')})")

# Competition mapping for better display
COMPETITION_NAMES = {
    'premierleague': 'Premier League',
    'bundesliga': 'Bundesliga',
    'seriea': 'Serie A',
    'liga': 'La Liga',
    'ligue1': 'Ligue 1',
    'championship': 'Championship',
    'cl': 'Champions League',
    'el': 'Europa League',
    'conf': 'Conference League',
    'cup': 'Domestic Cup',
    'liga1': 'Liga 1',
    'liga2': 'Liga 2',
    'liga3': 'Liga 3',
    'league1': 'League One',
    'league2': 'League Two',
    'nationalleague': 'National League',
    'bundesliga2': 'Bundesliga 2',
    'serieb': 'Serie B'
}

# Country mapping
COUNTRY_NAMES = {
    'eng-england': 'England',
    'de-deutschland': 'Germany',
    'it-italy': 'Italy',
    'es-espana': 'Spain',
    'fr-france': 'France',
    'champions-league': 'Europe',
    'europa-league': 'Europe'
}

def get_competition_name(file_path):
    """Extract competition name from file path"""
    file_name = os.path.basename(file_path).replace('.txt', '')
    
    # Handle formats like "1-premierleague.txt"
    if '-' in file_name:
        parts = file_name.split('-')
        if len(parts) > 1:
            file_name = parts[1]
    
    # Get proper name from mapping
    for key, value in COMPETITION_NAMES.items():
        if key.lower() in file_name.lower():
            return value
    
    return file_name.capitalize()

def get_country_name(file_path):
    """Extract country name from file path"""
    # Get the parent directory (country code)
    parent_dir = os.path.basename(os.path.dirname(os.path.dirname(file_path)))
    
    # Get proper name from mapping
    for key, value in COUNTRY_NAMES.items():
        if key.lower() == parent_dir.lower():
            return value
    
    return parent_dir.capitalize()

def get_season(file_path):
    """Extract season from file path"""
    # The season is the parent directory
    return os.path.basename(os.path.dirname(file_path))

def parse_fixtures(file_path):
    """Parse fixtures from a file for matches in the next 7 days"""
    fixtures = []
    current_date = None
    current_matchday = None
    season = get_season(file_path)
    competition = get_competition_name(file_path)
    country = get_country_name(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            
        in_fixture_section = False
        day_of_week = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Check for matchday
            if line.startswith("»") or line.startswith("="):
                current_matchday = line.replace("»", "").replace("=", "").strip()
                in_fixture_section = False
                
            # Check for date line
            elif re.match(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\w+/\d+', line):
                date_parts = line.split()
                day_of_week = date_parts[0]
                date_str = date_parts[1]  # Format like May/10
                
                # Extract month and day
                try:
                    date_match = re.match(r'(\w+)/(\d+)', date_str)
                    if date_match:
                        month_text, day = date_match.groups()
                        month_text = month_text.lower()
                        day = int(day)
                        
                        # Try to match this date with any in our date range
                        match_found = False
                        for match_date in date_range:
                            match_month_text = match_date.strftime("%b").lower()
                            match_day = match_date.day
                            
                            # Check standard format (may/10)
                            if month_text == match_month_text and day == match_day:
                                current_date = match_date
                                in_fixture_section = True
                                match_found = True
                                break
                                
                            # Try alternate month formats (full month name)
                            elif month_text in match_date.strftime("%B").lower() and day == match_day:
                                current_date = match_date
                                in_fixture_section = True
                                match_found = True
                                break
                                
                        if not match_found:
                            # If no match to the current date range, try to create a future date in the current year
                            try:
                                # Get the month number
                                if month_text in MONTH_MAP:
                                    month_num = MONTH_MAP[month_text]
                                else:
                                    # Try to match partial month name to a month number
                                    for month_name, num in MONTH_MAP.items():
                                        if month_text in month_name or month_name in month_text:
                                            month_num = num
                                            break
                                    else:
                                        month_num = None
                                
                                if month_num:
                                    # Create the date using the current year
                                    current_year = date.today().year
                                    try:
                                        fixture_date = date(current_year, month_num, day)
                                        
                                        # If the fixture date is in the past this year, use next year
                                        if fixture_date < date.today():
                                            fixture_date = date(current_year + 1, month_num, day)
                                            
                                        # Use this date if it's at most 6 months in the future
                                        future_cutoff = date.today() + timedelta(days=180)
                                        if fixture_date <= future_cutoff:
                                            current_date = fixture_date
                                            in_fixture_section = True
                                            match_found = True
                                    except ValueError:
                                        # Handle invalid dates like Feb 29 in non-leap years
                                        pass
                            except Exception as e:
                                print(f"Error creating date for {month_text}/{day}: {e}")
                            
                            if not match_found:
                                in_fixture_section = False
                
                except Exception as e:
                    print(f"Error parsing date {date_str}: {e}")
                    in_fixture_section = False
                
            # Process fixture lines if we're in the right date section
            elif in_fixture_section:
                # Check for time format (e.g., "15.00")
                time_match = re.match(r'^\s*(\d+\.\d+)', line)
                if time_match:
                    # Try to match different fixture formats
                    
                    # Format: "15.00  Team A  v  Team B"
                    match1 = re.match(r'^\s*(\d+\.\d+)\s+(.*?)\s+v\s+(.*?)$', line)
                    if match1:
                        time, home_team, away_team = match1.groups()
                        home_team = home_team.strip()
                        away_team = away_team.strip()
                    else:
                        # Format: "15.00  Team A  -  Team B"
                        match2 = re.match(r'^\s*(\d+\.\d+)\s+(.*?)\s+-\s+(.*?)$', line)
                        if match2:
                            time, home_team, away_team = match2.groups()
                            home_team = home_team.strip()
                            away_team = away_team.strip()
                        else:
                            # Check for score formats (for completed matches)
                            match3 = re.match(r'^\s*(\d+\.\d+)\s+(.*?)\s+\d+-\d+.*?\s+(.*?)$', line)
                            if match3:
                                continue  # Skip completed matches
                            else:
                                continue  # Unrecognized format
                    
                    # Add match if we have a valid date
                    if current_date:
                        fixtures.append({
                            'matchday': current_matchday,
                            'date': current_date,
                            'day_of_week': day_of_week,
                            'time': time,
                            'home_team': home_team,
                            'away_team': away_team,
                            'competition': competition,
                            'country': country,
                            'season': season
                        })
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
    
    return fixtures

def find_fixture_files(current_season=True):
    """Find all fixture files in the raw data directory"""
    fixture_files = []
    
    # Process current seasons first
    current_seasons = ['2023-24', '2024-25']
    
    # Get all directories in the raw data directory
    for league_dir in os.listdir(RAW_DATA_DIR):
        league_path = os.path.join(RAW_DATA_DIR, league_dir)
        if os.path.isdir(league_path):
            # First check current seasons
            if current_season:
                for season in current_seasons:
                    season_path = os.path.join(league_path, season)
                    if os.path.isdir(season_path):
                        # Find all txt files
                        for file_name in os.listdir(season_path):
                            if file_name.endswith('.txt') and not file_name.startswith('.'):
                                fixture_files.append(os.path.join(season_path, file_name))
            else:
                # Check all other seasons
                for season_dir in os.listdir(league_path):
                    if season_dir not in current_seasons and os.path.isdir(os.path.join(league_path, season_dir)):
                        season_path = os.path.join(league_path, season_dir)
                        # Find all txt files
                        for file_name in os.listdir(season_path):
                            if file_name.endswith('.txt') and not file_name.startswith('.'):
                                fixture_files.append(os.path.join(season_path, file_name))
    
    return fixture_files

def get_or_create_club(db, club_name):
    """Get or create a club by name"""
    club = db.query(Club).filter(func.lower(Club.name) == func.lower(club_name)).first()
    if not club:
        # Create a new club
        club = Club(
            name=club_name,
            founded_year=random.randint(1880, 1980),
            stadium_name=f"{club_name} Stadium",
            city=club_name.split()[0],  # Use first word as city
            country="Unknown"
        )
        db.add(club)
        db.flush()
    return club

def get_or_create_team(db, club):
    """Get or create a team for a club"""
    team = db.query(Team).filter(Team.club_id == club.id).first()
    if not team:
        team = Team(club_id=club.id, team_type="club")
        db.add(team)
        db.flush()
    return team

def get_or_create_competition(db, competition_name, country):
    """Get or create a competition by name"""
    competition = db.query(Competition).filter(func.lower(Competition.name) == func.lower(competition_name)).first()
    if not competition:
        comp_type = "league"
        if "cup" in competition_name.lower():
            comp_type = "cup"
        elif "champions league" in competition_name.lower() or "europa league" in competition_name.lower():
            comp_type = "international"
            
        competition = Competition(
            name=competition_name,
            country=country,
            competition_type=comp_type
        )
        db.add(competition)
        db.flush()
    return competition

def get_or_create_season(db, competition, season_name):
    """Get or create a season for a competition"""
    season = db.query(Season).filter(
        Season.competition_id == competition.id,
        Season.season_name == season_name
    ).first()
    
    if not season:
        # Parse year_start and year_end from season_name (e.g., 2023-24)
        if '-' in season_name:
            parts = season_name.split('-')
            if len(parts) == 2:
                try:
                    year_start = int('20' + parts[0])
                    year_end = int('20' + parts[1])
                except ValueError:
                    year_start = 2023
                    year_end = 2024
            else:
                year_start = 2023
                year_end = 2024
        else:
            year_start = 2023
            year_end = 2024
            
        season = Season(
            competition_id=competition.id,
            season_name=season_name,
            year_start=year_start,
            year_end=year_end
        )
        db.add(season)
        db.flush()
    
    return season

def update_database_with_fixtures(fixtures):
    """Update the database with fixtures"""
    # Connect to the database
    # Use environment settings instead of hardcoded values
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/football_predictor")
    print(f"Using database connection: {DATABASE_URL}")
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    fixture_count = 0
    try:
        # First, delete any existing upcoming fixtures using raw SQL with correct table name
        delete_sql = text(
            "DELETE FROM fixtures WHERE match_date >= :today AND is_completed = false"
        )
        db.execute(delete_sql, {"today": today})
        
        # Add the new fixtures
        for fixture in fixtures:
            # Get or create clubs
            home_club = get_or_create_club(db, fixture['home_team'])
            away_club = get_or_create_club(db, fixture['away_team'])
            
            # Get or create teams
            home_team = get_or_create_team(db, home_club)
            away_team = get_or_create_team(db, away_club)
            
            # Get or create competition
            competition = get_or_create_competition(db, fixture['competition'], fixture['country'])
            
            # Get or create season
            season = get_or_create_season(db, competition, fixture['season'])
            
            # Create the fixture
            match_time = fixture['time'].replace('.', ':')
            stage = fixture['matchday'] if fixture['matchday'] else "Regular Season"
            
            new_fixture = Fixture(
                season_id=season.id,
                match_date=fixture['date'],
                match_time=match_time,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                stage=stage,
                venue=f"{home_club.name} Stadium",
                is_completed=False
            )
            db.add(new_fixture)
            fixture_count += 1
        
        db.commit()
        return fixture_count
    except Exception as e:
        db.rollback()
        print(f"Error updating database: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        db.close()

def main():
    """Main function to find fixtures and update the database"""
    # Get fixtures for the next 7 days
    all_fixtures = []
    
    print("Searching in current season files...")
    current_season_files = find_fixture_files(current_season=True)
    for file_path in current_season_files:
        fixtures = parse_fixtures(file_path)
        all_fixtures.extend(fixtures)
    
    # If we didn't find any fixtures, check older seasons
    if not all_fixtures:
        print("No fixtures found in current seasons, checking older seasons...")
        older_season_files = find_fixture_files(current_season=False)
        for file_path in older_season_files:
            fixtures = parse_fixtures(file_path)
            all_fixtures.extend(fixtures)
    
    # Group fixtures by date
    fixtures_by_date = {}
    for d in date_range:
        fixtures_by_date[d] = [f for f in all_fixtures if f['date'] == d]
    
    # Print summary of fixtures found
    total_count = 0
    for d, fixtures in fixtures_by_date.items():
        count = len(fixtures)
        total_count += count
        print(f"Found {count} fixtures for {d.strftime('%A, %B %d')}")
    
    # Update the database
    if total_count > 0:
        fixture_count = update_database_with_fixtures(all_fixtures)
        print(f"Successfully added {fixture_count} upcoming fixtures to the database")
    else:
        print("No fixtures found to add to the database")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3

import os
import re
import sys
import datetime
from datetime import date, timedelta
from pathlib import Path
from sqlalchemy import create_engine, and_, or_, func
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.models import Fixture, Team, Club, Competition, Season
from app.core.config import settings

# Set the raw data directory
RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"

# Get today's date and future dates (for next 7 days)
today = date.today()
future_dates = [today + timedelta(days=i) for i in range(8)]  # Today + next 7 days

# Format dates for display and matching
date_formats = []
for d in future_dates:
    # Format with zero (e.g., may/09)
    date_formats.append(d.strftime("%b/%d").lower())
    # Format without zero (e.g., may/9)
    date_formats.append(d.strftime("%b/%-d").lower())

# Dictionary to store matches for each date
matches_by_date = {d: [] for d in future_dates}

# League names mapping
league_names = {
    "eng-england": "English",
    "es-espana": "Spanish",
    "de-deutschland": "German",
    "it-italy": "Italian", 
    "fr-france": "French",
    "champions-league": "Champions League",
    "europa-league": "Europa League",
}

def parse_date_line(line):
    """Parse a date line and return the date in a standard format."""
    # Extract date from format like [Fri May/10] or [Fri May/09]
    match = re.search(r'\[(.*) (.*?)\]', line)
    if match:
        return match.group(2).lower()  # Return like may/09 or may/10
    return None

def extract_match_info(match_lines, date_str, league, season, file_path):
    """Extract match information from the lines after a date header."""
    matches = []
    
    # Check if there are at least some valid match lines
    if not match_lines:
        return matches
    
    # Extract competition name from filename
    file_name = os.path.basename(file_path)
    competition = file_name.replace('.txt', '')
    if "-" in competition:
        # For league files like "1-premierleague.txt"
        parts = competition.split("-")
        if len(parts) > 1:
            competition = parts[1]
    
    for line in match_lines:
        line = line.strip()
        if not line or line.startswith('[') or line.startswith('#') or line.startswith('='):
            continue
            
        # Try to extract match time and teams
        # Common pattern: time home_team vs away_team
        # Format with score: "  20.00  Burnley FC               0-3 (0-2)  Manchester City FC"
        match = re.match(r'\s*(\d+\.\d+)\s+(.*?)\s+(?:\d+-\d+|\?)(?:\s+\(\d+-\d+\))?\s+(.*?)$', line)
        if match:
            time, home_team, away_team = match.groups()
            home_team = home_team.strip()
            away_team = away_team.strip()
            
            matches.append({
                'time': time,
                'home_team': home_team,
                'away_team': away_team,
                'league': league,
                'competition': competition,
                'season': season
            })
            continue
            
        # Format without score yet (for upcoming matches)
        match = re.match(r'\s*(\d+\.\d+)\s+(.*?)\s+[-–]\s+(.*?)$', line)
        if match:
            time, home_team, away_team = match.groups()
            home_team = home_team.strip()
            away_team = away_team.strip()
            
            matches.append({
                'time': time,
                'home_team': home_team,
                'away_team': away_team,
                'league': league,
                'competition': competition,
                'season': season
            })
            
    return matches

def find_matches_in_file(file_path, league, season):
    """Find matches for the next week in a given file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_date = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Check if this is a date line
        if line.startswith('['):
            date_str = parse_date_line(line)
            if date_str:
                current_date = date_str
                
                # Check if this date is in our list of formats
                for j, future_date in enumerate(future_dates):
                    fmt1 = future_date.strftime("%b/%d").lower()
                    fmt2 = future_date.strftime("%b/%-d").lower()
                    
                    if current_date in [fmt1, fmt2]:
                        # Find all lines until the next date or end of section
                        match_lines = []
                        k = i + 1
                        while k < len(lines) and not lines[k].strip().startswith('['):
                            match_lines.append(lines[k])
                            k += 1
                            
                        matches = extract_match_info(match_lines, current_date, league, season, file_path)
                        matches_by_date[future_date].extend(matches)
                        break

def scan_league_folder(league_path, league_name):
    """Scan a league folder for all season files."""
    # Iterate through all season folders
    for season_dir in sorted([d for d in os.listdir(league_path) if os.path.isdir(os.path.join(league_path, d))], reverse=True):
        season_path = os.path.join(league_path, season_dir)
        
        # Look for .txt files in the season directory
        for file_name in os.listdir(season_path):
            if file_name.endswith('.txt'):
                file_path = os.path.join(season_path, file_name)
                find_matches_in_file(file_path, league_name, season_dir)

def get_or_create_club(db, club_name):
    """Get or create a club by name."""
    club = db.query(Club).filter(func.lower(Club.name) == func.lower(club_name)).first()
    if not club:
        club = Club(name=club_name)
        db.add(club)
        db.flush()
    return club

def get_or_create_team(db, club):
    """Get or create a team for a club."""
    team = db.query(Team).filter(Team.club_id == club.id).first()
    if not team:
        team = Team(club_id=club.id, team_type="club")
        db.add(team)
        db.flush()
    return team

def get_or_create_competition(db, comp_name, country="Unknown"):
    """Get or create a competition by name."""
    competition = db.query(Competition).filter(func.lower(Competition.name) == func.lower(comp_name)).first()
    if not competition:
        competition = Competition(name=comp_name, country=country, competition_type="league")
        db.add(competition)
        db.flush()
    return competition

def get_or_create_season(db, competition, season_name):
    """Get or create a season for a competition."""
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

def create_fixture_from_match(db, match, match_date):
    """Create a fixture in the database from match data."""
    # Get or create clubs and teams
    home_club = get_or_create_club(db, match['home_team'])
    away_club = get_or_create_club(db, match['away_team'])
    
    home_team = get_or_create_team(db, home_club)
    away_team = get_or_create_team(db, away_club)
    
    # Get or create competition and season
    competition_name = match['competition']
    country = match['league'].split()[0] if ' ' in match['league'] else "Unknown"
    
    competition = get_or_create_competition(db, competition_name, country)
    season = get_or_create_season(db, competition, match['season'])
    
    # Check if the fixture already exists
    existing_fixture = db.query(Fixture).filter(
        Fixture.season_id == season.id,
        Fixture.home_team_id == home_team.id,
        Fixture.away_team_id == away_team.id,
        Fixture.match_date == match_date
    ).first()
    
    if not existing_fixture:
        # Create the fixture
        fixture = Fixture(
            season_id=season.id,
            match_date=match_date,
            match_time=match['time'].replace('.', ':'),
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            stage="Regular Season",
            venue=f"{home_club.name} Stadium",
            is_completed=False
        )
        db.add(fixture)
        return fixture
    
    return existing_fixture

def main():
    """Main function to scan for matches and update the database."""
    print(f"Looking for matches for the next week starting from {today.strftime('%A, %B %d')}...")
    
    # Scan all league folders
    for league_dir in os.listdir(RAW_DATA_DIR):
        league_path = os.path.join(RAW_DATA_DIR, league_dir)
        if os.path.isdir(league_path):
            league_name = league_names.get(league_dir, league_dir)
            scan_league_folder(league_path, league_name)
    
    # Connect to the database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://matchwise:matchwise@db:5432/matchwise")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # First, delete any existing upcoming fixtures
    try:
        db.query(Fixture).filter(
            Fixture.match_date >= today,
            Fixture.is_completed == False
        ).delete()
        
        # Create new fixtures from the matches we found
        fixtures_created = 0
        
        for future_date, matches in matches_by_date.items():
            if matches:
                print(f"\nAdding {len(matches)} fixtures for {future_date.strftime('%A, %B %d')}:")
                
                for match in sorted(matches, key=lambda x: x['time']):
                    fixture = create_fixture_from_match(db, match, future_date)
                    if fixture:
                        fixtures_created += 1
                        print(f"Added: {match['time']} - {match['home_team']} vs {match['away_team']} - {match['league']} {match['competition']}")
        
        db.commit()
        print(f"\nSuccessfully added {fixtures_created} upcoming fixtures to the database.")
        
    except Exception as e:
        db.rollback()
        print(f"Error updating fixtures: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    main() 
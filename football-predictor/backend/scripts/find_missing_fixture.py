#!/usr/bin/env python3

import os
import sys
from datetime import date, timedelta
import re

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload

from app.models.models import Fixture, Team, Club, Season, Competition

# Get database connection string from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/football_predictor")
print(f"Using database: {DATABASE_URL}")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Get tomorrow's date
tomorrow = date.today() + timedelta(days=1)
print(f"Checking fixtures for: {tomorrow}")

# 1. Search for all clubs containing Las Palmas or Rayo
print("\n1. Searching for clubs with Las Palmas or Rayo in the name:")
las_palmas_clubs = db.query(Club).filter(Club.name.ilike("%Las Palmas%")).all()
rayo_clubs = db.query(Club).filter(Club.name.ilike("%Rayo%")).all()

print("Las Palmas clubs:")
for club in las_palmas_clubs:
    print(f"  - Club ID {club.id}: {club.name}")

print("\nRayo clubs:")
for club in rayo_clubs:
    print(f"  - Club ID {club.id}: {club.name}")

# 2. Get all Spanish competition fixtures for tomorrow
print("\n2. All Spanish fixtures for tomorrow:")
spain_fixtures = db.query(Fixture).join(Fixture.season).join(Season.competition).filter(
    Competition.country.ilike("%Spain%"),
    Fixture.match_date == tomorrow
).options(
    joinedload(Fixture.home_team).joinedload(Team.club),
    joinedload(Fixture.away_team).joinedload(Team.club),
    joinedload(Fixture.season).joinedload(Season.competition)
).all()

for fixture in spain_fixtures:
    home_team = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else f"Unknown (ID: {fixture.home_team_id})"
    away_team = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else f"Unknown (ID: {fixture.away_team_id})"
    comp = fixture.season.competition.name if fixture.season and fixture.season.competition else "Unknown"
    time = fixture.match_time or "Unknown time"
    print(f"  - [{comp}] {home_team} vs {away_team} at {time}")

# 3. Look for any fixtures with these specific teams
print("\n3. Checking for any fixtures in the database with Las Palmas or Rayo:")
las_palmas_ids = [club.id for club in las_palmas_clubs]
rayo_ids = [club.id for club in rayo_clubs]

# Get team IDs for these clubs
las_palmas_teams = db.query(Team).filter(Team.club_id.in_(las_palmas_ids)).all() if las_palmas_ids else []
rayo_teams = db.query(Team).filter(Team.club_id.in_(rayo_ids)).all() if rayo_ids else []

las_palmas_team_ids = [team.id for team in las_palmas_teams]
rayo_team_ids = [team.id for team in rayo_teams]

print(f"Las Palmas Team IDs: {las_palmas_team_ids}")
print(f"Rayo Team IDs: {rayo_team_ids}")

if las_palmas_team_ids and rayo_team_ids:
    # Search for fixtures with these teams
    fixtures = db.query(Fixture).filter(
        Fixture.match_date >= date.today(),
        (
            (Fixture.home_team_id.in_(las_palmas_team_ids) & Fixture.away_team_id.in_(rayo_team_ids)) |
            (Fixture.home_team_id.in_(rayo_team_ids) & Fixture.away_team_id.in_(las_palmas_team_ids))
        )
    ).options(
        joinedload(Fixture.home_team).joinedload(Team.club),
        joinedload(Fixture.away_team).joinedload(Team.club),
        joinedload(Fixture.season).joinedload(Season.competition)
    ).all()
    
    if fixtures:
        print(f"Found {len(fixtures)} fixture(s) between Las Palmas and Rayo:")
        for fixture in fixtures:
            home_club = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else f"Unknown (ID: {fixture.home_team_id})"
            away_club = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else f"Unknown (ID: {fixture.away_team_id})"
            match_date = fixture.match_date
            match_time = fixture.match_time or "Unknown time"
            competition = fixture.season.competition.name if fixture.season and fixture.season.competition else "Unknown"
            print(f"  - {match_date} at {match_time}: {home_club} vs {away_club} ({competition})")
    else:
        print("No fixtures found between Las Palmas and Rayo teams")
else:
    print("Couldn't find team IDs for either Las Palmas or Rayo clubs")

# 4. Check the raw data files for Spanish fixtures
print("\n4. Checking raw data files for La Liga fixtures:")
raw_data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "raw", "es-espana")

try:
    latest_dir = None
    latest_year = 0
    
    # Find the most recent season directory
    for item in os.listdir(raw_data_path):
        if os.path.isdir(os.path.join(raw_data_path, item)) and re.match(r'^\d{4}-\d{2}$', item):
            year = int(item.split('-')[0])
            if year > latest_year:
                latest_year = year
                latest_dir = item
    
    if latest_dir:
        print(f"Found latest season directory: {latest_dir}")
        
        # Check for fixture files in this directory
        fixture_files = []
        for root, dirs, files in os.walk(os.path.join(raw_data_path, latest_dir)):
            for file in files:
                if file.endswith(".txt") and not file.startswith("README"):
                    fixture_files.append(os.path.join(root, file))
        
        print(f"Found {len(fixture_files)} fixture files")
        
        # Look for Las Palmas and Rayo in these files
        tomorrow_str = tomorrow.strftime("%a %b %d")
        las_palmas_matches = []
        
        for file_path in fixture_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Look for fixtures mentioning both teams and tomorrow's date
                if "Las Palmas" in content and "Rayo" in content and tomorrow_str in content:
                    match_lines = content.split('\n')
                    for i, line in enumerate(match_lines):
                        if tomorrow_str in line:
                            # Get the match context (3 lines before and after)
                            context_start = max(0, i-3)
                            context_end = min(len(match_lines), i+4)
                            match_context = match_lines[context_start:context_end]
                            las_palmas_matches.append("\n".join(match_context))
        
        if las_palmas_matches:
            print(f"Found {len(las_palmas_matches)} raw data entries for Las Palmas vs Rayo on {tomorrow_str}:")
            for i, match in enumerate(las_palmas_matches):
                print(f"\nMatch {i+1}:\n{match}")
        else:
            print(f"No matches found in raw data for Las Palmas vs Rayo on {tomorrow_str}")
    else:
        print("No season directories found")
except Exception as e:
    print(f"Error checking raw data files: {e}")

print("\nDONE") 
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

from app.models.models import Base, Fixture, Team, Club, Competition, Season
from app.core.config import settings
from scripts.update_fixtures_in_db import find_fixture_files, parse_fixtures

# Get database connection string from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/football_predictor")
print(f"Using database connection: {DATABASE_URL}")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all tables in the database"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")

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

def load_fixtures_to_db(fixtures):
    """Load fixtures into the database"""
    db = SessionLocal()
    
    fixture_count = 0
    try:
        # Add the new fixtures
        for fixture in fixtures:
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
                    
                    # Only use dates up to 6 months in the future
                    future_cutoff = date.today() + timedelta(days=180)
                    if new_date > future_cutoff:
                        # Skip this fixture
                        continue
                    
                    fixture['date'] = new_date
                except ValueError:
                    # Skip invalid dates (e.g., Feb 29 in non-leap years)
                    continue
            
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
    """Main function to set up the database and load fixtures"""
    # Step 1: Create all tables
    create_tables()
    
    # Step 2: Get fixtures
    all_fixtures = []
    
    # Process current seasons first
    print("Searching for fixture files...")
    current_season_files = find_fixture_files(current_season=True)
    
    print(f"Found {len(current_season_files)} fixture files, parsing...")
    for file_path in current_season_files:
        fixtures = parse_fixtures(file_path)
        all_fixtures.extend(fixtures)
    
    # Step 3: Load fixtures into the database
    if all_fixtures:
        print(f"Found {len(all_fixtures)} fixtures, loading to database...")
        fixture_count = load_fixtures_to_db(all_fixtures)
        print(f"Successfully added {fixture_count} fixtures to the database")
    else:
        print("No fixtures found to add to the database")

if __name__ == "__main__":
    main() 
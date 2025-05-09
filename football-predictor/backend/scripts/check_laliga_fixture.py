#!/usr/bin/env python3

import os
import sys
from datetime import date, timedelta

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, or_
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

# Check for La Liga fixtures
la_liga_fixtures = db.query(Fixture).join(Season).join(Competition).filter(
    Competition.name.ilike("%La Liga%"),
    Fixture.match_date == tomorrow
).options(
    joinedload(Fixture.home_team).joinedload(Team.club),
    joinedload(Fixture.away_team).joinedload(Team.club)
).all()

print(f"Found {len(la_liga_fixtures)} La Liga fixtures for tomorrow:")
for fixture in la_liga_fixtures:
    home_team = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else "Unknown"
    away_team = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else "Unknown"
    time = fixture.match_time or "Unknown time"
    print(f"  - {home_team} vs {away_team} at {time}")

# Check specifically for Las Palmas vs Rayo Vallecano - using a different approach
print("\nChecking specifically for Las Palmas vs Rayo Vallecano:")
las_palmas_fixtures = db.query(Fixture).join(
    Fixture.home_team
).join(
    Team.club, isouter=True
).join(
    Fixture.away_team, isouter=True
).join(
    Team.club, isouter=True
).filter(
    Fixture.match_date == tomorrow
).options(
    joinedload(Fixture.home_team).joinedload(Team.club),
    joinedload(Fixture.away_team).joinedload(Team.club)
).all()

found_match = False
for fixture in las_palmas_fixtures:
    home_team = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else "Unknown"
    away_team = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else "Unknown"
    
    if ("Las Palmas" in home_team and "Rayo" in away_team) or \
       ("Rayo" in home_team and "Las Palmas" in away_team):
        found_match = True
        time = fixture.match_time or "Unknown time"
        print(f"  - Found: {home_team} vs {away_team} at {time}")

if not found_match:
    print("  - No specific match found between Las Palmas and Rayo Vallecano")

# Let's just do a more basic search for any teams with these names
print("\nSearching for any clubs containing 'Las Palmas' or 'Rayo':")
las_palmas_clubs = db.query(Club).filter(Club.name.ilike("%Las Palmas%")).all()
rayo_clubs = db.query(Club).filter(Club.name.ilike("%Rayo%")).all()

print("Las Palmas clubs in database:")
for club in las_palmas_clubs:
    print(f"  - {club.id}: {club.name}")

print("Rayo clubs in database:")
for club in rayo_clubs:
    print(f"  - {club.id}: {club.name}")

# Look at all fixtures for tomorrow
print("\nAll La Liga fixtures in Spain for tomorrow:")
spain_fixtures = db.query(Fixture).join(Season).join(Competition).filter(
    Competition.country.ilike("%Spain%"),
    Fixture.match_date == tomorrow
).options(
    joinedload(Fixture.home_team).joinedload(Team.club),
    joinedload(Fixture.away_team).joinedload(Team.club)
).all()

for fixture in spain_fixtures:
    home_team = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else "Unknown"
    away_team = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else "Unknown"
    comp = fixture.season.competition.name if fixture.season and fixture.season.competition else "Unknown"
    time = fixture.match_time or "Unknown time"
    print(f"  - [{comp}] {home_team} vs {away_team} at {time}")

print("\nDONE") 
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

# Today's date
today = date.today()
print(f"Checking fixtures for today {today} - typically this is May 9, 2025")

# Get all La Liga fixtures for today
laliga_fixtures = db.query(Fixture).join(Fixture.season).join(Season.competition).filter(
    Competition.name.ilike("%La Liga%"),
    Fixture.match_date == today
).options(
    joinedload(Fixture.home_team).joinedload(Team.club),
    joinedload(Fixture.away_team).joinedload(Team.club),
    joinedload(Fixture.season).joinedload(Season.competition)
).all()

print(f"\nFound {len(laliga_fixtures)} La Liga fixtures for today:")
for fixture in laliga_fixtures:
    home_team = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else f"Unknown (ID: {fixture.home_team_id})"
    away_team = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else f"Unknown (ID: {fixture.away_team_id})"
    comp = fixture.season.competition.name if fixture.season and fixture.season.competition else "Unknown"
    country = fixture.season.competition.country if fixture.season and fixture.season.competition else "Unknown"
    time = fixture.match_time or "Unknown time"
    print(f"  - [{comp} ({country})] {home_team} vs {away_team} at {time}")

# Check specifically for Las Palmas vs Rayo Vallecano
print("\nSearching specifically for Las Palmas vs Rayo Vallecano today:")
las_palmas_clubs = db.query(Club).filter(Club.name.ilike("%Las Palmas%")).all()
rayo_clubs = db.query(Club).filter(Club.name.ilike("%Rayo%")).all()

las_palmas_ids = [club.id for club in las_palmas_clubs]
rayo_ids = [club.id for club in rayo_clubs]

las_palmas_teams = db.query(Team).filter(Team.club_id.in_(las_palmas_ids)).all() if las_palmas_ids else []
rayo_teams = db.query(Team).filter(Team.club_id.in_(rayo_ids)).all() if rayo_ids else []

las_palmas_team_ids = [team.id for team in las_palmas_teams]
rayo_team_ids = [team.id for team in rayo_teams]

if las_palmas_team_ids and rayo_team_ids:
    fixtures = db.query(Fixture).filter(
        Fixture.match_date == today,
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
        print("No fixtures found between Las Palmas and Rayo teams for today")
else:
    print("Could not find team IDs for Las Palmas or Rayo clubs")

print("\nDONE") 
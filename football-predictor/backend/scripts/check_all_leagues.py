#!/usr/bin/env python3

import os
import sys
from datetime import date, timedelta
from collections import defaultdict

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

# Get dates
today = date.today()
tomorrow = today + timedelta(days=1)

def get_fixtures_by_date(date_to_check):
    """Get all fixtures for a given date grouped by competition"""
    fixtures = db.query(Fixture).filter(
        Fixture.match_date == date_to_check
    ).options(
        joinedload(Fixture.home_team).joinedload(Team.club),
        joinedload(Fixture.away_team).joinedload(Team.club),
        joinedload(Fixture.season).joinedload(Season.competition)
    ).all()
    
    fixtures_by_comp = defaultdict(list)
    
    for fixture in fixtures:
        home_team = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else f"Unknown (ID: {fixture.home_team_id})"
        away_team = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else f"Unknown (ID: {fixture.away_team_id})"
        comp = fixture.season.competition.name if fixture.season and fixture.season.competition else "Unknown"
        country = fixture.season.competition.country if fixture.season and fixture.season.competition else "Unknown"
        time = fixture.match_time or "Unknown time"
        
        comp_key = f"{comp} ({country})"
        fixtures_by_comp[comp_key].append({
            "home": home_team,
            "away": away_team,
            "time": time,
            "id": fixture.id
        })
    
    return fixtures_by_comp

# Check fixtures for today
print(f"\n=== FIXTURES FOR TODAY ({today}) ===")
today_fixtures = get_fixtures_by_date(today)

if today_fixtures:
    for comp, matches in today_fixtures.items():
        print(f"\n{comp} - {len(matches)} matches:")
        for match in matches:
            print(f"  - {match['home']} vs {match['away']} at {match['time']}")
else:
    print("No fixtures found for today")

# Check fixtures for tomorrow
print(f"\n=== FIXTURES FOR TOMORROW ({tomorrow}) ===")
tomorrow_fixtures = get_fixtures_by_date(tomorrow)

if tomorrow_fixtures:
    for comp, matches in tomorrow_fixtures.items():
        print(f"\n{comp} - {len(matches)} matches:")
        for match in matches:
            print(f"  - {match['home']} vs {match['away']} at {match['time']}")
else:
    print("No fixtures found for tomorrow")

# Summary of leagues with fixtures
print("\n=== SUMMARY ===")
print(f"Today: {len(today_fixtures)} leagues with fixtures")
print(f"Tomorrow: {len(tomorrow_fixtures)} leagues with fixtures")

# Count total matches
today_match_count = sum(len(matches) for matches in today_fixtures.values())
tomorrow_match_count = sum(len(matches) for matches in tomorrow_fixtures.values())

print(f"Total matches today: {today_match_count}")
print(f"Total matches tomorrow: {tomorrow_match_count}")

print("\nDONE") 
#!/usr/bin/env python3

import os
import sys
import datetime
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.models import Fixture, Team, Club, Season, Competition

# Get database connection string from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/football_predictor")
print(f"Using database connection: {DATABASE_URL}")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_fixtures():
    """Check fixtures for today and tomorrow"""
    db = SessionLocal()
    
    try:
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        print(f"Checking fixtures for today ({today}) and tomorrow ({tomorrow})")
        print("\n=== TODAY'S FIXTURES ===")
        
        # Get today's fixtures with related data
        today_fixtures = db.query(Fixture).filter(
            Fixture.match_date == today
        ).options(
            joinedload(Fixture.home_team).joinedload(Team.club),
            joinedload(Fixture.away_team).joinedload(Team.club),
            joinedload(Fixture.season).joinedload(Season.competition)
        ).all()
        
        # Display fixtures grouped by competition
        fixtures_by_competition = {}
        for fixture in today_fixtures:
            comp_name = fixture.season.competition.name if fixture.season and fixture.season.competition else "Unknown"
            country = fixture.season.competition.country if fixture.season and fixture.season.competition else "Unknown"
            comp_key = f"{comp_name} ({country})"
            
            if comp_key not in fixtures_by_competition:
                fixtures_by_competition[comp_key] = []
            
            home_team = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else str(fixture.home_team_id)
            away_team = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else str(fixture.away_team_id)
            
            fixtures_by_competition[comp_key].append({
                'home': home_team,
                'away': away_team,
                'time': fixture.match_time or "15:00"
            })
        
        # Print today's fixtures by competition
        if fixtures_by_competition:
            for comp, fixtures in fixtures_by_competition.items():
                print(f"\n{comp}:")
                for f in fixtures:
                    print(f"  {f['home']} vs {f['away']} at {f['time']}")
        else:
            print("  No fixtures found for today")
        
        print("\n=== TOMORROW'S FIXTURES ===")
        
        # Get tomorrow's fixtures with related data
        tomorrow_fixtures = db.query(Fixture).filter(
            Fixture.match_date == tomorrow
        ).options(
            joinedload(Fixture.home_team).joinedload(Team.club),
            joinedload(Fixture.away_team).joinedload(Team.club),
            joinedload(Fixture.season).joinedload(Season.competition)
        ).all()
        
        # Display fixtures grouped by competition
        fixtures_by_competition = {}
        for fixture in tomorrow_fixtures:
            comp_name = fixture.season.competition.name if fixture.season and fixture.season.competition else "Unknown"
            country = fixture.season.competition.country if fixture.season and fixture.season.competition else "Unknown"
            comp_key = f"{comp_name} ({country})"
            
            if comp_key not in fixtures_by_competition:
                fixtures_by_competition[comp_key] = []
            
            home_team = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else str(fixture.home_team_id)
            away_team = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else str(fixture.away_team_id)
            
            fixtures_by_competition[comp_key].append({
                'home': home_team,
                'away': away_team,
                'time': fixture.match_time or "15:00"
            })
        
        # Print tomorrow's fixtures by competition
        if fixtures_by_competition:
            for comp, fixtures in fixtures_by_competition.items():
                print(f"\n{comp}:")
                for f in fixtures:
                    print(f"  {f['home']} vs {f['away']} at {f['time']}")
        else:
            print("  No fixtures found for tomorrow")
        
        print("\nTotal fixtures: Today:", len(today_fixtures), "Tomorrow:", len(tomorrow_fixtures))
        
    except Exception as e:
        print(f"Error checking fixtures: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_fixtures() 
#!/usr/bin/env python3

import os
import sys
from datetime import date, timedelta
from sqlalchemy import create_engine, and_, func
from sqlalchemy.orm import sessionmaker, joinedload

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.models import Fixture, Team, Club, Competition, Season

# Get database connection string from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/football_predictor")
print(f"Using database connection: {DATABASE_URL}")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_fixture_details(fixture, home_club, away_club, competition):
    """Format fixture details for display"""
    return {
        "date": fixture.match_date.strftime("%A, %B %d"),
        "time": fixture.match_time,
        "home_team": home_club.name if home_club else f"Team {fixture.home_team_id}",
        "away_team": away_club.name if away_club else f"Team {fixture.away_team_id}",
        "competition": competition.name if competition else "Unknown",
        "country": competition.country if competition else "Unknown",
        "stage": fixture.stage
    }

def show_fixtures_by_date():
    """Show fixtures grouped by date"""
    db = SessionLocal()
    
    try:
        # Get fixtures for the next 7 days
        today = date.today()
        end_date = today + timedelta(days=7)
        
        # Get fixtures with related data - fixed to avoid duplicate aliases
        fixtures = db.query(Fixture)\
            .filter(and_(
                Fixture.match_date >= today,
                Fixture.match_date <= end_date
            ))\
            .options(
                joinedload(Fixture.season).joinedload(Season.competition),
                joinedload(Fixture.home_team).joinedload(Team.club),
                joinedload(Fixture.away_team).joinedload(Team.club)
            )\
            .order_by(Fixture.match_date, Fixture.match_time)\
            .all()
            
        # Group fixtures by date
        fixtures_by_date = {}
        for fixture in fixtures:
            date_str = fixture.match_date.strftime("%Y-%m-%d")
            if date_str not in fixtures_by_date:
                fixtures_by_date[date_str] = []
                
            home_club = fixture.home_team.club if fixture.home_team else None
            away_club = fixture.away_team.club if fixture.away_team else None
            competition = fixture.season.competition if fixture.season else None
            
            fixtures_by_date[date_str].append(
                get_fixture_details(fixture, home_club, away_club, competition)
            )
        
        # Print fixtures by date
        if fixtures_by_date:
            for date_str, date_fixtures in sorted(fixtures_by_date.items()):
                date_obj = date.fromisoformat(date_str)
                print(f"\n\033[1m{date_obj.strftime('%A, %B %d')}\033[0m ({len(date_fixtures)} matches)")
                print("-" * 80)
                
                # Group fixtures by competition
                fixtures_by_competition = {}
                for fixture in date_fixtures:
                    comp_key = f"{fixture['country']} - {fixture['competition']}"
                    if comp_key not in fixtures_by_competition:
                        fixtures_by_competition[comp_key] = []
                    fixtures_by_competition[comp_key].append(fixture)
                
                # Print fixtures by competition
                for comp_name, comp_fixtures in sorted(fixtures_by_competition.items()):
                    print(f"\n  \033[1m{comp_name}\033[0m")
                    for fixture in sorted(comp_fixtures, key=lambda x: x['time'] or ''):
                        print(f"    {fixture['time'] or 'TBA'} - {fixture['home_team']} vs {fixture['away_team']}")
        else:
            print("No fixtures found for the next 7 days")
            
        # Count total fixtures in the database
        total_fixtures = db.query(func.count(Fixture.id)).scalar()
        print(f"\nTotal fixtures in database: {total_fixtures}")
        
    except Exception as e:
        print(f"Error querying database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    show_fixtures_by_date() 
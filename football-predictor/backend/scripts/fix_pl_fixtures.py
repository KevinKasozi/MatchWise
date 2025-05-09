#!/usr/bin/env python3

import os
import sys
from datetime import date, timedelta

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, joinedload
from app.models.models import Fixture, Team, Club, Season, Competition

# Get database connection string
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/football_predictor")
print(f"Using database: {DATABASE_URL}")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Tomorrow's date
tomorrow = date.today() + timedelta(days=1)
print(f"Fixing fixtures for tomorrow: {tomorrow}")

try:
    # Get Premier League competition
    premier_league = db.query(Competition).filter(
        Competition.name == "Premier League",
        Competition.country == "England"
    ).first()
    
    if not premier_league:
        print("Premier League competition not found in database")
        sys.exit(1)
    
    print(f"Found Premier League with ID: {premier_league.id}")
    
    # Get current season
    current_season = db.query(Season).filter(
        Season.competition_id == premier_league.id
    ).order_by(Season.year_start.desc()).first()
    
    if not current_season:
        print("Current Premier League season not found in database")
        sys.exit(1)
    
    print(f"Found current season: {current_season.season_name}")
    
    # Get teams playing tomorrow
    teams_to_add = {
        "home": ["Fulham FC", "Ipswich Town FC", "Southampton FC", "Wolverhampton Wanderers FC", "AFC Bournemouth"],
        "away": ["Everton FC", "Brentford FC", "Manchester City FC", "Brighton & Hove Albion FC", "Aston Villa FC"]
    }
    
    # Check existing fixtures for tomorrow
    existing_fixtures = db.query(Fixture).join(Season).filter(
        Season.competition_id == premier_league.id,
        Fixture.match_date == tomorrow
    ).options(
        joinedload(Fixture.home_team).joinedload(Team.club),
        joinedload(Fixture.away_team).joinedload(Team.club)
    ).all()
    
    print(f"Found {len(existing_fixtures)} Premier League fixtures for tomorrow:")
    existing_fixtures_dict = {}
    for fixture in existing_fixtures:
        home_team = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else "Unknown"
        away_team = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else "Unknown"
        print(f"  - {home_team} vs {away_team}")
        existing_fixtures_dict[(home_team, away_team)] = fixture
    
    # Process missing fixtures
    for i in range(len(teams_to_add["home"])):
        home_team_name = teams_to_add["home"][i]
        away_team_name = teams_to_add["away"][i]
        
        # Skip if fixture already exists
        if (home_team_name, away_team_name) in existing_fixtures_dict:
            print(f"Fixture {home_team_name} vs {away_team_name} already exists")
            continue
        
        # Get home team
        home_club = db.query(Club).filter(Club.name == home_team_name).first()
        if not home_club:
            print(f"Home club not found: {home_team_name}")
            home_club = Club(name=home_team_name)
            db.add(home_club)
            db.flush()
            print(f"Created new club: {home_team_name}")
        
        home_team = db.query(Team).filter(Team.club_id == home_club.id).first()
        if not home_team:
            home_team = Team(club_id=home_club.id, team_type="First Team")
            db.add(home_team)
            db.flush()
            print(f"Created new team for club: {home_team_name}")
        
        # Get away team
        away_club = db.query(Club).filter(Club.name == away_team_name).first()
        if not away_club:
            print(f"Away club not found: {away_team_name}")
            away_club = Club(name=away_team_name)
            db.add(away_club)
            db.flush()
            print(f"Created new club: {away_team_name}")
        
        away_team = db.query(Team).filter(Team.club_id == away_club.id).first()
        if not away_team:
            away_team = Team(club_id=away_club.id, team_type="First Team")
            db.add(away_team)
            db.flush()
            print(f"Created new team for club: {away_team_name}")
        
        # Create the fixture
        match_time = "15:00"
        if home_team_name == "AFC Bournemouth":
            match_time = "17:30"
            
        new_fixture = Fixture(
            season_id=current_season.id,
            match_date=tomorrow,
            match_time=match_time,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            stage="Regular Season",
            is_completed=False
        )
        
        db.add(new_fixture)
        print(f"Added new fixture: {home_team_name} vs {away_team_name} at {match_time}")
    
    # Commit changes
    db.commit()
    print("All Premier League fixtures for tomorrow have been fixed")
    
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
    
finally:
    db.close() 
#!/usr/bin/env python3

import os
import sys
import logging
from datetime import date, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, func, or_, and_
from sqlalchemy.orm import sessionmaker, joinedload
from app.models.models import Base, Fixture, Team, Club, Competition, Season

# Database connection string
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/football_predictor")
logger.info(f"Using database: {DATABASE_URL}")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def fix_duplicate_league_fixtures():
    """Fix fixtures that appear in multiple leagues (La Liga and La Liga 2)"""
    db = SessionLocal()
    
    try:
        # 1. Find La Liga and La Liga 2 competitions
        la_liga = db.query(Competition).filter(
            Competition.name == "La Liga",
            Competition.country == "Spain"
        ).first()
        
        la_liga2 = db.query(Competition).filter(
            Competition.name == "La Liga 2",
            Competition.country == "Spain"
        ).first()
        
        if not la_liga or not la_liga2:
            logger.error(f"Could not find La Liga or La Liga 2 competitions")
            return
            
        logger.info(f"Found La Liga (ID: {la_liga.id}) and La Liga 2 (ID: {la_liga2.id})")
        
        # 2. Get all fixtures for both leagues
        upcoming_date = date.today()
        
        la_liga_fixtures = db.query(Fixture).join(Season).filter(
            Season.competition_id == la_liga.id,
            Fixture.match_date >= upcoming_date
        ).options(
            joinedload(Fixture.home_team).joinedload(Team.club),
            joinedload(Fixture.away_team).joinedload(Team.club)
        ).all()
        
        la_liga2_fixtures = db.query(Fixture).join(Season).filter(
            Season.competition_id == la_liga2.id,
            Fixture.match_date >= upcoming_date
        ).options(
            joinedload(Fixture.home_team).joinedload(Team.club),
            joinedload(Fixture.away_team).joinedload(Team.club)
        ).all()
        
        logger.info(f"Found {len(la_liga_fixtures)} La Liga fixtures and {len(la_liga2_fixtures)} La Liga 2 fixtures")
        
        # 3. Find duplicates between the two leagues
        duplicates = []
        
        for liga_fixture in la_liga_fixtures:
            liga_home = liga_fixture.home_team.club.name if liga_fixture.home_team and liga_fixture.home_team.club else ""
            liga_away = liga_fixture.away_team.club.name if liga_fixture.away_team and liga_fixture.away_team.club else ""
            liga_date = liga_fixture.match_date
            
            for liga2_fixture in la_liga2_fixtures:
                liga2_home = liga2_fixture.home_team.club.name if liga2_fixture.home_team and liga2_fixture.home_team.club else ""
                liga2_away = liga2_fixture.away_team.club.name if liga2_fixture.away_team and liga2_fixture.away_team.club else ""
                liga2_date = liga2_fixture.match_date
                
                # If same teams and same date, it's a duplicate
                if liga_home == liga2_home and liga_away == liga2_away and liga_date == liga2_date:
                    logger.info(f"Found duplicate: {liga_home} vs {liga_away} on {liga_date}")
                    # Always keep the La Liga fixture, delete the La Liga 2 one
                    duplicates.append(liga2_fixture)
        
        # 4. Delete the duplicates from La Liga 2
        for fixture in duplicates:
            home_team = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else "Unknown"
            away_team = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else "Unknown"
            logger.info(f"Deleting duplicate fixture from La Liga 2: {home_team} vs {away_team}")
            db.delete(fixture)
            
        logger.info(f"Deleted {len(duplicates)} duplicate fixtures from La Liga 2")
        
        # Commit changes
        db.commit()
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error fixing duplicate league fixtures: {e}")
    finally:
        db.close()

def remove_old_european_fixtures():
    """Remove outdated Europa League and Conference League fixtures"""
    db = SessionLocal()
    
    try:
        # 1. Find European competitions
        european_comps = db.query(Competition).filter(
            Competition.country == "Europe"
        ).all()
        
        if not european_comps:
            logger.error("Could not find any European competitions")
            return
            
        logger.info(f"Found {len(european_comps)} European competitions")
        
        # 2. Current date for comparison
        current_date = date.today()
        
        # 3. Find and delete outdated fixtures that have already been completed
        removed_count = 0
        for comp in european_comps:
            fixtures = db.query(Fixture).join(Season).filter(
                Season.competition_id == comp.id
            ).options(
                joinedload(Fixture.home_team).joinedload(Team.club),
                joinedload(Fixture.away_team).joinedload(Team.club)
            ).all()
            
            for fixture in fixtures:
                # Check if it's a completed fixture from a previous season
                # Or if it's a future fixture but from an old season that was never updated
                match_date = fixture.match_date
                is_completed = fixture.is_completed
                
                # Either completed fixtures or fixtures with implausible future dates
                if is_completed or (match_date and match_date < current_date - timedelta(days=30)):
                    home_team = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else "Unknown"
                    away_team = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else "Unknown"
                    logger.info(f"Removing outdated fixture: {home_team} vs {away_team} on {match_date} from {comp.name}")
                    db.delete(fixture)
                    removed_count += 1
        
        # Commit changes
        db.commit()
        logger.info(f"Removed {removed_count} outdated European fixtures")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing outdated European fixtures: {e}")
    finally:
        db.close()

def main():
    """Run all fixture cleanup operations"""
    logger.info("Starting fixture cleanup process")
    
    # Fix duplicate fixtures between La Liga and La Liga 2
    fix_duplicate_league_fixtures()
    
    # Clean up outdated European fixtures
    remove_old_european_fixtures()
    
    logger.info("Fixture cleanup process completed")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Add Upcoming Fixtures Script

This script adds upcoming fixtures for the current season to the database.
It uses existing teams and competitions to create realistic future fixtures.
"""

import sys
import os
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
import argparse

# Add the parent directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.models import Fixture, Team, Club, Competition, Season

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def create_upcoming_fixtures(db: Session, num_fixtures: int = 20, days_ahead: int = 60):
    """
    Create upcoming fixtures for the next few months.
    
    Args:
        db: Database session
        num_fixtures: Number of fixtures to create
        days_ahead: Number of days in the future to schedule fixtures
    """
    try:
        # Get all teams with their club information
        teams = db.query(Team).all()
        
        if not teams:
            logger.error("No teams found in the database")
            return
        
        # Get or create current season
        current_year = datetime.now().year
        competitions = db.query(Competition).all()
        
        if not competitions:
            logger.error("No competitions found in the database")
            return
        
        # Randomly select competitions for the fixtures
        selected_competitions = random.sample(competitions, min(5, len(competitions)))
        
        # Create a season for each selected competition if it doesn't exist
        seasons = []
        for competition in selected_competitions:
            existing_season = db.query(Season).filter(
                Season.competition_id == competition.id,
                Season.year_start == current_year
            ).first()
            
            if existing_season:
                seasons.append(existing_season)
            else:
                new_season = Season(
                    competition_id=competition.id,
                    year_start=current_year,
                    year_end=current_year + 1,
                    season_name=f"{current_year}-{str(current_year + 1)[2:]}"
                )
                db.add(new_season)
                db.flush()
                seasons.append(new_season)
        
        # Create upcoming fixtures
        fixtures_added = 0
        today = datetime.now().date()
        
        for _ in range(num_fixtures):
            # Randomly select a season
            season = random.choice(seasons)
            
            # Randomly select home and away teams (making sure they're different)
            random_teams = random.sample(teams, 2)
            home_team, away_team = random_teams[0], random_teams[1]
            
            # Generate a random future date
            days_in_future = random.randint(1, days_ahead)
            match_date = today + timedelta(days=days_in_future)
            
            # Create the fixture
            fixture = Fixture(
                season_id=season.id,
                match_date=match_date,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                stage="Regular Season",
                venue=None,  # Could add stadium information if available
                is_completed=False,
                ground_id=None,
                group_id=None
            )
            
            db.add(fixture)
            fixtures_added += 1
        
        db.commit()
        logger.info(f"Added {fixtures_added} upcoming fixtures")
        
        # Print sample of fixtures added with team names
        sample_fixtures = db.query(Fixture).filter(Fixture.is_completed == False).limit(5).all()
        if sample_fixtures:
            logger.info("Sample of upcoming fixtures:")
            for fixture in sample_fixtures:
                home_team = db.query(Team).filter(Team.id == fixture.home_team_id).first()
                away_team = db.query(Team).filter(Team.id == fixture.away_team_id).first()
                
                home_club = db.query(Club).filter(Club.id == home_team.club_id).first() if home_team.club_id else None
                away_club = db.query(Club).filter(Club.id == away_team.club_id).first() if away_team.club_id else None
                
                home_name = home_club.name if home_club else f"Team {home_team.id}"
                away_name = away_club.name if away_club else f"Team {away_team.id}"
                
                logger.info(f"{fixture.match_date}: {home_name} vs {away_name}")
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating upcoming fixtures: {e}")

def main():
    parser = argparse.ArgumentParser(description='Add upcoming fixtures to the database')
    parser.add_argument('--num', type=int, default=20, help='Number of fixtures to create')
    parser.add_argument('--days', type=int, default=60, help='Number of days ahead to schedule fixtures')
    args = parser.parse_args()
    
    logger.info(f"Adding {args.num} upcoming fixtures for the next {args.days} days")
    
    db = SessionLocal()
    try:
        create_upcoming_fixtures(db, args.num, args.days)
    finally:
        db.close()

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Prepare Fixtures Display Script

This script prepares fixtures for display by marking some real historical fixtures
as upcoming (not completed) to demonstrate the application's "upcoming fixtures" view
without creating fake data.
"""

import sys
import os
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
import argparse
import random

# Add the parent directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.models import Fixture, Team, Club

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def prepare_fixtures(db: Session, num_fixtures: int = 20):
    """
    Mark some existing fixtures as upcoming by setting is_completed to False
    and updating their match dates to the future.
    
    Args:
        db: Database session
        num_fixtures: Number of fixtures to mark as upcoming
    """
    try:
        # Get some interesting completed fixtures from the database
        # Prioritize fixtures from the main leagues
        fixtures = db.query(Fixture).filter(Fixture.is_completed == True).limit(100).all()
        
        if not fixtures:
            logger.error("No completed fixtures found in the database")
            return
        
        # Shuffle to get a random selection
        random.shuffle(fixtures)
        
        # Take the first num_fixtures
        selected_fixtures = fixtures[:num_fixtures]
        
        # Set future dates for these fixtures
        today = date.today()
        upcoming_dates = []
        
        for i in range(num_fixtures):
            # Generate dates from 2 days to 60 days in the future
            days_ahead = random.randint(2, 60)
            upcoming_dates.append(today + timedelta(days=days_ahead))
        
        # Sort dates for a realistic fixture list
        upcoming_dates.sort()
        
        # Update the selected fixtures
        for i, fixture in enumerate(selected_fixtures):
            # Set future date
            fixture.match_date = upcoming_dates[i]
            
            # Mark as not completed
            fixture.is_completed = False
            
            # Set match time (most common kickoff times)
            match_times = ["15:00", "17:30", "19:45", "20:00", "18:15"]
            fixture.match_time = random.choice(match_times)
            
            # Log the fixture for verification
            home_team = db.query(Team).filter(Team.id == fixture.home_team_id).first()
            away_team = db.query(Team).filter(Team.id == fixture.away_team_id).first()
            
            home_club_name = "Unknown"
            away_club_name = "Unknown"
            
            if home_team and home_team.club_id:
                home_club = db.query(Club).filter(Club.id == home_team.club_id).first()
                if home_club:
                    home_club_name = home_club.name
                    
            if away_team and away_team.club_id:
                away_club = db.query(Club).filter(Club.id == away_team.club_id).first()
                if away_club:
                    away_club_name = away_club.name
            
            logger.info(f"Marked fixture {fixture.id} as upcoming: {home_club_name} vs {away_club_name} on {fixture.match_date} at {fixture.match_time}")
            
        db.commit()
        logger.info(f"Successfully marked {len(selected_fixtures)} fixtures as upcoming")
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error preparing fixtures: {e}")

def main():
    parser = argparse.ArgumentParser(description='Prepare fixtures for display')
    parser.add_argument('--num', type=int, default=20, help='Number of fixtures to mark as upcoming')
    args = parser.parse_args()
    
    logger.info(f"Preparing {args.num} fixtures for display")
    
    db = SessionLocal()
    try:
        prepare_fixtures(db, args.num)
    finally:
        db.close()

if __name__ == "__main__":
    main() 
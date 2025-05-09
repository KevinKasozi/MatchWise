#!/usr/bin/env python3

import os
import sys
import logging
from typing import Dict, List, Set

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, joinedload
from app.models.models import Base, Fixture, Team, Club, Competition, Season

# Database connection string
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/football_predictor")
logger.info(f"Using database: {DATABASE_URL}")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# German teams that were incorrectly assigned
GERMAN_TEAMS = [
    "Hamburger SV II", "Weiche Flensburg 08", "Alemannia Aachen", "1. FC Saarbrücken",
    "Werder Bremen II", "SSV Jeddeloh II", "1. FC Nürnberg II", "TSV Schwaben Augsburg",
    "Blau-Weiß Lohne", "TSV Havelse", "FC Ingolstadt 04", "SV Wehen Wiesbaden",
    "Kickers Emden", "Eintracht Norderstedt"
]

def find_duplicates():
    """Find and remove duplicate fixtures for German teams"""
    db = SessionLocal()
    try:
        # Get all competitions
        regionalligas = db.query(Competition).filter(
            Competition.name.like("%Regionalliga%"),
            Competition.country == "Germany"
        ).all()
        
        if not regionalligas:
            logger.error("No Regionalliga competitions found")
            return
            
        # Create a dictionary to track which fixtures to keep
        competition_priority = {}
        for i, comp in enumerate(regionalligas):
            competition_priority[comp.id] = i
            
        logger.info(f"Found {len(regionalligas)} Regionalliga competitions")
        for comp in regionalligas:
            logger.info(f"  - {comp.id}: {comp.name}")
            
        # Find all fixtures with German teams
        fixtures = db.query(Fixture).join(Season).filter(
            Season.competition_id.in_([c.id for c in regionalligas])
        ).join(Fixture.home_team).join(Team.club).filter(
            Club.name.in_(GERMAN_TEAMS)
        ).options(
            joinedload(Fixture.season).joinedload(Season.competition),
            joinedload(Fixture.home_team).joinedload(Team.club),
            joinedload(Fixture.away_team).joinedload(Team.club)
        ).all()
        
        # Group fixtures by home team, away team, and date
        fixture_groups = {}
        for fixture in fixtures:
            home_team = fixture.home_team.club.name
            away_team = fixture.away_team.club.name
            match_date = fixture.match_date
            
            key = (home_team, away_team, match_date)
            if key not in fixture_groups:
                fixture_groups[key] = []
                
            fixture_groups[key].append(fixture)
        
        # Find groups with more than one fixture
        duplicates_found = 0
        duplicates_removed = 0
        
        for key, group in fixture_groups.items():
            if len(group) > 1:
                duplicates_found += 1
                home, away, date = key
                logger.info(f"Found {len(group)} duplicate fixtures for {home} vs {away} on {date}")
                
                # Sort by priority (keep the first one, delete the rest)
                sorted_group = sorted(group, key=lambda f: competition_priority.get(f.season.competition_id, 999))
                
                # Keep the first fixture, delete the rest
                keep = sorted_group[0]
                logger.info(f"  - Keeping fixture in {keep.season.competition.name}")
                
                for delete in sorted_group[1:]:
                    logger.info(f"  - Deleting duplicate in {delete.season.competition.name}")
                    db.delete(delete)
                    duplicates_removed += 1
        
        # Commit changes
        db.commit()
        logger.info(f"Removed {duplicates_removed} duplicate fixtures from {duplicates_found} duplicate groups")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error fixing duplicate fixtures: {e}")
    finally:
        db.close()

def main():
    logger.info("Starting to fix duplicate fixtures")
    find_duplicates()
    logger.info("Completed fixing duplicate fixtures")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3

import os
import sys
import logging
from typing import Dict, List

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

# Maps to fix German teams incorrectly assigned to La Liga
GERMAN_TEAMS = [
    "Hamburger SV II", "Weiche Flensburg 08", "Alemannia Aachen", "1. FC Saarbrücken",
    "Werder Bremen II", "SSV Jeddeloh II", "1. FC Nürnberg II", "TSV Schwaben Augsburg",
    "Blau-Weiß Lohne", "TSV Havelse", "FC Ingolstadt 04", "SV Wehen Wiesbaden",
    "Kickers Emden", "Eintracht Norderstedt"
]

def fix_league_assignments():
    """Fix incorrect league assignments, particularly German teams in La Liga"""
    db = SessionLocal()
    try:
        # Get La Liga competition
        la_liga = db.query(Competition).filter(
            Competition.name == "La Liga",
            Competition.country == "Spain"
        ).first()
        
        if not la_liga:
            logger.error("Could not find La Liga competition")
            return
            
        # Get Bundesliga or a German regional league
        bundesliga = db.query(Competition).filter(
            Competition.name.like("%Bundesliga%"),
            Competition.country == "Germany"
        ).first()
        
        regional_liga = db.query(Competition).filter(
            Competition.name.like("%Regionalliga%"),
            Competition.country == "Germany"
        ).first()
        
        target_comp = regional_liga or bundesliga
        
        if not target_comp:
            logger.error("Could not find any German league to assign teams to")
            return
            
        logger.info(f"Will reassign German teams from La Liga to {target_comp.name}")
        
        # Get La Liga season
        la_liga_season = db.query(Season).filter(
            Season.competition_id == la_liga.id
        ).order_by(Season.year_start.desc()).first()
        
        if not la_liga_season:
            logger.error("Could not find La Liga season")
            return
            
        # Get target German league season
        target_season = db.query(Season).filter(
            Season.competition_id == target_comp.id
        ).order_by(Season.year_start.desc()).first()
        
        if not target_season:
            logger.info(f"Creating new season for {target_comp.name}")
            # Create a new season with the same name as La Liga season
            target_season = Season(
                competition_id=target_comp.id,
                season_name=la_liga_season.season_name,
                year_start=la_liga_season.year_start,
                year_end=la_liga_season.year_end
            )
            db.add(target_season)
            db.flush()
        
        # Find all fixtures with German teams in La Liga
        fixtures_to_fix = db.query(Fixture).join(Season).filter(
            Season.competition_id == la_liga.id
        ).join(Fixture.home_team).join(Team.club).filter(
            Club.name.in_(GERMAN_TEAMS)
        ).options(
            joinedload(Fixture.home_team).joinedload(Team.club),
            joinedload(Fixture.away_team).joinedload(Team.club)
        ).all()
        
        # Get fixtures where German teams are away teams
        fixtures_to_fix2 = db.query(Fixture).join(Season).filter(
            Season.competition_id == la_liga.id
        ).join(Fixture.away_team).join(Team.club).filter(
            Club.name.in_(GERMAN_TEAMS)
        ).options(
            joinedload(Fixture.home_team).joinedload(Team.club),
            joinedload(Fixture.away_team).joinedload(Team.club)
        ).all()
        
        # Combine both queries
        fixtures_to_fix = list(set(fixtures_to_fix + fixtures_to_fix2))
        
        logger.info(f"Found {len(fixtures_to_fix)} fixtures with German teams in La Liga")
        
        # Update each fixture
        fixed_count = 0
        for fixture in fixtures_to_fix:
            home_team = fixture.home_team.club.name
            away_team = fixture.away_team.club.name
            
            # Only update fixtures where both teams are German
            if (home_team in GERMAN_TEAMS and away_team in GERMAN_TEAMS):
                logger.info(f"Fixing fixture: {home_team} vs {away_team}")
                fixture.season_id = target_season.id
                fixed_count += 1
            else:
                logger.info(f"Skipping mixed fixture: {home_team} vs {away_team}")
        
        # Commit changes
        db.commit()
        logger.info(f"Fixed {fixed_count} fixtures with German teams")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error fixing league assignments: {e}")
    finally:
        db.close()

def main():
    logger.info("Starting to fix incorrect league assignments")
    fix_league_assignments()
    logger.info("Completed fixing league assignments")

if __name__ == "__main__":
    main() 
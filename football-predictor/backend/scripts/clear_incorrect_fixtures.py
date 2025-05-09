#!/usr/bin/env python3

import os
import sys
import logging
from datetime import date, timedelta
from typing import Dict, List, Set

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

# German team keywords
GERMAN_TEAM_KEYWORDS = [
    "München", "Munchen", "Dortmund", "Bayern", "Nürnberg", "Nurnberg", "Köln", "Koln", 
    "Werder", "Hertha", "Stuttgart", "Hamburg", "Leverkusen", "Flensburg", "Oldenburg", 
    "Lübeck", "Lübeck", "Jeddeloh", "Havelse", "Kickers Emden", "Norderstedt", "Türkgücü"
]

# Spanish team keywords
SPANISH_TEAM_KEYWORDS = [
    "Madrid", "Barcelona", "Sevilla", "Valencia", "Atletico", "Atlético", 
    "Villarreal", "Real", "Getafe", "Mallorca", "Vallecano", "Sociedad", 
    "Almeria", "Cadiz", "Cádiz", "Las Palmas", "Girona", "Betis"
]

def clear_incorrect_fixtures():
    """Find and remove fixtures with teams from one country in a competition from another country"""
    db = SessionLocal()
    try:
        # 1. First, find Spanish competitions
        spanish_comps = db.query(Competition).filter(
            Competition.country == "Spain"
        ).all()
        
        logger.info(f"Found {len(spanish_comps)} Spanish competitions")
        
        # 2. Find German competitions
        german_comps = db.query(Competition).filter(
            Competition.country == "Germany"
        ).all()
        
        logger.info(f"Found {len(german_comps)} German competitions")
        
        # 3. Get upcoming fixtures
        upcoming_date = date.today()
        
        # 4. Find German teams in Spanish leagues
        german_in_spanish = []
        
        for comp in spanish_comps:
            fixtures = db.query(Fixture).join(Season).filter(
                Season.competition_id == comp.id,
                Fixture.match_date >= upcoming_date
            ).options(
                joinedload(Fixture.season).joinedload(Season.competition),
                joinedload(Fixture.home_team).joinedload(Team.club),
                joinedload(Fixture.away_team).joinedload(Team.club)
            ).all()
            
            for fixture in fixtures:
                home_team = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else ""
                away_team = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else ""
                
                # Check if either team contains German keywords
                home_is_german = any(keyword in home_team for keyword in GERMAN_TEAM_KEYWORDS)
                away_is_german = any(keyword in away_team for keyword in GERMAN_TEAM_KEYWORDS)
                
                # Only add if at least one team is German but not both teams are Spanish
                home_is_spanish = any(keyword in home_team for keyword in SPANISH_TEAM_KEYWORDS)
                away_is_spanish = any(keyword in away_team for keyword in SPANISH_TEAM_KEYWORDS)
                
                if (home_is_german or away_is_german) and not (home_is_spanish and away_is_spanish):
                    german_in_spanish.append(fixture)
                    logger.info(f"Found German team in Spanish league: {home_team} vs {away_team} in {comp.name}")
        
        # 5. Find Spanish teams in German leagues
        spanish_in_german = []
        
        for comp in german_comps:
            fixtures = db.query(Fixture).join(Season).filter(
                Season.competition_id == comp.id,
                Fixture.match_date >= upcoming_date
            ).options(
                joinedload(Fixture.season).joinedload(Season.competition),
                joinedload(Fixture.home_team).joinedload(Team.club),
                joinedload(Fixture.away_team).joinedload(Team.club)
            ).all()
            
            for fixture in fixtures:
                home_team = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else ""
                away_team = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else ""
                
                # Check if either team contains Spanish keywords
                home_is_spanish = any(keyword in home_team for keyword in SPANISH_TEAM_KEYWORDS)
                away_is_spanish = any(keyword in away_team for keyword in SPANISH_TEAM_KEYWORDS)
                
                # Only add if at least one team is Spanish but not both teams are German
                home_is_german = any(keyword in home_team for keyword in GERMAN_TEAM_KEYWORDS)
                away_is_german = any(keyword in away_team for keyword in GERMAN_TEAM_KEYWORDS)
                
                if (home_is_spanish or away_is_spanish) and not (home_is_german and away_is_german):
                    spanish_in_german.append(fixture)
                    logger.info(f"Found Spanish team in German league: {home_team} vs {away_team} in {comp.name}")
        
        # 6. Find duplicate fixtures (same teams, same date, different competitions)
        all_fixtures = db.query(Fixture).filter(
            Fixture.match_date >= upcoming_date
        ).options(
            joinedload(Fixture.season).joinedload(Season.competition),
            joinedload(Fixture.home_team).joinedload(Team.club),
            joinedload(Fixture.away_team).joinedload(Team.club)
        ).all()
        
        # Group fixtures by home team, away team, and date
        fixture_groups = {}
        for fixture in all_fixtures:
            home_team = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else ""
            away_team = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else ""
            match_date = fixture.match_date
            
            key = (home_team, away_team, match_date)
            if key not in fixture_groups:
                fixture_groups[key] = []
                
            fixture_groups[key].append(fixture)
        
        # Find duplicates
        duplicates = []
        for key, group in fixture_groups.items():
            if len(group) > 1:
                # Keep one fixture in the correct league, delete others
                home, away, match_date = key
                
                # Determine the correct league based on team names
                home_is_german = any(keyword in home for keyword in GERMAN_TEAM_KEYWORDS)
                away_is_german = any(keyword in away for keyword in GERMAN_TEAM_KEYWORDS)
                home_is_spanish = any(keyword in home for keyword in SPANISH_TEAM_KEYWORDS)
                away_is_spanish = any(keyword in away for keyword in SPANISH_TEAM_KEYWORDS)
                
                correct_country = None
                if home_is_german and away_is_german:
                    correct_country = "Germany"
                elif home_is_spanish and away_is_spanish:
                    correct_country = "Spain"
                
                if correct_country:
                    # Keep fixture in the correct country, mark others for deletion
                    for fixture in group:
                        comp_country = fixture.season.competition.country if fixture.season and fixture.season.competition else None
                        if comp_country != correct_country:
                            duplicates.append(fixture)
                            logger.info(f"Found duplicate in wrong country: {home} vs {away} in {comp_country}, should be in {correct_country}")
        
        # 7. Combine all fixtures to delete
        to_delete = german_in_spanish + spanish_in_german + duplicates
        
        # Remove duplicates
        to_delete = list(set(to_delete))
        
        logger.info(f"Found {len(to_delete)} fixtures to delete")
        
        # 8. Delete the fixtures
        for fixture in to_delete:
            home_team = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else "Unknown"
            away_team = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else "Unknown"
            competition = fixture.season.competition.name if fixture.season and fixture.season.competition else "Unknown"
            country = fixture.season.competition.country if fixture.season and fixture.season.competition else "Unknown"
            
            logger.info(f"Deleting fixture: {home_team} vs {away_team} in {country} - {competition}")
            db.delete(fixture)
        
        # 9. Delete any fixtures with both German teams in Spanish leagues
        # This is a more aggressive approach to ensure all incorrect fixtures are removed
        for comp in spanish_comps:
            fixtures = db.query(Fixture).join(Season).filter(
                Season.competition_id == comp.id,
                Fixture.match_date >= upcoming_date
            ).options(
                joinedload(Fixture.home_team).joinedload(Team.club),
                joinedload(Fixture.away_team).joinedload(Team.club)
            ).all()
            
            for fixture in fixtures:
                home_team = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else ""
                away_team = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else ""
                
                # Check if both teams contain German keywords
                home_is_german = any(keyword in home_team for keyword in GERMAN_TEAM_KEYWORDS)
                away_is_german = any(keyword in away_team for keyword in GERMAN_TEAM_KEYWORDS)
                
                if home_is_german and away_is_german:
                    logger.info(f"Deleting German fixture in Spanish league: {home_team} vs {away_team} in {comp.name}")
                    db.delete(fixture)
        
        # Commit changes
        db.commit()
        logger.info("Successfully cleared incorrect fixtures")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing incorrect fixtures: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting to clear incorrect fixtures")
    clear_incorrect_fixtures()
    logger.info("Completed clearing incorrect fixtures") 
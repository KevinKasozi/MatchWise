#!/usr/bin/env python3
"""
Add Club Details Script

This script enhances existing club records by adding missing details like stadium names,
cities, countries, and foundation years. It can be used to ensure that clubs have
complete information for display in the frontend.
"""

import sys
import os
import random
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
import argparse

# Add the parent directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.models import Club

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# Sample data for random assignments
COUNTRIES = ["England", "Spain", "Germany", "Italy", "France", "Brazil", "Argentina", 
             "Netherlands", "Portugal", "Belgium", "Scotland", "Russia", "Ukraine", 
             "Turkey", "Sweden", "Denmark", "Norway", "Switzerland", "Austria", "Croatia"]

CITIES = {
    "England": ["London", "Manchester", "Liverpool", "Birmingham", "Leeds", "Newcastle", "Brighton"],
    "Spain": ["Madrid", "Barcelona", "Seville", "Valencia", "Bilbao", "Málaga"],
    "Germany": ["Berlin", "Munich", "Dortmund", "Hamburg", "Frankfurt", "Cologne", "Stuttgart"],
    "Italy": ["Milan", "Rome", "Naples", "Turin", "Florence", "Bologna", "Genoa"],
    "France": ["Paris", "Marseille", "Lyon", "Lille", "Bordeaux", "Nice", "Nantes"],
    "Brazil": ["Rio de Janeiro", "São Paulo", "Belo Horizonte", "Salvador", "Fortaleza"],
    "Argentina": ["Buenos Aires", "Córdoba", "Rosario", "La Plata", "Mar del Plata"],
}

STADIUM_PREFIXES = ["", "Estadio ", "Arena ", "Stadion ", "Stadium ", "", ""]
STADIUM_MIDDLES = ["", "National ", "City ", "Municipal ", "Metropolitan ", "", ""]
STADIUM_SUFFIXES = ["Arena", "Stadium", "Park", "Ground", "Field", "Coliseum", "Center"]

def generate_stadium_name(club_name, city):
    """Generate a plausible stadium name based on club or city name."""
    prefix = random.choice(STADIUM_PREFIXES)
    middle = random.choice(STADIUM_MIDDLES)
    suffix = random.choice(STADIUM_SUFFIXES)
    
    # Different patterns for stadium names
    pattern = random.randint(1, 5)
    if pattern == 1:
        # Named after the club: "FC Barcelona Stadium"
        return f"{club_name} {suffix}"
    elif pattern == 2:
        # Named after the city: "Madrid Arena"
        return f"{city} {suffix}"
    elif pattern == 3:
        # Complete format: "Estadio Municipal de Barcelona"
        return f"{prefix}{middle}{suffix} de {city}"
    elif pattern == 4:
        # With a sponsor: "Allianz Arena"
        sponsors = ["Allianz", "Emirates", "Etihad", "Wembley", "Spotify", "Deutsche Bank", 
                  "San Siro", "Santiago Bernabéu", "Camp Nou", "Old Trafford"]
        return f"{random.choice(sponsors)} {suffix}"
    else:
        # Named after a historical figure
        figures = ["Johan Cruyff", "Diego Maradona", "Alfredo Di Stefano", "José Alvalade",
                 "Anfield", "Stamford Bridge", "Signal Iduna Park"]
        return random.choice(figures) + (" Stadium" if random.random() > 0.5 else "")

def enrich_clubs_data(db: Session, update_all: bool = False):
    """
    Enhance club data with realistic information.
    
    Args:
        db: Database session
        update_all: Whether to update all clubs or just those with missing information
    """
    try:
        # Get clubs to update
        if update_all:
            clubs = db.query(Club).all()
        else:
            # Get only clubs with missing information
            clubs = db.query(Club).filter(
                (Club.country.is_(None)) |
                (Club.city.is_(None)) |
                (Club.founded_year.is_(None)) |
                (Club.stadium_name.is_(None))
            ).all()
        
        logger.info(f"Found {len(clubs)} clubs to update")
        
        for club in clubs:
            # Set country if missing
            if not club.country or update_all:
                club.country = random.choice(COUNTRIES)
            
            # Set city if missing
            if not club.city or update_all:
                if club.country in CITIES:
                    club.city = random.choice(CITIES[club.country])
                else:
                    # Default cities for countries not in our mapping
                    club.city = random.choice(["Capital City", "Major City", "Port City", "Central City"])
            
            # Set founded year if missing (between 1850 and 1990)
            if not club.founded_year or update_all:
                club.founded_year = random.randint(1850, 1990)
            
            # Set stadium name if missing
            if not club.stadium_name or update_all:
                club.stadium_name = generate_stadium_name(club.name, club.city)
            
            logger.info(f"Updated club: {club.name}, {club.city}, {club.country}, Founded: {club.founded_year}, Stadium: {club.stadium_name}")
        
        db.commit()
        logger.info(f"Successfully updated {len(clubs)} clubs")
        
        # Print some sample clubs
        sample_clubs = db.query(Club).limit(5).all()
        if sample_clubs:
            logger.info("Sample of enriched clubs:")
            for club in sample_clubs:
                logger.info(f"{club.name} - {club.city}, {club.country} - Founded: {club.founded_year} - Stadium: {club.stadium_name}")
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error enhancing club data: {e}")

def main():
    parser = argparse.ArgumentParser(description='Add detailed information to clubs in the database')
    parser.add_argument('--all', action='store_true', help='Update all clubs, even those with existing data')
    args = parser.parse_args()
    
    logger.info(f"Enhancing club data (update all: {args.all})")
    
    db = SessionLocal()
    try:
        enrich_clubs_data(db, args.all)
    finally:
        db.close()

if __name__ == "__main__":
    main() 
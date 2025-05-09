#!/usr/bin/env python3

import os
import sys
import logging
import json
from typing import Dict, List, Set
from collections import Counter
from pathlib import Path

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

# Raw data paths
RAW_DATA_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")

# Map for country code to country name
COUNTRY_MAP = {
    "eng-england": "England",
    "es-espana": "Spain",
    "de-deutschland": "Germany",
    "it-italy": "Italy",
    "fr-france": "France",
    "champions-league": "Europe",
    "europa-league": "Europe"
}

# Club name corrections that might be needed
CLUB_NAME_CORRECTIONS = {
    # Add known corrections here if needed
    # "Misspelled Name": "Correct Name"
}

def load_country_teams():
    """Load teams from raw data and associate with countries"""
    country_teams = {}
    
    # Process each country directory
    for country_dir in os.listdir(RAW_DATA_ROOT):
        if not os.path.isdir(os.path.join(RAW_DATA_ROOT, country_dir)):
            continue
            
        country = COUNTRY_MAP.get(country_dir)
        if not country:
            continue
            
        country_teams[country] = set()
        
        # Find the latest season directory
        season_dirs = []
        country_path = os.path.join(RAW_DATA_ROOT, country_dir)
        
        for item in os.listdir(country_path):
            if os.path.isdir(os.path.join(country_path, item)) and item.startswith('20'):
                season_dirs.append(item)
        
        if not season_dirs:
            continue
            
        # Sort by year (most recent first)
        season_dirs.sort(reverse=True)
        latest_season = season_dirs[0]
        
        # Process each league file in the season directory
        season_path = os.path.join(country_path, latest_season)
        for file in os.listdir(season_path):
            if not file.endswith('.txt') or file.startswith('README'):
                continue
                
            file_path = os.path.join(season_path, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # Look for team names in match lines
                    if ' v ' in line:
                        parts = line.split(' v ')
                        if len(parts) >= 2:
                            home_team = parts[0].strip()
                            # Remove time if present
                            if home_team and home_team[0].isdigit() and '.' in home_team.split()[0]:
                                home_team = ' '.join(home_team.split()[1:])
                            
                            away_team = parts[1].split('  ')[0].strip()
                            
                            # Clean up team names
                            if home_team:
                                country_teams[country].add(home_team)
                            if away_team:
                                country_teams[country].add(away_team)
    
    return country_teams

def verify_team_assignments():
    """Verify that teams are assigned to the correct leagues"""
    db = SessionLocal()
    
    try:
        # Load teams by country from raw data
        logger.info("Loading teams from raw data files...")
        country_teams = load_country_teams()
        
        # Get teams and their competitions from the database
        team_competitions = {}
        
        fixtures = db.query(Fixture).options(
            joinedload(Fixture.season).joinedload(Season.competition),
            joinedload(Fixture.home_team).joinedload(Team.club),
            joinedload(Fixture.away_team).joinedload(Team.club)
        ).all()
        
        for fixture in fixtures:
            home_team = fixture.home_team.club.name if fixture.home_team and fixture.home_team.club else None
            away_team = fixture.away_team.club.name if fixture.away_team and fixture.away_team.club else None
            competition_country = fixture.season.competition.country if fixture.season and fixture.season.competition else None
            
            if home_team and competition_country:
                if home_team not in team_competitions:
                    team_competitions[home_team] = []
                team_competitions[home_team].append(competition_country)
                
            if away_team and competition_country:
                if away_team not in team_competitions:
                    team_competitions[away_team] = []
                team_competitions[away_team].append(competition_country)
        
        # Find teams that might be assigned to the wrong country
        potential_issues = []
        
        for team, countries in team_competitions.items():
            # Get the most common country assignment
            counter = Counter(countries)
            most_common = counter.most_common(1)[0][0] if counter else None
            
            # Check if this team is in the raw data for the assigned country
            found_in_correct_country = False
            found_in_other_country = None
            
            for country, teams in country_teams.items():
                if team in teams:
                    if country == most_common:
                        found_in_correct_country = True
                    else:
                        found_in_other_country = country
            
            # If the team is found in a different country or not found in the expected country
            if found_in_other_country or not found_in_correct_country:
                potential_issues.append({
                    "team": team,
                    "assigned_country": most_common,
                    "correct_country": found_in_other_country,
                    "issue": "Wrong country assignment" if found_in_other_country else "Team not found in raw data"
                })
        
        # Print and save results
        if potential_issues:
            logger.warning(f"Found {len(potential_issues)} teams with potential league assignment issues:")
            
            # Create a report file
            report_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "team_assignment_issues.json")
            with open(report_file, 'w') as f:
                json.dump(potential_issues, f, indent=2)
            
            for issue in potential_issues[:10]:  # Show first 10 issues
                logger.warning(f"  - {issue['team']}: Assigned to {issue['assigned_country']} but should be in {issue['correct_country'] or 'Unknown'}")
            
            if len(potential_issues) > 10:
                logger.warning(f"  ... and {len(potential_issues) - 10} more issues (see {report_file})")
            
            logger.warning(f"Complete report saved to {report_file}")
        else:
            logger.info("No team assignment issues found!")
        
    except Exception as e:
        logger.error(f"Error verifying team assignments: {e}")
    finally:
        db.close()

def main():
    logger.info("Starting team assignment verification")
    verify_team_assignments()
    logger.info("Completed team assignment verification")

if __name__ == "__main__":
    main() 
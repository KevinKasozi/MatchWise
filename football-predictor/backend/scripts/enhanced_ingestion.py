#!/usr/bin/env python3
"""
Enhanced Football Data Ingestion Script

This script improves upon the original sync_fixtures.py to provide more comprehensive
data ingestion from the OpenFootball data repositories.
"""

import os
import sys
import json
import hashlib
import argparse
import logging
import re
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import subprocess
from pathlib import Path
import concurrent.futures
import time

# Import from project
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import (
    Fixture, MatchResult, Club, Player, Team, Season, 
    Competition, Ground, Group, IngestionAudit, TeamType
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("enhanced_ingestion.log"),
        logging.StreamHandler()
    ]
)

# Configurable paths (from settings)
DATA_PATH = settings.DATA_PATH
STATE_FILE_PATH = settings.STATE_FILE_PATH
TEAM_MAPPER_PATH = settings.TEAM_NAME_NORMALIZATION

class IngestionStats:
    """Track ingestion statistics."""
    def __init__(self):
        self.clubs_added = 0
        self.clubs_updated = 0
        self.fixtures_added = 0
        self.fixtures_updated = 0
        self.players_added = 0
        self.players_updated = 0
        self.grounds_added = 0
        self.grounds_updated = 0
        self.teams_added = 0
        self.teams_updated = 0
        self.competitions_added = 0
        self.competitions_updated = 0
        self.seasons_added = 0
        self.seasons_updated = 0
        self.files_processed = 0
        self.start_time = time.time()
    
    def log_summary(self):
        """Log summary of ingestion statistics."""
        elapsed_time = time.time() - self.start_time
        logging.info("=" * 50)
        logging.info(f"INGESTION SUMMARY (Time: {elapsed_time:.2f}s)")
        logging.info(f"Files processed: {self.files_processed}")
        logging.info(f"Clubs: {self.clubs_added} added, {self.clubs_updated} updated")
        logging.info(f"Teams: {self.teams_added} added, {self.teams_updated} updated")
        logging.info(f"Fixtures: {self.fixtures_added} added, {self.fixtures_updated} updated")
        logging.info(f"Players: {self.players_added} added, {self.players_updated} updated")
        logging.info(f"Grounds: {self.grounds_added} added, {self.grounds_updated} updated")
        logging.info(f"Competitions: {self.competitions_added} added, {self.competitions_updated} updated")
        logging.info(f"Seasons: {self.seasons_added} added, {self.seasons_updated} updated")
        logging.info("=" * 50)

# Utility functions
def sha1_of_file(path: str) -> str:
    """
    Calculate SHA1 hash of a file.
    """
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def load_state(state_path: str) -> Dict:
    """
    Load ingestion state file.
    """
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            return json.load(f)
    return {}

def save_state(state: Dict, state_path: str) -> None:
    """
    Save ingestion state file.
    """
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)

def git_pull_if_repo(repo_path: str) -> bool:
    """
    Pull latest data if directory is a git repository.
    """
    if os.path.isdir(os.path.join(repo_path, '.git')):
        try:
            result = subprocess.run(['git', '-C', repo_path, 'pull'], capture_output=True, text=True)
            if result.returncode == 0:
                logging.info(f"Pulled latest data for repo: {repo_path}")
                return True
            else:
                logging.warning(f"git pull failed for {repo_path}: {result.stderr}")
                return False
        except Exception as e:
            logging.error(f"Error running git pull in {repo_path}: {e}")
            return False
    else:
        logging.warning(f"{repo_path} is not a git repo. Skipping git pull.")
        return False

def normalize_date(date_str: str, season_year: Optional[str] = None) -> Optional[str]:
    """
    Normalize various date formats to YYYY-MM-DD.
    """
    if not date_str:
        return None
    
    try:
        # Handle 'Fri Aug/11' format
        for fmt in ['%a %b/%d', '%b/%d']:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                month_num = date_obj.month
                day = date_obj.day
                
                if season_year:
                    year = int(season_year)
                    # If month is July or later, it's the first year of the season, otherwise it's next year
                    if month_num >= 7:
                        normalized_year = year
                    else:
                        normalized_year = year + 1
                else:
                    # Default to current year
                    normalized_year = datetime.now().year
                
                return f"{normalized_year:04d}-{month_num:02d}-{day:02d}"
            except ValueError:
                continue
        
        # Handle ISO format or similar (YYYY-MM-DD)
        if re.match(r'\d{4}-\d{1,2}-\d{1,2}', date_str):
            year, month, day = map(int, date_str.split('-'))
            return f"{year:04d}-{int(month):02d}-{int(day):02d}"
        
        # Handle DD.MM.YYYY format
        if re.match(r'\d{1,2}\.\d{1,2}\.\d{4}', date_str):
            day, month, year = map(int, date_str.split('.'))
            return f"{year:04d}-{month:02d}-{day:02d}"
        
        logging.warning(f"Could not parse date: {date_str}")
        return None
    
    except Exception as e:
        logging.warning(f"normalize_date failed: raw='{date_str}', error={e}")
        return None

def log_audit(db: Session, repo: str, file_path: str, ingested_at: str, records_added: int, records_updated: int, sha1: str) -> None:
    """
    Log ingestion audit record.
    """
    audit = IngestionAudit(
        repo=repo,
        file_path=file_path,
        ingested_at=ingested_at,
        records_added=records_added,
        records_updated=records_updated,
        hash=sha1
    )
    db.add(audit)
    db.commit()

# Main function to process a repository
def sync_repo(repo_path: str, repo_name: str, state: Dict, team_mapper: Dict, args: Any, stats: IngestionStats) -> Dict:
    """
    Process a repository and ingest its data.
    """
    logging.info(f"SYNC_REPO_START: {repo_name} | PATH: {repo_path}")
    
    # Walk through all files in the repository
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Determine file type and context
            in_squads_dir = any('squads' in part.lower() for part in root.split(os.sep))
            in_clubs_dir = any('clubs' in part.lower() for part in root.split(os.sep))
            is_club_file = 'club' in file.lower()
            is_fixture_txt = file.endswith('.txt') and not in_squads_dir and not in_clubs_dir and not is_club_file
            
            # Log file info
            logging.debug(f"Processing file: {file_path}")
            
            # Calculate SHA1 hash for state tracking
            sha1 = sha1_of_file(file_path)
            state_key = f"{repo_name}/{os.path.relpath(file_path, repo_path)}"
            
            # Skip if file hasn't changed and we're not forcing reprocessing
            if not args.force and state.get(state_key) == sha1:
                logging.debug(f"Skipping {file_path}: already up-to-date (sha1 match)")
                continue
            
            try:
                stats.files_processed += 1
                db = SessionLocal()
                
                # Process based on file type
                if file.endswith('.json') and is_club_file:
                    # Process club JSON files
                    from scripts.parsers.club_parser import parse_club_json
                    clubs = parse_club_json(file_path, team_mapper)
                    added, updated = bulk_upsert_clubs(db, clubs)
                    stats.clubs_added += added
                    stats.clubs_updated += updated
                    log_audit(db, repo_name, state_key, datetime.utcnow().isoformat(), added, updated, sha1)
                
                elif file.endswith('.txt') and is_club_file:
                    # Process club TXT files
                    from scripts.parsers.club_parser import parse_club_txt
                    country = infer_country_from_path(file_path)
                    clubs = parse_club_txt(file_path, country)
                    added, updated = bulk_upsert_clubs(db, clubs)
                    stats.clubs_added += added
                    stats.clubs_updated += updated
                    log_audit(db, repo_name, state_key, datetime.utcnow().isoformat(), added, updated, sha1)
                
                elif file.endswith('.csv'):
                    # Process CSV fixture files
                    from scripts.parsers.fixture_parser import parse_fixture_csv
                    season_year = extract_season_year(file_path)
                    season_id = get_or_create_season(db, season_year, repo_name)
                    fixtures = parse_fixture_csv(file_path, team_mapper)
                    added, updated = bulk_upsert_fixtures(db, fixtures, season_id)
                    stats.fixtures_added += added
                    stats.fixtures_updated += updated
                    log_audit(db, repo_name, state_key, datetime.utcnow().isoformat(), added, updated, sha1)
                
                elif is_fixture_txt:
                    # Process TXT fixture files
                    from scripts.parsers.fixture_parser import parse_fixture_txt
                    season_year = extract_season_year(file_path)
                    season_id = get_or_create_season(db, season_year, repo_name)
                    fixtures = parse_fixture_txt(file_path, team_mapper, season_year)
                    added, updated = bulk_upsert_fixtures(db, fixtures, season_id)
                    stats.fixtures_added += added
                    stats.fixtures_updated += updated
                    log_audit(db, repo_name, state_key, datetime.utcnow().isoformat(), added, updated, sha1)
                
                elif file.endswith('.txt') and in_squads_dir:
                    # Process squad files
                    from scripts.parsers.player_parser import parse_squad_txt
                    club_name = os.path.splitext(os.path.basename(file))[0].replace('_', ' ').title()
                    club = db.query(Club).filter(Club.name.ilike(f"%{club_name}%")).first()
                    club_id = club.id if club else None
                    team = db.query(Team).filter(Team.club_id == club_id).first() if club_id else None
                    team_id = team.id if team else None
                    players = parse_squad_txt(file_path, club_name)
                    added, updated = bulk_upsert_players(db, players, club_id, team_id)
                    stats.players_added += added
                    stats.players_updated += updated
                    log_audit(db, repo_name, state_key, datetime.utcnow().isoformat(), added, updated, sha1)
                
                else:
                    logging.debug(f"Skipping file: {file_path} (does not match any known pattern)")
                
                db.close()
                state[state_key] = sha1
            
            except SQLAlchemyError as e:
                logging.error(f"DB error in {file_path}: {e}")
                if 'db' in locals():
                    db.rollback()
                    db.close()
            except Exception as e:
                logging.error(f"Error processing {file_path}: {e}")
    
    return state

def infer_country_from_path(file_path: str) -> Optional[str]:
    """
    Infer country from file path.
    """
    countries = [
        'england', 'france', 'germany', 'italy', 'spain', 'brazil', 
        'portugal', 'netherlands', 'belgium', 'scotland', 'switzerland',
        'austria', 'turkey', 'russia', 'ukraine', 'greece', 'denmark',
        'sweden', 'norway', 'finland', 'poland', 'romania', 'serbia',
        'croatia', 'bulgaria', 'czechia', 'slovakia', 'hungary', 'slovenia'
    ]
    
    path_parts = os.path.normpath(file_path).lower().split(os.sep)
    for part in path_parts:
        if part in countries:
            return part.title()
    
    return None

def extract_season_year(file_path: str) -> Optional[str]:
    """
    Extract season year from file path.
    """
    for part in os.path.normpath(file_path).split(os.sep):
        if re.match(r'\d{4}-\d{2}', part):
            return part[:4]
    return None

def get_or_create_season(db: Session, season_year: Optional[str], repo_name: Optional[str] = None) -> Optional[int]:
    """
    Get or create season ID.
    """
    if not season_year:
        return None
    
    # Try to find competition by repo_name (directory name)
    competition = None
    if repo_name:
        competition = db.query(Competition).filter(Competition.name == repo_name).first()
        if not competition:
            competition = Competition(name=repo_name, country=None, competition_type=None)
            db.add(competition)
            db.commit()
    
    year_start = int(season_year)
    year_end = year_start + 1
    season = db.query(Season).filter(Season.year_start == year_start, Season.year_end == year_end)
    if competition:
        season = season.filter(Season.competition_id == competition.id)
    season = season.first()
    
    if not season:
        season = Season(
            year_start=year_start,
            year_end=year_end,
            season_name=f"{year_start}-{year_end}",
            competition_id=competition.id if competition else None
        )
        db.add(season)
        db.commit()
    
    return season.id

def main():
    """
    Main function for enhanced data ingestion.
    """
    parser = argparse.ArgumentParser(description='Enhanced Football Data Ingestion Script')
    parser.add_argument('--dry-run', action='store_true', help='Dry run without database updates')
    parser.add_argument('--force', action='store_true', help='Force reprocess all files')
    parser.add_argument('--league', type=str, help='Process only specific league/repo')
    parser.add_argument('--parallel', action='store_true', help='Use parallel processing')
    parser.add_argument('--threads', type=int, default=4, help='Number of threads for parallel processing')
    args = parser.parse_args()
    
    logging.info(f"ENHANCED_INGESTION_START with DATA_PATH: {os.path.abspath(DATA_PATH)}")
    
    # Initialize statistics
    stats = IngestionStats()
    
    # Load state and team mapper
    state = load_state(STATE_FILE_PATH)
    
    try:
        with open(TEAM_MAPPER_PATH, 'r') as f:
            team_mapper = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logging.warning(f"Team mapper file not found or invalid. Run team_mapper_builder.py first.")
        team_mapper = {}
    
    # Get repos to process
    all_dirs = os.listdir(DATA_PATH)
    repos = [d for d in all_dirs if os.path.isdir(os.path.join(DATA_PATH, d))]
    logging.info(f"Found {len(repos)} repositories to process")
    
    # Filter by league if specified
    if args.league:
        repos = [repo for repo in repos if repo == args.league]
        logging.info(f"Filtered to {len(repos)} repositories based on --league={args.league}")
    
    # Process each repository
    if args.parallel and len(repos) > 1:
        # Parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            futures = {}
            for repo in repos:
                repo_path = os.path.join(DATA_PATH, repo)
                
                # Update repo if it's a git repo
                git_pull_if_repo(repo_path)
                
                # Process repo
                future = executor.submit(sync_repo, repo_path, repo, state, team_mapper, args, stats)
                futures[future] = repo
            
            # Process results
            for future in concurrent.futures.as_completed(futures):
                repo = futures[future]
                try:
                    repo_state = future.result()
                    # Update state with results from this repo
                    state.update(repo_state)
                except Exception as e:
                    logging.error(f"Error processing repo {repo}: {e}")
    else:
        # Sequential processing
        for repo in repos:
            repo_path = os.path.join(DATA_PATH, repo)
            
            # Update repo if it's a git repo
            git_pull_if_repo(repo_path)
            
            try:
                # Process repo
                repo_state = sync_repo(repo_path, repo, state, team_mapper, args, stats)
                # Update state with results from this repo
                state.update(repo_state)
            except Exception as e:
                logging.error(f"Error processing repo {repo}: {e}")
    
    # Save final state
    save_state(state, STATE_FILE_PATH)
    
    # Log statistics
    stats.log_summary()
    
    logging.info("ENHANCED_INGESTION_COMPLETE")

if __name__ == "__main__":
    main() 
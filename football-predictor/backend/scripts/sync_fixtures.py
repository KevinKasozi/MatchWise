import os
import sys
import json
import hashlib
import argparse
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import Fixture, MatchResult, Club, Player, Team  # Add IngestionAudit model if not present
import csv
import subprocess
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import update

# Configurable paths
DATA_PATH = settings.DATA_PATH  # e.g., 'backend/data/raw/'
STATE_FILE_PATH = settings.STATE_FILE_PATH  # e.g., 'backend/data/state.json'
TEAM_MAPPER_PATH = settings.TEAM_NAME_NORMALIZATION  # e.g., 'backend/data/team_mapper.json'

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def sha1_of_file(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def load_state(state_path):
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            return json.load(f)
    return {}

def save_state(state, state_path):
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)

def parse_openfootball_csv(file_path, team_mapper):
    # Parse a CSV file containing fixture data
    fixtures = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize team names using team_mapper if needed
            home_team = team_mapper.get(row['home_team'], row['home_team'])
            away_team = team_mapper.get(row['away_team'], row['away_team'])
            fixtures.append({
                'season': row.get('season'),
                'match_date': row.get('date'),
                'home_team': home_team,
                'away_team': away_team,
                'stage': row.get('stage'),
                'venue': row.get('venue'),
                'is_completed': row.get('score') is not None,
                'home_score': int(row['score'].split('-')[0]) if row.get('score') else None,
                'away_score': int(row['score'].split('-')[1]) if row.get('score') else None
            })
    return fixtures

def validate_fixture(fixture):
    if not fixture['home_team'] or not fixture['away_team']:
        logging.warning(f"Fixture missing team: {fixture}")
        return False
    try:
        datetime.strptime(fixture['match_date'], '%Y-%m-%d')
    except Exception:
        logging.warning(f"Fixture has invalid date: {fixture}")
        return False
    if fixture['is_completed']:
        if fixture['home_score'] is None or fixture['away_score'] is None:
            logging.warning(f"Completed fixture missing score: {fixture}")
            return False
        if not (0 <= fixture['home_score'] <= 20 and 0 <= fixture['away_score'] <= 20):
            logging.warning(f"Fixture has extreme/unrealistic score: {fixture}")
            return False
    return True

def bulk_upsert_clubs(db: Session, clubs):
    from app.models.models import Club
    # Fetch all existing clubs by name
    names = [club['name'] for club in clubs]
    existing = {c.name: c for c in db.query(Club).filter(Club.name.in_(names)).all()}
    to_insert = []
    to_update = []
    for club in clubs:
        if club['name'] in existing:
            db_club = existing[club['name']]
            changed = False
            for field in ['founded_year', 'stadium_name', 'city', 'country', 'alternative_names']:
                if getattr(db_club, field) != club[field]:
                    setattr(db_club, field, club[field])
                    changed = True
            if changed:
                to_update.append(db_club)
        else:
            to_insert.append(Club(**club))
    if to_insert:
        db.bulk_save_objects(to_insert)
    db.commit()
    # For updates, commit is enough since we set attributes directly
    return len(to_insert), len(to_update)

def bulk_upsert_fixtures(db: Session, fixtures):
    from app.models.models import Fixture, MatchResult, Team
    # Map team names to IDs
    team_names = set()
    for f in fixtures:
        team_names.add(f['home_team'])
        team_names.add(f['away_team'])
    teams = db.query(Team).filter(Team.name.in_(team_names)).all()
    team_map = {t.name: t.id for t in teams}
    # Fetch existing fixtures by (date, home_team_id, away_team_id)
    keys = [(f['match_date'], team_map.get(f['home_team']), team_map.get(f['away_team'])) for f in fixtures]
    existing = {(fx.match_date, fx.home_team_id, fx.away_team_id): fx for fx in db.query(Fixture).filter(
        Fixture.match_date.in_([k[0] for k in keys]),
        Fixture.home_team_id.in_([k[1] for k in keys if k[1]]),
        Fixture.away_team_id.in_([k[2] for k in keys if k[2]])
    ).all()}
    to_insert = []
    updated = 0
    for fixture in fixtures:
        home_id = team_map.get(fixture['home_team'])
        away_id = team_map.get(fixture['away_team'])
        if not home_id or not away_id:
            continue
        key = (fixture['match_date'], home_id, away_id)
        if key in existing:
            db_fixture = existing[key]
            # Update result if changed
            if db_fixture.result:
                if (db_fixture.result.home_score != fixture['home_score'] or
                    db_fixture.result.away_score != fixture['away_score']):
                    db_fixture.result.home_score = fixture['home_score']
                    db_fixture.result.away_score = fixture['away_score']
                    updated += 1
            else:
                db_fixture.result = MatchResult(
                    home_score=fixture['home_score'],
                    away_score=fixture['away_score']
                )
                updated += 1
        else:
            db_fixture = Fixture(
                match_date=fixture['match_date'],
                home_team_id=home_id,
                away_team_id=away_id,
                stage=fixture.get('stage'),
                venue=fixture.get('venue'),
                is_completed=fixture['is_completed']
            )
            if fixture['is_completed']:
                db_fixture.result = MatchResult(
                    home_score=fixture['home_score'],
                    away_score=fixture['away_score']
                )
            to_insert.append(db_fixture)
    if to_insert:
        db.bulk_save_objects(to_insert)
    db.commit()
    return len(to_insert), updated

def parse_openfootball_json(file_path, team_mapper):
    # Parse a JSON file containing club data
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # openfootball club JSON is usually a list of dicts
    clubs = []
    for club in data:
        clubs.append({
            'name': club.get('name'),
            'founded_year': club.get('founded'),
            'stadium_name': club.get('stadium'),
            'city': club.get('city'),
            'country': club.get('country'),
            'alternative_names': ','.join(club.get('alt_names', [])) if isinstance(club.get('alt_names'), list) else club.get('alt_names')
        })
    return clubs

def validate_club(club):
    if not club['name'] or not isinstance(club['name'], str):
        logging.warning(f"Club missing or invalid name: {club}")
        return False
    if club['founded_year'] is not None and (not isinstance(club['founded_year'], int) or club['founded_year'] < 1800 or club['founded_year'] > datetime.now().year):
        logging.warning(f"Club has invalid founded_year: {club}")
        return False
    if club['country'] and not isinstance(club['country'], str):
        logging.warning(f"Club has invalid country: {club}")
        return False
    return True

def upsert_club(db: Session, club):
    db_club = db.query(Club).filter_by(name=club['name']).first()
    added, updated = 0, 0
    if db_club:
        # Update fields if changed
        changed = False
        for field in ['founded_year', 'stadium_name', 'city', 'country', 'alternative_names']:
            if getattr(db_club, field) != club[field]:
                setattr(db_club, field, club[field])
                changed = True
        if changed:
            updated = 1
    else:
        db_club = Club(**club)
        db.add(db_club)
        added = 1
    return added, updated

def log_audit(db: Session, repo, file_path, ingested_at, records_added, records_updated, sha1):
    from app.models.models import IngestionAudit
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

def git_pull_if_repo(repo_path):
    if os.path.isdir(os.path.join(repo_path, '.git')):
        try:
            result = subprocess.run(['git', '-C', repo_path, 'pull'], capture_output=True, text=True)
            if result.returncode == 0:
                logging.info(f"Pulled latest data for repo: {repo_path}")
            else:
                logging.warning(f"git pull failed for {repo_path}: {result.stderr}")
        except Exception as e:
            logging.error(f"Error running git pull in {repo_path}: {e}")
    else:
        logging.warning(f"{repo_path} is not a git repo. Skipping git pull.")

def parse_openfootball_squad_txt(file_path, club_name=None):
    # Parse a squad TXT file (OpenFootball format)
    players = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('='):
                continue
            # Example:  1,  Aaron Ramsdale,                    GK,   b. 1998,   Sheffield U
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 3:
                continue
            name = parts[1]
            position = parts[2]
            birth_year = None
            nationality = None
            for p in parts[3:]:
                if p.startswith('b. '):
                    try:
                        birth_year = int(p.replace('b. ', '').strip())
                    except Exception:
                        birth_year = None
                elif '(' in p and ')' in p:
                    # e.g. David Raya (ESP)
                    nat = p[p.find('(')+1:p.find(')')]
                    if len(nat) <= 4:
                        nationality = nat
            players.append({
                'name': name,
                'position': position,
                'birth_year': birth_year,
                'nationality': nationality,
                'club_name': club_name
            })
    return players

def bulk_upsert_players(db: Session, players, club_id=None, team_id=None):
    from app.models.models import Player
    names = [p['name'] for p in players]
    existing = {p.name: p for p in db.query(Player).filter(Player.name.in_(names)).all()}
    to_insert = []
    to_update = []
    for p in players:
        if p['name'] in existing:
            db_player = existing[p['name']]
            changed = False
            for field, val in [('position', p['position']), ('nationality', p['nationality']), ('club_id', club_id), ('team_id', team_id)]:
                if getattr(db_player, field) != val and val is not None:
                    setattr(db_player, field, val)
                    changed = True
            if p['birth_year'] and (not db_player.date_of_birth or db_player.date_of_birth.year != p['birth_year']):
                try:
                    db_player.date_of_birth = datetime(p['birth_year'], 1, 1)
                    changed = True
                except Exception:
                    pass
            if changed:
                to_update.append(db_player)
        else:
            dob = None
            if p['birth_year']:
                try:
                    dob = datetime(p['birth_year'], 1, 1)
                except Exception:
                    pass
            to_insert.append(Player(
                name=p['name'],
                position=p['position'],
                nationality=p['nationality'],
                date_of_birth=dob,
                club_id=club_id,
                team_id=team_id
            ))
    if to_insert:
        db.bulk_save_objects(to_insert)
    db.commit()
    return len(to_insert), len(to_update)

def parse_openfootball_club_txt(file_path, country=None):
    clubs = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith('=') or line.startswith('#'):
            i += 1
            continue
        # Main club line: Club Name, 1886, @ Stadium, City (Region)   ## Region
        parts = [p.strip() for p in line.split(',')]
        if len(parts) < 1:
            i += 1
            continue
        name = parts[0]
        founded_year = None
        stadium_name = None
        city = None
        alt_names = []
        # Try to extract founded year
        if len(parts) > 1 and parts[1].isdigit():
            founded_year = int(parts[1])
        # Try to extract stadium and city
        for p in parts[2:]:
            if p.startswith('@'):
                stadium_name = p[1:].strip()
            elif '(' in p and ')' in p:
                city = p.split('(')[0].strip()
            elif p:
                city = p.strip()
        # Look ahead for alternative names (lines starting with '|')
        j = i + 1
        while j < len(lines) and lines[j].strip().startswith('|'):
            alt_line = lines[j].strip()[1:].strip()
            # Remove comments after '#'
            alt_line = alt_line.split('#')[0].strip()
            if alt_line:
                alt_names.extend([a.strip() for a in alt_line.split('|') if a.strip()])
            j += 1
        clubs.append({
            'name': name,
            'founded_year': founded_year,
            'stadium_name': stadium_name,
            'city': city,
            'country': country,
            'alternative_names': ','.join(alt_names) if alt_names else None
        })
        i = j
    return clubs

def sync_repo(repo_path, repo_name, state, team_mapper, args):
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            sha1 = sha1_of_file(file_path)
            state_key = f"{repo_name}/{os.path.relpath(file_path, repo_path)}"
            if not args.force and state.get(state_key) == sha1:
                continue
            try:
                db = SessionLocal()
                if file.endswith('.json') and 'club' in file:
                    clubs = parse_openfootball_json(file_path, team_mapper)
                    valid_clubs = [c for c in clubs if validate_club(c)]
                    added, updated = bulk_upsert_clubs(db, valid_clubs)
                    log_audit(db, repo_name, state_key, datetime.utcnow().isoformat(), added, updated, sha1)
                elif file.endswith('.txt') and 'clubs' in file:
                    # Try to infer country from path
                    country = None
                    for part in os.path.normpath(file_path).split(os.sep):
                        if part.lower() in ['england','france','germany','italy','spain','brazil']:
                            country = part.title()
                    clubs = parse_openfootball_club_txt(file_path, country=country)
                    valid_clubs = [c for c in clubs if validate_club(c)]
                    added, updated = bulk_upsert_clubs(db, valid_clubs)
                    log_audit(db, repo_name, state_key, datetime.utcnow().isoformat(), added, updated, sha1)
                elif file.endswith('.csv'):
                    fixtures = parse_openfootball_csv(file_path, team_mapper)
                    valid_fixtures = [f for f in fixtures if validate_fixture(f)]
                    added, updated = bulk_upsert_fixtures(db, valid_fixtures)
                    log_audit(db, repo_name, state_key, datetime.utcnow().isoformat(), added, updated, sha1)
                elif file.endswith('.txt') and 'squads' in root:
                    # Infer club name from file name or parent dir
                    club_name = os.path.splitext(os.path.basename(file))[0].replace('_', ' ').title()
                    # Try to find club_id
                    club = db.query(Club).filter(Club.name.ilike(f"%{club_name}%")).first()
                    club_id = club.id if club else None
                    # Try to find team_id
                    team = db.query(Team).filter(Team.club_id == club_id).first() if club_id else None
                    team_id = team.id if team else None
                    players = parse_openfootball_squad_txt(file_path, club_name=club_name)
                    added, updated = bulk_upsert_players(db, players, club_id=club_id, team_id=team_id)
                    log_audit(db, repo_name, state_key, datetime.utcnow().isoformat(), added, updated, sha1)
                db.close()
                state[state_key] = sha1
            except SQLAlchemyError as e:
                logging.error(f"DB error in {file_path}: {e}")
                db.rollback()
                db.close()
            except Exception as e:
                logging.error(f"Error processing {file_path}: {e}")
    return state

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--league', type=str)
    args = parser.parse_args()

    state = load_state(STATE_FILE_PATH)
    with open(TEAM_MAPPER_PATH, 'r') as f:
        team_mapper = json.load(f)

    repos = [d for d in os.listdir(DATA_PATH) if os.path.isdir(os.path.join(DATA_PATH, d))]
    for repo in repos:
        repo_path = os.path.join(DATA_PATH, repo)
        git_pull_if_repo(repo_path)
        if args.league and repo != args.league:
            continue
        state = sync_repo(repo_path, repo, state, team_mapper, args)

    save_state(state, STATE_FILE_PATH)

if __name__ == "__main__":
    main() 
print('SYNC_FIXTURES_SCRIPT_START')
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
import re

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
    # Log if fixture is in the future
    try:
        match_date = datetime.strptime(fixture['match_date'], '%Y-%m-%d').date()
        today = datetime.today().date()
        if match_date > today:
            logging.info(f"Fixture is in the future: {fixture}")
    except Exception:
        pass
    return True

def bulk_upsert_clubs(db: Session, clubs):
    from app.models.models import Club
    # Fetch all existing clubs by name (including those already in DB)
    names = [club['name'] for club in clubs]
    existing = {c.name for c in db.query(Club.name).filter(Club.name.in_(names)).all()}
    to_insert = []
    to_update = []
    for club in clubs:
        if club['name'] in existing:
            db_club = db.query(Club).filter_by(name=club['name']).first()
            if db_club is None:
                logging.warning(f"Club {club['name']} listed as existing but not found in DB. Skipping update.")
                continue
            changed = False
            for field in ['founded_year', 'stadium_name', 'city', 'country', 'alternative_names']:
                if getattr(db_club, field) != club[field]:
                    setattr(db_club, field, club[field])
                    changed = True
            if changed:
                to_update.append(db_club)
        else:
            to_insert.append(Club(**club))
            existing.add(club['name'])  # Prevent duplicates in this batch
    if to_insert:
        db.bulk_save_objects(to_insert)
    db.commit()
    return len(to_insert), len(to_update)

def normalize_openfootball_date(date_str, season_year):
    # Convert 'Fri Aug/11' to '2023-08-11' using the season year
    import datetime
    if not date_str:
        return None
    try:
        # Remove weekday if present
        parts = date_str.split()
        if len(parts) == 2:
            _, md = parts
        else:
            md = parts[0]
        month, day = md.split('/')
        month_num = datetime.datetime.strptime(month, '%b').month
        year = int(season_year)
        # If month is July or later, it's the first year of the season; otherwise, it's the next year
        if month_num >= 7:
            normalized_year = year
        else:
            normalized_year = year + 1
        normalized_date = f"{normalized_year:04d}-{month_num:02d}-{int(day):02d}"
        logging.debug(f"normalize_openfootball_date: raw='{date_str}', season_year='{season_year}', normalized='{normalized_date}'")
        return normalized_date
    except Exception as e:
        logging.warning(f"normalize_openfootball_date failed: raw='{date_str}', season_year='{season_year}', error={e}")
        return None

def parse_openfootball_fixture_txt(file_path, team_mapper, season_year=None):
    # Parse OpenFootball .txt fixture file
    fixtures = []
    import re
    from datetime import datetime
    current_date = None
    logging.info(f"Parsing file: {file_path} | season_year: {season_year}")
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('=') or line.startswith('#') or line.startswith('Matchday'):
                continue
            # Date header
            date_match = re.match(r'\[(.+)\]', line)
            if date_match:
                current_date = date_match.group(1)
                continue
            # Match line: time  home_team  score (ht)  away_team
            match = re.match(r'(\d{1,2}\.\d{2})?\s*([\w &\'\-\.]+?)\s+(\d+)-(\d+)(?: \([^)]+\))?\s+([\w &\'\-\.]+)', line)
            if match:
                time, home_team, home_score, away_score, away_team = match.groups()
                home_team = team_mapper.get(home_team.strip(), home_team.strip())
                away_team = team_mapper.get(away_team.strip(), away_team.strip())
                match_date = normalize_openfootball_date(current_date, season_year) if current_date and season_year else None
                # Set is_completed based on whether the match_date is in the future
                is_completed = True
                if match_date:
                    try:
                        match_date_obj = datetime.strptime(match_date, '%Y-%m-%d').date()
                        today = datetime.today().date()
                        is_completed = match_date_obj <= today
                    except Exception:
                        pass
                fixtures.append({
                    'match_date': match_date,
                    'home_team': home_team,
                    'away_team': away_team,
                    'stage': None,
                    'venue': None,
                    'is_completed': is_completed,
                    'home_score': int(home_score),
                    'away_score': int(away_score)
                })
    logging.info(f"Parsed {len(fixtures)} fixtures from {file_path}. Sample dates: {[fx['match_date'] for fx in fixtures[:5]]}")
    return fixtures

def get_or_create_season(db, season_year, repo_name=None):
    from app.models.models import Season, Competition
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
        season = Season(year_start=year_start, year_end=year_end, season_name=f"{year_start}-{year_end}", competition_id=competition.id if competition else None)
        db.add(season)
        db.commit()
    return season.id

def bulk_upsert_fixtures(db: Session, fixtures, season_id=None):
    from app.models.models import Fixture, MatchResult, Team, Club
    logging.info(f"Parsing {len(fixtures)} fixtures...")
    # Map team names to IDs using Club.name
    team_names = set()
    for f in fixtures:
        team_names.add(f['home_team'])
        team_names.add(f['away_team'])
    clubs = db.query(Club).filter(Club.name.in_(team_names)).all()
    club_map = {c.name: c.id for c in clubs}
    teams = db.query(Team).filter(Team.club_id.in_(club_map.values())).all()
    # Map team by club name (1:1 for club teams)
    team_map = {}
    for t in teams:
        club = db.query(Club).filter(Club.id == t.club_id).first()
        if club:
            team_map[club.name] = t.id
    logging.info(f"Found {len(teams)} teams and {len(clubs)} clubs for {len(team_names)} unique team names.")
    # Fetch existing fixtures by (date, home_team_id, away_team_id)
    keys = [(f['match_date'], team_map.get(f['home_team']), team_map.get(f['away_team'])) for f in fixtures]
    existing = {(fx.match_date, fx.home_team_id, fx.away_team_id): fx for fx in db.query(Fixture).filter(
        Fixture.match_date.in_([k[0] for k in keys]),
        Fixture.home_team_id.in_([k[1] for k in keys if k[1]]),
        Fixture.away_team_id.in_([k[2] for k in keys if k[2]])
    ).all()}
    to_insert = []
    updated = 0
    skipped = 0
    placeholders = 0
    attempted = 0
    for fixture in fixtures:
        attempted += 1
        logging.debug(f"Processing fixture: {fixture}")
        home_id = team_map.get(fixture['home_team'])
        away_id = team_map.get(fixture['away_team'])
        # Create placeholder for missing home team
        if not home_id:
            club_id = club_map.get(fixture['home_team'])
            if not club_id:
                placeholder_club = db.query(Club).filter_by(name=fixture['home_team']).first()
                if not placeholder_club:
                    placeholder_club = Club(name=fixture['home_team'], country=None)
                    db.add(placeholder_club)
                    db.commit()
                    logging.warning(f"Created placeholder Club: {fixture['home_team']}")
                club_id = placeholder_club.id
                club_map[fixture['home_team']] = club_id
            placeholder_team = db.query(Team).filter_by(club_id=club_id, team_type='club').first()
            if not placeholder_team:
                placeholder_team = Team(club_id=club_id, team_type='club')
                db.add(placeholder_team)
                db.commit()
                logging.warning(f"Created placeholder Team: {fixture['home_team']}")
                placeholders += 1
            home_id = placeholder_team.id
            team_map[fixture['home_team']] = home_id
        # Create placeholder for missing away team
        if not away_id:
            club_id = club_map.get(fixture['away_team'])
            if not club_id:
                placeholder_club = db.query(Club).filter_by(name=fixture['away_team']).first()
                if not placeholder_club:
                    placeholder_club = Club(name=fixture['away_team'], country=None)
                    db.add(placeholder_club)
                    db.commit()
                    logging.warning(f"Created placeholder Club: {fixture['away_team']}")
                club_id = placeholder_club.id
                club_map[fixture['away_team']] = club_id
            placeholder_team = db.query(Team).filter_by(club_id=club_id, team_type='club').first()
            if not placeholder_team:
                placeholder_team = Team(club_id=club_id, team_type='club')
                db.add(placeholder_team)
                db.commit()
                logging.warning(f"Created placeholder Team: {fixture['away_team']}")
                placeholders += 1
            away_id = placeholder_team.id
            team_map[fixture['away_team']] = away_id
        key = (fixture['match_date'], home_id, away_id)
        if not home_id or not away_id:
            skipped += 1
            logging.warning(f"Skipping fixture {fixture['home_team']} vs {fixture['away_team']} on {fixture['match_date']} due to missing team IDs.")
            continue
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
                is_completed=fixture['is_completed'],
                season_id=season_id
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
    logging.info(f"Fixtures parsed: {len(fixtures)} | Attempted: {attempted} | Inserted: {len(to_insert)} | Updated: {updated} | Skipped: {skipped} | Placeholders created: {placeholders}")
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
    print(f"SYNC_REPO_START: {repo_name} | PATH: {repo_path}")
    logging.info(f"SYNC_REPO_START: {repo_name} | PATH: {repo_path}")
    if repo_name == "eng-england":
        print(f"*** DEBUG: ENTERED eng-england repo at {repo_path}")
        logging.info(f"*** DEBUG: ENTERED eng-england repo at {repo_path}")
    for root, dirs, files in os.walk(repo_path):
        if "2024-25" in root:
            print(f"*** DEBUG: INSIDE 2024-25 DIR: {root}")
            logging.info(f"*** DEBUG: INSIDE 2024-25 DIR: {root}")
        print(f"FILES_IN_DIR: REPO={repo_name} ROOT={root} FILES={files}")
        logging.info(f"FILES_IN_DIR: REPO={repo_name} ROOT={root} FILES={files}")
        for file in files:
            if repo_name == "eng-england" and "2024-25" in root:
                print(f"*** DEBUG: eng-england/2024-25 processing file: {file}")
                print(f"*** DEBUG: is_fixture_txt={is_fixture_txt}, in_squads_dir={in_squads_dir}, in_clubs_dir={in_clubs_dir}, is_club_file={is_club_file}")
                logging.info(f"*** DEBUG: is_fixture_txt={is_fixture_txt}, in_squads_dir={in_squads_dir}, in_clubs_dir={in_clubs_dir}, is_club_file={is_club_file}")
            print(f"ENTER_FILE_LOOP: REPO={repo_name} ROOT={root} FILE={file}")
            logging.info(f"ENTER_FILE_LOOP: REPO={repo_name} ROOT={root} FILE={file}")
            file_path = os.path.join(root, file)
            in_squads_dir = any('squads' in part.lower() for part in root.split(os.sep))
            in_clubs_dir = any('clubs' in part.lower() for part in root.split(os.sep))
            is_club_file = 'club' in file.lower()
            is_fixture_txt = file.endswith('.txt') and not in_squads_dir and not in_clubs_dir and not is_club_file
            if repo_name == "eng-england" and "2024-25" in root:
                print(f"*** DEBUG: eng-england/2024-25 processing file: {file}")
                print(f"*** DEBUG: is_fixture_txt={is_fixture_txt}, in_squads_dir={in_squads_dir}, in_clubs_dir={in_clubs_dir}, is_club_file={is_club_file}")
                logging.info(f"*** DEBUG: is_fixture_txt={is_fixture_txt}, in_squads_dir={in_squads_dir}, in_clubs_dir={in_clubs_dir}, is_club_file={is_club_file}")
            logging.info(f"[DEEPLOG] REPO={repo_name} ROOT={root} FILE={file} PATH={file_path} in_squads_dir={in_squads_dir} in_clubs_dir={in_clubs_dir} is_club_file={is_club_file} is_fixture_txt={is_fixture_txt}")
            if is_fixture_txt:
                logging.info(f"[DEEPLOG] Will process as FIXTURE: {file_path}")
            elif is_club_file:
                logging.info(f"[DEEPLOG] Will process as CLUB: {file_path}")
            elif in_squads_dir:
                logging.info(f"[DEEPLOG] Will process as SQUAD: {file_path}")
            else:
                logging.info(f"[DEEPLOG] Will SKIP: {file_path}")
            sha1 = sha1_of_file(file_path)
            state_key = f"{repo_name}/{os.path.relpath(file_path, repo_path)}"
            if not args.force and state.get(state_key) == sha1:
                logging.info(f"Skipping {file_path}: already up-to-date (sha1 match)")
                continue
            try:
                db = SessionLocal()
                if file.endswith('.json') and is_club_file:
                    logging.info(f"Parsing club JSON: {file_path}")
                    clubs = parse_openfootball_json(file_path, team_mapper)
                    valid_clubs = [c for c in clubs if validate_club(c)]
                    added, updated = bulk_upsert_clubs(db, valid_clubs)
                    log_audit(db, repo_name, state_key, datetime.utcnow().isoformat(), added, updated, sha1)
                elif file.endswith('.txt') and is_club_file:
                    logging.info(f"Parsing club TXT: {file_path}")
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
                    season_year = None
                    for part in os.path.normpath(file_path).split(os.sep):
                        if re.match(r'\d{4}-\d{2}', part):
                            season_year = part[:4]
                    logging.info(f"Parsing CSV: {file_path} | season_year: {season_year}")
                    season_id = get_or_create_season(db, season_year, repo_name)
                    fixtures = parse_openfootball_csv(file_path, team_mapper)
                    valid_fixtures = [f for f in fixtures if validate_fixture(f)]
                    added, updated = bulk_upsert_fixtures(db, valid_fixtures, season_id=season_id)
                    log_audit(db, repo_name, state_key, datetime.utcnow().isoformat(), added, updated, sha1)
                elif is_fixture_txt:
                    season_year = None
                    for part in os.path.normpath(file_path).split(os.sep):
                        if re.match(r'\d{4}-\d{2}', part):
                            season_year = part[:4]
                    logging.info(f"Parsing fixture TXT: {file_path} | season_year: {season_year}")
                    season_id = get_or_create_season(db, season_year, repo_name)
                    fixtures = parse_openfootball_fixture_txt(file_path, team_mapper, season_year=season_year)
                    valid_fixtures = [f for f in fixtures if validate_fixture(f)]
                    added, updated = bulk_upsert_fixtures(db, valid_fixtures, season_id=season_id)
                    log_audit(db, repo_name, state_key, datetime.utcnow().isoformat(), added, updated, sha1)
                elif file.endswith('.txt') and in_squads_dir:
                    logging.info(f"Parsing squad TXT: {file_path}")
                    club_name = os.path.splitext(os.path.basename(file))[0].replace('_', ' ').title()
                    club = db.query(Club).filter(Club.name.ilike(f"%{club_name}%")).first()
                    club_id = club.id if club else None
                    team = db.query(Team).filter(Team.club_id == club_id).first() if club_id else None
                    team_id = team.id if team else None
                    players = parse_openfootball_squad_txt(file_path, club_name=club_name)
                    added, updated = bulk_upsert_players(db, players, club_id=club_id, team_id=team_id)
                    log_audit(db, repo_name, state_key, datetime.utcnow().isoformat(), added, updated, sha1)
                else:
                    logging.info(f"Skipping file: {file_path} (does not match any known pattern)")
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
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--league', type=str)
    args = parser.parse_args()

    logging.info(f"ABSOLUTE DATA_PATH: {os.path.abspath(DATA_PATH)}")
    logging.info(f"DATA_PATH contents: {os.listdir(DATA_PATH)}")
    import sys
    sys.stdout.flush()
    sys.stderr.flush()
    state = load_state(STATE_FILE_PATH)
    with open(TEAM_MAPPER_PATH, 'r') as f:
        team_mapper = json.load(f)

    logging.info(f"DATA_PATH: {DATA_PATH}")
    all_dirs = os.listdir(DATA_PATH)
    print(f"ALL_DIRS_IN_DATA_PATH: {all_dirs}")
    logging.info(f"ALL_DIRS_IN_DATA_PATH: {all_dirs}")
    repos = [d for d in all_dirs if os.path.isdir(os.path.join(DATA_PATH, d))]
    print(f"REPOS_LIST: {repos}")
    logging.info(f"REPOS_LIST: {repos}")
    for repo in repos:
        print(f"REPO_LOOP_START: {repo}")
        logging.info(f"REPO_LOOP_START: {repo}")
        repo_path = os.path.join(DATA_PATH, repo)
        print(f"REPO_LOOP: {repo} | ABS_PATH: {os.path.abspath(repo_path)}")
        logging.info(f"REPO_LOOP: {repo} | ABS_PATH: {os.path.abspath(repo_path)}")
        print(f"BEFORE_GIT_PULL: {repo}")
        logging.info(f"BEFORE_GIT_PULL: {repo}")
        try:
            git_pull_if_repo(repo_path)
        except Exception as e:
            print(f"GIT_PULL_EXCEPTION: {repo} | {e}")
            logging.error(f"GIT_PULL_EXCEPTION: {repo} | {e}")
            continue
        print(f"AFTER_GIT_PULL: {repo}")
        logging.info(f"AFTER_GIT_PULL: {repo}")
        try:
            if args.league and repo != args.league:
                logging.info(f"Skipping repo {repo} due to --league argument")
                continue
            logging.info(f"Processing repo: {repo}")
            if repo == "eng-england":
                print(f"*** DEBUG: About to call sync_repo for eng-england")
                logging.info(f"*** DEBUG: About to call sync_repo for eng-england")
            state = sync_repo(repo_path, repo, state, team_mapper, args)
            if repo == "eng-england":
                print(f"*** DEBUG: Finished sync_repo for eng-england")
                logging.info(f"*** DEBUG: Finished sync_repo for eng-england")
        except Exception as e:
            print(f"EXCEPTION_IN_REPO: {repo} | {e}")
            logging.error(f"Error processing repo {repo}: {e}")
        print(f"REPO_LOOP_END: {repo}")
        logging.info(f"REPO_LOOP_END: {repo}")

    save_state(state, STATE_FILE_PATH)

if __name__ == "__main__":
    main() 
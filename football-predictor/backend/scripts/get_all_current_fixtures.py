#!/usr/bin/env python3

import os
import re
import datetime
from datetime import date, timedelta
from pathlib import Path
import glob

# Set the raw data directory
RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"

# Get today's date and tomorrow's date
today = date.today()
tomorrow = today + timedelta(days=1)

# Format dates for matching in the data files
today_month = today.strftime("%b").lower()
today_day = today.day
tomorrow_month = tomorrow.strftime("%b").lower()
tomorrow_day = tomorrow.day

print(f"Looking for matches on {today.strftime('%A, %B %d')} and {tomorrow.strftime('%A, %B %d')}...")
print(f"Searching for date formats: {today_month}/{today_day} and {tomorrow_month}/{tomorrow_day}")

# Competition mapping for better display
COMPETITION_NAMES = {
    'premierleague': 'Premier League',
    'bundesliga': 'Bundesliga',
    'seriea': 'Serie A',
    'liga': 'La Liga',
    'ligue1': 'Ligue 1',
    'championship': 'Championship',
    'cl': 'Champions League',
    'el': 'Europa League',
    'conf': 'Conference League',
    'cup': 'Domestic Cup',
    'liga1': 'Liga 1',
    'liga2': 'Liga 2',
    'liga3': 'Liga 3',
    'league1': 'League One',
    'league2': 'League Two',
    'nationalleague': 'National League',
    'bundesliga2': 'Bundesliga 2',
    'serieb': 'Serie B'
}

# Country mapping
COUNTRY_NAMES = {
    'eng-england': 'England',
    'de-deutschland': 'Germany',
    'it-italy': 'Italy',
    'es-espana': 'Spain',
    'fr-france': 'France',
    'champions-league': 'Europe',
    'europa-league': 'Europe'
}

def get_competition_name(file_path):
    """Extract competition name from file path"""
    file_name = os.path.basename(file_path).replace('.txt', '')
    
    # Handle formats like "1-premierleague.txt"
    if '-' in file_name:
        parts = file_name.split('-')
        if len(parts) > 1:
            file_name = parts[1]
    
    # Get proper name from mapping
    for key, value in COMPETITION_NAMES.items():
        if key.lower() in file_name.lower():
            return value
    
    return file_name.capitalize()

def get_country_name(file_path):
    """Extract country name from file path"""
    # Get the parent directory (country code)
    parent_dir = os.path.basename(os.path.dirname(os.path.dirname(file_path)))
    
    # Get proper name from mapping
    for key, value in COUNTRY_NAMES.items():
        if key.lower() == parent_dir.lower():
            return value
    
    return parent_dir.capitalize()

def get_season(file_path):
    """Extract season from file path"""
    # The season is the parent directory
    return os.path.basename(os.path.dirname(file_path))

def parse_fixtures(file_path):
    """Parse fixtures from a file for today and tomorrow's dates"""
    fixtures = []
    current_date = None
    current_matchday = None
    season = get_season(file_path)
    competition = get_competition_name(file_path)
    country = get_country_name(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            
        in_fixture_section = False
        day_of_week = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Check for matchday
            if line.startswith("»") or line.startswith("="):
                current_matchday = line.replace("»", "").replace("=", "").strip()
                in_fixture_section = False
                
            # Check for date line
            elif re.match(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\w+/\d+', line):
                date_parts = line.split()
                day_of_week = date_parts[0]
                date_str = date_parts[1]  # Format like May/10
                
                # Extract month and day
                try:
                    date_match = re.match(r'(\w+)/(\d+)', date_str)
                    if date_match:
                        month, day = date_match.groups()
                        month = month.lower()
                        day = int(day)
                        
                        # Check if this is today or tomorrow
                        if (month == today_month and day == today_day) or \
                           (month == tomorrow_month and day == tomorrow_day):
                            current_date = date_str
                            in_fixture_section = True
                        else:
                            in_fixture_section = False
                except Exception as e:
                    print(f"Error parsing date {date_str}: {e}")
                    in_fixture_section = False
                
            # Process fixture lines if we're in the right date section
            elif in_fixture_section:
                # Check for time format (e.g., "15.00")
                time_match = re.match(r'^\s*(\d+\.\d+)', line)
                if time_match:
                    # Try to match different fixture formats
                    
                    # Format: "15.00  Team A  v  Team B"
                    match1 = re.match(r'^\s*(\d+\.\d+)\s+(.*?)\s+v\s+(.*?)$', line)
                    if match1:
                        time, home_team, away_team = match1.groups()
                        home_team = home_team.strip()
                        away_team = away_team.strip()
                    else:
                        # Format: "15.00  Team A  -  Team B"
                        match2 = re.match(r'^\s*(\d+\.\d+)\s+(.*?)\s+-\s+(.*?)$', line)
                        if match2:
                            time, home_team, away_team = match2.groups()
                            home_team = home_team.strip()
                            away_team = away_team.strip()
                        else:
                            # Check for score formats (for completed matches)
                            match3 = re.match(r'^\s*(\d+\.\d+)\s+(.*?)\s+\d+-\d+.*?\s+(.*?)$', line)
                            if match3:
                                continue  # Skip completed matches
                            else:
                                continue  # Unrecognized format
                    
                    # Only add matches for today or tomorrow
                    if current_date:
                        # Extract month and day
                        date_match = re.match(r'(\w+)/(\d+)', current_date)
                        if date_match:
                            month, day = date_match.groups()
                            month = month.lower()
                            day = int(day)
                            
                            # Determine if it's today or tomorrow
                            is_today = (month == today_month and day == today_day)
                            
                            fixtures.append({
                                'matchday': current_matchday,
                                'date': current_date,
                                'is_today': is_today,
                                'day_of_week': day_of_week,
                                'time': time,
                                'home_team': home_team,
                                'away_team': away_team,
                                'competition': competition,
                                'country': country,
                                'season': season
                            })
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
    
    return fixtures

def find_fixture_files(current_season=True):
    """Find all fixture files in the raw data directory"""
    fixture_files = []
    
    # Process current seasons first
    current_seasons = ['2023-24', '2024-25']
    
    # Get all directories in the raw data directory
    for league_dir in os.listdir(RAW_DATA_DIR):
        league_path = os.path.join(RAW_DATA_DIR, league_dir)
        if os.path.isdir(league_path):
            # First check current seasons
            if current_season:
                for season in current_seasons:
                    season_path = os.path.join(league_path, season)
                    if os.path.isdir(season_path):
                        # Find all txt files
                        for file_name in os.listdir(season_path):
                            if file_name.endswith('.txt') and not file_name.startswith('.'):
                                fixture_files.append(os.path.join(season_path, file_name))
            else:
                # Check all other seasons
                for season_dir in os.listdir(league_path):
                    if season_dir not in current_seasons and os.path.isdir(os.path.join(league_path, season_dir)):
                        season_path = os.path.join(league_path, season_dir)
                        # Find all txt files
                        for file_name in os.listdir(season_path):
                            if file_name.endswith('.txt') and not file_name.startswith('.'):
                                fixture_files.append(os.path.join(season_path, file_name))
    
    return fixture_files

def main():
    """Main function to find fixtures for today and tomorrow"""
    # First check current seasons
    today_fixtures = []
    tomorrow_fixtures = []
    
    print("Searching in current season files...")
    current_season_files = find_fixture_files(current_season=True)
    for file_path in current_season_files:
        fixtures = parse_fixtures(file_path)
        
        for fixture in fixtures:
            if fixture['is_today']:
                today_fixtures.append(fixture)
            else:
                tomorrow_fixtures.append(fixture)
    
    # If we didn't find any fixtures, check older seasons
    if not today_fixtures and not tomorrow_fixtures:
        print("No fixtures found in current seasons, checking older seasons...")
        older_season_files = find_fixture_files(current_season=False)
        for file_path in older_season_files:
            fixtures = parse_fixtures(file_path)
            
            for fixture in fixtures:
                if fixture['is_today']:
                    today_fixtures.append(fixture)
                else:
                    tomorrow_fixtures.append(fixture)
    
    # Group fixtures by competition
    today_by_competition = {}
    for fixture in today_fixtures:
        key = (fixture['country'], fixture['competition'])
        if key not in today_by_competition:
            today_by_competition[key] = []
        today_by_competition[key].append(fixture)
    
    tomorrow_by_competition = {}
    for fixture in tomorrow_fixtures:
        key = (fixture['country'], fixture['competition'])
        if key not in tomorrow_by_competition:
            tomorrow_by_competition[key] = []
        tomorrow_by_competition[key].append(fixture)
    
    # Display today's fixtures
    print(f"\nMatches for TODAY ({today.strftime('%A, %B %d')}):")
    if today_by_competition:
        for (country, competition), fixtures in sorted(today_by_competition.items()):
            print(f"\n{country} - {competition}:")
            for fixture in sorted(fixtures, key=lambda x: x['time']):
                print(f"  {fixture['time']} - {fixture['home_team']} vs {fixture['away_team']}")
    else:
        print("No matches found for today.")
    
    # Display tomorrow's fixtures
    print(f"\nMatches for TOMORROW ({tomorrow.strftime('%A, %B %d')}):")
    if tomorrow_by_competition:
        for (country, competition), fixtures in sorted(tomorrow_by_competition.items()):
            print(f"\n{country} - {competition}:")
            for fixture in sorted(fixtures, key=lambda x: x['time']):
                print(f"  {fixture['time']} - {fixture['home_team']} vs {fixture['away_team']}")
    else:
        print("No matches found for tomorrow.")
    
    print(f"\nTotal fixtures found: {len(today_fixtures)} for today, {len(tomorrow_fixtures)} for tomorrow")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3

import os
import re
import datetime
from datetime import date, timedelta
from pathlib import Path

# Set the raw data directory
RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"

# Get today's date and tomorrow's date
today = date.today()
tomorrow = today + timedelta(days=1)

print(f"Script running on {today.strftime('%Y-%m-%d')}")

# Different possible date formats in the files
# Format 1: [Fri May/09] or [Fri May/9]
# Format 2: [09/05/14] (DD/MM/YY)
# Format 3: [2014-05-09]

# Create a list of possible date formats to search for
date_patterns = [
    # Primary format with slashes - try both with and without leading zeros
    today.strftime("%b/%d").lower(),  # may/09
    today.strftime("%b/%-d").lower(),  # may/9
    tomorrow.strftime("%b/%d").lower(),  # may/10
    tomorrow.strftime("%b/%-d").lower(),  # may/10
    
    # UK date format
    today.strftime("%d/%m/%y"),  # 09/05/24
    tomorrow.strftime("%d/%m/%y"),  # 10/05/24
    
    # ISO format
    today.strftime("%Y-%m-%d"),  # 2024-05-09
    tomorrow.strftime("%Y-%m-%d"),  # 2024-05-10
]

print(f"Searching for date patterns: {date_patterns}")

# Dictionary to store today's and tomorrow's matches
todays_matches = []
tomorrows_matches = []

# League names for display
league_names = {
    "eng-england": "English",
    "es-espana": "Spanish",
    "de-deutschland": "German",
    "it-italy": "Italian", 
    "fr-france": "French",
    "champions-league": "Champions League",
    "europa-league": "Europa League",
}

def parse_date_line(line):
    """Parse a date line and return the date in a standard format."""
    # Try each date format
    if '[' in line and ']' in line:
        date_text = line[line.find('[') + 1:line.find(']')].strip().lower()
        
        # Format 1: [Fri May/09]
        if '/' in date_text and any(month in date_text for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
            # Extract just the date part, ignoring day of week
            parts = date_text.split()
            if len(parts) > 1:
                return parts[-1]  # Return just "may/09" part
            
        # Return the full date string for other formats
        return date_text
    
    return None

def extract_match_info(match_lines, date_str, league, season, file_name):
    """Extract match information from the lines after a date header."""
    matches = []
    
    # Check if there are at least some valid match lines
    if not match_lines:
        return matches
    
    # Extract competition name from filename
    competition = os.path.basename(file_name).replace('.txt', '')
    if "-" in competition:
        # For league files like "1-premierleague.txt"
        parts = competition.split("-")
        if len(parts) > 1:
            competition = parts[1]
    
    for line in match_lines:
        line = line.strip()
        if not line or line.startswith('[') or line.startswith('#') or line.startswith('='):
            continue
            
        # Common format: time home_team score away_team
        # Example: "  20.00  Burnley FC               0-3 (0-2)  Manchester City FC"
        # or: "  15.00  AFC Bournemouth          1-1 (0-0)  West Ham United FC"
        match = re.match(r'\s*(\d+\.\d+)\s+(.*?)\s+(?:\d+-\d+|\?)(?:\s+\(\d+-\d+\))?\s+(.*?)$', line)
        if match:
            time, home_team, away_team = match.groups()
            home_team = home_team.strip()
            away_team = away_team.strip()
            
            matches.append({
                'time': time,
                'home_team': home_team,
                'away_team': away_team,
                'league': league,
                'competition': competition,
                'season': season,
                'date_str': date_str
            })
            continue
            
        # Format without score yet (for upcoming matches)
        match = re.match(r'\s*(\d+\.\d+)\s+(.*?)\s+[-–]\s+(.*?)$', line)
        if match:
            time, home_team, away_team = match.groups()
            home_team = home_team.strip()
            away_team = away_team.strip()
            
            matches.append({
                'time': time,
                'home_team': home_team,
                'away_team': away_team,
                'league': league,
                'competition': competition,
                'season': season,
                'date_str': date_str
            })
            
    return matches

def find_matches_in_file(file_path, league, season):
    """Find matches for today and tomorrow in a given file."""
    print(f"Checking file: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    matches_for_date = []
    current_date = None
    file_name = os.path.basename(file_path)
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Check if this is a date line
        if line.startswith('['):
            date_str = parse_date_line(line)
            if date_str:
                current_date = date_str
                print(f"  Found date: {current_date} in {file_path}")
                
                # If this date matches today or tomorrow, extract matches
                if any(pattern in current_date for pattern in date_patterns):
                    print(f"  > Matched date pattern: {current_date}")
                    
                    # Find all lines until the next date or end of section
                    match_lines = []
                    j = i + 1
                    while j < len(lines) and not lines[j].strip().startswith('['):
                        match_lines.append(lines[j])
                        j += 1
                        
                    matches = extract_match_info(match_lines, current_date, league, season, file_path)
                    
                    # Add to appropriate list based on which pattern matched
                    is_today = any(pattern in current_date for pattern in date_patterns[:4])
                    if is_today:
                        todays_matches.extend(matches)
                    else:
                        tomorrows_matches.extend(matches)
    
    return matches_for_date

def scan_league_folder(league_path, league_name):
    """Scan a league folder for all season files."""
    # First check this season's files as they're most likely to have matches
    print(f"Scanning league: {league_name}")
    
    # Look for current season directories (2023-24, 2024-25, etc.)
    current_seasons = ['2023-24', '2024-25']
    all_season_dirs = sorted([d for d in os.listdir(league_path) if os.path.isdir(os.path.join(league_path, d))], reverse=True)
    
    # First check current seasons
    for season_dir in [d for d in all_season_dirs if d in current_seasons]:
        season_path = os.path.join(league_path, season_dir)
        print(f"Checking current season: {season_dir}")
        
        # Look for .txt files in the season directory
        for file_name in os.listdir(season_path):
            if file_name.endswith('.txt'):
                file_path = os.path.join(season_path, file_name)
                find_matches_in_file(file_path, league_name, season_dir)
    
    # Then check other seasons if needed
    if not todays_matches and not tomorrows_matches:
        for season_dir in [d for d in all_season_dirs if d not in current_seasons]:
            season_path = os.path.join(league_path, season_dir)
            
            # Look for .txt files in the season directory
            for file_name in os.listdir(season_path):
                if file_name.endswith('.txt'):
                    file_path = os.path.join(season_path, file_name)
                    find_matches_in_file(file_path, league_name, season_dir)

def main():
    """Main function to find today's and tomorrow's matches."""
    print(f"Looking for matches on {today.strftime('%A, %B %d')} and {tomorrow.strftime('%A, %B %d')}...")
    
    # Prioritize major leagues first
    priority_leagues = ["eng-england", "es-espana", "de-deutschland", "it-italy", "champions-league"]
    
    # First scan priority leagues
    for league_dir in priority_leagues:
        league_path = os.path.join(RAW_DATA_DIR, league_dir)
        if os.path.isdir(league_path):
            league_name = league_names.get(league_dir, league_dir)
            scan_league_folder(league_path, league_name)
    
    # Then scan remaining leagues if needed
    if not todays_matches and not tomorrows_matches:
        for league_dir in os.listdir(RAW_DATA_DIR):
            if league_dir not in priority_leagues:
                league_path = os.path.join(RAW_DATA_DIR, league_dir)
                if os.path.isdir(league_path):
                    league_name = league_names.get(league_dir, league_dir)
                    scan_league_folder(league_path, league_name)
    
    # Print today's matches
    print(f"\nMatches for TODAY ({today.strftime('%A, %B %d')}):")
    if todays_matches:
        # Sort by time
        for match in sorted(todays_matches, key=lambda x: x['time']):
            competition = match['competition']
            print(f"{match['time']} - {match['home_team']} vs {match['away_team']} - {match['league']} {competition} ({match['season']}) [{match['date_str']}]")
    else:
        print("No matches found for today in the raw data.")
    
    # Print tomorrow's matches
    print(f"\nMatches for TOMORROW ({tomorrow.strftime('%A, %B %d')}):")
    if tomorrows_matches:
        # Sort by time
        for match in sorted(tomorrows_matches, key=lambda x: x['time']):
            competition = match['competition']
            print(f"{match['time']} - {match['home_team']} vs {match['away_team']} - {match['league']} {competition} ({match['season']}) [{match['date_str']}]")
    else:
        print("No matches found for tomorrow in the raw data.")
    
    print(f"\nTotal matches found: {len(todays_matches)} for today, {len(tomorrows_matches)} for tomorrow")

if __name__ == "__main__":
    main() 
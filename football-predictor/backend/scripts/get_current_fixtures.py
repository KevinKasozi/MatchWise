#!/usr/bin/env python3

import os
import re
import datetime
from datetime import date
from pathlib import Path

# Set the current date
today = date.today()
today_str = today.strftime("%Y-%m-%d")
print(f"Current date: {today_str}")

# This script specifically targets current fixtures in the Premier League for this weekend
target_file = Path(__file__).parent.parent / "data" / "raw" / "eng-england" / "2024-25" / "1-premierleague.txt"

def parse_fixtures(file_path):
    """Parse fixtures from the Premier League file"""
    fixtures = []
    current_date = None
    current_matchday = None
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
        
    in_fixture_section = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Check for matchday
        if line.startswith("»"):
            current_matchday = line.replace("»", "").strip()
            in_fixture_section = False
            
        # Check for date line
        elif re.match(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\w+/\d+', line):
            date_parts = line.split()
            day_of_week = date_parts[0]
            date_str = date_parts[1]  # Format like May/10
            current_date = date_str
            in_fixture_section = True
            
        # Process fixture lines
        elif in_fixture_section and re.match(r'^\s+\d+\.\d+', line):  # Match time like 15.00
            match = re.match(r'^\s+(\d+\.\d+)\s+(.*?)\s+v\s+(.*?)$', line)
            if match:
                time, home_team, away_team = match.groups()
                home_team = home_team.strip()
                away_team = away_team.strip()
                
                fixtures.append({
                    'matchday': current_matchday,
                    'date': current_date,
                    'day_of_week': day_of_week if 'day_of_week' in locals() else "Unknown",
                    'time': time,
                    'home_team': home_team,
                    'away_team': away_team
                })
    
    return fixtures

def main():
    """Main function to display current fixtures"""
    # Check if file exists
    if not target_file.exists():
        print(f"Error: Premier League fixture file not found at {target_file}")
        return
        
    print(f"Reading fixtures from: {target_file}")
    fixtures = parse_fixtures(target_file)
    
    # Filter for this weekend (May 10-11)
    may_10_fixtures = [f for f in fixtures if f['date'] == 'May/10']
    may_11_fixtures = [f for f in fixtures if f['date'] == 'May/11']
    
    # Display fixtures for May 10 (Saturday)
    if may_10_fixtures:
        print("\nPremier League Fixtures - Saturday, May 10:")
        for fixture in sorted(may_10_fixtures, key=lambda x: x['time']):
            print(f"{fixture['time']} - {fixture['home_team']} vs {fixture['away_team']}")
    else:
        print("\nNo Premier League fixtures found for Saturday, May 10")
        
    # Display fixtures for May 11 (Sunday)
    if may_11_fixtures:
        print("\nPremier League Fixtures - Sunday, May 11:")
        for fixture in sorted(may_11_fixtures, key=lambda x: x['time']):
            print(f"{fixture['time']} - {fixture['home_team']} vs {fixture['away_team']}")
    else:
        print("\nNo Premier League fixtures found for Sunday, May 11")
        
    print(f"\nTotal fixtures: {len(may_10_fixtures)} for Saturday, {len(may_11_fixtures)} for Sunday")

if __name__ == "__main__":
    main() 
import requests
import datetime
from pprint import pprint

# Base URL (updated port to 8001)
BASE_URL = "http://localhost:8001/api/v1"

def get_upcoming_fixtures():
    """Fetch upcoming fixtures from the API"""
    url = f"{BASE_URL}/fixtures"
    params = {
        "status": "upcoming",
        "limit": 50
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        fixtures = response.json()
        return fixtures
    except requests.exceptions.RequestException as e:
        print(f"Error fetching fixtures: {e}")
        return []

def main():
    print("Retrieving upcoming fixtures...")
    fixtures = get_upcoming_fixtures()
    
    # Group fixtures by date
    fixtures_by_date = {}
    for fixture in fixtures:
        match_date = fixture.get("match_date")
        if match_date not in fixtures_by_date:
            fixtures_by_date[match_date] = []
        fixtures_by_date[match_date].append(fixture)
    
    # Print fixtures by date
    for date in sorted(fixtures_by_date.keys()):
        print(f"\n=== Fixtures on {date} ===")
        for fixture in fixtures_by_date[date]:
            home_team = fixture.get("home_team_name", "Unknown Home Team")
            away_team = fixture.get("away_team_name", "Unknown Away Team")
            match_time = fixture.get("match_time", "TBD")
            stage = fixture.get("stage", "Regular Season")
            
            print(f"{match_time} - {home_team} vs {away_team} ({stage})")
    
    if not fixtures:
        print("No upcoming fixtures found.")

if __name__ == "__main__":
    main() 
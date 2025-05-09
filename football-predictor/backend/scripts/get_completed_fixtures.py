import requests
import datetime
from pprint import pprint

# Base URL (updated port to 8001)
BASE_URL = "http://localhost:8001/api/v1"

def get_completed_fixtures():
    """Fetch completed fixtures from the API"""
    url = f"{BASE_URL}/fixtures"
    params = {
        "status": "completed",
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
    print("Retrieving completed fixtures...")
    fixtures = get_completed_fixtures()
    
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
        day_fixtures = fixtures_by_date[date]
        # Sort fixtures by competition/season if available
        for fixture in day_fixtures:
            home_team = fixture.get("home_team_name", "Unknown Home Team")
            away_team = fixture.get("away_team_name", "Unknown Away Team")
            stage = fixture.get("stage", "Regular Season")
            
            result = ""
            if "result" in fixture and fixture["result"]:
                home_score = fixture["result"].get("home_score", "?")
                away_score = fixture["result"].get("away_score", "?")
                result = f" - Final Score: {home_score}-{away_score}"
                
            print(f"{home_team} vs {away_team} ({stage}){result}")
    
    if not fixtures:
        print("No completed fixtures found.")
        
    print(f"\nTotal fixtures found: {len(fixtures)}")

if __name__ == "__main__":
    main() 
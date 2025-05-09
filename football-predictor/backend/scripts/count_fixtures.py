#!/usr/bin/env python3

import os
import sys
from datetime import date, timedelta

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.models.models import Fixture, Season, Competition

def main():
    db = next(get_db())
    
    # Get tomorrow's date
    tomorrow = date.today() + timedelta(days=1)
    
    # Get all competitions
    comps = db.query(Competition).all()
    
    print(f"FIXTURES BY LEAGUE FOR TOMORROW ({tomorrow}):")
    print("="*50)
    
    total = 0
    
    # Group competitions by country
    competitions_by_country = {}
    for comp in comps:
        if comp.country not in competitions_by_country:
            competitions_by_country[comp.country] = []
        competitions_by_country[comp.country].append(comp)
    
    # Print fixtures by country and competition
    for country, comps_list in sorted(competitions_by_country.items()):
        country_total = 0
        country_fixtures = []
        
        for comp in comps_list:
            fixtures = db.query(Fixture).join(Season).filter(
                Season.competition_id == comp.id,
                Fixture.match_date == tomorrow
            ).count()
            
            if fixtures > 0:
                country_fixtures.append((comp.name, fixtures))
                country_total += fixtures
        
        if country_total > 0:
            print(f"\n{country}:")
            for comp_name, count in country_fixtures:
                print(f"  - {comp_name}: {count} fixtures")
            print(f"  Total: {country_total} fixtures")
            total += country_total
    
    print("\n" + "="*50)
    print(f"Total fixtures for tomorrow ({tomorrow}): {total}")

if __name__ == "__main__":
    main() 
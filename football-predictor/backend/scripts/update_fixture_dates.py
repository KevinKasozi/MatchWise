#!/usr/bin/env python3

import os
import sys
from datetime import date, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.models import Fixture
from app.core.config import settings

# Get database connection string from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/football_predictor")
print(f"Using database connection: {DATABASE_URL}")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def update_fixture_dates():
    """Update all fixture dates to be in the current year"""
    db = SessionLocal()
    
    try:
        # Get all fixtures
        fixtures = db.query(Fixture).all()
        
        current_year = date.today().year
        today = date.today()
        future_cutoff = today + timedelta(days=180)  # Only show fixtures up to 6 months in the future
        
        updated_count = 0
        future_fixtures = 0
        
        for fixture in fixtures:
            # Get current fixture date
            fixture_date = fixture.match_date
            
            # If the fixture date is not in the current year
            if fixture_date.year != current_year:
                try:
                    # Create new date with same month/day but current year
                    new_date = date(current_year, fixture_date.month, fixture_date.day)
                    
                    # If the new date is in the past, use next year
                    if new_date < today:
                        new_date = date(current_year + 1, fixture_date.month, fixture_date.day)
                    
                    # Don't show fixtures too far in the future
                    if new_date > future_cutoff:
                        fixture.is_completed = True  # Mark as completed to hide from upcoming fixtures
                        future_fixtures += 1
                    else:
                        fixture.match_date = new_date
                        fixture.is_completed = False  # Make sure it's shown as upcoming
                        updated_count += 1
                        
                except ValueError:
                    # Skip invalid dates (e.g., Feb 29 in non-leap years)
                    pass
        
        db.commit()
        print(f"Updated {updated_count} fixtures to current year dates")
        print(f"Marked {future_fixtures} fixtures as completed (too far in the future)")
        
    except Exception as e:
        db.rollback()
        print(f"Error updating fixture dates: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    update_fixture_dates() 
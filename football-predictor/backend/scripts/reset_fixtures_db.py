#!/usr/bin/env python3

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.models import Base, Fixture, Team, Club, Competition, Season
from scripts.setup_db_and_fixtures import create_tables, load_fixtures_to_db
from scripts.update_fixtures_in_db import find_fixture_files, parse_fixtures

# Get database connection string from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/football_predictor")
print(f"Using database connection: {DATABASE_URL}")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def reset_fixtures():
    """Delete all fixtures and related entities from the database"""
    db = SessionLocal()
    
    try:
        print("Deleting all fixtures...")
        delete_fixtures_sql = text("DELETE FROM fixtures")
        db.execute(delete_fixtures_sql)
        db.commit()
        print("All fixtures deleted")
    except Exception as e:
        db.rollback()
        print(f"Error deleting fixtures: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def main():
    """Main function to reset the database and load fixtures with correct years"""
    # Step 1: Delete all fixtures
    reset_fixtures()
    
    # Step 2: Get fixtures
    all_fixtures = []
    
    # Process current seasons first
    print("Searching for fixture files...")
    current_season_files = find_fixture_files(current_season=True)
    
    print(f"Found {len(current_season_files)} fixture files, parsing...")
    for file_path in current_season_files:
        fixtures = parse_fixtures(file_path)
        all_fixtures.extend(fixtures)
    
    # Step 3: Load fixtures into the database
    if all_fixtures:
        print(f"Found {len(all_fixtures)} fixtures, loading to database...")
        fixture_count = load_fixtures_to_db(all_fixtures)
        print(f"Successfully added {fixture_count} fixtures to the database")
    else:
        print("No fixtures found to add to the database")

if __name__ == "__main__":
    main() 
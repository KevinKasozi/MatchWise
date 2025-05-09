#!/usr/bin/env python3
"""
Cleanup Fake Fixtures Script

This script removes all fake upcoming fixtures from the database to ensure
we're only displaying real fixtures from the dataset.
"""

import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
import argparse

# Add the parent directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.models import Fixture

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def cleanup_fake_fixtures(db: Session):
    """
    Remove all fixtures marked as not completed (upcoming) since these are likely fake.
    """
    try:
        # Get all upcoming fixtures (these are the fake ones we generated)
        fake_fixtures = db.query(Fixture).filter(Fixture.is_completed == False).all()
        
        logger.info(f"Found {len(fake_fixtures)} fake upcoming fixtures to remove")
        
        # Delete them all
        for fixture in fake_fixtures:
            db.delete(fixture)
        
        db.commit()
        logger.info(f"Successfully removed all fake fixtures")
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing fake fixtures: {e}")

def main():
    parser = argparse.ArgumentParser(description='Remove fake fixtures from the database')
    parser.add_argument('--confirm', action='store_true', help='Confirm deletion without prompting')
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        if not args.confirm:
            count = db.query(Fixture).filter(Fixture.is_completed == False).count()
            confirm = input(f"This will delete {count} upcoming fixtures. Are you sure? (y/n): ")
            if confirm.lower() != 'y':
                logger.info("Operation cancelled by user")
                return
        
        cleanup_fake_fixtures(db)
    finally:
        db.close()

if __name__ == "__main__":
    main() 
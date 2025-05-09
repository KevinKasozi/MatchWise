#!/usr/bin/env python3

import sys
from app.core.database import SessionLocal
from app.models.models import Fixture, Season, Competition, MatchResult

def cleanup_spanish_leagues(target_seasons=["2024-2025"]):
    db = SessionLocal()
    try:
        for comp_name in ["La Liga", "La Liga 2"]:
            comp = db.query(Competition).filter(
                Competition.name == comp_name,
                Competition.country == "Spain"
            ).first()
            if not comp:
                print(f"Competition not found: {comp_name}")
                continue

            for season_name in target_seasons:
                season = db.query(Season).filter(
                    Season.competition_id == comp.id,
                    Season.season_name == season_name
                ).first()
                if not season:
                    print(f"Season not found: {season_name} for {comp_name}")
                    continue

                # Delete all match results for fixtures in this season
                fixture_ids = [f.id for f in db.query(Fixture).filter(Fixture.season_id == season.id).all()]
                if fixture_ids:
                    db.query(MatchResult).filter(MatchResult.fixture_id.in_(fixture_ids)).delete(synchronize_session=False)
                    print(f"Deleted MatchResults for {comp_name} {season_name}")

                # Delete all fixtures for this season
                db.query(Fixture).filter(Fixture.season_id == season.id).delete(synchronize_session=False)
                print(f"Deleted Fixtures for {comp_name} {season_name}")

                # Delete the season itself
                db.delete(season)
                print(f"Deleted Season: {season_name} for {comp_name}")

        db.commit()
        print("Cleanup complete.")
    except Exception as e:
        db.rollback()
        print(f"Error during cleanup: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # You can add more seasons to this list if needed
    cleanup_spanish_leagues(target_seasons=["2024-2025"]) 
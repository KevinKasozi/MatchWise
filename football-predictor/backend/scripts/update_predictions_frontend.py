#!/usr/bin/env python3

import os
import sys
import logging
import json
from datetime import date, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.models import Fixture, Team, Club, Competition, Season, Prediction, MatchResult

def get_team_features(db: Session, team_id: int, match_date: date):
    """Get key features for a team to display on the frontend"""
    
    # Get past matches where the team was either home or away
    past_matches = (
        db.query(Fixture, MatchResult)
        .join(MatchResult)
        .filter(
            (Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id),
            Fixture.match_date < match_date,
            Fixture.is_completed == True
        )
        .order_by(Fixture.match_date.desc())
        .limit(5)
        .all()
    )
    
    # Calculate basic features
    win_streak = 0
    form = []
    for fixture, result in past_matches:
        is_home = fixture.home_team_id == team_id
        
        # Determine result from this team's perspective
        if is_home:
            if result.home_score > result.away_score:
                form.append('W')
                win_streak += 1 if win_streak >= 0 else -win_streak + 1
            elif result.home_score < result.away_score:
                form.append('L')
                win_streak = win_streak <= 0 and win_streak - 1 or -1
            else:
                form.append('D')
                win_streak = 0
        else:
            if result.away_score > result.home_score:
                form.append('W')
                win_streak += 1 if win_streak >= 0 else -win_streak + 1
            elif result.away_score < result.home_score:
                form.append('L')
                win_streak = win_streak <= 0 and win_streak - 1 or -1
            else:
                form.append('D')
                win_streak = 0
    
    # Return features in a user-friendly format
    features = []
    
    # Add win streak if it exists
    if win_streak != 0:
        streak_type = "Win" if win_streak > 0 else "Loss"
        features.append({
            "label": f"{streak_type} Streak",
            "value": abs(win_streak)
        })
    
    # Add form
    if form:
        features.append({
            "label": "Recent Form",
            "value": " ".join(form[:3])  # Last 3 matches
        })
    
    return features

def find_upcoming_predictions(days=7):
    """Find upcoming matches with predictions to show on the frontend"""
    logger.info(f"Finding predictions for matches in the next {days} days")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get date range
        today = date.today()
        end_date = today + timedelta(days=days)
        
        # Find fixtures with predictions
        fixtures_with_predictions = (
            db.query(Fixture, Prediction)
            .join(Prediction, Fixture.id == Prediction.fixture_id)
            .filter(
                Fixture.match_date >= today,
                Fixture.match_date <= end_date,
                Fixture.is_completed == False
            )
            .options(
                joinedload(Fixture.home_team).joinedload(Team.club),
                joinedload(Fixture.away_team).joinedload(Team.club),
                joinedload(Fixture.season).joinedload(Season.competition)
            )
            .order_by(Fixture.match_date, Fixture.match_time)
            .all()
        )
        
        logger.info(f"Found {len(fixtures_with_predictions)} upcoming fixtures with predictions")
        
        # Format data for frontend
        formatted_predictions = []
        
        for fixture, prediction in fixtures_with_predictions:
            home_team = fixture.home_team.club
            away_team = fixture.away_team.club
            
            # Get winner based on highest probability
            winner = None
            max_prob = max(prediction.home_win_probability, prediction.draw_probability, prediction.away_win_probability)
            if max_prob == prediction.home_win_probability:
                winner = home_team.name
            elif max_prob == prediction.away_win_probability:
                winner = away_team.name
            else:
                winner = "Draw"
            
            # Format prediction data
            pred_data = {
                "id": fixture.id,
                "home": {
                    "name": home_team.name,
                    "crest": home_team.logo_url or f"https://ui-avatars.com/api/?name={home_team.name}&background=random&color=fff&size=128",
                    "color": home_team.primary_color or "#1a365d"
                },
                "away": {
                    "name": away_team.name,
                    "crest": away_team.logo_url or f"https://ui-avatars.com/api/?name={away_team.name}&background=random&color=fff&size=128",
                    "color": away_team.primary_color or "#1a365d"
                },
                "kickoff": fixture.match_time,
                "competition": fixture.season.competition.name,
                "match_date": fixture.match_date.strftime("%Y-%m-%d"),
                "features": [
                    *get_team_features(db, fixture.home_team_id, fixture.match_date),
                    *get_team_features(db, fixture.away_team_id, fixture.match_date)
                ],
                "prediction": {
                    "home": prediction.home_win_probability,
                    "draw": prediction.draw_probability,
                    "away": prediction.away_win_probability,
                    "winner": winner,
                    "home_score": prediction.predicted_home_score,
                    "away_score": prediction.predicted_away_score
                }
            }
            
            formatted_predictions.append(pred_data)
        
        # Create predictions file for frontend
        frontend_dir = os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "frontend", "src", "data"
        ))
        
        # Create data directory if it doesn't exist
        os.makedirs(frontend_dir, exist_ok=True)
        
        # Write predictions to JSON file
        predictions_file = os.path.join(frontend_dir, "predictions.json")
        with open(predictions_file, "w") as f:
            json.dump(formatted_predictions, f, indent=2)
        
        logger.info(f"Successfully wrote {len(formatted_predictions)} predictions to {predictions_file}")
        
        return len(formatted_predictions)
    except Exception as e:
        logger.error(f"Error finding predictions: {e}")
        return 0
    finally:
        db.close()

def main():
    """Main entry point for updating the frontend with predictions"""
    logger.info("Starting prediction update process for frontend")
    
    # Update predictions for frontend
    count = find_upcoming_predictions(days=14)  # Next 14 days
    
    logger.info(f"Prediction update process complete. Updated {count} predictions.")

if __name__ == "__main__":
    main() 
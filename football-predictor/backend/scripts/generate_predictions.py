#!/usr/bin/env python3

import os
import sys
import logging
from datetime import date, timedelta
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.models import Fixture, Team, Club, Competition, Season, Prediction
from ml.train import train_models, predict_match
from ml.features import create_match_features

def train_ml_models():
    """Train the ML models using historical data"""
    logger.info("Starting ML model training")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Train the models
        metrics = train_models(db)
        
        # Log training metrics
        logger.info(f"Model training complete with the following metrics:")
        logger.info(f"- Result prediction accuracy: {metrics['result_accuracy']:.4f}")
        logger.info(f"- Home score MSE: {metrics['home_score_mse']:.4f}")
        logger.info(f"- Away score MSE: {metrics['away_score_mse']:.4f}")
        
        # Log feature importance
        logger.info("Feature importance:")
        for feature, importance in sorted(
            metrics['feature_importance'].items(), 
            key=lambda x: x[1], 
            reverse=True
        ):
            logger.info(f"- {feature}: {importance:.4f}")
            
        return True
    except Exception as e:
        logger.error(f"Error training models: {e}")
        return False
    finally:
        db.close()

def generate_predictions_for_upcoming_matches(days=7):
    """Generate predictions for upcoming matches in the next N days"""
    logger.info(f"Generating predictions for matches in the next {days} days")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get date range
        today = date.today()
        end_date = today + timedelta(days=days)
        
        # Find upcoming fixtures
        fixtures = db.query(Fixture).filter(
            Fixture.match_date >= today,
            Fixture.match_date <= end_date,
            Fixture.is_completed == False
        ).options(
            joinedload(Fixture.home_team).joinedload(Team.club),
            joinedload(Fixture.away_team).joinedload(Team.club),
            joinedload(Fixture.season).joinedload(Season.competition)
        ).all()
        
        logger.info(f"Found {len(fixtures)} upcoming fixtures to predict")
        
        # Generate predictions for each fixture
        predictions_count = 0
        
        for fixture in fixtures:
            # Check if prediction already exists
            existing_prediction = db.query(Prediction).filter(
                Prediction.fixture_id == fixture.id
            ).first()
            
            if existing_prediction:
                logger.info(f"Prediction already exists for fixture {fixture.id} ({fixture.home_team.club.name} vs {fixture.away_team.club.name})")
                continue
            
            try:
                # Generate prediction
                prediction_result = predict_match(
                    db,
                    home_team_id=fixture.home_team_id,
                    away_team_id=fixture.away_team_id,
                    match_date=fixture.match_date.strftime("%Y-%m-%d")
                )
                
                # Create prediction record
                prediction = Prediction(
                    fixture_id=fixture.id,
                    home_team_id=fixture.home_team_id,
                    away_team_id=fixture.away_team_id,
                    match_date=fixture.match_date,
                    home_win_probability=prediction_result['home_win_probability'],
                    draw_probability=prediction_result['draw_probability'],
                    away_win_probability=prediction_result['away_win_probability'],
                    predicted_home_score=prediction_result['predicted_home_score'],
                    predicted_away_score=prediction_result['predicted_away_score'],
                    prediction_date=today
                )
                
                # Save prediction to database
                db.add(prediction)
                predictions_count += 1
                
                # Log the prediction
                logger.info(f"Generated prediction for {fixture.home_team.club.name} vs {fixture.away_team.club.name} on {fixture.match_date}")
                logger.info(f"  - Home win: {prediction_result['home_win_probability']:.2f}, Draw: {prediction_result['draw_probability']:.2f}, Away win: {prediction_result['away_win_probability']:.2f}")
                logger.info(f"  - Predicted score: {prediction_result['predicted_home_score']}-{prediction_result['predicted_away_score']}")
                
            except Exception as e:
                logger.error(f"Error generating prediction for fixture {fixture.id}: {e}")
        
        # Commit all predictions to database
        db.commit()
        logger.info(f"Successfully generated {predictions_count} new predictions")
        
        return predictions_count
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating predictions: {e}")
        return 0
    finally:
        db.close()

def main():
    """Main entry point for the prediction script"""
    logger.info("Starting prediction generation process")
    
    # First, train/retrain the models
    model_trained = train_ml_models()
    
    if not model_trained:
        logger.error("Failed to train models, cannot generate predictions")
        return
    
    # Generate predictions for upcoming matches
    predictions_count = generate_predictions_for_upcoming_matches(days=14)  # Set to 14 days by default
    
    logger.info(f"Prediction process complete. Generated {predictions_count} new predictions.")

if __name__ == "__main__":
    main() 
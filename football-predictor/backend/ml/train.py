import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
import joblib
import json
from sqlalchemy.orm import Session
from .features import create_training_dataset
from ..app.core.config import settings

def train_models(db: Session):
    """Train the prediction models."""
    # Create dataset
    df = create_training_dataset(db)
    
    # Prepare features for result prediction
    feature_cols = [
        'home_avg_goals_scored', 'home_avg_goals_conceded',
        'home_win_rate', 'home_draw_rate', 'home_form',
        'away_avg_goals_scored', 'away_avg_goals_conceded',
        'away_win_rate', 'away_draw_rate', 'away_form',
        'goal_scoring_diff', 'goal_conceding_diff',
        'win_rate_diff', 'form_diff'
    ]
    
    X = df[feature_cols]
    y_result = df['result']
    y_home_score = df['home_score']
    y_away_score = df['away_score']

    # Split data
    X_train, X_test, y_result_train, y_result_test = train_test_split(
        X, y_result, test_size=0.2, random_state=42
    )
    _, _, y_home_train, y_home_test = train_test_split(
        X, y_home_score, test_size=0.2, random_state=42
    )
    _, _, y_away_train, y_away_test = train_test_split(
        X, y_away_score, test_size=0.2, random_state=42
    )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train result prediction model
    result_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42
    )
    result_model.fit(X_train_scaled, y_result_train)

    # Train score prediction models
    home_score_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42
    )
    home_score_model.fit(X_train_scaled, y_home_train)

    away_score_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42
    )
    away_score_model.fit(X_train_scaled, y_away_train)

    # Calculate feature importance
    feature_importance = {
        feature: importance
        for feature, importance in zip(
            feature_cols,
            result_model.feature_importances_
        )
    }

    # Save models and scaler
    model_data = {
        'result_model': result_model,
        'home_score_model': home_score_model,
        'away_score_model': away_score_model,
        'scaler': scaler,
        'feature_cols': feature_cols
    }
    joblib.dump(model_data, settings.MODEL_PATH)

    # Save feature importance
    with open(settings.FEATURE_IMPORTANCE_PATH, 'w') as f:
        json.dump(feature_importance, f, indent=2)

    # Calculate and return metrics
    result_accuracy = result_model.score(X_test_scaled, y_result_test)
    home_score_mse = np.mean((home_score_model.predict(X_test_scaled) - y_home_test) ** 2)
    away_score_mse = np.mean((away_score_model.predict(X_test_scaled) - y_away_test) ** 2)

    return {
        'result_accuracy': result_accuracy,
        'home_score_mse': home_score_mse,
        'away_score_mse': away_score_mse,
        'feature_importance': feature_importance
    }

def predict_match(
    db: Session,
    home_team_id: int,
    away_team_id: int,
    match_date: str
) -> dict:
    """Make predictions for a match."""
    # Load model data
    model_data = joblib.load(settings.MODEL_PATH)
    result_model = model_data['result_model']
    home_score_model = model_data['home_score_model']
    away_score_model = model_data['away_score_model']
    scaler = model_data['scaler']
    feature_cols = model_data['feature_cols']

    # Create features for the match
    features = create_match_features(db, home_team_id, away_team_id, match_date)
    X = pd.DataFrame([features])[feature_cols]
    X_scaled = scaler.transform(X)

    # Make predictions
    result_probs = result_model.predict_proba(X_scaled)[0]
    predicted_home_score = round(float(home_score_model.predict(X_scaled)[0]))
    predicted_away_score = round(float(away_score_model.predict(X_scaled)[0]))

    # Get result probabilities
    result_mapping = result_model.classes_
    probabilities = {
        result: prob
        for result, prob in zip(result_mapping, result_probs)
    }

    return {
        'home_win_probability': probabilities.get('home_win', 0.0),
        'draw_probability': probabilities.get('draw', 0.0),
        'away_win_probability': probabilities.get('away_win', 0.0),
        'predicted_home_score': predicted_home_score,
        'predicted_away_score': predicted_away_score
    } 
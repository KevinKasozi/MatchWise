import pandas as pd
import numpy as np
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import Fixture, MatchResult, Team

def get_team_stats(db: Session, team_id: int, before_date: str) -> Dict[str, float]:
    """Calculate team statistics from past matches."""
    # Get past matches where the team was either home or away
    past_matches = (
        db.query(Fixture, MatchResult)
        .join(MatchResult)
        .filter(
            (Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id),
            Fixture.match_date < before_date,
            Fixture.is_completed == True
        )
        .order_by(Fixture.match_date.desc())
        .limit(10)
        .all()
    )

    if not past_matches:
        return {
            'avg_goals_scored': 0.0,
            'avg_goals_conceded': 0.0,
            'win_rate': 0.0,
            'draw_rate': 0.0,
            'form': 0.0,
        }

    goals_scored = []
    goals_conceded = []
    results = []  # 1 for win, 0 for draw, -1 for loss

    for fixture, result in past_matches:
        is_home = fixture.home_team_id == team_id
        
        if is_home:
            goals_scored.append(result.home_score)
            goals_conceded.append(result.away_score)
            if result.home_score > result.away_score:
                results.append(1)
            elif result.home_score == result.away_score:
                results.append(0)
            else:
                results.append(-1)
        else:
            goals_scored.append(result.away_score)
            goals_conceded.append(result.home_score)
            if result.away_score > result.home_score:
                results.append(1)
            elif result.away_score == result.home_score:
                results.append(0)
            else:
                results.append(-1)

    # Calculate statistics
    stats = {
        'avg_goals_scored': np.mean(goals_scored),
        'avg_goals_conceded': np.mean(goals_conceded),
        'win_rate': len([r for r in results if r == 1]) / len(results),
        'draw_rate': len([r for r in results if r == 0]) / len(results),
        'form': np.mean([1 if r >= 0 else 0 for r in results]),  # Recent form (including draws)
    }

    return stats

def create_match_features(
    db: Session,
    home_team_id: int,
    away_team_id: int,
    match_date: str
) -> Dict[str, float]:
    """Create features for a match prediction."""
    # Get team statistics
    home_stats = get_team_stats(db, home_team_id, match_date)
    away_stats = get_team_stats(db, away_team_id, match_date)

    # Create feature dictionary
    features = {
        # Home team features
        'home_avg_goals_scored': home_stats['avg_goals_scored'],
        'home_avg_goals_conceded': home_stats['avg_goals_conceded'],
        'home_win_rate': home_stats['win_rate'],
        'home_draw_rate': home_stats['draw_rate'],
        'home_form': home_stats['form'],

        # Away team features
        'away_avg_goals_scored': away_stats['avg_goals_scored'],
        'away_avg_goals_conceded': away_stats['avg_goals_conceded'],
        'away_win_rate': away_stats['win_rate'],
        'away_draw_rate': away_stats['draw_rate'],
        'away_form': away_stats['form'],

        # Relative strength features
        'goal_scoring_diff': home_stats['avg_goals_scored'] - away_stats['avg_goals_scored'],
        'goal_conceding_diff': home_stats['avg_goals_conceded'] - away_stats['avg_goals_conceded'],
        'win_rate_diff': home_stats['win_rate'] - away_stats['win_rate'],
        'form_diff': home_stats['form'] - away_stats['form'],
    }

    return features

def create_training_dataset(db: Session) -> pd.DataFrame:
    """Create a training dataset from historical matches."""
    # Get completed matches with results
    matches = (
        db.query(Fixture, MatchResult)
        .join(MatchResult)
        .filter(Fixture.is_completed == True)
        .order_by(Fixture.match_date)
        .all()
    )

    data = []
    for fixture, result in matches:
        # Create features for this match
        features = create_match_features(
            db,
            fixture.home_team_id,
            fixture.away_team_id,
            fixture.match_date
        )

        # Add match result
        features.update({
            'home_score': result.home_score,
            'away_score': result.away_score,
            'result': (
                'home_win' if result.home_score > result.away_score
                else 'draw' if result.home_score == result.away_score
                else 'away_win'
            )
        })

        data.append(features)

    return pd.DataFrame(data) 
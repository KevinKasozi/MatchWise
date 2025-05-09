from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class PredictionRequest(BaseModel):
    home_team_id: int
    away_team_id: int
    match_date: str  # ISO date string

class PredictionResponse(BaseModel):
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    predicted_home_score: int
    predicted_away_score: int

class PredictionBatchRequest(BaseModel):
    matches: List[PredictionRequest]

class PredictionBatchResponse(BaseModel):
    predictions: List[PredictionResponse]

class PredictionCreate(BaseModel):
    fixture_id: Optional[int] = None
    home_team_id: int
    away_team_id: int
    match_date: date
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    predicted_home_score: int
    predicted_away_score: int
    actual_home_score: Optional[int] = None
    actual_away_score: Optional[int] = None

class PredictionRead(PredictionCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True 
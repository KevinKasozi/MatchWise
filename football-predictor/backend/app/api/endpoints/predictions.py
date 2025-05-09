from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.core.database import get_db
from app.schemas.prediction import PredictionRequest, PredictionResponse, PredictionBatchRequest, PredictionBatchResponse, PredictionCreate, PredictionRead
from ml.train import predict_match
from app.models.models import Prediction
from typing import List, Optional
from datetime import date

router = APIRouter()

@router.post("/", response_model=PredictionResponse)
def get_prediction(
    req: PredictionRequest,
    db: Session = Depends(get_db)
):
    try:
        result = predict_match(
            db,
            home_team_id=req.home_team_id,
            away_team_id=req.away_team_id,
            match_date=req.match_date
        )
        return PredictionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch", response_model=PredictionBatchResponse)
def get_batch_predictions(
    req: PredictionBatchRequest,
    db: Session = Depends(get_db)
):
    predictions = []
    for match in req.matches:
        try:
            result = predict_match(
                db,
                home_team_id=match.home_team_id,
                away_team_id=match.away_team_id,
                match_date=match.match_date
            )
            predictions.append(PredictionResponse(**result))
        except Exception as e:
            predictions.append(PredictionResponse(
                home_win_probability=0.0,
                draw_probability=0.0,
                away_win_probability=0.0,
                predicted_home_score=0,
                predicted_away_score=0
            ))
    return PredictionBatchResponse(predictions=predictions)

@router.get("/stored", response_model=List[PredictionRead])
def list_predictions(
    db: Session = Depends(get_db),
    fixture_id: Optional[int] = None,
    home_team_id: Optional[int] = None,
    away_team_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = 100,
    skip: int = 0
):
    query = db.query(Prediction)
    if fixture_id:
        query = query.filter(Prediction.fixture_id == fixture_id)
    if home_team_id:
        query = query.filter(Prediction.home_team_id == home_team_id)
    if away_team_id:
        query = query.filter(Prediction.away_team_id == away_team_id)
    if from_date:
        query = query.filter(Prediction.match_date >= from_date)
    if to_date:
        query = query.filter(Prediction.match_date <= to_date)
    return query.offset(skip).limit(limit).all()

@router.post("/store", response_model=PredictionRead)
def store_prediction(
    pred: PredictionCreate,
    db: Session = Depends(get_db)
):
    db_pred = Prediction(**pred.dict())
    db.add(db_pred)
    db.commit()
    db.refresh(db_pred)
    return db_pred

# Add predictions endpoints here 
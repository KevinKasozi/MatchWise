from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from ...core.database import get_db
from ...models.models import Fixture
from ...schemas.fixture import FixtureRead

router = APIRouter()

@router.get("/", response_model=List[FixtureRead])
def get_fixtures(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None, description="upcoming, completed, or all"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    team_id: Optional[int] = Query(None)
):
    query = db.query(Fixture)
    if status == "upcoming":
        query = query.filter(Fixture.is_completed == False)
    elif status == "completed":
        query = query.filter(Fixture.is_completed == True)
    # else: all (no filter)
    if from_date:
        query = query.filter(Fixture.match_date >= from_date)
    if to_date:
        query = query.filter(Fixture.match_date <= to_date)
    if team_id:
        query = query.filter((Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id))
    return query.offset(skip).limit(limit).all()

# Add fixtures endpoints here 
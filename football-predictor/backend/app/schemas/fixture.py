from typing import Optional
from pydantic import BaseModel
from datetime import date

class FixtureRead(BaseModel):
    id: int
    season_id: int
    match_date: date
    home_team_id: int
    away_team_id: int
    stage: Optional[str] = None
    venue: Optional[str] = None
    is_completed: bool
    ground_id: Optional[int] = None
    group_id: Optional[int] = None

    class Config:
        from_attributes = True

class FixtureWithTeamNamesRead(FixtureRead):
    home_team_name: Optional[str] = None
    away_team_name: Optional[str] = None
    match_time: Optional[str] = None
    competition_name: Optional[str] = None
    competition_country: Optional[str] = None 
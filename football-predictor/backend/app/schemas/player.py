from typing import Optional
from pydantic import BaseModel
from datetime import date

class PlayerBase(BaseModel):
    name: str
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = None
    position: Optional[str] = None
    team_id: Optional[int] = None
    club_id: Optional[int] = None

class PlayerCreate(PlayerBase):
    pass

class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = None
    position: Optional[str] = None
    team_id: Optional[int] = None
    club_id: Optional[int] = None

class PlayerResponse(PlayerBase):
    id: int
    class Config:
        from_attributes = True 
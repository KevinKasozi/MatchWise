from typing import Optional, List
from pydantic import BaseModel, Field
from .player import PlayerResponse

class ClubBase(BaseModel):
    name: str
    founded_year: Optional[int] = None
    stadium_name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    alternative_names: Optional[str] = None

class ClubCreate(ClubBase):
    pass

class ClubUpdate(BaseModel):
    name: Optional[str] = None
    founded_year: Optional[int] = None
    stadium_name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    alternative_names: Optional[str] = None

class ClubResponse(ClubBase):
    id: int
    players: Optional[List[PlayerResponse]] = None

    class Config:
        from_attributes = True 
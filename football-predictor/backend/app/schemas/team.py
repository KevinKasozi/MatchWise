from typing import Optional
from pydantic import BaseModel

class TeamBase(BaseModel):
    club_id: Optional[int] = None
    team_type: str

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    club_id: Optional[int] = None
    team_type: Optional[str] = None

class TeamRead(TeamBase):
    id: int
    class Config:
        from_attributes = True 
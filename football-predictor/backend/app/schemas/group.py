from typing import Optional
from pydantic import BaseModel

class GroupBase(BaseModel):
    season_id: int
    name: str

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    season_id: Optional[int] = None
    name: Optional[str] = None

class GroupResponse(GroupBase):
    id: int
    class Config:
        from_attributes = True 
from typing import Optional
from pydantic import BaseModel

class GroundBase(BaseModel):
    name: str
    city: Optional[str] = None
    country: Optional[str] = None
    capacity: Optional[int] = None

class GroundCreate(GroundBase):
    pass

class GroundUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    capacity: Optional[int] = None

class GroundResponse(GroundBase):
    id: int
    class Config:
        from_attributes = True 
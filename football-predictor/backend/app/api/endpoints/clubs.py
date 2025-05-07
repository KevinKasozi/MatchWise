from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...models.models import Club
from ...schemas.club import ClubCreate, ClubUpdate, ClubResponse

router = APIRouter()

@router.get("/", response_model=List[ClubResponse])
def get_clubs(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    country: Optional[str] = None
):
    """Get all clubs with optional filtering by country."""
    query = db.query(Club)
    if country:
        query = query.filter(Club.country == country)
    return query.offset(skip).limit(limit).all()

@router.get("/{club_id}", response_model=ClubResponse)
def get_club(club_id: int, db: Session = Depends(get_db)):
    """Get a specific club by ID."""
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club

@router.post("/", response_model=ClubResponse)
def create_club(club: ClubCreate, db: Session = Depends(get_db)):
    """Create a new club."""
    db_club = Club(**club.dict())
    db.add(db_club)
    db.commit()
    db.refresh(db_club)
    return db_club

@router.put("/{club_id}", response_model=ClubResponse)
def update_club(
    club_id: int,
    club_update: ClubUpdate,
    db: Session = Depends(get_db)
):
    """Update a club's information."""
    db_club = db.query(Club).filter(Club.id == club_id).first()
    if not db_club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    for field, value in club_update.dict(exclude_unset=True).items():
        setattr(db_club, field, value)
    
    db.commit()
    db.refresh(db_club)
    return db_club

@router.delete("/{club_id}")
def delete_club(club_id: int, db: Session = Depends(get_db)):
    """Delete a club."""
    db_club = db.query(Club).filter(Club.id == club_id).first()
    if not db_club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    db.delete(db_club)
    db.commit()
    return {"message": "Club deleted successfully"} 
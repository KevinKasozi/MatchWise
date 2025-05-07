from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...models.models import Ground
from ...schemas.ground import GroundCreate, GroundUpdate, GroundResponse

router = APIRouter()

@router.get("/", response_model=List[GroundResponse])
def get_grounds(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return db.query(Ground).offset(skip).limit(limit).all()

@router.get("/{ground_id}", response_model=GroundResponse)
def get_ground(ground_id: int, db: Session = Depends(get_db)):
    ground = db.query(Ground).filter(Ground.id == ground_id).first()
    if not ground:
        raise HTTPException(status_code=404, detail="Ground not found")
    return ground

@router.post("/", response_model=GroundResponse)
def create_ground(ground: GroundCreate, db: Session = Depends(get_db)):
    db_ground = Ground(**ground.dict())
    db.add(db_ground)
    db.commit()
    db.refresh(db_ground)
    return db_ground

@router.put("/{ground_id}", response_model=GroundResponse)
def update_ground(ground_id: int, ground_update: GroundUpdate, db: Session = Depends(get_db)):
    db_ground = db.query(Ground).filter(Ground.id == ground_id).first()
    if not db_ground:
        raise HTTPException(status_code=404, detail="Ground not found")
    for field, value in ground_update.dict(exclude_unset=True).items():
        setattr(db_ground, field, value)
    db.commit()
    db.refresh(db_ground)
    return db_ground

@router.delete("/{ground_id}")
def delete_ground(ground_id: int, db: Session = Depends(get_db)):
    db_ground = db.query(Ground).filter(Ground.id == ground_id).first()
    if not db_ground:
        raise HTTPException(status_code=404, detail="Ground not found")
    db.delete(db_ground)
    db.commit()
    return {"message": "Ground deleted successfully"} 
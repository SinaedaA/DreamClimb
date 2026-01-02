from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas import SectorResponse, ProblemResponse
from app.models import Sector
from app.database import get_db

router = APIRouter()

@router.get("/sectors", response_model=list[SectorResponse])
def read_sectors(db: Session = Depends(get_db)):
    sectors = db.query(Sector).all()
    return sectors

@router.get("/sectors/{sector_slug}/problems", response_model=list[ProblemResponse])
def get_sector_problems(sector_slug: str, db: Session = Depends(get_db)):
    sector = db.query(Sector).filter(Sector.slug == sector_slug).first()
    if not sector:
        return []
    return sector.problems

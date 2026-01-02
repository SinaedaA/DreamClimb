from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.schemas import ProblemResponse
from app.models import Problem
from app.database import get_db
from sqlalchemy import or_, and_
from enum import Enum

router = APIRouter()

class TagsMode(str, Enum):
    ANY = "any"
    ALL = "all"

def convert_grade_to_order(grade: str) -> int:
    grade_order_mapping = {
        "1": 1, "1+": 2, "2-": 3, "2": 4, "2+": 5, 
        "3-": 6, "3": 7, "3+": 8, "4-": 9, "4": 10, "4+": 11,
        "5-": 12, "5": 13, "5+": 14, "6a": 15, "6a+": 16, "6b": 17,
        "6b+": 18, "6c": 19, "6c+": 20, "7a": 21, "7a+": 22, "7b": 23,
        "7b+": 24, "7c": 25, "7c+": 26, "8a": 27, "8a+": 28, "8b": 29,
        "8b+": 30, "8c": 31, "8c+": 32, "9a": 33
    }
    return grade_order_mapping.get(grade, 0)

@router.get("/problems", response_model=list[ProblemResponse])
def read_problems(
                    min_grade: str | None = "1", 
                    max_grade: str | None = "9a",
                    sector_slug: str | None = None,
                    tags: list[str] | None = Query(
                        None,
                        example = ["dévers","réglette"],
                        description = "List of tags/styles to filter by."
                    ),
                    tags_mode: TagsMode = TagsMode.ANY,
                    db: Session = Depends(get_db)):
    ## Define the paramters
    min_order = convert_grade_to_order(min_grade)
    max_order = convert_grade_to_order(max_grade)

    ## Filter by grade (but don't return all() yet):
    query = db.query(Problem).filter(
        Problem.grade_order <= max_order,
        Problem.grade_order >= min_order
    )

    ## Further by sector if provided
    if sector_slug:
        query = query.filter(Problem.sector.has(slug=sector_slug))
    ## Further by tags if provided
    if tags:
        tag_filters = [Problem.styles.ilike(f"%{tag}%") for tag in tags]

        if tags_mode == TagsMode.ALL:
            query = query.filter(and_(*tag_filters))
        else:
            query = query.filter(or_(*tag_filters))
    
    ## sort by rating and problem grade
    query = query.order_by(Problem.rating.desc().nulls_last(), Problem.grade_order)
    query = query.limit(100) # to limit response size for now.
    return query.all()

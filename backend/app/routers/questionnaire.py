from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import SessionLocal
from app.models import UserResponse, UserClimbedProblem, UserPreferredTag, Problem
from app.schemas import QuestionnaireSubmission, TagOption, ProblemResponse

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/questionnaire/submit")
def submit_questionnaire(
    submission: QuestionnaireSubmission,
    db: Session = Depends(get_db)
):
    """Submit a completed questionnaire"""
    
    # Create user response
    user_response = UserResponse(
        gender=submission.gender,
        height=submission.height,
        arm_span=submission.arm_span
    )
    db.add(user_response)
    db.flush()  # Get the ID
    
    # Add climbed problems
    for problem_id in submission.climbed_problem_ids:
        climbed = UserClimbedProblem(
            user_response_id=user_response.id,
            problem_id=problem_id
        )
        db.add(climbed)
    
    # Add preferred tags
    for tag in submission.preferred_tags:
        pref_tag = UserPreferredTag(
            user_response_id=user_response.id,
            tag=tag
        )
        db.add(pref_tag)
    
    db.commit()
    
    return {
        "message": "Topped boulders submitted successfully!",
        "response_id": user_response.id
    }

@router.get("/questionnaire/available-tags", response_model=List[TagOption])
def get_available_tags(db: Session = Depends(get_db)):
    """Get all unique tags from problems with counts"""
    
    # Get all styles, split by comma, count occurrences
    problems = db.query(Problem).all()
    tag_counts = {}
    
    for problem in problems:
        if problem.styles:
            tags = [tag.strip() for tag in problem.styles.split(',')]
            for tag in tags:
                if tag:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # Sort by count (most common first)
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    
    return [{"tag": tag, "count": count} for tag, count in sorted_tags]

@router.get("/questionnaire/search-problems", response_model=List[ProblemResponse])
def search_problems(
    q: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Search problems by name for autocomplete"""
    
    problems = db.query(Problem).filter(
        Problem.name.ilike(f"%{q}%")
    ).limit(limit).all()
    
    return problems
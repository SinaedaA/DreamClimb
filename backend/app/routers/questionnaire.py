from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import SessionLocal
from app.models import UserResponse, UserClimbedProblem, UserPreferredTag, Problem
from app.schemas import QuestionnaireSubmission, TagOption, ProblemResponse
from app.translations import translate_tag

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

@router.get("/questionnaire/available-tags")
def get_available_tags(
    language: str = "en",  # 'en' or 'fr'
    db: Session = Depends(get_db)
):
    """
    Get all unique climbing style tags with translations.
    
    Query params:
        language: 'en' for English (default), 'fr' for French
    
    Returns:
        List of tags with counts and translations
    """
    # Get all problems and extract tags
    problems = db.query(Problem).all()
    tag_counts = {}
    
    for problem in problems:
        if problem.styles:
            # Split comma-separated tags
            tags = [tag.strip() for tag in problem.styles.split(',')]
            for tag in tags:
                if tag:
                    # Store in lowercase for consistency
                    tag_lower = tag.lower()
                    tag_counts[tag_lower] = tag_counts.get(tag_lower, 0) + 1
    
    # Sort by count (most common first)
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Build response based on language
    if language == "en":
        return [
            {
                "tag": translate_tag(tag),  # English translation
                "tag_original": tag,  # Keep French for submission
                "count": count
            }
            for tag, count in sorted_tags
        ]
    else:  # French
        return [
            {
                "tag": tag,
                "count": count
            }
            for tag, count in sorted_tags
        ]

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

# Example of how to use in problem filtering endpoint
@router.get("/problems/filter")
def filter_problems(
    styles: str = None,  # Comma-separated, can be English or French
    language: str = "en",
    db: Session = Depends(get_db)
):
    """
    Filter problems by styles (accepts English or French tags).
    
    Example: /problems/filter?styles=overhang,crimps&language=en
    """
    query = db.query(Problem)
    
    if styles:
        # User might send English tags, but database has French
        from app.translations import get_reverse_translations, translate_tag
        reverse_trans = get_reverse_translations()
        
        requested_styles = [s.strip().lower() for s in styles.split(',')]
        
        # Convert English to French if needed
        french_styles = []
        for style in requested_styles:
            # Check if it's English (in reverse mapping)
            if style in reverse_trans:
                french_styles.append(reverse_trans[style])
            else:
                # Assume it's already French
                french_styles.append(style)
        
        # Filter by French tags in database
        for french_style in french_styles:
            query = query.filter(Problem.styles.ilike(f"%{french_style}%"))
    
    problems = query.limit(100).all()  # Limit for performance
    
    # Return with translated styles if English requested
    if language == "en":
        result = []
        for p in problems:
            problem_dict = {
                "id": p.id,
                "name": p.name,
                "grade": p.grade,
                "styles": p.styles,  # French
                "styles_translated": [
                    translate_tag(s.strip()) 
                    for s in p.styles.split(',')
                ] if p.styles else []
            }
            result.append(problem_dict)
        return result
    else:
        return problems
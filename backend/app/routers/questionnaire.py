from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import secrets
from app.database import SessionLocal
from app.models import UserResponse, UserClimbedProblem, UserPreferredTag, Problem
from app.schemas import QuestionnaireSubmission, TagOption, ProblemResponse
from app.translations import translate_tag
from datetime import datetime

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
    """
    Submit or update a climbing questionnaire.
    Handles returning users by merging data.
    """
    
    # ==========================================
    # STEP 1: Find existing user
    # ==========================================
    existing_user = None
    match_method = None
    
    # Try browser_id first (most reliable)
    if submission.browser_id:
        existing_user = db.query(UserResponse).filter(
            UserResponse.browser_id == submission.browser_id
        ).first()
        if existing_user:
            match_method = "browser_id"
    
    # Fallback to email if provided and no browser match
    if not existing_user and submission.email:
        existing_user = db.query(UserResponse).filter(
            UserResponse.email == submission.email
        ).first()
        if existing_user:
            match_method = "email"

    # Fallback to update_code if provided and no previous match
    if not existing_user and submission.update_code:
        existing_user = db.query(UserResponse).filter(
            UserResponse.update_code == submission.update_code
        ).first()
        if existing_user:
            match_method = "update_code"
    
    # ==========================================
    # STEP 2A: Update existing user
    # ==========================================
    if existing_user:
        print(f"Found existing user {existing_user.id} via {match_method}")
        
        # Update demographics (only if new values provided)
        if submission.gender:
            existing_user.gender = submission.gender
        if submission.height:
            existing_user.height = submission.height
        if submission.arm_span:
            existing_user.arm_span = submission.arm_span
        
        # Update email if provided
        if submission.email:
            existing_user.email = submission.email
        
        # Update browser_id if provided (user might have switched browsers)
        if submission.browser_id and not existing_user.browser_id:
            existing_user.browser_id = submission.browser_id
        
        # MERGE CLIMBED PROBLEMS (don't duplicate)
        existing_problem_ids = {
            cp.problem_id 
            for cp in existing_user.climbed_problems
        }
        
        new_problem_count = 0
        for problem_id in submission.climbed_problem_ids:
            if problem_id not in existing_problem_ids:
                # Add new problem
                climbed = UserClimbedProblem(
                    user_response_id=existing_user.id,
                    problem_id=problem_id
                )
                db.add(climbed)
                new_problem_count += 1
        
        # MERGE PREFERRED TAGS
        existing_tags = {
            upt.tag 
            for upt in existing_user.preferred_tags
        }
        new_tags = 0
        for tag in submission.preferred_tags:
            if tag not in existing_tags:
                pref_tag = UserPreferredTag(
                    user_response_id=existing_user.id,
                    tag=tag
                )
                db.add(pref_tag)
                new_tags += 1
        
        db.commit()
        
        total_problems = len(existing_problem_ids) + new_problem_count
        
        return {
            "message": "Profile updated successfully!",
            "user_id": existing_user.id,
            "update_code": existing_user.update_code,
            "is_update": True,
            "new_problems_added": new_problem_count,
            "total_problems": total_problems,
            "matched_via": match_method
        }
    
    # ==========================================
    # STEP 2B: Create new user
    # ==========================================
    else:
        print("Creating new user profile")
        # Create user response
        user_response = UserResponse(
            browser_id=submission.browser_id,
            email=submission.email,
            update_code=secrets.token_hex(4).upper(),
            gender=submission.gender,
            height=submission.height,
            arm_span=submission.arm_span,
            created_at=datetime.utcnow()
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
            "message": "Profile created successfully!",
            "user_id": user_response.id,
            "update_code": user_response.update_code,
            "is_update": False,
            "total_problems": len(submission.climbed_problem_ids),
            "matched_via": None
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
    
@router.get("/questionnaire/stats")
def get_questionnaire_stats(db: Session = Depends(get_db)):
    """Get statistics about collected data"""
    
    total_users = db.query(UserResponse).count()
    total_problems_logged = db.query(UserClimbedProblem).count()
    
    # Users with email
    users_with_email = db.query(UserResponse).filter(
        UserResponse.email.isnot(None)
    ).count()
    
    # Users with browser_id
    users_with_browser_id = db.query(UserResponse).filter(
        UserResponse.browser_id.isnot(None)
    ).count()
    
    # Average problems per user
    avg_problems = total_problems_logged / total_users if total_users > 0 else 0
    
    return {
        "total_users": total_users,
        "total_problems_logged": total_problems_logged,
        "avg_problems_per_user": round(avg_problems, 1),
        "users_with_email": users_with_email,
        "users_with_browser_id": users_with_browser_id,
        "email_rate": f"{(users_with_email/total_users*100):.1f}%" if total_users > 0 else "0%"
    }

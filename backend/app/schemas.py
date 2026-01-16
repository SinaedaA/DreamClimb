## Pydantic schemas for request and response models (for API later)
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# ===================
# Sector schemas
# ===================
class SectorResponse(BaseModel):
    id: int
    name: str
    slug: str
    grade_range: str | None = None

    class Config:
        from_attributes = True

class SectorBasic(BaseModel):
    name: str
    slug: str

    class Config:
        from_attributes = True

# ===================
# Problem schemas
# ===================
class ProblemBasic(BaseModel):
    """Minimal problem info"""
    id: str
    name: str
    grade: str
    
    class Config:
        from_attributes = True
class ProblemResponse(BaseModel):
    id: str
    name: str
    url: str
    grade: str
    #grade_order: int
    alt_grade: str | None = None
    first_ascent: str | None = None
    styles: str  # Comma-separated styles for simplicity
    sector: SectorBasic
    rating: float | None = None

    class Config:
        from_attributes = True

# ===================
# Circuit schemas
# ===================
class CircuitResponse(BaseModel):
    id: str
    name: str
    url: str
    sector_id: int
    circuit_level: str | None = None

    class Config:
        from_attributes = True

class CircuitProblemResponse(BaseModel):
    circuit_id: str
    problem_id: str
    number: str | None = None

    class Config:
        from_attributes = True

# ==========================================
# User schemas (survey)
# ==========================================
class QuestionnaireSubmission(BaseModel):
    """Schema for receiving questionnaire submissions"""
    # Identification
    browser_id: Optional[str] = None
    email: Optional[str] = None
    update_code: Optional[str] = None
    subscribe_newsletter: Optional[bool] = False
    
    # Demographics
    gender: Optional[str] = None
    height: Optional[int] = None
    arm_span: Optional[int] = None
    
    # Climbing data
    climbed_problem_ids: List[str]
    preferred_tags: List[str]


class TagOption(BaseModel):
    """Schema for available tag options"""
    tag: str
    count: int

class UserResponseDetail(BaseModel):
    """Detailed user response (for admin view)"""
    id: int
    browser_id: Optional[str]
    email: Optional[str]
    gender: Optional[str]
    height: Optional[int]
    arm_span: Optional[int]
    created_at: datetime
    problem_count: int
    tag_count: int
    
    class Config:
        from_attributes = True
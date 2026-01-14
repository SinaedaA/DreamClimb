## Pydantic schemas for request and response models (for API later)
from pydantic import BaseModel
from typing import List, Optional

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


# For receiving questionnaire data
class QuestionnaireSubmission(BaseModel):
    gender: str | None = None
    height: int | None = None
    arm_span: int | None = None
    climbed_problem_ids: List[str]  # List of problem IDs
    preferred_tags: List[str]  # List of style tags

# For getting available tags
class TagOption(BaseModel):
    tag: str
    count: int  # How many problems have this tag
# SQLAlchemy models (table definitions)
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

# =================================
# Fontainebleau specific models
# =================================
class Sector(Base):
    __tablename__ = "sectors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    slug = Column(String, unique=True, index=True)
    grade_range = Column(String, nullable=True)
    # Relationships
    problems = relationship("Problem", back_populates="sector")
    circuits = relationship("Circuit", back_populates="sector")

class Problem(Base):
    __tablename__ = "problems"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    url = Column(String, unique=True, index=True)
    grade = Column(String)
    grade_order = Column(Integer, index=True)
    alt_grade = Column(String)
    first_ascent = Column(String)
    styles = Column(String)  # Comma-separated styles for simplicity
    rating = Column(Float, nullable=True)
    # Relationships
    sector_id = Column(Integer, ForeignKey("sectors.id"))
    sector = relationship("Sector", back_populates="problems")
    circuit_problems = relationship("CircuitProblem", back_populates="problem")

class CircuitProblem(Base):
    __tablename__ = "circuit_problems"
    circuit_id = Column(String, ForeignKey("circuits.id"), primary_key=True)
    problem_id = Column(String, ForeignKey("problems.id"), primary_key=True)
    number = Column(String, nullable=True)  # Order of the problem in the circuit

    # Relationships
    circuit = relationship("Circuit", back_populates="circuit_problems")
    problem = relationship("Problem", back_populates="circuit_problems")

class Circuit(Base):
    __tablename__ = "circuits"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    url = Column(String, unique = True, index = True)
    circuit_level = Column(String, nullable=True)
    circuit_order = Column(Integer, nullable=True)
    # Relationships
    sector_id = Column(Integer, ForeignKey("sectors.id"))
    sector = relationship("Sector", back_populates="circuits")
    circuit_problems = relationship("CircuitProblem", back_populates="circuit")

# ====================
# User models
# ====================
class UserResponse(Base):
    __tablename__ = "user_responses"

    id = Column(Integer, primary_key=True, index=True)
    browser_id = Column(String, index=True, nullable = True) # add nullable=True for scraped data
    email = Column(String, nullable=True, index=True)
    update_code = Column(String, nullable=True)
    subscribe_newsletter = Column(Boolean, default=False)
    bleau_info_user = Column(String, nullable=True)
    
    # Demographics
    gender = Column(String, nullable=True)
    height = Column(Integer, nullable=True)  # in cm
    arm_span = Column(Integer, nullable=True)  # in cm
    nationality = Column(String, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    climbed_problems = relationship("UserClimbedProblem", back_populates="user_response")
    preferred_tags = relationship("UserPreferredTag", back_populates="user_response")

class UserClimbedProblem(Base):
    __tablename__ = "user_climbed_problems"
    
    id = Column(Integer, primary_key=True, index=True)
    user_response_id = Column(Integer, ForeignKey("user_responses.id"))
    problem_id = Column(String, ForeignKey("problems.id"))
    date_climbed = Column(DateTime, nullable=True)
    
    user_response = relationship("UserResponse", back_populates="climbed_problems")
    problem = relationship("Problem")

class UserPreferredTag(Base):
    __tablename__ = "user_preferred_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    user_response_id = Column(Integer, ForeignKey("user_responses.id"))
    tag = Column(String)  # e.g., "dévers", "réglettes"
    
    user_response = relationship("UserResponse", back_populates="preferred_tags")
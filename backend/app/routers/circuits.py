from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.schemas import CircuitResponse, CircuitProblemResponse, ProblemResponse
from app.models import Circuit, CircuitProblem, Problem
from app.database import get_db
from enum import Enum

router = APIRouter()

CIRC_LVLS = ["EN", "F", "PD-", "PD", "PD+", "AD-", "AD", "AD+",
             "D-", "D", "D+", "TD-", "TD", "TD+", "ED-", "ED", "ED+"]

class Strictness(str, Enum):
    STRICT = "strict"
    LOOSE = "loose"

@router.get("/circuits", response_model=list[CircuitResponse])
def read_circuits(
                    sector_slug: str | None = None,
                    difficulty_levels: list[str] | None = Query(
                        None,
                        example = ["PD", "AD"],
                        description = "List of circuit difficulty levels to filter by."
                    ),
                    matching: Strictness = Strictness.LOOSE,
                    db: Session = Depends(get_db)):
    query = db.query(Circuit)
    
    if sector_slug:
        query = query.filter(Circuit.sector.has(slug=sector_slug))
    
    if difficulty_levels:
        if matching == Strictness.STRICT:
            query = query.filter(Circuit.circuit_level.in_(difficulty_levels))
        else:
            expanded_levels = [
                variant
                for level in difficulty_levels
                for variant in [f"{level}-", level, f"{level}+"]
                if variant in CIRC_LVLS
            ]
            query = query.filter(Circuit.circuit_level.in_(expanded_levels))
    
    return query.all()

@router.get("/circuits/{circuit_id}/problems", response_model=list[ProblemResponse])
def get_circuit_problems(circuit_id: str, db: Session = Depends(get_db)):
    circuit = db.query(Circuit).filter(Circuit.id == circuit_id).first()
    if not circuit:
        return []
    problems = [
        cp.problem
        for cp in db.query(CircuitProblem).filter(CircuitProblem.circuit_id == circuit_id).all()
    ]
    return problems
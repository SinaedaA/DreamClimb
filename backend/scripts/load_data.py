import os
from pathlib import Path
import json
from app.database import SessionLocal
from app.models import Sector, Problem, Circuit, CircuitProblem

GRADE_ORDER = {
    "1": 1, "1+": 2, "2-": 3, "2": 4, "2+": 5, 
    "3-": 6, "3": 7, "3+": 8, "4-": 9, "4": 10, "4+": 11,
    "5-": 12, "5": 13, "5+": 14, "6a": 15, "6a+": 16, "6b": 17,
    "6b+": 18, "6c": 19, "6c+": 20, "7a": 21, "7a+": 22, "7b": 23,
    "7b+": 24, "7c": 25, "7c+": 26, "8a": 27, "8a+": 28, "8b": 29,
    "8b+": 30, "8c": 31, "8c+": 32, "9a": 33
}
CIRCUIT_ORDER = {
    ## ABO circuits not included, they are mixed
    "EN": 1, "F": 2, "PD-": 3, "PD": 4, "PD+": 5, "AD-": 6, 
    "AD": 7, "AD+": 8, "D-": 9, "D": 10, "D+": 11, "TD-": 12, 
    "TD": 13, "TD+": 14, "ED-": 15, "ED": 16, "ED+": 17
}
CIRC_LVLS = ["EN", "F", "PD-", "PD", "PD+", "AD-", "AD", "AD+",
             "D-", "D", "D+", "TD-", "TD", "TD+", "ED-", "ED", "ED+"]

def main():
    db = SessionLocal()

    boulder_path = Path(__file__).parent.parent / "data" / "raw" / "boulders"
    circuit_path = Path(__file__).parent.parent / "data" / "raw" / "circuits"
    
    # Read and process JSON files
    sector_records, boulder_records = read_boulder_jsons(boulder_path)
    circuit_records, circuit_problem_records = read_circuit_jsons(circuit_path)

    # Load into database
    slug2id = load_records(db, Sector, sector_records, return_slug_mapping=True)
    load_records(db, Problem, boulder_records, sector_slug_2_id=slug2id, extract_sector_slug=True)
    load_records(db, Circuit, circuit_records, sector_slug_2_id=slug2id, extract_sector_slug=True)
    load_circuit_problems_if_missing(db, circuit_problem_records, sector_slug_2_id=slug2id)

    # Deduplicate circuit problems before loading
    unique_circuit_problems = {
        (r["circuit_id"], r["problem_id"]): r 
        for r in circuit_problem_records
    }.values()
    
    circuit_problem_records = list(unique_circuit_problems)
    load_records(db, CircuitProblem, circuit_problem_records)
    
    db.close()

def read_json_files(data_path):
    """Generic function to read all JSON files from a path."""
    json_files = list(data_path.glob("*.json"))
    for file in json_files:
        sector_slug = file.stem
        with open(file, "r") as f:
            data = json.load(f)
            sector_name = data.get("sector")
            if sector_name == "":
                print(f"⚠️ Warning: Sector name missing in {file.name}. Skipping...")
                continue
            yield sector_slug, data

def read_boulder_jsons(data_path):
    """Read and process boulder JSON files."""
    sector_records = []
    boulder_records = []
    
    for sector_slug, data in read_json_files(data_path):
        sector_record = make_sector_record(data, sector_slug)
        sector_records.append(sector_record)
        boulder_records.extend(make_boulder_records(data, sector_slug))
                
    return sector_records, boulder_records

def read_circuit_jsons(data_path):
    """Read and process circuit JSON files."""
    circuit_records = []
    circuit_problem_records = []
    
    for sector_slug, data in read_json_files(data_path):
        circuit_records.extend(make_circuit_records(data, sector_slug))
        circuit_problem_records.extend(make_circuit_problem_records(data, sector_slug))
        
    return circuit_records, circuit_problem_records

def make_sector_record(data, sector_slug):
    """Extract sector metadata from JSON."""
    sector_name = data.get("sector")
    grades = [p.get("grade") for p in data.get("problems", []) if p.get("grade")]
    grade_range = f"{grades[-1]} - {grades[0]}" if grades else ""
    
    return {
        "name": sector_name,
        "slug": sector_slug,
        "grade_range": grade_range
    }

def make_boulder_records(data, sector_slug):
    """Extract boulder problems from JSON."""
    records = []
    for problem in data.get("problems", []):
        url = problem.get("url", "")
        unique_id = f"{sector_slug}-{url.split('/')[-1].split('.')[0]}"
        grade = problem.get("grade", "")

        records.append({
            "id": unique_id,
            "name": problem.get("name", "Unnamed Problem"),
            "url": url,
            "grade": grade,
            "grade_order": GRADE_ORDER.get(grade, 0),
            "alt_grade": problem.get("alt_grade", ""),
            "rating": problem.get("rating", None),
            "first_ascent": problem.get("first_ascensionist", ""),
            "styles": ",".join(problem.get("styles", []))
        })
    return records

def make_circuit_records(data, sector_slug):
    """Extract circuits from JSON."""
    records = []
    for circuit in data.get("circuits", []):
        url = circuit.get("url", "")
        unique_id = f"{sector_slug}-{url.split('/')[-1].split('.')[0]}"
        # extract difficulty rating from name
        name_words = circuit.get("name", "").split(" ")
        level = list(set(name_words) & set(CIRC_LVLS))
        circuit_order = CIRCUIT_ORDER.get(level[0], 0) if level else 0
        
        records.append({
            "id": unique_id,
            "name": circuit.get("name", "Unnamed Circuit"),
            "url": url,
            "circuit_level": level[0] if level else "",
            "circuit_order": circuit_order
        })
    return records

def make_circuit_problem_records(data, sector_slug):
    """Extract circuit-problem relationships from JSON."""
    records = []
    for circuit in data.get("circuits", []):
        circuit_url = circuit.get("url", "")
        circuit_id = f"{sector_slug}-{circuit_url.split('/')[-1].split('.')[0]}"
        
        for problem in circuit.get("problems", []):
            problem_url = problem.get("url", "")
            problem_id = f"{sector_slug}-{problem_url.split('/')[-1].split('.')[0]}"
            
            records.append({
                "circuit_id": circuit_id,
                "problem_id": problem_id,
                "number": problem.get("id", "")  # Using 'id' field from circuit[problems] data as number
            })
    return records

def load_circuit_problems_if_missing(db, circuit_problem_records, sector_slug_2_id):
    """Load circuit problems in the problems table, if they are missing from it."""
    existing_problem_ids = {p.id for p in db.query(Problem).all()}
    missing_records = [r for r in circuit_problem_records if r["problem_id"] not in existing_problem_ids]
    print(f"Found {len(missing_records)} missing problems from circuit problems.")
    
    missing_created = 0
    for record in missing_records:
        sector_slug = record["problem_id"].split("-")[0]
        problem_url = f"https://bleau.info/{sector_slug}/{record['problem_id'].split('-')[1]}.html"

        new_problem = Problem(
            id = record["problem_id"],
            name = "Unknown Problem", # missing name comes from scraping
            url = problem_url,
            grade = "",
            alt_grade = "",
            first_ascent = "",
            styles = "",
            sector_id = sector_slug_2_id.get(sector_slug)
        )
        db.add(new_problem)
        db.flush()
        missing_created += 1
    db.commit()
    if missing_created > 0:
        print(f"✅ Created {missing_created} missing problems from circuit problems.")

def load_records(db, model_class, records, sector_slug_2_id=None, 
                extract_sector_slug=False, return_slug_mapping=False):
    """
    Generic function to load records into database.
    
    Args:
        db: Database session
        model_class: SQLAlchemy model class (Sector, Problem, Circuit, etc.)
        records: List of dicts with record data
        sector_slug_2_id: Mapping of sector slugs to IDs (for FKs)
        extract_sector_slug: If True, extract sector_slug from 'id' field and add sector_id FK
        return_slug_mapping: If True, return dict of slug->id for Sectors
    
    Returns:
        Dict of slug->id if return_slug_mapping=True, else None
    """
    model_name = model_class.__name__
    slug_mapping = {}
    
    try:
        for record_data in records:
            # Handle sector foreign key if needed
            if extract_sector_slug and sector_slug_2_id:
                sector_slug = record_data["id"].split("-")[0]
                record_data["sector_id"] = sector_slug_2_id.get(sector_slug)
            
            # Create model instance
            instance = model_class(**record_data)
            db.add(instance)
            
            # Track slug->id mapping for sectors
            if return_slug_mapping:
                db.flush()  # Assign ID without committing
                slug_mapping[instance.slug] = instance.id
        
        db.commit()
        print(f"✅ Loaded {len(records)} {model_name.lower()}(s)")
        
        return slug_mapping if return_slug_mapping else None
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error loading {model_name.lower()}s: {e}")
        raise

if __name__ == "__main__":
    main()
import sys
sys.path.insert(0, '/opt/airflow')

import json
from app.database import SessionLocal
from app.models import Problem, UserResponse, UserClimbedProblem
import datetime
from tqdm import tqdm
import click
from pathlib import Path

## New ascents contain:
# BLEAU
# {"name": "Mathieu Preteseille", "profile_url": "https://bleau.info/profiles/mathieu.preteseille", "height": 177.0, "span": 183.0, "nationality": "FR", "source": "bleau_info" ...
# "repetitions": [{"date": "2026-01-20", "ascent": "En Chantier", "grade": "7a"}, {"date": "2026-01-20", "ascent": "La Fissure en Chantier", "grade": "7a"}]}

# BETTY
# {"name": "C\u00e9line", "profile_url": "https://bettybeta.com/bouldering/climber/celine75", "n_ascents": 1, "height": 168, "span": 177, "source": "betty_beta", ...
# "repetitions": [{"ascent": "Le Petit Suisse", "grade": "7b+", "date": "20-01-2026", "bleau_link": "https://bleau.info/restant/23775.html"}]},

# use click to pass json path as argument
@click.command()
@click.option('--json_path', type=click.Path(exists=True), help='Path to the JSON file containing new ascents data.')
def main(json_path):
    db = SessionLocal()
    print(json_path)
    json_path = Path(json_path)
    if not json_path.exists():
        print(f"❌ Data file not found at {json_path}. Exiting.")
        return

    with open(json_path, "r") as f:
        ascent_data = json.load(f)
    print(f"Loaded {len(ascent_data)} user records from {json_path}.")

    for data in tqdm(ascent_data, desc="Processing user records"):
        try:
            user_record = make_user_response(data)
            profile_url = data.get("profile_url")
            user = db.query(UserResponse).filter_by(profile_url=profile_url).first()
            if not user:
                print(f"⚠️ User not found for {profile_url}")
                continue
            user.height = user_record['height']
            user.arm_span = user_record['arm_span']
            user.nationality = user_record['nationality']
            user.modified_at = datetime.datetime.utcnow()

            ## Get the user_id from the existing user, to update the climbed problems
            user_id = user.id
            for rep in data.get("repetitions", []): 
                climbed_record = make_climbed_record(rep, db)
                climbed_record['user_response_id'] = user_id

                # Check if this ascent already exists
                existing = db.query(UserClimbedProblem).filter_by(
                    user_response_id=user_id,
                    problem_id=climbed_record['problem_id'],
                    date_climbed=climbed_record['date_climbed']
                ).first()
                if existing:
                    continue
                
                # Add new climbed problem if it doesn't exist
                climbed_instance = UserClimbedProblem(**climbed_record)
                db.add(climbed_instance)
            
            db.commit()  # commit climbed problems for this user
        except Exception as e:
            db.rollback()
            print(f"❌ Error processing user {data.get('name', 'unknown')}: {e}")
    db.close()

def make_climbed_record(data, db):
    """Convert a climbed problem data dict into a DB-ready record."""
    boulder_name = data.get("ascent", None)
    grade = data.get("grade", None)
    bleau_link = data.get("bleau_link", None)

    # Get date string and convert to date object
    date_str = data.get("date", None)
    if date_str:
        date_climbed = datetime.datetime.strptime(date_str, "%d-%m-%Y").date()
    else:
        date_climbed = None
    
    # Link to problems table
    if bleau_link:
        try:
            problem = db.query(Problem).filter_by(url=bleau_link).first()
        except Exception as e:
            print(f"❌ Error fetching problem {boulder_name} with URL {bleau_link}: {e}. Probably a forbidden area.")
            problem = None
    else: # only executed if there is no link to bleau info
        try:
            problem = db.query(Problem).filter_by(name=boulder_name, grade = grade).first()
        except Exception as e:
            print(f"❌ Error fetching problem {boulder_name} with grade {grade}: {e}")
            problem = None
    return {
        'user_response_id': None,
        'problem_id': problem.id if problem else None,
        'date_climbed': date_climbed,
    }

def make_user_response(data):
    """Convert a climber data dict into a DB-ready record."""
    ## Make the record with only information that is likely to be changed through scraping
    return {
        "name": data.get("name", None),
        "profile_url": data.get("profile_url", None),
        "height": data.get("height", None),
        "arm_span": data.get("span", None),
        "nationality": data.get("nationality", None)
    }

if __name__ == "__main__":
    main()
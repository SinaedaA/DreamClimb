from pathlib import Path
import json
from app.database import SessionLocal
from app.models import Problem, CircuitProblem, UserResponse, UserClimbedProblem
import datetime
from tqdm import tqdm
import gender_guesser.detector as gender

d = gender.Detector()

JSON_PATH = Path(__file__).parent.parent / "data" / "raw" / "ascents" / "bleau_climbers.json" # for testing only
#JSON_PATH = Path(__file__).parent.parent / "data" / "raw" / "ascents" / "betty_climbers_final.json" # for testing only

def main(json_path: str = JSON_PATH):
    db = SessionLocal()

    if not json_path.exists():
        print(f"❌ Data file not found at {json_path}. Exiting.")
        return

    with open(json_path, "r") as f:
        ascent_data = json.load(f)
    print(f"Loaded {len(ascent_data)} user records from {json_path}.")

    for data in tqdm(ascent_data, desc="Processing user records"):
        try:
            user_record, source = make_user_response(data)
            user_instance = UserResponse(**user_record)
            db.add(user_instance)
            db.flush()  # auto-generate user_instance.id to link it to the climbed problems

            for rep in data.get("repetitions", []): 
                climbed_record = make_climbed_record(rep, db, source)
                climbed_record['user_response_id'] = user_instance.id
                climbed_instance = UserClimbedProblem(**climbed_record)
                db.add(climbed_instance)
            
            db.commit()  # commit climbed problems for this user
        except Exception as e:
            db.rollback()
            print(f"❌ Error processing user {data.get('name', 'unknown')}: {e}")
    db.close()

def make_climbed_record(data, db, source):
    """Convert a climbed problem data dict into a DB-ready record."""
    boulder_name = data.get("ascent", None)
    grade = data.get("grade", None)
    bleau_link = data.get("bleau_link", None)

    date_climbed = parse_date(data.get("date", None), source)
    
    # First try to find by bleau_link if available
    if bleau_link:
        try:
            problem = db.query(Problem).filter_by(url=bleau_link).first()
        except Exception as e:
            print(f"❌ Error fetching problem {boulder_name} with URL {bleau_link}: {e}. Probably a forbidden area.")
            problem = None
    else: # only executed if there is not link to bleau info
        try:
            problem = db.query(Problem).filter_by(name=boulder_name, grade = grade).first()
        except Exception as e:
            print(f"❌ Error fetching problem {boulder_name} with grade {grade}: {e}")
            try:
                problem = db.query(CircuitProblem).filter_by(name=boulder_name, grade = grade).first()
            except Exception as e:
                print(f"❌ Error fetching circuit problem {boulder_name} with grade {grade}: {e}")
                problem = None
    return {
        'user_response_id': None,  # to be filled after UserResponse is created
        'problem_id': problem.id if problem else None,
        'date_climbed': date_climbed,
    }

def parse_date(date_str, source):
    date_str = date_str.replace(":", "")
    try:
        if source == "bleau_info":
            return datetime.datetime.strptime(date_str, "%d-%m-%Y")
        elif source == "betty_beta":
            return datetime.datetime.strptime(date_str, "%m/%d/%Y")
    except ValueError:
        print(f"⚠️ Failed to parse date: {date_str} from {source}")
        return None

def make_user_response(data):
    """Convert a climber data dict into a DB-ready record."""
    info_id = data["url"].split("/")[-1] # https://bleau.info/profiles/antoine.maire
    source = "bleau_info" if "bleau.info" in data.get("url", "") else "betty_beta"
    
    first_name = data.get("name", "").split(" ")[0]
    data['gender'] = d.get_gender(first_name)
    ## Make the record
    return {
        # data that is None for scraping
        "browser_id": None,
        "email": None,
        "subscribe_newsletter": False,
        "update_code": None,
        # name and bleau_info_user (if from bleau.info)
        "name": data.get("name", None),
        "bleau_info_user": info_id if source == "bleau_info" else None,
        "betty_userid": info_id if source == "betty_beta" else None,
        "profile_url": data.get("url", None),
        # demographics
        "height": data.get("height", None),
        "arm_span": data.get("span", None),
        "nationality": data.get("nationality", None),
        "gender": data.get("gender", None),
        # created_at will be made automatically
    }, source

if __name__ == "__main__":
    main()
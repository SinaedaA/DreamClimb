from app.database import engine, Base
from app.models import Sector, Problem, Circuit, CircuitProblem, UserResponse, UserClimbedProblem, UserPreferredTag
from sqlalchemy import inspect

def main():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    if existing_tables:
        print(f"✅ Tables already exist ({len(existing_tables)} tables found). Skipping creation.")
        return
    
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")

if __name__ == "__main__":
    main()
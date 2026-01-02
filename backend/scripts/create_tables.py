from app.database import engine, Base
from app.models import Sector, Problem, Circuit, CircuitProblem

def main():
    print("Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)

    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    main()
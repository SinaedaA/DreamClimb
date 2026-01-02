# scripts/setup_database.py

from .create_tables import main as create_tables
from .load_data import main as load_data

def main():
    print("\n[1/2] Creating tables...")
    create_tables()
    
    print("\n[2/2] Loading data...")
    load_data()

if __name__ == "__main__":
    main()
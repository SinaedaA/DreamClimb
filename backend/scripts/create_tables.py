# from app.database import engine, Base
# from app.models import Sector, Problem, Circuit, CircuitProblem, UserResponse, UserClimbedProblem, UserPreferredTag
# from sqlalchemy import inspect
# import click

# # get command line argument for --force, using click
# @click.command()
# @click.option('--force', is_flag=True, help='Force drop existing tables before creation')

# def main(force):
#     inspector = inspect(engine)
#     existing_tables = inspector.get_table_names()
    
#     if existing_tables and not force:
#         print(f"✅ Tables already exist ({len(existing_tables)} tables found). Skipping creation.")
#         return
#     elif existing_tables and force:
#             print("⚠️ Dropping existing tables...")
#             Base.metadata.drop_all(bind=engine)
#             print("✅ Existing tables dropped.")
    
#     print("Creating database tables...")
#     Base.metadata.create_all(bind=engine)
#     print("✅ Tables created successfully!")

# # if __name__ == "__main__":
# #     main()
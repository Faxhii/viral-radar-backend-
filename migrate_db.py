import os
import sqlalchemy
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def run_migrations():
    if not DATABASE_URL:
        print("DATABASE_URL not set. Skipping migrations.")
        return

    print(f"Running migrations on {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local db'}...")
    
    try:
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)
        
        with engine.connect() as conn:
            # Check users table columns
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'is_verified' not in columns:
                print("Adding 'is_verified' column...")
                # Postgres and SQLite syntax compatibility
                is_sqlite = 'sqlite' in DATABASE_URL
                if is_sqlite:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0"))
                else:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE"))
            else:
                print("'is_verified' column already exists.")

            if 'verification_token' not in columns:
                print("Adding 'verification_token' column...")
                conn.execute(text("ALTER TABLE users ADD COLUMN verification_token VARCHAR"))
            else:
                print("'verification_token' column already exists.")
                
            conn.commit()
            print("Database migration completed.")
            
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    run_migrations()

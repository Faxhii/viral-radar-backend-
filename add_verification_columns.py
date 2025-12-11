from sqlalchemy import create_engine, text
import os

DATABASE_URL = "sqlite:///./viralvision.db"

def add_columns():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        try:
            # Check if columns exist first (to avoid errors on re-run)
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'is_verified' not in columns:
                print("Adding 'is_verified' column...")
                conn.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0"))
            else:
                print("'is_verified' column already exists.")

            if 'verification_token' not in columns:
                print("Adding 'verification_token' column...")
                conn.execute(text("ALTER TABLE users ADD COLUMN verification_token VARCHAR"))
            else:
                print("'verification_token' column already exists.")
                
            conn.commit()
            print("Database migration completed successfully.")
        except Exception as e:
            print(f"Error migrating database: {e}")

if __name__ == "__main__":
    add_columns()

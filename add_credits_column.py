from database import SessionLocal, engine
from models import Base
from sqlalchemy import text

def add_credits_column():
    db = SessionLocal()
    try:
        # Check if column exists
        result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='credits'"))
        if result.fetchone():
            print("Column 'credits' already exists.")
        else:
            print("Adding 'credits' column to users table...")
            db.execute(text("ALTER TABLE users ADD COLUMN credits FLOAT DEFAULT 3.0"))
            db.commit()
            print("Column added successfully.")
    except Exception as e:
        print(f"Error adding column: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_credits_column()

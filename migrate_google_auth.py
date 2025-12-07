from database import engine, SessionLocal
from sqlalchemy import text

def migrate():
    print("Starting migration...")
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        try:
            # Add google_sub column
            print("Adding google_sub column...")
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_sub VARCHAR UNIQUE;"))
            
            # Add picture column
            print("Adding picture column...")
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS picture VARCHAR;"))
            
            print("Migration successful!")
        except Exception as e:
            print(f"Migration failed: {e}")
            # Don't raise, just print. It might fail if columns exist (handled by IF NOT EXISTS usually, but Postgres specific)

if __name__ == "__main__":
    migrate()

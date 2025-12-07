from database import engine
from sqlalchemy import text

def verify():
    with engine.connect() as conn:
        try:
            # Try to select the new column
            conn.execute(text("SELECT google_sub FROM users LIMIT 1;"))
            print("VERIFICATION SUCCESS: google_sub column exists.")
        except Exception as e:
            print(f"VERIFICATION FAILED: {e}")

if __name__ == "__main__":
    verify()

import sqlite3
import os

DB_FILE = "viralvision.db"

def fix_db():
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. Fix Videos Table
    print("Checking 'videos' table...")
    cursor.execute("PRAGMA table_info(videos)")
    columns = [info[1] for info in cursor.fetchall()]
    
    video_fields = [
        ("duration", "INTEGER"),
        ("title", "VARCHAR")
    ]

    for field, type_ in video_fields:
        if field not in columns:
            print(f"Adding '{field}' column to 'videos' table...")
            try:
                cursor.execute(f"ALTER TABLE videos ADD COLUMN {field} {type_}")
                print(f"Added '{field}'.")
            except Exception as e:
                print(f"Error adding '{field}': {e}")
        else:
            print(f"'{field}' column exists.")

    # 2. Fix Users Table
    print("\nChecking 'users' table...")
    cursor.execute("PRAGMA table_info(users)")
    columns = [info[1] for info in cursor.fetchall()]
    
    user_fields = [
        ("full_name", "VARCHAR"),
        ("primary_platform", "VARCHAR"),
        ("primary_category", "VARCHAR"),
        ("avg_length", "VARCHAR"),
        ("lemon_squeezy_customer_id", "VARCHAR"),
        ("lemon_squeezy_subscription_id", "VARCHAR")
    ]
    
    for field, type_ in user_fields:
        if field not in columns:
            print(f"Adding '{field}' column to 'users' table...")
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {field} {type_}")
                print(f"Added '{field}'.")
            except Exception as e:
                print(f"Error adding '{field}': {e}")
        else:
            print(f"'{field}' column exists.")

    conn.commit()
    conn.close()
    print("\nDatabase fix completed.")

if __name__ == "__main__":
    fix_db()

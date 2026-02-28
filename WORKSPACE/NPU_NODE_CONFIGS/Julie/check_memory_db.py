import sqlite3
import json

DB_PATH = "/home/happy/ai_library_stable/memory_db/conversations.db"

def check_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables: {tables}")
        
        if "conversations" in tables:
            cursor.execute("SELECT * FROM conversations;")
            rows = cursor.fetchall()
            print(f"Total rows in conversations: {len(rows)}")
            for row in rows:
                print(f" - {row['id']}: {row['name']} (Status: {row['status']}, Project: {row['project']})")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()

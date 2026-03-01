import sqlite3
import os

db_path = "mcp_servers/vjlive3brain/brain.db"
if not os.path.exists(db_path):
    print("Database not found!")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    
    for table_name in [t[0] for t in tables]:
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        print(f"\nTable {table_name} columns:")
        for col in columns:
            print("  ", col[1], col[2])
            
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"  Total records: {count}")
    
    # If there is a concepts or memories table, let's list it
    for table_name in [t[0] for t in tables]:
        if "document" in table_name.lower() or "concept" in table_name.lower():
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
            rows = cursor.fetchall()
            print(f"\nSample from {table_name}:")
            for row in rows:
                print("  ", row)

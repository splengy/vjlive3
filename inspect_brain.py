import sqlite3
import json
import os

db_path = '/tmp/vjlive3_brain.sqlite'

try:
    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
        cursor = conn.cursor()
        
        # 1. Get total number of distinct concept IDs and their names
        cursor.execute("SELECT concept_id, name, category, role_assignment FROM concepts")
        all_concepts = cursor.fetchall()
        
        # 2. Extract current board IDs
        with open("/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/BOARD.md", "r") as f:
            board_data = f.read()
            
        board_lines = [line.strip() for line in board_data.split('\n') if line.startswith('| P')]
        # e.g., | P3-EXT006 | analog tv ...
        board_names = set()
        for line in board_lines:
            parts = line.split('|')
            if len(parts) >= 3:
                name_clean = parts[2].strip().lower().replace(" ", "_").replace("(", "").replace(")", "")
                board_names.add(name_clean)
                
        # 3. Find missing ones
        missing = []
        for c in all_concepts:
            cid, name, category, role = c
            name_norm = name.lower().replace(" ", "_").replace("(", "").replace(")", "")
            
            # Substring matching in case the board name is a bit different
            found = False
            for bn in board_names:
                if name_norm in bn or bn in name_norm:
                    found = True
                    break
            
            if not found:
                missing.append(c)

        print(f"Total concepts in DB: {len(all_concepts)}")
        print(f"Total concepts marked missing from board: {len(missing)}")
        
        if len(missing) > 0:
            print("Examples of missing:", missing[:5])
            print(f"Role Assignments: {set([c[3] for c in missing])}")
            print(f"Categories: {set([c[2] for c in missing])}")
            
except Exception as e:
    print('Failed:', e)

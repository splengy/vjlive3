import sqlite3
import os

db_path = '/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/WORKSPACE/MEMORY_BANK/vjlive3_brain.sqlite'
board_path = '/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/BOARD.md'

try:
    conn = sqlite3.connect(db_path, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute("SELECT concept_id, name, category, role_assignment FROM concepts")
    all_concepts = cursor.fetchall()
    
    with open(board_path, "r") as f:
        board_data = f.read()
        
    board_lines = [line.strip() for line in board_data.split('\n') if line.startswith('| P')]
    board_names = set()
    for line in board_lines:
        parts = line.split('|')
        if len(parts) >= 3:
            name_clean = parts[2].strip().lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "")
            board_names.add(name_clean)
            
    missing_by_category = {}
    missing_count = 0
    
    for c in all_concepts:
        cid, name, category, role = c
        # Some db names might be clean, some might have spaces
        name_norm = name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "")
        
        found = False
        for bn in board_names:
            if name_norm in bn or bn in name_norm:
                found = True
                break
                
        if not found:
            missing_count += 1
            if category not in missing_by_category:
                missing_by_category[category] = []
            missing_by_category[category].append(c)
            
    print(f"Total concepts in Brain: {len(all_concepts)}")
    print(f"Total concepts currently listed on BOARD.md: {len(board_lines)}")
    print(f"Total MISSING concepts to add: {missing_count}")
    
    with open("/tmp/missing_categories.txt", "w") as out:
        for cat, items in missing_by_category.items():
            out.write(f"Category: {cat} - {len(items)} items\n")
            
except Exception as e:
    print('Failed:', e)

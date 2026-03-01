import re

def get_board_specs():
    specs = set()
    with open('BOARD.md', 'r') as f:
        for line in f:
            if '| P' in line:
                # Extract the component name inside parentheses if it exists
                # Format: | P4-COR003 | automation_timeline (AIBrain) | P0 | ...
                match = re.search(r'\|\s*[A-Z0-9-]+\s*\|\s*[^|]*\(([^)]+)\)', line)
                if match:
                    specs.add(match.group(1).strip().lower())
                else:
                    # Try to extract just the component name
                    match = re.search(r'\|\s*[A-Z0-9-]+\s*\|\s*([^|]+)\s*\|', line)
                    if match:
                        name = match.group(1).strip().lower()
                        # Clean up formatting like bolding or links
                        name = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', name)
                        name = name.replace('*', '').replace('`', '')
                        specs.add(name)
    return specs

def get_db_core_concepts():
    concepts = set()
    with open('core_concepts_dump.txt', 'r') as f:
        for line in f:
            parts = line.split('|')
            if len(parts) >= 2:
                # Clean up the title/name
                title = parts[1].strip()
                # Remove common prefixes/suffixes
                title = title.replace(' Effect', '').replace(' Node', '').replace(' Gen', '')
                if title and not title.isspace() and 'Init' not in title:
                    # Try converting CamelCase to snake_case or just keeping it flat
                    flat_name = title.replace(' ', '').lower()
                    concepts.add((flat_name, title))
    return concepts

board_specs = get_board_specs()
db_concepts = get_db_core_concepts()

missing = []
for flat_name, display_name in db_concepts:
    found = False
    for spec in board_specs:
        if flat_name in spec.replace(' ', '').replace('_', '').lower() or spec.replace(' ', '').replace('_', '').lower() in flat_name:
            found = True
            break
    if not found:
        missing.append(display_name)

print(f"Total specs on BOARD: {len(board_specs)}")
print(f"Total core concepts in DB: {len(db_concepts)}")
print(f"\nMissing concepts ({len(missing)}):")
for m in sorted(list(set(missing))):
    print(f"- {m}")


import urllib.request
import json

qdrant_url = "http://192.168.1.60:6333/collections/vjlive_code/points/scroll"
board_path = '/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/BOARD.md'

with open(board_path, "r") as f:
    board_data = f.read()

board_lines = [line.strip() for line in board_data.split('\n') if line.startswith('| P')]
board_names = set()
for line in board_lines:
    parts = line.split('|')
    if len(parts) >= 3:
        name_clean = parts[2].strip().lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "")
        board_names.add(name_clean)

missing_plugins = []
offset = None

while True:
    data = {"limit": 100, "with_payload": True, "with_vector": False}
    if offset:
        data["offset"] = offset

    req = urllib.request.Request(qdrant_url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            
            points = res_json.get("result", {}).get("points", [])
            for point in points:
                payload = point.get("payload", {})
                
                # Check different possible fields for name/id
                filename = payload.get("filename", "")
                filepath = payload.get("filepath", "")
                content = payload.get("content", "")
                
                # Try to guess a "plugin name" from the filename
                if filepath and "plugins/" in filepath and filepath.endswith(".py"):
                    base = filepath.split("/")[-1].replace(".py", "")
                    
                    name_norm = base.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "")
                    
                    found = False
                    for bn in board_names:
                        if name_norm in bn or bn in name_norm:
                            found = True
                            break
                            
                    if not found and base not in [mp["base"] for mp in missing_plugins]:
                        missing_plugins.append({
                            "base": base,
                            "filepath": filepath
                        })
                        
            offset = res_json.get("result", {}).get("next_page_offset")
            print(f"Scrolled {len(points)} points. Next offset: {offset}")
            if not offset:
                break
    except Exception as e:
        print("Error connecting to Qdrant:", e)
        break

print(f"Total missing legacy plugins found in Qdrant vjlive_code: {len(missing_plugins)}")
if len(missing_plugins) > 0:
    print("Examples:")
    for mp in missing_plugins[:10]:
        print(f" - {mp['base']} ({mp['filepath']})")

    with open("/tmp/missing_qdrant_legacy.json", "w") as f:
        json.dump(missing_plugins, f, indent=2)

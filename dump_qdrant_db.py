import urllib.request
import json
import os

qdrant_url = "http://192.168.1.60:6333/collections/vjlive_code/points/scroll"
output_file = "WORKSPACE/MEMORY_BANK/QDRANT_FULL_BACKUP.json"
os.makedirs(os.path.dirname(output_file), exist_ok=True)

all_points = []
offset = None

print("Starting full Qdrant DB extraction from Julie (192.168.1.60)...")

while True:
    data = {"limit": 100, "with_payload": True, "with_vector": True}
    if offset is not None:
        data["offset"] = offset

    req = urllib.request.Request(
        qdrant_url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            points = res_json.get("result", {}).get("points", [])
            
            if not points:
                break
                
            all_points.extend(points)
            offset = res_json.get("result", {}).get("next_page_offset")
            print(f"Captured {len(points)} points... (Total: {len(all_points)})")
            
            if not offset:
                break
    except Exception as e:
        print("Error reading from Qdrant:", e)
        break

with open(output_file, "w") as f:
    json.dump(all_points, f, indent=2)

print(f"Extraction complete. Saved {len(all_points)} total payload records to {output_file}.")

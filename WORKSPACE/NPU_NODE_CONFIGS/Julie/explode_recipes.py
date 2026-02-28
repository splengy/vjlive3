import json
import os
from pathlib import Path

JSON_PATH = '/mnt/library/cookbooks/wikibooks-cookbook/recipes_parsed.json'
OUTPUT_DIR = '/mnt/library/cookbooks/wikibooks-cookbook/individual'

os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f'Loading {JSON_PATH}...')
with open(JSON_PATH, 'r') as f:
    recipes = json.load(f)

print(f'Exploding {len(recipes)} recipes...')
for i, recipe in enumerate(recipes):
    data = recipe.get('recipe_data', {})
    title = data.get('title', f'Recipe {i}')
    filename = recipe.get('filename', f'recipe_{i}.txt').replace('/', '_').replace('.html', '.txt')
    
    # Construct content
    lines = [f'# {title}']
    url = data.get('url', '')
    if url: lines.append(f'Source: {url}')
    
    infobox = data.get('infobox', {})
    if infobox:
        lines.append('\n## Details')
        for k, v in infobox.items():
            if v: lines.append(f'- {k.capitalize()}: {v}')
    
    lines.append('\n## Ingredients / Steps')
    for line in data.get('text_lines', []):
        text = line.get('text', '').strip()
        if text: lines.append(text)
    
    content = '\n'.join(lines)
    
    out_path = Path(OUTPUT_DIR) / filename
    with open(out_path, 'w') as f:
        f.write(content)
    
    if (i+1) % 100 == 0:
        print(f'Processed {i+1}/{len(recipes)} recipes...')

print(f'Done! Files saved to {OUTPUT_DIR}')

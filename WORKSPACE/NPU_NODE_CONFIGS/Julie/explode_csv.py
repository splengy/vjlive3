import csv
import os
import sys
from pathlib import Path

# Set field size limit for large CSV fields
csv.field_size_limit(sys.maxsize)

OUTPUT_DIR = '/mnt/library/cookbooks/csv_exploded'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def explode_train_csv():
    path = '/mnt/library/cookbooks/cookGPT/train.csv'
    if not os.path.exists(path): return
    print(f'Exploding {path}...')
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            text = row.get('text', '').strip()
            if not text: continue
            filename = f'train_{i:04d}.txt'
            with open(Path(OUTPUT_DIR) / filename, 'w', encoding='utf-8') as out:
                out.write(text)
            if (i+1) % 500 == 0: print(f'  Processed {i+1} rows...')

def explode_data_csv():
    path = '/mnt/library/cookbooks/CookingRecipes/Data.csv'
    if not os.path.exists(path): return
    print(f'Exploding {path}...')
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            title = row.get('title', f'Recipe {i}').strip()
            ingredients = row.get('ingredients', '').strip()
            directions = row.get('directions', '').strip()
            link = row.get('link', '').strip()
            
            content = f'# {title}\n\n'
            if link: content += f'Source: {link}\n\n'
            
            content += '## Ingredients\n'
            # Simple cleaning of stringified lists
            ings = ingredients.replace('[', '').replace(']', '').replace('"', '').split(', ')
            content += '\n'.join([f'- {ing.strip()}' for ing in ings if ing.strip()])
                
            content += '\n\n## Directions\n'
            dirs = directions.replace('[', '').replace(']', '').replace('"', '').split('., ')
            for j, step in enumerate(dirs):
                step = step.strip()
                if step:
                    if not step.endswith('.'): step += '.'
                    content += f'{j+1}. {step}\n'
                
            filename = f'recipe_csv_{i:04d}.txt'
            with open(Path(OUTPUT_DIR) / filename, 'w', encoding='utf-8') as out:
                out.write(content)
            if (i+1) % 500 == 0: print(f'  Processed {i+1} rows...')

if __name__ == "__main__":
    try:
        explode_train_csv()
        explode_data_csv()
        print(f'Done! Files in {OUTPUT_DIR}')
    except Exception as e:
        print(f'Fatal Error: {e}')

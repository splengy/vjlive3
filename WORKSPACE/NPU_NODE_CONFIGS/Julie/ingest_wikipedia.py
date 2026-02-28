#!/usr/bin/env python3
import time
import requests
import json
import logging
import argparse
from pathlib import Path
from libzim.reader import Archive
from libzim.search import Query, Searcher
from bs4 import BeautifulSoup

# Julie's Local RAG API
RAG_API_URL = "http://127.0.0.1:8080/ingest" 
# DIRECT DB ACCESS (If faster than API for bulk):
# We will use API for now to ensure consistency, but might need direct DB for speed.

# CONFIG
ZIM_PATH = Path("/home/happy/ai_library_stable/wikipedia/wikipedia_en_all_maxi.zim")
CHUNK_SIZE = 1000 # ingest 1000 articles per batch
CHECKPOINT_FILE = Path("/home/happy/wiki_checkpoint.txt")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_checkpoint():
    if CHECKPOINT_FILE.exists():
        try:
            return int(CHECKPOINT_FILE.read_text().strip())
        except:
            return 0
    return 0

def save_checkpoint(index):
    CHECKPOINT_FILE.write_text(str(index))

def clean_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    # minimal cleaning for speed
    text = soup.get_text(separator=' ', strip=True)
    return text

def ingest_zim(zim_path, start_index=0, limit=None):
    if not zim_path.exists():
        logging.error(f"ZIM file not found: {zim_path}")
        return

    logging.info(f"Opening ZIM: {zim_path}")
    zim = Archive(str(zim_path))
    total_articles = zim.entry_count
    logging.info(f"Total Entries: {total_articles}")

    current_idx = start_index
    processed = 0

    while current_idx < total_articles:
        if limit and processed >= limit:
            break

        try:
            entry = zim._get_entry_by_id(current_idx)
            if not entry.is_redirect:
                item = entry.get_item()
                if item.mimetype == 'text/html':
                    title = entry.title
                content = item.content.tobytes() # returns bytes
                
                # We want HTML/Text. 
                # ZIM content is often HTML.
                try:
                    text_content = clean_html(content)
                    if len(text_content) > 100: # Skip stubs
                        # Send to Julie's Memory/RAG
                        payload = {
                            "subject": f"Wiki: {title}",
                            "content": text_content[:5000], # Truncate massive articles for now
                            "media_type": "text/wiki",
                            "source": "wikipedia_zim"
                        }
                        r = requests.post(RAG_API_URL, json=payload)
                        logging.info(f"Ingested [{current_idx}] {title} - Status: {r.status_code}")
                except Exception as e:
                    logging.warning(f"Error parsing {title}: {e}")

        except Exception as e:
            logging.error(f"Error reading index {current_idx}: {e}")

        current_idx += 1
        processed += 1
        
        if processed % 100 == 0:
            save_checkpoint(current_idx)
            logging.info(f"Checkpoint saved at {current_idx}")

    save_checkpoint(current_idx)
    logging.info("Ingestion Complete (or limit reached).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Limit number of articles")
    args = parser.parse_args()

    start = get_checkpoint()
    ingest_zim(ZIM_PATH, start_index=start, limit=args.limit)

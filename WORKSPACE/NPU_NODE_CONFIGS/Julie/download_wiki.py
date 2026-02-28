import os
import requests
import sys
import time
from pathlib import Path

# URL for the maximized English Wikipedia ZIM (Caution: ~100GB+)
# Using a mirror or direct link. Kiwix official dump.
URL = "https://download.kiwix.org/zim/wikipedia/wikipedia_en_all_maxi.zim"

# Path to save
# Adjust this if you want it elsewhere, but this matches ingest_wikipedia.py config
# Adjust this if you want it elsewhere, but this matches ingest_wikipedia.py config
if os.name == 'nt':
    DEST_DIR = Path(r"C:\Users\Happy\ai_library_stable\wikipedia")
else:
    DEST_DIR = Path("/home/happy/ai_library_stable/wikipedia")

FILENAME = "wikipedia_en_all_maxi.zim"
DEST_PATH = DEST_DIR / FILENAME

def download_file():
    if not DEST_DIR.exists():
        print(f"Creating directory: {DEST_DIR}")
        DEST_DIR.mkdir(parents=True, exist_ok=True)

    # Check existing size for resume
    resume_byte_pos = 0
    if DEST_PATH.exists():
        resume_byte_pos = DEST_PATH.stat().st_size
        print(f"Found existing file: {resume_byte_pos / (1024*1024*1024):.2f} GB")
        print("Resuming download...")
    else:
        print("Starting new download...")

    headers = {}
    if resume_byte_pos > 0:
        headers = {'Range': f'bytes={resume_byte_pos}-'}

    try:
        # Stream response
        r = requests.get(URL, stream=True, headers=headers, timeout=60)
        
        # Handle 416 Range Not Satisfiable (file might be complete)
        if r.status_code == 416:
            print("Download appears complete (Server returned 416).")
            return

        r.raise_for_status()

        total_size = int(r.headers.get('content-length', 0)) + resume_byte_pos
        print(f"Total Size: {total_size / (1024*1024*1024):.2f} GB")

        with open(DEST_PATH, "ab") as f:
            start_time = time.time()
            downloaded_bytes = 0
            
            for chunk in r.iter_content(chunk_size=1024*1024): # 1MB chunks
                if chunk:
                    f.write(chunk)
                    downloaded_bytes += len(chunk)
                    
                    # Status update
                    current_size = resume_byte_pos + downloaded_bytes
                    elapsed = time.time() - start_time
                    speed = downloaded_bytes / elapsed if elapsed > 0 else 0
                    percent = (current_size / total_size) * 100 if total_size > 0 else 0
                    
                    sys.stdout.write(f"\rProgress: {percent:.2f}% | {current_size / (1024**3):.2f} GB | Speed: {speed / (1024**2):.2f} MB/s")
                    sys.stdout.flush()

        print("\nDownload Complete!")

    except KeyboardInterrupt:
        print("\nDownload paused (interrupted by user).")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    download_file()

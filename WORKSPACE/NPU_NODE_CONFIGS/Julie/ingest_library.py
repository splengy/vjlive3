#!/usr/bin/env python3
"""
Multimodal Library Ingestor for Julie
Recursively scans /mnt/library/cookbooks and indexes various formats into ChromaDB.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Configuration
SOURCE_DIR = Path("/mnt/library/cookbooks")
DB_DIR = Path("/home/happy/ai_library_stable/vector_db")
LOG_FILE = "/home/happy/ingest_debug.log"

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_vector_db():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return Chroma(persist_directory=str(DB_DIR), embedding_function=embeddings)

def process_parquet(file_path):
    """Process HuggingFace parquet datasets in chunks."""
    try:
        df = pd.read_parquet(file_path) # Parquet is usually small or already partitioned
        text_cols = df.select_dtypes(include=['object', 'string']).columns
        for i, row in df.iterrows():
            content = " ".join([str(row[col]) for col in text_cols if pd.notnull(row[col])])
            if len(content.strip()) > 50:
                yield Document(
                    page_content=content,
                    metadata={"source": str(file_path), "format": "parquet", "row": i}
                )
    except Exception as e:
        logging.error(f"Error processing Parquet {file_path}: {e}")

def process_csv(file_path):
    """Process massive CSV files in chunks."""
    try:
        logging.info(f"Steaming CSV: {file_path}")
        chunk_iter = pd.read_csv(file_path, chunksize=1000, on_bad_lines='skip')
        for chunk in chunk_iter:
            text_cols = chunk.select_dtypes(include=['object', 'string']).columns
            for i, row in chunk.iterrows():
                content = " ".join([str(row[col]) for col in text_cols if pd.notnull(row[col])])
                if len(content.strip()) > 50:
                    yield Document(
                        page_content=content,
                        metadata={"source": str(file_path), "format": "csv", "row": i}
                    )
    except Exception as e:
        logging.error(f"Error processing CSV {file_path}: {e}")

def process_pdf(file_path):
    """Process PDF documents page-by-page."""
    try:
        reader = PdfReader(file_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and len(text.strip()) > 50:
                yield Document(
                    page_content=text,
                    metadata={"source": str(file_path), "format": "pdf", "page": i}
                )
    except Exception as e:
        logging.error(f"Error processing PDF {file_path}: {e}")

def process_html(file_path):
    """Process HTML files."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            if len(text.strip()) > 50:
                yield Document(
                    page_content=text,
                    metadata={"source": str(file_path), "format": "html"}
                )
    except Exception as e:
        logging.error(f"Error processing HTML {file_path}: {e}")

def process_json(file_path):
    """Process JSON and JSONL files."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Check if it's JSONL or JSON
            first_line = f.readline()
            f.seek(0)
            try:
                json.loads(first_line)
                # JSONL
                for i, line in enumerate(f):
                    data = json.loads(line)
                    yield Document(
                        page_content=json.dumps(data, indent=2),
                        metadata={"source": str(file_path), "format": "jsonl", "line": i}
                    )
            except:
                # Regular JSON
                data = json.load(f)
                yield Document(
                    page_content=json.dumps(data, indent=2),
                    metadata={"source": str(file_path), "format": "json"}
                )
    except Exception as e:
        logging.error(f"Error processing JSON {file_path}: {e}")

def main():
    print(f"🚀 Starting Stream-Based Ingestion from {SOURCE_DIR}...")
    logging.info("Starting stream-based mass ingestion...")
    
    vector_db = get_vector_db()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    total_files = 0
    total_chunks = 0
    
    for root, _, files in os.walk(SOURCE_DIR):
        for file in files:
            file_path = Path(root) / file
            ext = file_path.suffix.lower()
            
            generator = None
            if ext == '.parquet': generator = process_parquet(file_path)
            elif ext == '.csv': generator = process_csv(file_path)
            elif ext == '.pdf': generator = process_pdf(file_path)
            elif ext == '.html': generator = process_html(file_path)
            elif ext in ['.json', '.jsonl']: generator = process_json(file_path)
            elif ext in ['.txt', '.md']:
                try:
                    text = file_path.read_text(encoding='utf-8')
                    generator = (Document(page_content=text, metadata={"source": str(file_path), "format": ext[1:]}) for _ in range(1))
                except: continue

            if generator:
                print(f"\n[FILE] Processing {file_path}...")
                total_files += 1
                doc_batch = []
                try:
                    for doc in generator:
                        doc_batch.append(doc)
                        if len(doc_batch) >= 100:
                            split_docs = splitter.split_documents(doc_batch)
                            vector_db.add_documents(split_docs)
                            total_chunks += len(split_docs)
                            doc_batch = []
                            print(f"    -> Progress: {total_chunks} total chunks indexed", end='\r')
                except Exception as e:
                    print(f"\n[ERROR] Failed to process {file}: {e}")
                    logging.error(f"Failed to process {file}: {e}")
                
                if doc_batch:
                    split_docs = splitter.split_documents(doc_batch)
                    vector_db.add_documents(split_docs)
                    total_chunks += len(split_docs)
                
                print(f"  Indexed {file}. TotalChunks: {total_chunks}")
                logging.info(f"Completed {file_path}. TotalChunks: {total_chunks}")

    print(f"\n✅ All files processed. Total indexed: {total_chunks} chunks.")

if __name__ == "__main__":
    main()


"""
Persistent Conversation Memory System
Stores conversations with unique IDs, names, and enables cross-conversation recall.
"""

import sqlite3
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import logging
import traceback

# Setup logging
logging.basicConfig(
    filename='/home/happy/memory_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Storage paths
MEMORY_DIR = Path("/home/happy/ai_library_stable/memory_db") # Use absolute path
DB_PATH = MEMORY_DIR / "conversations.db"
VECTOR_DIR = MEMORY_DIR / "memory_vectors"

# Lazy-loaded embeddings and vector store
_embeddings = None
_vector_db = None

def get_vector_db():
    """Get or initialize the ChromaDB vector store for semantic search."""
    global _embeddings, _vector_db
    if _vector_db is None:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            from langchain_community.vectorstores import Chroma
            
            logging.info(f"Initializing vector DB at {VECTOR_DIR}...")
            if not MEMORY_DIR.exists():
                logging.warning(f"MEMORY_DIR {MEMORY_DIR} does not exist!")
            
            _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            _vector_db = Chroma(
                persist_directory=str(VECTOR_DIR),
                embedding_function=_embeddings,
                collection_name="conversation_memories"
            )
            logging.info(f"Memory vectors initialized. Count: {_vector_db._collection.count()}")
        except Exception as e:
            logging.error(f"Could not initialize vector DB: {e}\n{traceback.format_exc()}")
            return None
    return _vector_db

def init_database():
    """Initialize SQLite database with comprehensive schema."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Main conversation record
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        
        -- Categorization
        tags TEXT,
        category TEXT,
        project TEXT,
        
        -- Status & Priority
        status TEXT DEFAULT 'active',
        priority INTEGER DEFAULT 0,
        is_favorite INTEGER DEFAULT 0,
        
        -- Relationships
        parent_id TEXT,
        related_ids TEXT,
        
        -- AI-generated metadata
        summary TEXT,
        key_topics TEXT,
        scenario TEXT,
        sentiment TEXT,
        
        -- Stats
        message_count INTEGER DEFAULT 0,
        total_tokens INTEGER DEFAULT 0
    )
    """)
    
    # Individual messages
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id TEXT NOT NULL,
        
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP,
        
        -- Media & Attachments
        media_urls TEXT,
        media_types TEXT,
        
        -- Citations & Sources
        citations TEXT,
        web_sources TEXT,
        rag_sources TEXT,
        
        -- Metadata
        sentiment TEXT,
        confidence REAL,
        token_count INTEGER,
        embedding_id TEXT,
        
        -- Editing & Versioning
        edited_at TIMESTAMP,
        edit_count INTEGER DEFAULT 0,
        original_content TEXT,
        
        -- Flags
        is_pinned INTEGER DEFAULT 0,
        is_hidden INTEGER DEFAULT 0,
        
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
    )
    """)
    
    # Media attachments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS media_attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id INTEGER,
        conversation_id TEXT,
        
        file_path TEXT,
        file_url TEXT,
        file_type TEXT,
        file_name TEXT,
        file_size INTEGER,
        mime_type TEXT,
        
        description TEXT,
        extracted_text TEXT,
        
        created_at TIMESTAMP,
        
        FOREIGN KEY (message_id) REFERENCES messages(id),
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
    )
    """)
    
    # Conversation links
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversation_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id TEXT NOT NULL,
        target_id TEXT NOT NULL,
        link_type TEXT,
        created_at TIMESTAMP,
        notes TEXT,
        
        FOREIGN KEY (source_id) REFERENCES conversations(id),
        FOREIGN KEY (target_id) REFERENCES conversations(id)
    )
    """)
    
    # Tags
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        color TEXT,
        created_at TIMESTAMP
    )
    """)
    
    # Participants
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id TEXT,
        agent_name TEXT,
        role TEXT,
        joined_at TIMESTAMP,
        
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
    )
    """)
    
    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_status ON conversations(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_project ON conversations(project)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_msg_time ON messages(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_conv ON media_attachments(conversation_id)")
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def get_connection():
    """Get database connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============ Conversation CRUD ============

def create_conversation(
    name: str,
    description: str = None,
    tags: List[str] = None,
    category: str = None,
    project: str = None,
    parent_id: str = None
) -> Dict[str, Any]:
    """Create a new conversation with unique ID."""
    conv_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO conversations 
        (id, name, description, created_at, updated_at, tags, category, project, parent_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        conv_id, name, description, now, now,
        json.dumps(tags) if tags else None,
        category, project, parent_id
    ))
    
    conn.commit()
    conn.close()
    
    return {"id": conv_id, "name": name, "created_at": now}

def list_conversations(
    status: str = "active",
    project: str = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """List conversations with optional filters."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM conversations WHERE status = ?"
    params = [status]
    
    if project:
        query += " AND project = ?"
        params.append(project)
    
    query += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_conversation(conv_id: str = None, name: str = None) -> Optional[Dict[str, Any]]:
    """Get conversation by ID or name."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if conv_id:
        cursor.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
    elif name:
        cursor.execute("SELECT * FROM conversations WHERE name = ?", (name,))
    else:
        return None
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None

def update_conversation(conv_id: str, **updates) -> bool:
    """Update conversation fields."""
    if not updates:
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Build dynamic update query
    set_clauses = ", ".join([f"{k} = ?" for k in updates.keys()])
    set_clauses += ", updated_at = ?"
    
    values = list(updates.values()) + [datetime.now().isoformat(), conv_id]
    
    cursor.execute(
        f"UPDATE conversations SET {set_clauses} WHERE id = ?",
        values
    )
    
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    
    return success

# ============ Message Operations ============

def save_message(
    conversation_id: str,
    role: str,
    content: str,
    media_urls: List[str] = None,
    citations: List[str] = None,
    web_sources: List[str] = None,
    rag_sources: List[str] = None,
    token_count: int = None
) -> int:
    """Save a message to a conversation."""
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO messages 
        (conversation_id, role, content, timestamp, media_urls, citations, 
         web_sources, rag_sources, token_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        conversation_id, role, content, now,
        json.dumps(media_urls) if media_urls else None,
        json.dumps(citations) if citations else None,
        json.dumps(web_sources) if web_sources else None,
        json.dumps(rag_sources) if rag_sources else None,
        token_count
    ))
    
    message_id = cursor.lastrowid
    
    # Update conversation stats
    cursor.execute("""
        UPDATE conversations 
        SET message_count = message_count + 1, updated_at = ?
        WHERE id = ?
    """, (now, conversation_id))
    
    conn.commit()
    conn.close()
    
    return message_id

def get_messages(
    conversation_id: str,
    limit: int = 100,
    include_hidden: bool = False
) -> List[Dict[str, Any]]:
    """Get messages for a conversation."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM messages WHERE conversation_id = ?"
    if not include_hidden:
        query += " AND is_hidden = 0"
    query += " ORDER BY timestamp ASC LIMIT ?"
    
    cursor.execute(query, (conversation_id, limit))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_recent_messages(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent messages across all conversations."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT m.*, c.name as conversation_name
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        WHERE m.is_hidden = 0
        ORDER BY m.timestamp DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

# ============ Linking & Relationships ============

def link_conversations(
    source_id: str,
    target_id: str,
    link_type: str = "related",
    notes: str = None
) -> int:
    """Create a link between two conversations."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO conversation_links (source_id, target_id, link_type, created_at, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (source_id, target_id, link_type, datetime.now().isoformat(), notes))
    
    link_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return link_id

def get_related_conversations(conv_id: str) -> List[Dict[str, Any]]:
    """Get conversations related to a given one."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.*, cl.link_type, cl.notes
        FROM conversations c
        JOIN conversation_links cl ON c.id = cl.target_id
        WHERE cl.source_id = ?
        UNION
        SELECT c.*, cl.link_type, cl.notes
        FROM conversations c
        JOIN conversation_links cl ON c.id = cl.source_id
        WHERE cl.target_id = ?
    """, (conv_id, conv_id))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

# ============ Semantic Search ============

def embed_message(message_id: int, conversation_id: str, conversation_name: str, 
                  role: str, content: str) -> bool:
    """Embed a message in the vector database for semantic search."""
    logging.info(f"Embedding message {message_id} from '{conversation_name}' (Role: {role})")
    
    vector_db = get_vector_db()
    if vector_db is None:
        logging.error("Failed to embed: vector_db is None")
        return False
    
    try:
        # Robust Document import
        try:
            from langchain_core.documents import Document
        except ImportError:
            from langchain.schema import Document
        
        # Create document with metadata
        doc = Document(
            page_content=content,
            metadata={
                "message_id": message_id,
                "conversation_id": conversation_id,
                "conversation_name": conversation_name,
                "role": role,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Add to vector store
        logging.debug(f"Adding document to Chroma for msg {message_id}...")
        vector_db.add_documents([doc])
        
        # Force persistence if method exists
        if hasattr(vector_db, 'persist'):
            vector_db.persist()
            logging.debug("Vector DB persisted.")
        
        # Update message with embedding reference in SQLite
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE messages SET embedding_id = ? WHERE id = ?",
            (f"chroma_{message_id}", message_id)
        )
        conn.commit()
        conn.close()
        
        logging.info(f"Successfully embedded message {message_id}")
        return True
    except Exception as e:
        logging.error(f"Error embedding message {message_id}: {e}\n{traceback.format_exc()}")
        return False


def semantic_search(query: str, limit: int = 5, 
                    conversation_id: str = None) -> List[Dict[str, Any]]:
    """Search for semantically similar messages across conversations."""
    vector_db = get_vector_db()
    if vector_db is None:
        return []
    
    try:
        # Search with optional filter
        filter_dict = None
        if conversation_id:
            filter_dict = {"conversation_id": conversation_id}
        
        results = vector_db.similarity_search_with_score(query, k=limit, filter=filter_dict)
        
        memories = []
        for doc, score in results:
            memories.append({
                "content": doc.page_content,
                "conversation_id": doc.metadata.get("conversation_id"),
                "conversation_name": doc.metadata.get("conversation_name"),
                "role": doc.metadata.get("role"),
                "timestamp": doc.metadata.get("timestamp"),
                "similarity": 1 - score  # Convert distance to similarity
            })
        
        return memories
    except Exception as e:
        print(f"Error in semantic search: {e}")
        return []

def recall_memories(query: str, limit: int = 5) -> str:
    """Search memories and format as context string for LLM."""
    memories = semantic_search(query, limit=limit)
    
    if not memories:
        return ""
    
    context = "--- PAST MEMORIES ---\n"
    for mem in memories:
        context += f"[{mem['conversation_name']} - {mem['role']}]: {mem['content'][:300]}...\n\n"
    
    return context

# Initialize on import
if __name__ == "__main__":
    init_database()
    print("Memory system ready!")


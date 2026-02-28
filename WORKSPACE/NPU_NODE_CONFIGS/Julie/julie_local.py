"""
Julie - Search + Memory Service
Provides RAG (local files + web) and persistent conversation memory.
Now with Tavily Search for LLM-optimized web results.
"""

import os
import re
import json
from datetime import datetime
from flask import Flask, request, jsonify
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from pathlib import Path
import memory

# Tavily Search (primary)
try:
    from tavily import TavilyClient
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None
    if tavily_client:
        print("✓ Tavily Search initialized")
    else:
        print("⚠ Tavily API key not set (TAVILY_API_KEY env var)")
except ImportError:
    tavily_client = None
    print("⚠ Tavily not installed (pip install tavily-python)")

# DuckDuckGo Search (fallback)
try:
    from ddgs import DDGS
    ddg_available = True
except ImportError:
    ddg_available = False

app = Flask(__name__)

# File RAG config
DB_DIR = Path("/home/happy/ai_library_stable/vector_db")
USAGE_FILE = Path("/home/happy/ai_library_stable/api_usage.json")
embeddings = None
vector_db = None

# ============ API Usage Tracking ============

def load_usage():
    """Load API usage stats from file."""
    if USAGE_FILE.exists():
        with open(USAGE_FILE, 'r') as f:
            return json.load(f)
    return {
        "tavily": {
            "total_calls": 0,
            "calls_this_month": 0,
            "monthly_limit": 1000,
            "last_reset": datetime.now().strftime("%Y-%m")
        }
    }

def save_usage(usage):
    """Save API usage stats to file."""
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USAGE_FILE, 'w') as f:
        json.dump(usage, f, indent=2)

def increment_tavily_usage():
    """Increment Tavily usage counter, reset monthly if needed."""
    usage = load_usage()
    current_month = datetime.now().strftime("%Y-%m")
    
    # Reset monthly counter if new month
    if usage["tavily"].get("last_reset") != current_month:
        usage["tavily"]["calls_this_month"] = 0
        usage["tavily"]["last_reset"] = current_month
    
    usage["tavily"]["total_calls"] += 1
    usage["tavily"]["calls_this_month"] += 1
    save_usage(usage)
    return usage["tavily"]

def tavily_quota_ok():
    """Check if we haven't exceeded Tavily monthly quota."""
    usage = load_usage()
    current_month = datetime.now().strftime("%Y-%m")
    if usage["tavily"].get("last_reset") != current_month:
        return True  # New month, quota reset
    return usage["tavily"]["calls_this_month"] < usage["tavily"]["monthly_limit"]

def init_rag():
    global embeddings, vector_db
    if embeddings is None:
        print("Loading embedding model...")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vector_db = Chroma(persist_directory=str(DB_DIR), embedding_function=embeddings)
        print(f"ChromaDB loaded with {vector_db._collection.count()} documents")

# ============ Search Endpoints ============

@app.route("/search", methods=["POST"])
def search():
    """Combined RAG + Web search with source metadata."""
    data = request.json
    query = data.get("query", "")
    print(f"Received query: {query}")
    
    if not query:
        return jsonify({"results": "No query provided.", "sources": {}}), 400

    context = ""
    web_search_error = None
    
    # Source tracking
    sources = {
        "web": [],
        "local": [],
        "images": [],
        "has_web": False,
        "has_local": False
    }
    
    # 1. Search local files (ChromaDB)
    try:
        init_rag()
        docs = vector_db.similarity_search(query, k=3)
        if docs:
            sources["has_local"] = True
            context += "--- LOCAL LIBRARY ---\n"
            for doc in docs:
                source_path = doc.metadata.get("source", "unknown")
                doc_type = doc.metadata.get("format", "unknown")
                subject = doc.metadata.get("subject", "")
                
                # Add to sources list
                sources["local"].append({
                    "path": source_path,
                    "type": doc_type,
                    "subject": subject,
                    "snippet": doc.page_content[:200]
                })
                
                context += f"[{source_path}]: {doc.page_content[:500]}...\n\n"
    except Exception as e:
        print(f"RAG error: {e}")
    
    # 2. Search web (Tavily primary, DDG fallback)
    # Detect if query mentions a specific domain
    domain_match = re.search(r'([\w-]+\.(com|org|net|io|gov|edu))', query.lower())
    include_domains = [domain_match.group(1)] if domain_match else None
    
    web_results = None
    tavily_answer = None
    
    # Try Tavily first
    if tavily_client and tavily_quota_ok():
        try:
            print(f"[Tavily] Searching: {query}")
            if include_domains:
                print(f"[Tavily] Restricting to domains: {include_domains}")
            
            response = tavily_client.search(
                query,
                max_results=3,
                include_answer=True,
                include_images=True,
                include_image_descriptions=True,
                search_depth="advanced",
                include_domains=include_domains
            )
            
            usage = increment_tavily_usage()
            print(f"[Tavily] Success! (calls this month: {usage['calls_this_month']}/{usage['monthly_limit']})")
            
            web_results = response.get("results", [])
            tavily_answer = response.get("answer")
            
            # Capture images from Tavily
            tavily_images = response.get("images", [])
            if tavily_images:
                print(f"[Tavily] Found {len(tavily_images)} images")
                for img in tavily_images[:5]:  # Limit to 5 images
                    if isinstance(img, dict):
                        sources["images"].append({
                            "url": img.get("url", ""),
                            "description": img.get("description", "")
                        })
                    elif isinstance(img, str):
                        sources["images"].append({"url": img, "description": ""})
            
        except Exception as e:
            print(f"[Tavily] Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Fallback to DDG if Tavily failed/unavailable
    if not web_results and ddg_available:
        try:
            print(f"[DDG Fallback] Searching: {query}")
            ddgs = DDGS()
            ddg_results = list(ddgs.text(query, max_results=3))
            web_results = [
                {"url": r.get("href", ""), "title": r.get("title", ""), "content": r.get("body", "")}
                for r in ddg_results
            ]
            print(f"[DDG] Got {len(web_results)} results")
        except Exception as e:
            web_search_error = str(e)
            print(f"[DDG] Error: {e}")
    
    # Process web results
    if web_results:
        sources["has_web"] = True
        context += "--- WEB SEARCH ---\n"
        
        # Add Tavily's AI answer first if available
        if tavily_answer:
            context += f"AI Summary: {tavily_answer}\n\n"
        
        for r in web_results:
            sources["web"].append({
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "snippet": r.get("content", "")[:200]
            })
            # Tavily returns full content, DDG returns snippets
            content = r.get("content", "") or r.get("snippet", "")
            context += f"Title: {r.get('title', 'Unknown')}\nContent: {content[:500]}\n\n"
    elif not sources["has_local"]:
        web_search_error = web_search_error or "No web results found"
    
    if not context:
        if web_search_error:
            context = f"No results found. Web search error: {web_search_error}"
        else:
            context = "No results found from library or web."
        
    return jsonify({"results": context, "sources": sources})

@app.route("/ingest", methods=["POST"])
def ingest_document():
    """Ingest a document directly into ChromaDB for RAG."""
    data = request.json
    content = data.get("content", "")
    subject = data.get("subject", "Unknown")
    source = data.get("source", "unknown")
    media_type = data.get("media_type", "text/plain")
    
    if not content:
        return jsonify({"error": "content required"}), 400
    
    try:
        init_rag()
        # Add document to vector store
        from langchain_core.documents import Document
        doc = Document(
            page_content=content,
            metadata={
                "source": source,
                "subject": subject,
                "media_type": media_type
            }
        )
        vector_db.add_documents([doc])
        return jsonify({"success": True, "subject": subject})
    except Exception as e:
        print(f"Ingest error: {e}")
        return jsonify({"error": str(e)}), 500

# ============ API Usage Endpoint ============

@app.route("/api-usage", methods=["GET"])
def api_usage():
    """Get API usage statistics."""
    usage = load_usage()
    tavily = usage.get("tavily", {})
    
    # Check if we need to show reset (new month)
    current_month = datetime.now().strftime("%Y-%m")
    if tavily.get("last_reset") != current_month:
        calls_this_month = 0
    else:
        calls_this_month = tavily.get("calls_this_month", 0)
    
    monthly_limit = tavily.get("monthly_limit", 1000)
    
    return jsonify({
        "tavily": {
            "calls_this_month": calls_this_month,
            "monthly_limit": monthly_limit,
            "remaining": monthly_limit - calls_this_month,
            "total_all_time": tavily.get("total_calls", 0),
            "last_reset": tavily.get("last_reset", "never")
        },
        "tavily_available": tavily_client is not None,
        "ddg_available": ddg_available
    })

# ============ Memory Endpoints ============

@app.route("/memory/new", methods=["POST"])
def memory_new():
    """Create a new conversation."""
    data = request.json
    name = data.get("name", "Unnamed Conversation")
    description = data.get("description")
    tags = data.get("tags")
    category = data.get("category")
    project = data.get("project")
    parent_id = data.get("parent_id")
    
    result = memory.create_conversation(
        name=name,
        description=description,
        tags=tags,
        category=category,
        project=project,
        parent_id=parent_id
    )
    return jsonify(result)

@app.route("/memory/list", methods=["GET"])
def memory_list():
    """List all conversations."""
    status = request.args.get("status", "active")
    project = request.args.get("project")
    limit = int(request.args.get("limit", 50))
    
    conversations = memory.list_conversations(status=status, project=project, limit=limit)
    return jsonify({"conversations": conversations})

@app.route("/memory/get", methods=["POST"])
def memory_get():
    """Get a specific conversation by ID or name."""
    data = request.json
    conv_id = data.get("id")
    name = data.get("name")
    
    conv = memory.get_conversation(conv_id=conv_id, name=name)
    if conv:
        messages = memory.get_messages(conv["id"])
        return jsonify({"conversation": conv, "messages": messages})
    return jsonify({"error": "Conversation not found"}), 404

@app.route("/memory/save", methods=["POST"])
def memory_save():
    """Save a message to a conversation."""
    data = request.json
    conversation_id = data.get("conversation_id")
    role = data.get("role", "user")
    content = data.get("content", "")
    media_urls = data.get("media_urls")
    citations = data.get("citations")
    web_sources = data.get("web_sources")
    rag_sources = data.get("rag_sources")
    
    if not conversation_id or not content:
        return jsonify({"error": "conversation_id and content required"}), 400
    
    message_id = memory.save_message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        media_urls=media_urls,
        citations=citations,
        web_sources=web_sources,
        rag_sources=rag_sources
    )
    return jsonify({"message_id": message_id})

@app.route("/memory/update", methods=["POST"])
def memory_update():
    """Update conversation metadata."""
    data = request.json
    conv_id = data.pop("id", None)
    
    if not conv_id:
        return jsonify({"error": "id required"}), 400
    
    success = memory.update_conversation(conv_id, **data)
    return jsonify({"success": success})

@app.route("/memory/link", methods=["POST"])
def memory_link():
    """Link two conversations."""
    data = request.json
    source_id = data.get("source_id")
    target_id = data.get("target_id")
    link_type = data.get("link_type", "related")
    notes = data.get("notes")
    
    if not source_id or not target_id:
        return jsonify({"error": "source_id and target_id required"}), 400
    
    link_id = memory.link_conversations(source_id, target_id, link_type, notes)
    return jsonify({"link_id": link_id})

@app.route("/memory/related", methods=["POST"])
def memory_related():
    """Get related conversations."""
    data = request.json
    conv_id = data.get("id")
    
    if not conv_id:
        return jsonify({"error": "id required"}), 400
    
    related = memory.get_related_conversations(conv_id)
    return jsonify({"related": related})

@app.route("/memory/recent", methods=["GET"])
def memory_recent():
    """Get recent messages across all conversations."""
    limit = int(request.args.get("limit", 20))
    messages = memory.get_recent_messages(limit=limit)
    return jsonify({"messages": messages})

@app.route("/memory/recall", methods=["POST"])
def memory_recall():
    """Semantic search across all conversation memories."""
    data = request.json
    query = data.get("query", "")
    limit = data.get("limit", 5)
    conversation_id = data.get("conversation_id")  # Optional: filter to specific conv
    
    if not query:
        return jsonify({"error": "query required"}), 400
    
    memories = memory.semantic_search(query, limit=limit, conversation_id=conversation_id)
    return jsonify({"memories": memories})

@app.route("/memory/embed", methods=["POST"])
def memory_embed():
    """Embed a message for semantic search."""
    data = request.json
    message_id = data.get("message_id")
    conversation_id = data.get("conversation_id")
    conversation_name = data.get("conversation_name", "Unknown")
    role = data.get("role")
    content = data.get("content")
    
    if not all([message_id, conversation_id, role, content]):
        return jsonify({"error": "message_id, conversation_id, role, and content required"}), 400
    
    success = memory.embed_message(message_id, conversation_id, conversation_name, role, content)
    return jsonify({"success": success})

# ============ Startup ============

if __name__ == "__main__":
    print("Initializing memory database...")
    memory.init_database()
    print("Starting Julie with File RAG + Web Search + Memory + Semantic Recall...")
    app.run(host="0.0.0.0", port=8080)


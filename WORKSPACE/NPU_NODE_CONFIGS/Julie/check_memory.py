#!/usr/bin/env python3
import sqlite3
conn = sqlite3.connect("/home/happy/ai_library_stable/memory_db/conversations.db")
c = conn.cursor()
print("=== CONVERSATIONS ===")
c.execute("SELECT id, name, message_count, created_at FROM conversations")
for row in c.fetchall():
    print(f"  {row[1]} ({row[2]} msgs) - {row[0][:8]}...")
print("\n=== MESSAGES ===")
c.execute("SELECT conversation_id, role, content, embedding_id FROM messages ORDER BY timestamp DESC LIMIT 5")
for row in c.fetchall():
    emb = "✅" if row[3] else "❌"
    print(f"  {emb} [{row[1]}]: {row[2][:60]}...")
conn.close()

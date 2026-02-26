#!/usr/bin/env python3
"""
Test the Phase 4 Database-Backed Pipeline via vjlive-switchboard.
"""
import sys
import os

# We need to import the switchboard DB functions directly to test it locally
# since the MCP server runs out-of-process in Roo.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp_servers", "vjlive_switchboard"))
from server import VJLiveSwitchboard

def run_test():
    print("🧪 Testing new vjlive-switchboard pipeline...")
    
    sb = VJLiveSwitchboard()
    
    # 1. Backup and clear the queue for test
    original_tasks = sb._tasks.copy()
    sb._tasks.clear()
    sb._persist_tasks_to_disk()
    
    # 2. Manager queues a task
    print("\n1️⃣ Manager: Queueing task P3-EXT999")
    spec_path = "docs/specs/P3-EXT999_spec.md"
    ok = sb.queue_task("P3-EXT999", spec_path)
    print(f"   Result: {'Success' if ok else 'Failed'}")
    assert ok, "Failed to queue task"
    
    # 3. Worker requests work
    print("\n2️⃣ Worker (julie-roo): Requesting work")
    task = sb.request_work("julie-roo")
    print(f"   Received: {task.task_id if task else 'None'}")
    assert task is not None, "Worker got no task"
    assert task.task_id == "P3-EXT999", "Got wrong task"
    
    # 4. Another worker tries to request work (should be empty)
    print("\n3️⃣ Worker (maxx-roo): Requesting work")
    task2 = sb.request_work("maxx-roo")
    print(f"   Received: {task2.task_id if task2 else 'None'}")
    assert task2 is None, "Maxx-roo got a task that Julie locked!"
    
    # 5. Worker posts a message
    print("\n4️⃣ Worker (julie-roo): Posting message")
    sb.post_message("julie-roo", "I am working on EXT999", channel="general")
    msgs = sb.get_messages("general", limit=5)
    print(f"   Messages: {[m.content for m in msgs]}")
    assert len(msgs) > 0
    
    # 6. Worker completes task
    print("\n5️⃣ Worker (julie-roo): Completing task")
    ok = sb.complete_task("P3-EXT999")
    print(f"   Result: {'Success' if ok else 'Failed'}")
    assert ok, "Failed to complete task"
    
    # 7. Check final state
    status = sb._tasks["P3-EXT999"].status
    print(f"\n✅ Final task status in queue: {status}")
    assert status == 'completed', "Task not marked completed"
    
    # Clean up test
    sb._tasks = original_tasks
    sb._persist_tasks_to_disk()
    
    print("\n🎉 Pipeline test PASSED!")

if __name__ == "__main__":
    run_test()

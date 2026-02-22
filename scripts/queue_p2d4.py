import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

async def main():
    try:
        async with sse_client("http://localhost:8000/sse") as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                
                print("Queueing P2-D4...")
                res = await session.call_tool("queue_task", {"task_id": "P2-D4", "spec_path": "docs/specs/P2-D4_show_control.md"})
                print(res)
    except Exception as e:
        print(f"Failed to queue task via MCP: {e}")
        # fallback to manipulating the json directly if server isn't running
        import json
        import os
        from datetime import datetime
        queue_file = "WORKSPACE/COMMS/QUEUE.json"
        
        if os.path.exists(queue_file):
            with open(queue_file, "r") as f:
                queue = json.load(f)
        else:
            queue = {"pending_tasks": [], "assigned_tasks": {}, "completed_tasks": []}
            
        queue["pending_tasks"].append({
            "task_id": "P2-D4",
            "spec_path": "docs/specs/P2-D4_show_control.md",
            "queued_at": datetime.now().isoformat()
        })
        
        with open(queue_file, "w") as f:
            json.dump(queue, f, indent=2)
        print("Task queued manually via QUEUE.json")

if __name__ == "__main__":
    asyncio.run(main())

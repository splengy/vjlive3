#!/usr/bin/env python3
import sys
import json
import logging
from server import VJLiveSwitchboard

# Disable noisy logging for CLI
logging.getLogger("vjlive3.mcp.switchboard").setLevel(logging.CRITICAL)

sb = VJLiveSwitchboard()
cmd = sys.argv[1] if len(sys.argv) > 1 else ""

if cmd == "request":
    worker = sys.argv[2]
    task = sb.request_work(worker)
    if task:
        print(json.dumps({"task_id": task.task_id, "spec_path": task.spec_path, "status": task.status}))
    else:
        print(json.dumps({"has_work": False}))
elif cmd == "status":
    task_id = sys.argv[2]
    if task_id in sb._tasks:
        print(sb._tasks[task_id].status)
    else:
        print("not_found")
elif cmd == "queue":
    task_id = sys.argv[2]
    spec_path = sys.argv[3]
    success = sb.queue_task(task_id, spec_path)
    print(json.dumps({"ok": success}))
elif cmd == "complete":
    task_id = sys.argv[2]
    success = sb.complete_task(task_id)
    print(json.dumps({"ok": success}))

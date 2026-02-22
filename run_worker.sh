#!/bin/bash

# VJLive3 Worker Loop
WORKER_NAME=${1:-Beta}
echo "Starting Antigravity Worker Loop for [$WORKER_NAME]..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
CLI_PY="$SCRIPT_DIR/mcp_servers/vjlive_switchboard/cli.py"

while true; do
    echo "=========================================================="
    echo "Waking Worker $WORKER_NAME to check the queue..."
    echo "=========================================================="
    
    # Check the queue via the switchboard direct CLI
    OUTPUT=$("$CLI_PY" request "$WORKER_NAME")
    
    HAS_WORK=$(echo "$OUTPUT" | jq -r '.has_work // empty')
    
    if [ "$HAS_WORK" == "false" ]; then
        echo "No work in queue. Sleeping for 15 seconds..."
        sleep 15
        continue
    fi
    
    # Parse task Details
    TASK_ID=$(echo "$OUTPUT" | jq -r '.task_id')
    SPEC_PATH=$(echo "$OUTPUT" | jq -r '.spec_path')
    
    if [ -z "$TASK_ID" ] || [ "$TASK_ID" == "null" ]; then
        echo "Error parsing task from switchboard:"
        echo "$OUTPUT"
        sleep 15
        continue
    fi
    
    echo ">>> WORKER ASSIGNED TASK: $TASK_ID"
    echo ">>> SPEC PATH: $SPEC_PATH"
    
    # Spawn Antigravity synchronously using 'antigravity chat'
    # We pass the exact spec and task ID. 
    # NOTE: The --wait flag ensures the bash script blocks until the agent session finishes. 
    echo ">>> Spawning Antigravity Agent to execute spec..."
    antigravity --wait chat "You are Worker Agent ($WORKER_NAME). Your task is $TASK_ID. 
READ the spec at $SPEC_PATH carefully. 
IMPLEMENT the code EXACTLY to spec. 
WRITE passing tests. 
When tests pass, you MUST call complete_task(task_id=\"$TASK_ID\") via your MCP switchboard tool. 
DO NOT modify architecture. DO NOT write specs. Be brief, just do the work."
    
    # Once the agent exits (either via task completion or error)
    # Check the task status on the server
    STATUS=$("$CLI_PY" status "$TASK_ID")
    
    if [ "$STATUS" == "completed" ]; then
        echo ">>> Agent successfully completed Task $TASK_ID"
    else
        echo ">>> Session ended but task $TASK_ID is still $STATUS"
        echo ">>> The task will remain assigned to $WORKER_NAME."
    fi
    
    echo "Worker session ended. Sleeping 5 seconds before next poll..."
    sleep 5
done

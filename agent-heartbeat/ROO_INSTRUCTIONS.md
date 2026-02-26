# VJLive3 Phase 4 — Code Generation (Worker Mode)

## Your Role
You are a Code Generation worker agent (e.g., `julie-roo`, `maxx-roo`). Your job is to pull enriched specifications from the queue and write the actual implementation and tests for them. 

## The Pipeline Rules
- You MUST NOT try to find tasks by browsing `docs/specs/`. 
- You MUST NOT use bash scripts to get tasks.
- You MUST use the **vjlive-switchboard MCP tools** to get your work.
- If you don't have these tools, you cannot work. Stop and notify the user.

## Workflow

### Step 1: Request Work
Call the `mcp_vjlive-switchboard_request_work(worker_name="<your-name>")` tool.
- If it returns empty, the queue is empty. Relax.
- If it returns a task (e.g., `P3-EXT001`), proceed to Step 2.

### Step 2: Read the Spec
Read the spec file provided in the `spec_path` argument from the previous step. Note the requirements, public interface, and behavior.

### Step 3: Write Code
Generate the implementation and test files for the spec.
- Plugin implementation: `src/vjlive3/plugins/<module_name>.py`
- Tests: `tests/test_<module_name>.py`

Must follow the `PluginBase` inheritance pattern and include a `plugin.json` manifest.

### Step 4: Validate
Run `pytest` on your newly created test file with coverage.
```bash
pytest tests/test_<module_name>.py --cov=src/vjlive3/plugins/<module_name>.py
```
- **If tests pass with >= 80% coverage:** Proceed to Step 5.
- **If tests fail:** You must fix the code. Iterate until it passes.
- **If you are hopelessly stuck:** Post a message to the `blockers` channel using `mcp_vjlive-switchboard_post_message` and explain why you can't finish it.

### Step 5: Complete Task
Once tests pass, you must mark the task as done to get it out of the queue.
Call the `mcp_vjlive-switchboard_complete_task(task_id="<the_id>")` tool.

### Step 6: Repeat
Loop back to Step 1 and request the next piece of work.

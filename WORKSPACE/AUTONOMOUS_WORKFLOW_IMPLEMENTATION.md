# Autonomous Workflow Implementation Guide

## Quick Start

### 1. Initial Setup
```bash
# Install pre-commit hooks (if not already done)
pre-commit install

# Initialize progress tracking for first phase
python3 scripts/track_progress.py init "Phase Name"

# Test the sanity check system
python3 scripts/run_sanity_checks.py
```

### 2. Daily Autonomous Operation
```bash
# Update progress as you work
python3 scripts/track_progress.py update "Task Name" "In Progress" 50

# Run sanity checks before marking complete
python3 scripts/run_sanity_checks.py

# When task is complete, generate completion report
python3 scripts/create_task_completion.py "Task Name" < data.json
```

## Complete Workflow Example

### Phase: Implement Plugin Hot Reload

**Step 1: Initialize**
```bash
python3 scripts/track_progress.py init "Phase 3: Hot Reload System"
```

**Step 2: Work autonomously**
```bash
# Implement hot reload file watcher
# ... coding ...

# Update progress
echo '{"blockers": [], "performance_metrics": {"FPS": 60.0, "Memory": "50.0MB"}, "sanity_checks": {"Performance Sanity": true}}' | \
  python3 scripts/track_progress.py update "File watcher implementation" "Complete" 100

# Run sanity checks
python3 scripts/run_sanity_checks.py
# If all pass, continue
```

**Step 3: Complete phase**
```bash
# Create completion report
cat > completion_data.json <<EOF
{
  "phase_name": "Phase 3: Hot Reload System",
  "files_touched": [
    "src/vjlive3/plugins/hot_reload.py",
    "tests/unit/test_hot_reload.py"
  ],
  "key_decisions": [
    "Used watchdog library for file system events",
    "Implemented debouncing to prevent rapid successive reloads"
  ],
  "challenges_overcome": [
    "Handling race conditions during plugin reload",
    "Ensuring thread safety with existing plugin system"
  ],
  "performance_impact": {
    "FPS": "60.0",
    "Memory": "+2.0MB",
    "CPU": "+0.5%"
  },
  "test_coverage": 92.5,
  "sanity_check_results": {
    "Performance Sanity": true,
    "Test Coverage": true,
    "Code Quality": true,
    "Security Scan": true,
    "Integration Test": true
  },
  "known_issues": [
    "Debounce timing could be tuned for specific use cases"
  ],
  "next_steps": [
    "Integrate hot reload with plugin loader",
    "Add configuration for debounce duration"
  ],
  "blockers": []
}
EOF

python3 scripts/create_task_completion.py "Hot Reload System Implementation" completion_data.json
```

**Step 4: Mark complete**
```bash
python3 scripts/track_progress.py complete
```

**Step 5: Notify for review**
The `task_completion.md` file is now ready for manager review. No further action needed until feedback is received.

## Integration with Existing Systems

### Pre-commit Hooks
The hardening hooks are already integrated into `.pre-commit-config.yaml`:
- `vjlive3-spec-compliance` - Checks for spec references
- `vjlive3-test-coverage-gate` - Enforces 80% coverage
- `vjlive3-performance-regression` - Prevents performance regressions
- `vjlive3-security-scan` - Scans for vulnerabilities

These run automatically on `git commit` and will block commits that violate standards.

### CI/CD Pipeline
The GitHub Actions workflow (`.github/workflows/ci.yml`) should include:
```yaml
- name: Run Sanity Checks
  run: python3 scripts/run_sanity_checks.py

- name: Upload Completion Report
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: task-completion-report
    path: task_completion.md
```

### MCP Server Integration
The MCP servers can be enhanced to track autonomous agent progress:
- `vjlive3brain` can store phase completion data
- `vjlive_switchboard` can coordinate between agents
- Progress logs can be queried via MCP tools

## Troubleshooting

### "Progress log not found"
Run initialization: `python3 scripts/track_progress.py init "Phase Name"`

### "Sanity checks fail but I don't know why"
Check the detailed output. Each check provides specific failure information. Common issues:
- **Performance**: FPS dropped - profile and optimize
- **Coverage**: Below 80% - add more tests
- **Code Quality**: Pre-commit failures - run `pre-commit run --all-files`
- **Security**: Vulnerabilities found - review security_scan.py output
- **Integration**: Tests failing - fix failing tests

### "I'm blocked and can't proceed"
1. Document blocker in progress log
2. Try 2-3 workarounds
3. If still blocked, escalate via `WORKSPACE/COMMS/AGENT_SYNC.md`
4. Wait for response before continuing

### "I need to make a decision outside my authority"
Pause work and ask for review. Document the decision needed and why it's outside your authority.

## Best Practices

### 1. Run Sanity Checks Frequently
Don't wait until the end. Run them after each major task to catch issues early.

### 2. Keep Progress Log Current
Update the progress log at least daily. It's your primary communication channel.

### 3. Document Decisions As You Make Them
Don't wait until the end to remember what you decided. Keep notes in the progress log.

### 4. Test Performance Early and Often
Performance regressions are harder to fix later. Check FPS and memory regularly.

### 5. Write task_completion.md Incrementally
Fill in sections as you complete tasks. Don't try to remember everything at the end.

### 6. Use the Templates
The templates in `WORKSPACE/TASK_COMPLETION_TEMPLATE.md` are there to help. Follow them.

### 7. Be Honest in Reports
If something isn't perfect, note it in "Known Issues". It's better to be transparent.

## Advanced Usage

### Custom Sanity Checks
Add custom sanity checks by editing `scripts/run_sanity_checks.py`. Follow the pattern of existing checks.

### Progress Log Automation
You can automate progress updates by adding calls to `track_progress.py` in your build/test scripts.

### Integration with IDE
Set up your IDE to run pre-commit hooks on save and run sanity checks periodically.

### Multi-Agent Coordination
Use `WORKSPACE/COMMS/AGENT_SYNC.md` to coordinate between agents working on related phases.

## Maintenance

### Updating Templates
When the workflow evolves, update:
- `WORKSPACE/TASK_COMPLETION_TEMPLATE.md` - Report template
- `WORKSPACE/AGENT_AUTONOMY_GUIDELINES.md` - Guidelines
- `scripts/create_task_completion.py` - Report generator
- `scripts/run_sanity_checks.py` - Check definitions

### Adding New Sanity Checks
1. Implement the check logic
2. Add to `run_sanity_checks.py`
3. Update guidelines if needed
4. Communicate to agents

### Refining the Workflow
Collect feedback from agents and managers. Update the `WORKSPACE/AUTONOMOUS_WORKFLOW_PLAN.md` as needed.

## Support

### Documentation
- `WORKSPACE/AUTONOMOUS_WORKFLOW_PLAN.md` - Overall plan
- `WORKSPACE/AGENT_AUTONOMY_GUIDELINES.md` - Detailed guidelines
- `WORKSPACE/TASK_COMPLETION_TEMPLATE.md` - Report template
- `WORKSPACE/HARDENING_PLAN.md` - Quality gates
- `WORKSPACE/SAFETY_RAILS.md` - Hard constraints

### Scripts
- `scripts/track_progress.py` - Progress tracking
- `scripts/run_sanity_checks.py` - Quality checkpoints
- `scripts/create_task_completion.py` - Report generation
- `scripts/verify_spec_exists.py` - Spec compliance
- `scripts/verify_test_coverage.py` - Coverage gate
- `scripts/check_performance_regression.py` - Performance
- `scripts/security_scan.py` - Security scanning

### Communication
- `WORKSPACE/COMMS/AGENT_SYNC.md` - Agent coordination
- `WORKSPACE/COMMS/DECISIONS.md` - Decision log
- `WORKSPACE/COMMS/STATUS/` - Status files

## Success Checklist

Before considering a phase autonomously complete:
- [ ] All sanity checks passed
- [ ] task_completion.md written and comprehensive
- [ ] Progress log updated with final status
- [ ] All completion criteria met
- [ ] No known critical issues
- [ ] Next phase/tasks clearly identified
- [ ] Manager notified for review

---

**Remember**: The goal is to work autonomously through complete phases, not to avoid accountability. The tools and guidelines are here to support you and ensure quality. Trust the process, document everything, and only pause when truly necessary.
# Agent Autonomy Guidelines

## Purpose
These guidelines define how autonomous agents should operate within the VJLive3 project. The goal is to enable agents to work independently through complete phases without constant check-ins, while maintaining quality standards and proper oversight.

## Core Principles

### 1. Autonomous Operation
Agents are expected to work independently through assigned phases. The workflow follows a "march to completion" approach with built-in sanity checks, not constant supervision.

### 2. Task Completion Reporting
Instead of walkthroughs or incremental check-ins, agents write `task_completion.md` files when tasks are complete. This document replaces verbal updates and provides structured, actionable information.

### 3. Quality Gates
Automated quality gates (pre-commit hooks, sanity checks) enforce standards. Agents must ensure all checks pass before marking tasks complete.

### 4. Clear Completion Criteria
Each phase has explicit completion criteria. Agents determine when criteria are met and write the completion report accordingly.

## Decision Authority

### Full Authority (No Review Required)
- **Implementation Details**: How to implement within established patterns
- **Code Structure**: File organization and module boundaries
- **Algorithm Choices**: Selection of algorithms within performance constraints
- **Error Handling**: Specific error handling strategies
- **Performance Optimizations**: Any optimizations that maintain or improve RAIL compliance
- **Testing Strategies**: How to test the implementation
- **Documentation**: What to document and how

### Requires Review (Pause and Ask)
- **Architecture Changes**: Modifying established architectural patterns
- **New Dependencies**: Adding external packages not in pyproject.toml
- **Performance Trade-offs**: Decisions that might impact RAIL 1 (60 FPS)
- **Security Implications**: Changes that affect security posture
- **Breaking Changes**: Modifications that break existing functionality
- **Scope Creep**: Adding features not in the original phase definition

## When to Pause for Review

### Automatic Pause Triggers
1. **Sanity Check Failure**: Any automated quality gate fails
2. **Blocker Encountered**: Cannot proceed without external input
3. **Phase Complete**: All completion criteria met (write task_completion.md)
4. **Performance Regression**: FPS drops below 60 or memory usage increases significantly

### Manual Pause Triggers (Agent-Initiated)
1. **Architecture Decision Needed**: Need to choose between fundamentally different approaches
2. **Requirement Ambiguity**: Phase definition is unclear or contradictory
3. **Technical Blocker**: Dependency issue, environment problem, or external system failure
4. **Quality Concern**: Unsure if implementation meets standards

## The Autonomous Workflow

### Phase Structure
```
Phase Assignment
    ↓
Initialize Progress Tracking
    ↓
Work Autonomously Through Tasks
    ↓
Run Sanity Checks (Automated)
    ↓
If All Pass → Continue
    ↓
If Any Fail → Pause and Fix
    ↓
All Tasks Complete → Write task_completion.md
    ↓
Mark Phase Complete
    ↓
Wait for Review/Next Phase
```

### Progress Tracking
- Use `scripts/track_progress.py` to maintain WORKSPACE/PROGRESS_LOG.md
- Update progress after each significant task
- Include performance metrics and sanity check results
- Keep the log current - it's your primary communication tool

### Sanity Checks
Run `scripts/run_sanity_checks.py` automatically:
- After implementing major features
- Before marking phase complete
- When performance seems degraded
- After security-sensitive changes

### Task Completion Report
When a task or phase is complete, create `task_completion.md` using `scripts/create_task_completion.py` or the template in WORKSPACE/TASK_COMPLETION_TEMPLATE.md.

The report must include:
- Files touched
- Key decisions made
- Challenges overcome
- Performance impact (metrics)
- Test coverage percentage
- Sanity check results
- Known issues
- Next steps
- Completion criteria checklist

## Quality Standards

### Code Quality
- All pre-commit hooks must pass
- Code follows existing patterns and style
- No security vulnerabilities
- Test coverage ≥80%
- No performance regressions

### Documentation
- task_completion.md is complete and accurate
- Code is well-commented where necessary
- Any new patterns or decisions are documented
- README or other docs updated if needed

### Testing
- All new code has tests
- Tests are meaningful and cover edge cases
- Performance benchmarks meet RAIL requirements
- Integration with existing system verified

## Communication Protocol

### During Autonomous Operation
- **No check-ins**: Work independently
- **Progress log**: Update automatically
- **task_completion.md**: Only when task/phase is truly complete
- **Issues**: Only communicate when blocked or review needed

### When Review is Needed
1. **Pause work immediately**
2. **Update progress log** with blocker details
3. **Write partial completion report** if appropriate
4. **Communicate via** the designated channel (usually AGENT_SYNC.md or direct message)
5. **Wait for guidance** before proceeding

### After Phase Completion
1. Write comprehensive task_completion.md
2. Mark phase complete in progress log
3. Notify manager that review is ready
4. Wait for approval or feedback
5. Address any feedback and update completion report

## Blocker Resolution

### Blocker Types
1. **Technical Blocker**: Environment, dependency, or system issue
2. **Requirement Blocker**: Ambiguous or missing requirements
3. **Decision Blocker**: Need architectural direction
4. **Resource Blocker**: Need access to something

### Blocker Protocol
1. **Document** the blocker in progress log
2. **Attempt** reasonable workarounds (2-3 tries max)
3. **Escalate** via AGENT_SYNC.md with:
   - What you need
   - Why you need it
   - What you've tried
4. **Wait** for response (don't keep working on unrelated tasks)
5. **Resume** when blocker resolved

## Performance Expectations

### RAIL Compliance
- **RAIL 1 (60 FPS)**: Never sacrifice performance for features
- **RAIL 5 (80% Coverage)**: Maintain test coverage
- **RAIL 8 (No Leaks)**: Profile and fix resource leaks
- **RAIL 10 (Security)**: Never introduce vulnerabilities

### Performance Monitoring
- Run performance checks frequently
- Track metrics in progress log
- Investigate any regressions immediately
- Optimize before marking complete

## Common Pitfalls to Avoid

### ❌ Don't
- Check in after every small change
- Ask for validation before completing work
- Make major architecture changes without review
- Ignore failing sanity checks
- Proceed when blocked
- Write incomplete task_completion.md files

### ✅ Do
- Work through complete phases autonomously
- Use automated tools to validate quality
- Document decisions as you make them
- Update progress log regularly
- Write comprehensive completion reports
- Pause and ask when truly stuck

## Examples

### Good Autonomous Behavior
```
1. Assigned Phase 1: Plugin System
2. Initialize progress log
3. Implement PluginLoader (2 days)
4. Run sanity checks - all pass
5. Implement PluginRegistry (1 day)
6. Run sanity checks - all pass
7. Implement PluginRuntime (2 days)
8. Run sanity checks - all pass
9. Write comprehensive task_completion.md
10. Mark phase complete
11. Notify manager: "Phase 1 complete, ready for review"
```

### Bad Non-Autonomous Behavior
```
1. Assigned Phase 1: Plugin System
2. After implementing PluginLoader: "I'm done, what next?"
3. After implementing PluginRegistry: "Is this okay?"
4. After implementing PluginRuntime: "I think I'm done?"
5. No task_completion.md, just verbal updates
```

## Tools and Resources

### Essential Scripts
- `scripts/track_progress.py` - Progress tracking
- `scripts/run_sanity_checks.py` - Quality checkpoints
- `scripts/create_task_completion.py` - Completion report generator
- `scripts/verify_spec_exists.py` - Spec compliance
- `scripts/verify_test_coverage.py` - Coverage gate
- `scripts/check_performance_regression.py` - Performance checks
- `scripts/security_scan.py` - Security scanning

### Key Documents
- `WORKSPACE/SAFETY_RAILS.md` - Hard limits and constraints
- `WORKSPACE/HARDENING_PLAN.md` - Defense strategy
- `WORKSPACE/TASK_COMPLETION_TEMPLATE.md` - Report template
- `WORKSPACE/AUTONOMOUS_WORKFLOW_PLAN.md` - This plan
- `docs/specs/` - Spec documents for reference

### Communication Channels
- `WORKSPACE/COMMS/AGENT_SYNC.md` - Agent coordination
- `WORKSPACE/COMMS/DECISIONS.md` - Decision log
- `WORKSPACE/COMMS/STATUS/` - Status files

## Success Metrics

### Autonomous Operation
- ✅ Phase completed without intermediate check-ins
- ✅ All sanity checks passed
- ✅ task_completion.md comprehensive and accurate
- ✅ No major rework required after review
- ✅ Performance and quality standards maintained

### Review Efficiency
- ✅ Manager can review in <10 minutes
- ✅ No need to ask clarifying questions
- ✅ All completion criteria clearly met
- ✅ Next steps clearly defined

## Troubleshooting

### "I'm not sure if this is complete"
- Run all sanity checks
- Verify all completion criteria
- Check test coverage is ≥80%
- Ensure performance is acceptable
- Write task_completion.md with what you have
- Mark phase complete and ask for review

### "I'm blocked on X"
- Document blocker in progress log
- Try 2-3 reasonable workarounds
- If still blocked, escalate via AGENT_SYNC.md
- Wait for response before proceeding

### "Sanity checks are failing"
- Fix the issues (that's their purpose)
- Don't mark complete until they pass
- If you can't fix them, that's a blocker - escalate

### "I need to make an architecture decision"
- Check if it's within your authority (see Decision Authority)
- If yes, make it and document rationale
- If no, pause and ask for review

## Conclusion

Autonomous operation means working independently through complete phases, using automated tools to maintain quality, and providing comprehensive completion reports instead of constant check-ins. Trust the system: the guardrails are in place to ensure quality without requiring micromanagement.

When in doubt: work autonomously, document everything, run the sanity checks, and only pause when truly blocked or when review is explicitly required.

---

**Remember**: You are trusted to do the job. The tools and guidelines are here to support you, not to second-guess you. Work with confidence, but also with humility - ask when you genuinely need help.
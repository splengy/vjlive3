# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P8-I7_user_acceptance_testing.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P8-I7 — User Acceptance Testing

**What This Module Does**

Provides a comprehensive framework for conducting User Acceptance Testing (UAT) of VJLive3, ensuring the system meets end-user requirements and expectations before production release. This module manages test scenario execution, feedback collection, issue tracking, and sign-off workflows, enabling systematic validation of the system from the user's perspective.

---

## Architecture Decisions

- **Pattern:** Test Management + Feedback Collection
- **Rationale:** UAT requires structured scenario execution, real-time feedback capture, and systematic issue tracking. A dedicated framework ensures consistent testing across all user roles and use cases.
- **Constraints:**
  - Must support both in-person and remote testing scenarios
  - Must capture quantitative (ratings) and qualitative (comments) feedback
  - Must integrate with existing issue tracking systems
  - Must generate comprehensive UAT reports
  - Must be accessible to non-technical testers

---

## Legacy References

| Codebase | File | Class/Function | Status |
|----------|------|----------------|--------|
| VJlive-2 | `web_ui/src/docs/dynamic_mixer_deployment_plan.md` | Deployment plan with UAT steps | Port — UAT process |
| VJlive-2 | `core/timeline/ai_suggestion_engine.py` | User feedback tracking | Port — feedback mechanism |
| VJlive-2 | `plugins/vcore/living_fractal_consciousness.py` | User acceptance learning | Port — acceptance tracking |
| VJlive-1 | `scripts/uat_runner.py` | `UATRunner` | Port — test execution |
| VJlive-1 | `scripts/feedback_collector.py` | `FeedbackCollector` | Port — feedback collection |

---

## Public Interface

```python
class UserAcceptanceTesting:
    def __init__(self, config: UATConfig) -> None:...
    def load_scenarios(self) -> List[TestScenario]:...
    def execute_scenario(self, scenario_id: str) -> TestResult:...
    def collect_feedback(self, scenario_id: str, feedback: UserFeedback) -> None:...
    def report_issue(self, issue: IssueReport) -> None:...
    def generate_report(self) -> UATReport:...
    def validate_signoff(self) -> bool:...
    def export_results(self, format: str) -> str:...
    def cleanup(self) -> None:...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `config` | `UATConfig` | UAT configuration (scenarios, testers, etc.) | Must include all required parameters |
| `scenario_id` | `str` | Identifier for test scenario | Must match loaded scenario |
| `feedback` | `UserFeedback` | User feedback (ratings, comments) | Must include all required fields |
| `issue` | `IssueReport` | Issue/bug report | Must include reproducible steps |
| **Output** | `UATReport` | Comprehensive UAT results | Must be exportable to multiple formats |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `pandas` — data analysis and reporting — fallback: use CSV export only
  - `matplotlib` — visualization — fallback: skip charts
  - `sqlite3` — issue tracking storage — fallback: use in-memory storage
  - `email` — notification sending — fallback: skip notifications
- Internal modules this depends on:
  - `vjlive3.core.frame_utils` — for frame validation during testing
  - `vjlive3.plugins.manager` — for plugin loading and testing
  - `vjlive3.test_runner` — for automated test execution
  - `vjlive3.ui.main_window` — for UI interaction testing

---

## Error Cases

| Error Condition | Exception / Response | Recovery |
|-----------------|---------------------|----------|
| Missing scenario | `ValueError("Scenario not found")` | Load scenario first |
| Invalid feedback | `ValidationError("Missing required fields")` | Provide complete feedback |
| Issue tracking unavailable | `RuntimeError("Issue tracker offline")` | Store issues locally for later sync |
| Export format unsupported | `ValueError("Unsupported format")` | Use supported formats (JSON, CSV, PDF) |
| Tester not authorized | `PermissionError("Unauthorized tester")` | Verify tester credentials |
| Scenario timeout | `TimeoutError("Scenario exceeded time limit")` | Increase timeout or optimize scenario |

---

## Configuration Schema

| Field | Type | Default | Range / Constraints | Description |
|-------|------|---------|-------------------|-------------|
| `scenarios_path` | `str` | `docs/uat_scenarios/` | — | Path to test scenario definitions |
| `testers_path` | `str` | `docs/uat_testers/` | — | Path to tester assignments |
| `results_path` | `str` | `docs/uat_results/` | — | Path to store UAT results |
| `issue_tracker_url` | `str` | `""` | — | URL for issue tracking system |
| `notification_email` | `str` | `""` | — | Email for UAT notifications |
| `scenario_timeout` | `int` | `1800` | `60 - 3600` | Timeout per scenario (seconds) |
| `require_signoff` | `bool` | `True` | — | Require formal sign-off to complete |
| `auto_export` | `bool` | `False` | — | Auto-export results after completion |

---

## State Management

- **Per-scenario state:** (cleared each scenario)
  - Current scenario execution
  - Step-by-step progress
  - Temporary feedback
- **Persistent state:** (survives across sessions)
  - Test scenario definitions
  - Tester assignments and credentials
  - Feedback collection database
  - Issue tracking integration
  - Historical UAT results
- **Initialization state:** (set once at startup)
  - Scenario loader
  - Feedback validator
  - Issue tracker connector
  - Report generator
- **Cleanup required:** Yes — close database connections, export final results

---

## GPU Resources

This module is **CPU-only** and does not use GPU resources.

**Memory Budget:**
- Scenario definitions: ~10-50 MB
- Feedback database: ~50-200 MB
- Report generation: ~100-500 MB
- Total: ~200-750 MB (light)

---

## Test Scenarios

UAT scenarios should cover all critical user workflows:

### Core Functionality
1. **System Startup**: Launch VJLive3, verify all components initialize
2. **Plugin Loading**: Load all plugins, verify no errors
3. **Video Input**: Connect cameras, verify video streams
4. **Audio Input**: Connect audio, verify reactivity
5. **Effect Application**: Apply effects, verify visual output
6. **Performance**: Verify 60 FPS stability
7. **Resource Usage**: Monitor memory and CPU usage

### User Workflows
1. **VJ Performance**: Simulate live performance scenario
2. **Recording**: Record and save performance
3. **Plugin Management**: Install, enable, disable plugins
4. **Configuration**: Change settings, save/load presets
5. **Error Recovery**: Test crash recovery, hardware disconnect

### Edge Cases
1. **Hardware Failure**: Disconnect/reconnect cameras
2. **Resource Exhaustion**: Test with many plugins active
3. **Long-Running**: Run for 4+ hours continuously
4. **Rapid Changes**: Quickly switch effects/plugins
5. **Audio Peaks**: Test with loud audio signals

---

## Feedback Collection

Collect both quantitative and qualitative feedback:

### Quantitative Metrics
- **Performance**: FPS stability (1-10 rating)
- **Ease of Use**: User interface intuitiveness (1-10)
- **Reliability**: System stability (1-10)
- **Feature Completeness**: All expected features present (1-10)
- **Overall Satisfaction**: Net Promoter Score style (0-10)

### Qualitative Feedback
- **Comments**: Free-form text feedback
- **Issues Encountered**: List of bugs/problems
- **Feature Requests**: Suggested improvements
- **Workflow Gaps**: Missing functionality
- **Comparison to Legacy**: How it compares to VJLive2

---

## Issue Reporting

Standardized issue reporting format:

```python
@dataclass
class IssueReport:
    scenario_id: str
    step_number: int
    severity: str  # Critical, Major, Minor, Cosmetic
    title: str
    description: str
    reproducible: bool
    steps_to_reproduce: List[str]
    expected_behavior: str
    actual_behavior: str
    screenshots: List[str]  # Paths to screenshots
    logs: List[str]  # Paths to log files
    system_info: dict  # OS, hardware, versions
    reporter_id: str
    timestamp: float
```

---

## Sign-off Workflow

UAT completion requires formal sign-off from stakeholders:

1. **Tester Sign-off**: Each tester confirms they've completed all assigned scenarios
2. **Team Lead Sign-off**: Technical lead verifies all critical issues resolved
3. **Product Owner Sign-off**: Product owner confirms feature completeness
4. **Operations Sign-off**: Ops team confirms deployment readiness

All sign-offs required before production deployment.

---

## Reporting

Generate comprehensive UAT reports:

### Summary Report
- Overall pass/fail status
- Key metrics (average ratings, issue counts)
- Critical issues summary
- Sign-off status
- Recommendation (approve/deny with conditions)

### Detailed Report
- Scenario-by-scenario results
- Individual tester feedback
- All issues reported (with severity)
- Performance metrics
- Comparison to baseline (if available)

### Export Formats
- **JSON**: Machine-readable for CI/CD integration
- **CSV**: Spreadsheet analysis
- **PDF**: Human-readable for stakeholders
- **HTML**: Interactive web report

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if hardware absent |
| `test_scenario_loading` | Scenarios load correctly from definitions |
| `test_scenario_execution` | Scenarios execute with proper step tracking |
| `test_feedback_collection` | Feedback captured and stored correctly |
| `test_issue_reporting` | Issues reported with all required fields |
| `test_report_generation` | Reports generated in all formats |
| `test_signoff_workflow` | Sign-off process enforces all required approvals |
| `test_export_functionality` | Export to JSON/CSV/PDF works correctly |
| `test_validation_rules` | Feedback validation rules enforced |
| `test_timeout_handling` | Scenarios timeout correctly |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-8] P8-I7: User Acceptance Testing` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Use these to fill in the spec. These are the REAL implementations:

### web_ui/src/docs/dynamic_mixer_deployment_plan.md (L49-68) [VJlive-2 (Original)]
```markdown
### Environment Setup
- [ ] Staging environment ready
- [ ] Production environment ready
- [ ] Database backups created
- [ ] Rollback procedures documented
- [ ] Monitoring systems configured

## Deployment Steps

### Step 1: Staging Deployment
1. **Code Merge**: Merge feature branch to main branch
2. **Build Process**: Run automated build process
3. **Staging Deployment**: Deploy to staging environment
4. **Validation**: Run validation tests in staging
5. **User Testing**: Conduct user acceptance testing

### Step 2: Production Deployment
1. **Maintenance Mode**: Enable maintenance mode
2. **Database Backup**: Create production database backup
```

This shows the UAT process is part of the deployment pipeline, occurring after staging deployment and before production deployment.

### core/timeline/ai_suggestion_engine.py (L577-596) [VJlive-2 (Original)]
```python
        stype = suggestion.type.value
        self._type_acceptance.setdefault(stype, []).append(accepted)
        # Keep only last 50 entries per type
        if len(self._type_acceptance[stype]) > 50:
            self._type_acceptance[stype] = self._type_acceptance[stype][-50:]

        # Track per-user acceptance
        self._user_acceptance.setdefault(user_id, []).append(accepted)
        if len(self._user_acceptance[user_id]) > 50:
            self._user_acceptance[user_id] = self._user_acceptance[user_id][-50:]

        # Adjust suggestion cooldown based on overall acceptance rate
        all_recent = [fb['accepted'] for fb in self._feedback_history[-100:]]
        if len(all_recent) >= 10:
            acceptance_rate = sum(all_recent) / len(all_recent)
            # High acceptance → faster suggestions; low → slow down
            self.suggestion_cooldown = max(1.0, min(10.0, 2.0 / max(acceptance_rate, 0.1)))

        logger.info("AI suggestion feedback: %s - %s (accepted: %s, user: %s)",
                     suggestion.type.value, suggestion.reason, accepted, user_id)
```

This demonstrates a feedback tracking mechanism that could be adapted for UAT feedback collection, tracking acceptance rates and user-specific feedback patterns.

### plugins/vcore/living_fractal_consciousness.py (L497-516) [VJlive (Original)]
```python
                    # Suggest a nudge in a direction that increases complexity
                    direction = 1.0 if current < 5.0 else -1.0
                    suggestion[param] = current + direction * 0.5
                    suggestion[param] = max(0.0, min(10.0, suggestion[param]))
        
        # Learn from user acceptance (simplified)
        if suggestion and random.random() < self.learning_rate:
            self.suggestion_history.append({
                'suggestion': suggestion,
                'timestamp': time.time(),
                'accepted': None  # Would be set by UI
            })
        
        return suggestion
```

This shows a pattern for learning from user acceptance, which could inform UAT feedback analysis to identify common pain points.

---

## Notes for Implementers

1. **Core Concept**: User Acceptance Testing validates that the system meets real-world user needs. It's the final quality gate before production.

2. **UAT Strategy**: Use realistic scenarios that mirror actual VJ performance workflows. Include both novice and expert testers.

3. **Scenario Design**: Scenarios should be specific, measurable, and time-bound. Include preconditions, steps, and expected outcomes.

4. **Feedback Collection**: Capture both quantitative (ratings) and qualitative (comments) feedback. Make it easy for testers to provide feedback.

5. **Issue Tracking**: Integrate with existing issue tracking (GitHub Issues, Jira, etc.) to ensure bugs are tracked and resolved.

6. **Sign-off Process**: Formal sign-off from all stakeholders is required before production deployment.

7. **Reporting**: Generate comprehensive reports that highlight critical issues and provide clear recommendations.

8. **Remote Testing**: Support both in-person and remote testing scenarios with appropriate tools (screen recording, remote access).

9. **Tester Management**: Track tester assignments, credentials, and completion status.

10. **Continuous Improvement**: Use UAT results to improve future development cycles.

---

## Implementation Tips

1. **Python Implementation**:
   ```python
   import json
   import pandas as pd
   from datetime import datetime
   from typing import List, Dict, Optional
   from dataclasses import dataclass, asdict
   
   @dataclass
   class TestScenario:
       id: str
       name: str
       description: str
       preconditions: List[str]
       steps: List[Step]
       expected_outcome: str
       timeout: int = 1800
   
   @dataclass
   class UserFeedback:
       scenario_id: str
       tester_id: str
       ratings: Dict[str, int]  # 1-10 scales
       comments: str
       issues: List[str]
       timestamp: float
   
   class UserAcceptanceTesting:
       def __init__(self, config: UATConfig):
           self.config = config
           self.scenarios = {}
           self.feedback_db = {}
           self.issues = []
       
       def load_scenarios(self) -> List[TestScenario]:
           # Load from YAML/JSON files
           pass
       
       def execute_scenario(self, scenario_id: str) -> TestResult:
           # Execute scenario, track steps, capture results
           pass
       
       def collect_feedback(self, scenario_id: str, feedback: UserFeedback):
           # Validate and store feedback
           pass
   ```

2. **Scenario Storage**: Use YAML or JSON for scenario definitions. Keep them human-editable.

3. **Feedback Storage**: Use SQLite for local storage, with export to JSON/CSV for analysis.

4. **Reporting**: Use pandas for data analysis, matplotlib for charts, and reportlab for PDF generation.

5. **Issue Integration**: Use GitHub Issues API or Jira API for automatic issue creation.

6. **Notifications**: Use email or Slack notifications for UAT milestones.

7. **Web Interface**: Consider a simple web UI for testers to access scenarios and submit feedback.

8. **Automation**: Where possible, automate scenario execution (e.g., UI automation with Selenium).

---
-

## References

- User Acceptance Testing best practices
- Software testing methodologies
- Issue tracking systems (GitHub, Jira)
- Reporting and analytics tools
- VJLive-2 deployment and UAT processes

---

## Conclusion

The User Acceptance Testing module provides a structured framework for validating VJLive3 against real-world user expectations. By managing scenarios, collecting feedback, tracking issues, and enforcing sign-off workflows, it ensures the system is truly ready for production deployment and meets the needs of its intended users.

---

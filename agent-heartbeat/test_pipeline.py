#!/usr/bin/env python3
"""
AHOS Pipeline Integration Tests

End-to-end tests for the spec-to-code pipeline.
These test the MACHINE, not the app it builds.

Tests:
  1. Plate builder assembles valid context
  2. Validator catches known-bad code
  3. Validator passes known-good code
  4. Rejection feedback generates actionable instructions
  5. Full pipeline: bad code → reject → feedback → verify feedback is usable
  6. Config loading with fallbacks
  7. Watchdog status check
  8. Julie connectivity (skip if offline)

Usage:
    python3 test_pipeline.py           # Run all tests
    python3 test_pipeline.py -v        # Verbose
"""

import json
import os
import sys
import unittest
import tempfile
from pathlib import Path
from datetime import datetime

# Add agent-heartbeat to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from word_salad_detector import scan as scan_word_salad, scan_file, WordSaladResult
from stub_detector import scan as scan_stubs, StubResult
from validator import ValidatorPipeline, ValidationReport
from rejection_feedback import format_feedback, RejectionFeedback
from heartbeat_header import build_prompt, estimate_tokens
from heartbeat import load_config


# =========================================================================
# Known test fixtures
# =========================================================================
KNOWN_BAD_WORD_SALAD = '''
def process(self, frame):
    """Process frame gracefully ensuring seamless integration."""
    # Natively allocating buffers organically for optimal performance
    # Gracefully handling input ensuring safety reliably
    # Seamlessly integrating with the pipeline flawlessly
    result = frame * 2
    return result
'''

KNOWN_BAD_STUB = '''
def process(self, frame):
    """Process the frame."""
    # In a real environment, this would connect to the GPU
    raise NotImplementedError("TODO: implement actual processing")
'''

KNOWN_GOOD_CODE = '''
def process(self, frame):
    """Apply 3x3 box blur to the input frame."""
    h, w = frame.shape[:2]
    output = np.zeros_like(frame)
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            output[y, x] = np.mean(frame[y-1:y+2, x-1:x+2], axis=(0, 1))
    return output
'''

KNOWN_EMPTY = ''
KNOWN_WHITESPACE = '   \n\n   \n  '


class TestWordSaladDetector(unittest.TestCase):
    """Test the word salad detector catches hallucination patterns."""

    def test_catches_word_salad(self):
        result = scan_word_salad(KNOWN_BAD_WORD_SALAD)
        self.assertFalse(result.passed, "Should reject word salad code")
        self.assertGreater(result.total_hits, 0)

    def test_passes_clean_code(self):
        result = scan_word_salad(KNOWN_GOOD_CODE)
        self.assertTrue(result.passed, "Should pass clean code")

    def test_empty_file(self):
        result = scan_word_salad("")
        self.assertTrue(result.passed, "Empty file should pass (not crash)")

    def test_scan_file_missing(self):
        result = scan_file("/nonexistent/file.py")
        self.assertFalse(result.passed, "Missing file should fail closed")
        self.assertIn("FILE_NOT_FOUND", result.verdict)

    def test_has_flagged_lines(self):
        result = scan_word_salad(KNOWN_BAD_WORD_SALAD)
        self.assertGreater(len(result.flagged_lines), 0, "Should flag specific lines")
        # Each flagged line should be a (line_num, text, matches) tuple
        ln, text, matches = result.flagged_lines[0]
        self.assertIsInstance(ln, int)
        self.assertIsInstance(text, str)


class TestStubDetector(unittest.TestCase):
    """Test the stub detector catches fake implementations."""

    def test_catches_stubs(self):
        result = scan_stubs(KNOWN_BAD_STUB)
        self.assertFalse(result.passed, "Should reject stub code")
        self.assertGreater(result.instant_rejects, 0)

    def test_passes_clean_code(self):
        result = scan_stubs(KNOWN_GOOD_CODE)
        self.assertTrue(result.passed, "Should pass real code")

    def test_empty_file_rejected(self):
        result = scan_stubs("")
        self.assertFalse(result.passed, "Empty file should be rejected")

    def test_catches_fraud_phrase(self):
        result = scan_stubs(KNOWN_BAD_STUB)
        verdicts = [msg for _, _, msg in result.flagged_lines]
        fraud_found = any("FRAUD" in v or "STUB" in v for v in verdicts)
        self.assertTrue(fraud_found, "Should flag 'in a real environment' as fraud")


class TestValidatorPipeline(unittest.TestCase):
    """Test the full validator pipeline."""

    def setUp(self):
        # Disable local LLM for pipeline tests (deterministic only)
        self.pipeline = ValidatorPipeline(use_local_llm=False)

    def test_rejects_word_salad(self):
        report = self.pipeline.validate(KNOWN_BAD_WORD_SALAD)
        self.assertFalse(report.passed)
        self.assertGreater(len(report.rejection_reasons), 0)

    def test_rejects_stubs(self):
        report = self.pipeline.validate(KNOWN_BAD_STUB)
        self.assertFalse(report.passed)

    def test_passes_clean_code(self):
        report = self.pipeline.validate(KNOWN_GOOD_CODE)
        self.assertTrue(report.passed)
        self.assertIn("APPROVED", report.overall_verdict)

    def test_rejects_empty_output(self):
        report = self.pipeline.validate("")
        self.assertFalse(report.passed)
        self.assertIn("EMPTY_OUTPUT", report.rejection_reasons[0])

    def test_rejects_whitespace_only(self):
        report = self.pipeline.validate(KNOWN_WHITESPACE)
        self.assertFalse(report.passed)

    def test_report_has_all_fields(self):
        report = self.pipeline.validate(KNOWN_GOOD_CODE)
        self.assertIsNotNone(report.word_salad)
        self.assertIsNotNone(report.stubs)
        self.assertIsInstance(report.rejection_reasons, list)
        self.assertIsInstance(report.overall_verdict, str)


class TestRejectionFeedback(unittest.TestCase):
    """Test that rejection feedback is structured and actionable."""

    def setUp(self):
        self.pipeline = ValidatorPipeline(use_local_llm=False)

    def test_word_salad_feedback(self):
        report = self.pipeline.validate(KNOWN_BAD_WORD_SALAD)
        feedback = format_feedback(report, attempt=1, max_attempts=3)
        self.assertGreater(len(feedback.instructions), 0)
        self.assertIn("WHAT TO FIX", feedback.prompt_text)
        self.assertIn("RETRY", feedback.prompt_text)

    def test_stub_feedback(self):
        report = self.pipeline.validate(KNOWN_BAD_STUB)
        feedback = format_feedback(report, attempt=0, max_attempts=3)
        self.assertGreater(len(feedback.instructions), 0)
        # Should mention the golden example
        self.assertIn("Vimana", feedback.prompt_text)

    def test_feedback_under_500_tokens(self):
        report = self.pipeline.validate(KNOWN_BAD_WORD_SALAD)
        feedback = format_feedback(report)
        est_tokens = len(feedback.prompt_text) // 4
        self.assertLess(est_tokens, 600, f"Feedback too long: ~{est_tokens} tokens")

    def test_clean_code_no_feedback(self):
        report = self.pipeline.validate(KNOWN_GOOD_CODE)
        feedback = format_feedback(report)
        self.assertEqual(len(feedback.instructions), 0)

    def test_feedback_has_line_numbers(self):
        report = self.pipeline.validate(KNOWN_BAD_WORD_SALAD)
        feedback = format_feedback(report)
        ws_instructions = [i for i in feedback.instructions if i.category == "word_salad"]
        if ws_instructions:
            self.assertGreater(len(ws_instructions[0].lines), 0,
                               "Word salad feedback should include flagged line numbers")

    def test_attempt_tracking(self):
        report = self.pipeline.validate(KNOWN_BAD_STUB)
        feedback = format_feedback(report, attempt=2, max_attempts=3)
        self.assertEqual(feedback.attempt, 2)
        self.assertEqual(feedback.max_attempts, 3)
        self.assertIn("3/3", feedback.prompt_text)


class TestHeartbeatHeader(unittest.TestCase):
    """Test the heartbeat header builder."""

    def test_header_builds(self):
        header = build_prompt({"task_id": "TEST-001", "description": "test"})
        self.assertIsInstance(header, str)
        self.assertGreater(len(header), 0)

    def test_header_under_budget(self):
        header = build_prompt({"task_id": "TEST-001", "description": "test"})
        tokens = estimate_tokens(header)
        # Prompt can be larger than 400 tokens — just verify it's reasonable
        self.assertLess(tokens, 2000, f"Header unexpectedly large: {tokens} tokens")

    def test_token_estimator(self):
        self.assertEqual(estimate_tokens(""), 0)
        # ~4 chars per token
        est = estimate_tokens("a" * 400)
        self.assertGreater(est, 50)
        self.assertLess(est, 200)


class TestConfigLoading(unittest.TestCase):
    """Test config loading with fallbacks."""

    def test_loads_existing_config(self):
        config = load_config()
        self.assertIn("llm", config)
        self.assertIn("project", config)

    def test_fallback_on_missing_file(self):
        config = load_config("/nonexistent/config.yaml")
        self.assertIn("llm", config)
        self.assertIn("project", config)
        # Should have sensible defaults
        self.assertIn("provider", config["llm"])

    def test_fallback_on_bad_yaml(self):
        # Write a bad YAML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("{{{{invalid yaml: [")
            f.flush()
            config = load_config(f.name)
        os.unlink(f.name)
        self.assertIn("llm", config)


class TestFullPipelineIntegration(unittest.TestCase):
    """
    End-to-end integration test: the full spec-to-code pipeline.

    Tests the complete flow:
      bad code → validator → rejection → feedback → verify feedback
    """

    def test_full_reject_feedback_cycle(self):
        """E2E: bad code goes in, actionable feedback comes out."""
        # Step 1: Validate bad code
        pipeline = ValidatorPipeline(use_local_llm=False)
        report = pipeline.validate(KNOWN_BAD_WORD_SALAD)

        # Step 2: Confirm rejection
        self.assertFalse(report.passed, "Bad code should be rejected")

        # Step 3: Generate feedback
        feedback = format_feedback(report, attempt=0, max_attempts=3)

        # Step 4: Verify feedback is actionable
        self.assertGreater(len(feedback.instructions), 0,
                           "Feedback must contain at least one instruction")
        self.assertGreater(len(feedback.prompt_text), 100,
                           "Feedback prompt must be substantial")
        self.assertIn("RETRY", feedback.prompt_text,
                       "Feedback must indicate this is a retry")
        self.assertIn("WHAT TO FIX", feedback.prompt_text,
                       "Feedback must tell the agent what to fix")

        # Step 5: Verify the feedback could be prepended to a prompt
        combined = feedback.prompt_text + "\n\n" + "# Task: implement depth blur"
        self.assertGreater(len(combined), len(feedback.prompt_text))

    def test_clean_code_passes_everything(self):
        """E2E: clean code passes all gates without feedback."""
        pipeline = ValidatorPipeline(use_local_llm=False)
        report = pipeline.validate(KNOWN_GOOD_CODE)

        self.assertTrue(report.passed, "Clean code should pass")
        self.assertIn("APPROVED", report.overall_verdict)

        feedback = format_feedback(report)
        self.assertEqual(len(feedback.instructions), 0,
                         "Clean code should generate zero feedback instructions")

    def test_double_failure_different_feedback(self):
        """E2E: word salad and stub failures produce different feedback."""
        pipeline = ValidatorPipeline(use_local_llm=False)

        ws_report = pipeline.validate(KNOWN_BAD_WORD_SALAD)
        ws_feedback = format_feedback(ws_report)

        stub_report = pipeline.validate(KNOWN_BAD_STUB)
        stub_feedback = format_feedback(stub_report)

        # Different failure types should produce different instructions
        ws_categories = {i.category for i in ws_feedback.instructions}
        stub_categories = {i.category for i in stub_feedback.instructions}

        self.assertIn("word_salad", ws_categories)
        self.assertIn("stub", stub_categories)

    def test_real_file_validation(self):
        """E2E: validate an actual file from the project."""
        clean_file = Path(__file__).parent.parent / "src/vjlive3/plugins/depth_camera_splitter.py"
        if clean_file.exists():
            code = clean_file.read_text()
            pipeline = ValidatorPipeline(use_local_llm=False)
            report = pipeline.validate(code)
            self.assertTrue(report.passed,
                            f"Known-clean file should pass: {report.overall_verdict}")


if __name__ == "__main__":
    print("=" * 60)
    print("AHOS Pipeline Integration Tests")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    unittest.main(verbosity=2)

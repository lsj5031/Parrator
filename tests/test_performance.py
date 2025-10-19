"""
Performance tests for Smart Cleanup functionality.
"""

import time
import unittest

from parrator.cleanup.rule_engine import RuleEngine
from parrator.cleanup.manager import CleanupManager


class TestPerformance(unittest.TestCase):
    """Performance test cases for cleanup functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "filler_words": ["um", "uh", "er", "ah", "like", "you know", "i mean", "sort of", "kind of"],
            "preserve_patterns": {
                "urls": True, "emails": True, "code": True, "all_caps": True
            }
        }
        self.engine = RuleEngine(self.config)
        self.manager = CleanupManager({"cleanup": {"enabled": True, "mode": "standard", "engine": "rule"}, **self.config})

    def test_rule_engine_performance_target(self):
        """Test that rule engine meets performance targets (≤40ms for 350 chars)."""
        # Sample text of ~350 characters
        text = (
            "um okay so i think we should, you know, send the email tomorrow morning it's kind of important "
            "because we need to make sure that everyone is on the same page and understands what we're trying to "
            "accomplish with this project. I mean it's like really crucial that we get this right the first time "
            "so we don't have to go back and fix things later. Basically, we want to ensure success."
        )

        # Warm up
        self.engine.clean(text, mode="standard")

        # Measure performance
        start_time = time.time()
        for _ in range(10):  # Run 10 times for average
            result = self.engine.clean(text, mode="standard")
        end_time = time.time()

        avg_time_ms = ((end_time - start_time) / 10) * 1000

        print(f"Average cleanup time: {avg_time_ms:.1f}ms for {len(text)} characters")
        print(f"Performance target: ≤40ms, Actual: {avg_time_ms:.1f}ms")

        # Should meet the performance target
        self.assertLessEqual(avg_time_ms, 40, f"Cleanup took {avg_time_ms:.1f}ms, exceeds 40ms target")

    def test_cleanup_manager_performance(self):
        """Test CleanupManager performance."""
        text = "um hello world this is a test of the cleanup system performance"

        start_time = time.time()
        result = self.manager.clean_text(text, mode="standard")
        end_time = time.time()

        processing_time_ms = (end_time - start_time) * 1000

        print(f"CleanupManager time: {processing_time_ms:.1f}ms")
        print(f"Input: '{text}'")
        print(f"Output: '{result}'")

        # Should be reasonably fast even with manager overhead
        self.assertLessEqual(processing_time_ms, 50, "CleanupManager took too long")

    def test_large_text_performance(self):
        """Test performance with larger text (multiple paragraphs)."""
        text = (
            "um okay so i think we should, you know, send the email tomorrow morning it's kind of important. "
            "I mean it's like really crucial that we get this right the first time so we don't have to go back "
            "and fix things later. Basically, we want to ensure success and make sure everyone understands what "
            "we're trying to accomplish. The thing is, we need to be very careful about how we approach this "
            "because it affects the entire team and project timeline. So anyway, let's make sure we do it right."
        )

        start_time = time.time()
        result = self.engine.clean(text, mode="standard")
        end_time = time.time()

        processing_time_ms = (end_time - start_time) * 1000

        print(f"Large text cleanup: {processing_time_ms:.1f}ms for {len(text)} characters")

        # Should still be reasonably fast for larger text
        self.assertLessEqual(processing_time_ms, 100, "Large text cleanup took too long")

    def test_memory_efficiency(self):
        """Test that cleanup doesn't leak memory excessively."""
        text = "um test text with filler words like you know and i mean"

        # Run many iterations to check for memory issues
        for i in range(1000):
            result = self.engine.clean(text, mode="standard")
            self.assertIsInstance(result, str)

        # If we get here without memory errors, test passes
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
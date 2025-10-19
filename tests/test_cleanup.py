"""
Unit tests for Smart Cleanup functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock

from parrator.cleanup.rule_engine import RuleEngine
from parrator.cleanup.llm_engine import LocalLLMEngine
from parrator.cleanup.http_engine import HttpEngine
from parrator.cleanup.manager import CleanupManager


class TestRuleEngine(unittest.TestCase):
    """Test cases for RuleEngine."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "filler_words": ["um", "uh", "like", "you know", "i mean"],
            "preserve_patterns": {
                "urls": True,
                "emails": True,
                "code": True,
                "hashtags": True,
                "emojis": True,
                "all_caps": True
            }
        }
        self.engine = RuleEngine(self.config)

    def test_conservative_mode(self):
        """Test conservative cleanup mode."""
        # Basic grammar and punctuation only
        text = "um okay so i think we should, you know, send the email tomorrow morning it's kind of important"
        result = self.engine.clean(text, mode="conservative")

        # Should fix capitalization and basic grammar, but not remove fillers
        self.assertIn("I think", result)
        self.assertTrue(result[0].isupper())
        self.assertNotIn("i think", result)

    def test_standard_mode(self):
        """Test standard cleanup mode."""
        text = "um okay so i think we should, you know, send the email tomorrow morning it's kind of important"
        result = self.engine.clean(text, mode="standard")

        # Should remove fillers and tighten wording
        self.assertNotIn("um", result)
        self.assertNotIn("you know", result)
        self.assertNotIn("kind of", result)
        self.assertTrue(result[0].isupper())

    def test_rewrite_mode(self):
        """Test rewrite cleanup mode."""
        text = "um okay so i think we should, you know, send the email tomorrow morning it's kind of important"
        result = self.engine.clean(text, mode="rewrite")

        # Should be more concise and professional
        self.assertNotIn("um", result)
        self.assertNotIn("I think", result)
        self.assertNotIn("you know", result)
        self.assertTrue(result[0].isupper())

    def test_url_preservation(self):
        """Test that URLs are preserved."""
        text = "check this link https://example.com and email john_doe@example.com um thanks"
        result = self.engine.clean(text, mode="standard")

        self.assertIn("https://example.com", result)
        self.assertIn("john_doe@example.com", result)
        self.assertNotIn("um", result)

    def test_code_preservation(self):
        """Test that code blocks are preserved."""
        text = "run `npm install` and open https://foo.bar/docs um thanks"
        result = self.engine.clean(text, mode="conservative")

        self.assertIn("`npm install`", result)
        self.assertIn("https://foo.bar/docs", result)
        self.assertNotIn("um", result)

    def test_filler_removal_safety(self):
        """Test that filler words are not removed inside other words."""
        text = "the album was umami and amazing"
        result = self.engine.clean(text, mode="standard")

        # "um" should not be removed from "album" or "umami"
        self.assertIn("album", result)
        self.assertIn("umami", result)

    def test_repeated_words_removal(self):
        """Test removal of repeated words."""
        text = "the the quick brown fox jumped over the the lazy dog"
        result = self.engine.clean(text, mode="conservative")

        self.assertNotIn("the the", result)
        self.assertEqual(result.count("the"), 2)  # Should appear twice normally

    def test_repeated_letters_fixing(self):
        """Test fixing of repeated letters."""
        text = "soooo goooood"
        result = self.engine.clean(text, mode="conservative")

        self.assertNotIn("soooo", result)
        self.assertNotIn("goooood", result)
        self.assertIn("soo", result)
        self.assertIn("goo", result)

    def test_empty_text(self):
        """Test handling of empty text."""
        self.assertEqual(self.engine.clean("", mode="standard"), "")
        self.assertEqual(self.engine.clean("   ", mode="standard"), "")

    def test_is_available(self):
        """Test that rule engine is always available."""
        self.assertTrue(self.engine.is_available())

    def test_get_status(self):
        """Test status message."""
        status = self.engine.get_status()
        self.assertIn("Rule-based engine", status)


class TestLocalLLMEngine(unittest.TestCase):
    """Test cases for LocalLLMEngine."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "local_llm_endpoint": "http://127.0.0.1:11434",
            "local_llm_model": "llama3.2:3b",
            "local_llm_timeout": 30
        }

    @patch('parrator.cleanup.llm_engine.requests')
    def test_ollama_success(self, mock_requests):
        """Test successful Ollama API call."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Cleaned text"}
        mock_response.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_response

        engine = LocalLLMEngine(self.config)
        result = engine.clean("test text", mode="standard")

        self.assertEqual(result, "Cleaned text")

    @patch('parrator.cleanup.llm_engine.requests')
    def test_openai_compatible_success(self, mock_requests):
        """Test successful OpenAI-compatible API call."""
        # Change endpoint to non-Ollama
        config = self.config.copy()
        config["local_llm_endpoint"] = "http://127.0.0.1:8080"

        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Cleaned text"}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_response

        engine = LocalLLMEngine(config)
        result = engine.clean("test text", mode="standard")

        self.assertEqual(result, "Cleaned text")

    @patch('parrator.cleanup.llm_engine.requests')
    def test_api_failure_fallback(self, mock_requests):
        """Test fallback to rule engine on API failure."""
        # Mock failed response
        mock_requests.post.side_effect = Exception("API error")

        engine = LocalLLMEngine(self.config)
        result = engine.clean("test text", mode="standard")

        # Should return some cleaned text (from fallback)
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, "test text")  # Should be processed

    @patch('parrator.cleanup.llm_engine.requests')
    def test_is_available_success(self, mock_requests):
        """Test availability check success."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        engine = LocalLLMEngine(self.config)
        self.assertTrue(engine.is_available())

    @patch('parrator.cleanup.llm_engine.requests')
    def test_is_available_failure(self, mock_requests):
        """Test availability check failure."""
        mock_requests.get.side_effect = Exception("Connection error")

        engine = LocalLLMEngine(self.config)
        self.assertFalse(engine.is_available())


class TestHttpEngine(unittest.TestCase):
    """Test cases for HttpEngine."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "http_endpoint": "http://127.0.0.1:5055",
            "http_timeout": 10,
            "http_api_key": "test-key"
        }

    @patch('parrator.cleanup.http_engine.requests')
    def test_successful_cleanup(self, mock_requests):
        """Test successful HTTP cleanup."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"cleaned_text": "Cleaned result"}
        mock_response.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_response

        engine = HttpEngine(self.config)
        result = engine.clean("test text", mode="standard")

        self.assertEqual(result, "Cleaned result")

    @patch('parrator.cleanup.http_engine.requests')
    def test_different_response_formats(self, mock_requests):
        """Test handling of different response formats."""
        engine = HttpEngine(self.config)

        # Test "text" field
        mock_response = Mock()
        mock_response.json.return_value = {"text": "Result text"}
        mock_response.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_response

        result = engine.clean("test", mode="standard")
        self.assertEqual(result, "Result text")

        # Test "result" field
        mock_response.json.return_value = {"result": "Result result"}
        result = engine.clean("test", mode="standard")
        self.assertEqual(result, "Result result")

    @patch('parrator.cleanup.http_engine.requests')
    def test_api_failure_fallback(self, mock_requests):
        """Test fallback to rule engine on API failure."""
        mock_requests.post.side_effect = Exception("HTTP error")

        engine = HttpEngine(self.config)
        result = engine.clean("test text", mode="standard")

        # Should return processed text from fallback
        self.assertIsInstance(result, str)

    @patch('parrator.cleanup.http_engine.requests')
    def test_is_available_success(self, mock_requests):
        """Test availability check success."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        engine = HttpEngine(self.config)
        self.assertTrue(engine.is_available())

    def test_payload_building(self):
        """Test payload building for different modes."""
        engine = HttpEngine(self.config)

        payload = engine._build_payload("test text", "standard")

        self.assertEqual(payload["text"], "test text")
        self.assertEqual(payload["mode"], "standard")
        self.assertTrue(payload["preserve"]["urls"])
        self.assertEqual(payload["api_key"], "test-key")


class TestCleanupManager(unittest.TestCase):
    """Test cases for CleanupManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "cleanup": {
                "enabled": True,
                "mode": "standard",
                "engine": "rule"
            },
            "filler_words": ["um", "uh", "like"]
        }

    def test_rule_engine_cleanup(self):
        """Test cleanup using rule engine."""
        manager = CleanupManager(self.config)
        result = manager.clean_text("um hello world", mode="standard")

        self.assertNotIn("um", result)
        self.assertIn("hello", result)

    def test_bypass_cleanup(self):
        """Test bypassing cleanup."""
        manager = CleanupManager(self.config)
        original = "um hello world"
        result = manager.clean_text(original, bypass=True)

        self.assertEqual(result, original)

    def test_disabled_cleanup(self):
        """Test when cleanup is disabled."""
        config = self.config.copy()
        config["cleanup"]["enabled"] = False

        manager = CleanupManager(config)
        original = "um hello world"
        result = manager.clean_text(original)

        self.assertEqual(result, original)

    @patch('parrator.cleanup.llm_engine.requests')
    def test_engine_fallback(self, mock_requests):
        """Test fallback from primary to rule engine."""
        config = self.config.copy()
        config["cleanup"]["engine"] = "localllm"
        config["local_llm_endpoint"] = "http://127.0.0.1:11434"

        # Mock LLM failure
        mock_requests.post.side_effect = Exception("LLM error")

        manager = CleanupManager(config)
        result = manager.clean_text("um hello world", mode="standard")

        # Should still get cleaned text from rule engine fallback
        self.assertIsInstance(result, str)

    def test_get_engine_status(self):
        """Test getting engine status."""
        manager = CleanupManager(self.config)
        status = manager.get_engine_status()

        self.assertIn("rule", status)
        self.assertIsInstance(status["rule"], str)

    def test_get_available_engines(self):
        """Test getting list of available engines."""
        manager = CleanupManager(self.config)
        available = manager.get_available_engines()

        self.assertIn("rule", available)
        self.assertIsInstance(available, list)


class TestSampleInputsOutputs(unittest.TestCase):
    """Test the exact sample inputs/outputs from the issue specification."""

    def setUp(self):
        """Set up test fixtures."""
        config = {
            "filler_words": ["um", "uh", "like", "you know", "i mean", "sort of", "kind of"],
            "preserve_patterns": {
                "urls": True, "emails": True, "code": True, "all_caps": True
            }
        }
        self.engine = RuleEngine(config)

    def test_sample_input_1_conservative(self):
        """Test sample input 1 in conservative mode."""
        text = "um okay so i think we should, you know, send the email tomorrow morning it's kind of important"
        result = self.engine.clean(text, mode="conservative")

        # Conservative mode: fixes grammar/punctuation but doesn't remove fillers
        expected = "Um okay so I think we should, you know, send the email tomorrow morning it's kind of important."
        self.assertEqual(result, expected)

    def test_sample_input_1_standard(self):
        """Test sample input 1 in standard mode."""
        text = "um okay so i think we should, you know, send the email tomorrow morning it's kind of important"
        result = self.engine.clean(text, mode="standard")

        # Standard mode: removes fillers and "I think", capitalizes properly
        expected = "Okay so we should, send the email tomorrow morning it's important."
        self.assertEqual(result, expected)

    def test_sample_input_1_rewrite(self):
        """Test sample input 1 in rewrite mode."""
        text = "um okay so i think we should, you know, send the email tomorrow morning it's kind of important"
        result = self.engine.clean(text, mode="rewrite")

        # Rewrite mode: currently same as standard (could be enhanced later)
        expected = "Okay so we should, send the email tomorrow morning it's important."
        self.assertEqual(result, expected)

    def test_sample_input_2_standard(self):
        """Test sample input 2 in standard mode."""
        text = "check this link https://example.com and email john_doe@example.com um thanks"
        result = self.engine.clean(text, mode="standard")

        expected = "Check this link: https://example.com and email john_doe@example.com. Thanks."
        self.assertEqual(result, expected)

    def test_sample_input_3_standard(self):
        """Test sample input 3 in standard mode."""
        text = "i mean it's like really really slow"
        result = self.engine.clean(text, mode="standard")

        expected = "It's really slow."
        self.assertEqual(result, expected)

    def test_sample_input_4_conservative(self):
        """Test sample input 4 in conservative mode."""
        text = "run `npm install` and open https://foo.bar/docs"
        result = self.engine.clean(text, mode="conservative")

        expected = "Run `npm install` and open https://foo.bar/docs."
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
"""
Cleanup manager for coordinating different cleanup engines.
"""

import time
from typing import Any, Dict, Optional

from .engine_base import CleanupEngineBase
from .http_engine import HttpEngine
from .llm_engine import LocalLLMEngine
from .rule_engine import RuleEngine


class CleanupManager:
    """Manages text cleanup using different engines based on configuration."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.engines: Dict[str, CleanupEngineBase] = {}
        self._initialize_engines()

    def _initialize_engines(self):
        """Initialize all available cleanup engines."""
        # Rule engine is always available
        # Extract cleanup-specific config for the rule engine
        cleanup_config = self.config.get("cleanup", {})
        rule_engine_config = {
            "filler_words": cleanup_config.get(
                "filler_words",
                [
                    "um",
                    "uh",
                    "er",
                    "ah",
                    "like",
                    "you know",
                    "i mean",
                    "sort of",
                    "kind of",
                    "right",
                    "yeah",
                    "yep",
                    "yup",
                    "hmm",
                    "well",
                    "anyway",
                    "basically",
                ],
            ),
            "preserve_patterns": cleanup_config.get(
                "preserve_patterns",
                {
                    "urls": True,
                    "emails": True,
                    "code": True,
                    "hashtags": True,
                    "emojis": True,
                    "all_caps": True,
                },
            ),
        }
        self.engines["rule"] = RuleEngine(rule_engine_config)

        # Local LLM engine (optional)
        try:
            self.engines["localllm"] = LocalLLMEngine(self.config)
        except Exception as e:
            print(f"Failed to initialize LocalLLM engine: {e}")

        # HTTP engine (optional)
        try:
            self.engines["http"] = HttpEngine(self.config)
        except Exception as e:
            print(f"Failed to initialize HTTP engine: {e}")

    def clean_text(
        self, text: str, mode: Optional[str] = None, bypass: bool = False
    ) -> str:
        """
        Clean text using the configured engine.

        Args:
            text: Input text to clean
            mode: Cleanup mode ("conservative", "standard", "rewrite")
            bypass: If True, bypass cleanup and return original text

        Returns:
            Cleaned text
        """
        if bypass or not text or not text.strip():
            return text

        # Check if cleanup is enabled
        if not self.config.get("cleanup", {}).get("enabled", True):
            return text

        start_time = time.time()
        original_length = len(text)

        # Get the configured engine
        engine_name = self.config.get("cleanup", {}).get("engine", "rule")
        # Use the provided mode parameter, fallback to config mode if not provided
        if mode is None:
            mode = self.config.get("cleanup", {}).get("mode", "standard")

        # Try the primary engine first
        cleaned_text = self._try_engine(engine_name, text, mode or "standard")

        # If primary engine fails, fallback to rule engine
        if cleaned_text == text and engine_name != "rule":
            print(f"Primary engine '{engine_name}' failed, falling back to rule engine")
            cleaned_text = self._try_engine("rule", text, mode or "standard")

        processing_time = (time.time() - start_time) * 1000
        chars_saved = original_length - len(cleaned_text)

        if chars_saved > 0:
            print(
                f"Cleanup complete: {original_length} → {len(cleaned_text)} "
                f"chars • {processing_time:.0f}ms"
            )

        return cleaned_text

    def _try_engine(self, engine_name: str, text: str, mode: str) -> str:
        """Try to clean text using a specific engine."""
        engine = self.engines.get(engine_name)
        if not engine:
            return text

        if not engine.is_available():
            print(f"Engine '{engine_name}' is not available")
            return text

        try:
            return engine.clean(text, mode)
        except Exception as e:
            print(f"Engine '{engine_name}' failed: {e}")
            return text

    def get_engine_status(self) -> Dict[str, str]:
        """Get status of all engines."""
        status = {}
        for name, engine in self.engines.items():
            status[name] = engine.get_status()
        return status

    def is_engine_available(self, engine_name: str) -> bool:
        """Check if a specific engine is available."""
        engine = self.engines.get(engine_name)
        return engine.is_available() if engine else False

    def get_available_engines(self) -> list[str]:
        """Get list of available engines."""
        return [name for name, engine in self.engines.items() if engine.is_available()]

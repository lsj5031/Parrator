"""
Local LLM cleanup engine.

Provides AI-powered text cleaning using local LLM services like Ollama.
"""

import json
import time
from typing import Dict, Any, Optional

import requests  # type: ignore[import-untyped]

from .engine_base import CleanupEngineBase


class LocalLLMEngine(CleanupEngineBase):
    """Local LLM cleanup engine using services like Ollama."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.endpoint = config.get("local_llm_endpoint", "http://127.0.0.1:11434")
        self.model = config.get("local_llm_model", "llama3.2:3b")
        self.timeout = config.get("local_llm_timeout", 30)

    def clean(self, text: str, mode: str = "standard") -> str:
        """Clean text using local LLM."""
        if not text or not text.strip():
            return text

        start_time = time.time()
        original_length = len(text)

        try:
            prompt = self._get_prompt(text, mode)
            cleaned_text = self._call_llm(prompt)

            if cleaned_text:
                processing_time = (time.time() - start_time) * 1000
                chars_saved = original_length - len(cleaned_text)
                print(f"LLM Cleaned: {original_length} → {len(cleaned_text)} chars • {processing_time:.0f}ms")
                return cleaned_text.strip()
            else:
                print("LLM returned empty response, falling back to rule-based")
                return self._fallback_clean(text, mode)

        except Exception as e:
            print(f"LLM cleanup failed: {e}, falling back to rule-based")
            return self._fallback_clean(text, mode)

    def _get_prompt(self, text: str, mode: str) -> str:
        """Get appropriate prompt for the cleanup mode."""
        base_prompt = "You are a writing corrector. "

        if mode == "conservative":
            prompt = (
                base_prompt +
                "Fix grammar and punctuation only. Do not change wording or meaning. "
                "Preserve URLs, emails, numbers, code-like text, and proper nouns. "
                "Return only the corrected text.\n\n"
                f"Text: {text}"
            )
        elif mode == "standard":
            prompt = (
                base_prompt +
                "Fix grammar and punctuation, remove filler words ('um', 'uh', 'like', 'you know', 'I mean'), "
                "and lightly tighten wording. Do not change meaning. Do not fabricate content. "
                "Preserve URLs, emails, numbers, code-like text, and proper nouns. "
                "Return only the cleaned text.\n\n"
                f"Text: {text}"
            )
        else:  # rewrite
            prompt = (
                base_prompt +
                "Fix grammar and punctuation, remove all filler words and disfluencies, "
                "and rewrite for clarity and conciseness. Make it professional and neutral in tone. "
                "Preserve meaning, URLs, emails, numbers, code-like text, and proper nouns. "
                "Do not fabricate content. Return only the rewritten text.\n\n"
                f"Text: {text}"
            )

        return prompt

    def _call_llm(self, prompt: str) -> Optional[str]:
        """Call the local LLM service."""
        try:
            # Try Ollama API first
            if "11434" in self.endpoint:
                return self._call_ollama(prompt)
            else:
                # Try generic OpenAI-compatible API
                return self._call_openai_compatible(prompt)

        except Exception as e:
            print(f"LLM API call failed: {e}")
            return None

    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama API."""
        url = f"{self.endpoint}/api/generate"
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for consistent results
                "top_p": 0.9,
                "max_tokens": min(len(prompt) + 200, 1000)  # Reasonable limit
            }
        }

        response = requests.post(url, json=data, timeout=self.timeout)
        response.raise_for_status()

        result = response.json()
        return result.get("response", "").strip()

    def _call_openai_compatible(self, prompt: str) -> Optional[str]:
        """Call OpenAI-compatible API."""
        url = f"{self.endpoint}/v1/chat/completions"
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": min(len(prompt) + 200, 1000),
            "stream": False
        }

        response = requests.post(url, json=data, timeout=self.timeout)
        response.raise_for_status()

        result = response.json()
        choices = result.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "").strip()

        return None

    def _fallback_clean(self, text: str, mode: str) -> str:
        """Fallback to rule-based cleaning."""
        from .rule_engine import RuleEngine
        rule_engine = RuleEngine(self.config)
        return rule_engine.clean(text, mode)

    def is_available(self) -> bool:
        """Check if local LLM service is available."""
        try:
            # Try to ping the service
            if "11434" in self.endpoint:
                # Ollama health check
                url = f"{self.endpoint}/api/tags"
            else:
                # Generic health check
                url = f"{self.endpoint}/v1/models"

            response = requests.get(url, timeout=5)
            return response.status_code == 200

        except Exception:
            return False

    def get_status(self) -> str:
        """Get LLM engine status."""
        if self.is_available():
            return f"Local LLM available at {self.endpoint}"
        else:
            return f"Local LLM unavailable at {self.endpoint}"
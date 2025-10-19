"""
HTTP endpoint cleanup engine.

Provides text cleaning using custom HTTP endpoints.
"""

import json
import time
from typing import Dict, Any, Optional

import requests  # type: ignore[import-untyped]

from .engine_base import CleanupEngineBase


class HttpEngine(CleanupEngineBase):
    """HTTP endpoint cleanup engine."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.endpoint = config.get("http_endpoint", "http://127.0.0.1:5055")
        self.timeout = config.get("http_timeout", 10)
        self.api_key = config.get("http_api_key", "")
        self.headers = config.get("http_headers", {})

    def clean(self, text: str, mode: str = "standard") -> str:
        """Clean text using HTTP endpoint."""
        if not text or not text.strip():
            return text

        start_time = time.time()
        original_length = len(text)

        try:
            payload = self._build_payload(text, mode)
            cleaned_text = self._call_endpoint(payload)

            if cleaned_text:
                processing_time = (time.time() - start_time) * 1000
                chars_saved = original_length - len(cleaned_text)
                print(f"HTTP Cleaned: {original_length} → {len(cleaned_text)} chars • {processing_time:.0f}ms")
                return cleaned_text.strip()
            else:
                print("HTTP endpoint returned empty response, falling back to rule-based")
                return self._fallback_clean(text, mode)

        except Exception as e:
            print(f"HTTP cleanup failed: {e}, falling back to rule-based")
            return self._fallback_clean(text, mode)

    def _build_payload(self, text: str, mode: str) -> Dict[str, Any]:
        """Build HTTP request payload."""
        # Default payload format
        payload = {
            "text": text,
            "mode": mode,
            "preserve": {
                "urls": True,
                "emails": True,
                "code": True,
                "hashtags": True,
                "emojis": True,
                "all_caps": True
            }
        }

        # Add API key if configured
        if self.api_key:
            payload["api_key"] = self.api_key

        return payload

    def _call_endpoint(self, payload: Dict[str, Any]) -> Optional[str]:
        """Call the HTTP endpoint."""
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Parrator/1.0"
        }

        # Add custom headers
        headers.update(self.headers)

        # Add API key to header if configured (alternative to payload)
        if self.api_key and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            # Try to parse response
            result = response.json()

            # Common response formats
            if "cleaned_text" in result:
                return result["cleaned_text"]
            elif "text" in result:
                return result["text"]
            elif "result" in result:
                return result["result"]
            elif "cleaned" in result:
                return result["cleaned"]
            else:
                # If the response is just a string, return it
                if isinstance(result, str):
                    return result
                # If it's a simple response with one key, return that value
                elif len(result) == 1:
                    return next(iter(result.values()))

        except requests.exceptions.RequestException as e:
            print(f"HTTP request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in HTTP call: {e}")
            return None

        return None

    def _fallback_clean(self, text: str, mode: str) -> str:
        """Fallback to rule-based cleaning."""
        from .rule_engine import RuleEngine
        rule_engine = RuleEngine(self.config)
        return rule_engine.clean(text, mode)

    def is_available(self) -> bool:
        """Check if HTTP endpoint is available."""
        try:
            # Try a simple health check or ping
            health_url = self.endpoint.rstrip("/v1/clean") + "/health"

            try:
                response = requests.get(health_url, timeout=5)
                return response.status_code == 200
            except requests.exceptions.RequestException:
                # If health endpoint fails, try the main endpoint with a minimal test
                test_payload = {"text": "test", "mode": "conservative"}
                response = requests.post(
                    self.endpoint,
                    json=test_payload,
                    timeout=2
                )
                return response.status_code in [200, 400, 422]  # Accept errors as "available"

        except Exception:
            return False

    def get_status(self) -> str:
        """Get HTTP engine status."""
        if self.is_available():
            return f"HTTP endpoint available at {self.endpoint}"
        else:
            return f"HTTP endpoint unavailable at {self.endpoint}"
"""HTTP client for remote inference server."""

from typing import Optional

import requests


def transcribe_http(
    pcm_bytes: bytes, sr: int, lang: str, endpoint: str, timeout: int = 15
) -> tuple[bool, Optional[str]]:
    """Send audio to inference server for transcription.

    Args:
        pcm_bytes: Raw PCM audio data
        sr: Sample rate
        lang: Language code
        endpoint: Server endpoint URL
        timeout: Request timeout in seconds

    Returns:
        Tuple of (success, text)
    """
    try:
        url = f"{endpoint}/v1/transcribe"
        params = {"sr": sr, "lang": lang, "format": "pcm_s16le"}

        response = requests.post(
            url,
            params=params,
            data=pcm_bytes,
            timeout=timeout,
            headers={"Content-Type": "application/octet-stream"},
        )
        response.raise_for_status()

        result = response.json()
        text = result.get("text", "").strip()
        latency = result.get("latency_ms", 0)

        print(f"HTTP transcription completed in {latency:.1f}ms")
        return True, text if text else None

    except requests.exceptions.Timeout:
        print(f"HTTP transcription timeout after {timeout}s")
        return False, None
    except requests.exceptions.ConnectionError:
        print("HTTP transcription failed: Connection error")
        return False, None
    except requests.exceptions.HTTPError as e:
        print(
            f"HTTP transcription failed: {e.response.status_code} - {e.response.text}"
        )
        return False, None
    except Exception as e:
        print(f"HTTP transcription failed: {e}")
        return False, None


def check_server_health(endpoint: str, timeout: int = 5) -> bool:
    """Check if inference server is healthy.

    Args:
        endpoint: Server endpoint URL
        timeout: Request timeout in seconds

    Returns:
        True if server is healthy
    """
    try:
        url = f"{endpoint}/healthz"
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        result = response.json()
        status = result.get("status")
        if status == "healthy":
            model = result.get("model", "unknown")
            backend = result.get("backend", "unknown")
            print(f"Server healthy: model={model}, backend={backend}")
            return True
        else:
            print(f"Server unhealthy: status={status}")
            return False

    except Exception as e:
        print(f"Health check failed: {e}")
        return False

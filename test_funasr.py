#!/usr/bin/env python3
"""Integration smoke test for optional FunASR backend."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "parrator"))

from parrator.config import Config  # noqa: E402
from parrator.transcriber import Transcriber  # noqa: E402


def _skip(message: str) -> bool:
    print(message)
    return True


def test_funasr_integration() -> bool:
    print("Testing FunASR integration...")

    config = Config()
    config.set("backend", "funasr")
    config.set("model_name", "funasr/paraformer-zh")

    transcriber = Transcriber(config)

    if not Transcriber.funasr_supported():
        return _skip("⚠ FunASR dependencies not installed, skipping FunASR model load test")

    print("Loading FunASR model...")
    if transcriber.load_model():
        print("✓ FunASR model loaded successfully!")
        print(f"Model name: {transcriber.model_name}")
        return True

    print("✗ Failed to load FunASR model")
    return False


def test_onnx_fallback() -> bool:
    print("\nTesting ONNX fallback...")

    config = Config()
    config.set("backend", "onnx")
    config.set("model_name", "nemo-parakeet-tdt-0.6b-v2")

    transcriber = Transcriber(config)

    print("Loading ONNX model...")
    if transcriber.load_model():
        print("✓ ONNX model loaded successfully!")
        print(f"Model name: {transcriber.model_name}")
        return True

    print("✗ Failed to load ONNX model")
    return False


if __name__ == "__main__":
    print("Parrator FunASR Integration Test")
    print("=" * 40)

    funasr_success = test_funasr_integration()
    onnx_success = test_onnx_fallback()

    print("\n" + "=" * 40)
    print("Test Results:")
    print(f"FunASR: {'✓ PASS' if funasr_success else '⚠ SKIPPED' if Transcriber.funasr_supported() is False else '✗ FAIL'}")
    print(f"ONNX: {'✓ PASS' if onnx_success else '✗ FAIL'}")

    if funasr_success or onnx_success:
        print("\nIntegration test completed!")
        sys.exit(0)

    print("\nIntegration test failed!")
    sys.exit(1)

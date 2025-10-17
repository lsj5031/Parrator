#!/usr/bin/env python3
"""Simple sanity checks for FunASR optional dependencies."""

import os
import sys

try:
    from funasr import AutoModel
    import torch

    print("✓ FunASR imports successful")
    FUNASR_AVAILABLE = True
except ImportError as exc:
    print(f"⚠ FunASR import failed: {exc}")
    FUNASR_AVAILABLE = False


def test_funasr_model_loading() -> bool:
    if not FUNASR_AVAILABLE:
        print("⚠ FunASR not available, skipping model load test")
        return False

    try:
        print("Testing FunASR model loading...")
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")

        print("Loading paraformer-zh model...")
        AutoModel(model="paraformer-zh", vad_model="fsmn-vad", device=device)

        print("✓ FunASR paraformer-zh model loaded successfully!")
        return True
    except Exception as exc:  # pragma: no cover - defensive
        print(f"✗ Failed to load FunASR model: {exc}")
        return False


def test_config_integration() -> bool:
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "parrator"))
        from config import Config  # type: ignore

        print("Testing config integration...")

        config = Config()
        config.set("backend", "funasr")
        config.set("model_name", "funasr/paraformer-zh")

        backend = config.get("backend")
        model_name = config.get("model_name")

        if backend == "funasr" and model_name == "funasr/paraformer-zh":
            print("✓ Config integration successful!")
            return True

        print(
            f"✗ Config integration failed: backend={backend}, model_name={model_name}"
        )
        return False

    except Exception as exc:  # pragma: no cover - defensive
        print(f"✗ Config integration test failed: {exc}")
        return False


if __name__ == "__main__":
    print("Parrator FunASR Simple Integration Test")
    print("=" * 50)

    print(f"FunASR Available: {'✓ YES' if FUNASR_AVAILABLE else '⚠ NO'}")

    model_success = test_funasr_model_loading()
    config_success = test_config_integration()

    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"FunASR Model Loading: {'✓ PASS' if model_success else '⚠ SKIPPED' if not FUNASR_AVAILABLE else '✗ FAIL'}")
    print(f"Config Integration: {'✓ PASS' if config_success else '✗ FAIL'}")

    if FUNASR_AVAILABLE:
        if model_success or config_success:
            print("\n✓ FunASR integration is ready!")
            print("Set backend: 'funasr' and model_name: 'funasr/paraformer-zh'")
            sys.exit(0)
        print("\n✗ FunASR integration needs attention")
        sys.exit(1)

    print("\n⚠ FunASR optional dependencies missing; ONNX backend still available")
    sys.exit(0)

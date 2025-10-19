#!/usr/bin/env python3
"""
Demo script for Smart Cleanup functionality.

This script demonstrates the different cleanup modes and engines.
"""

import sys
import os

# Add the parrator module to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parrator.cleanup.manager import CleanupManager


def demo_cleanup():
    """Demonstrate Smart Cleanup functionality."""
    print("🎤 Parrator Smart Cleanup Demo")
    print("=" * 50)

    # Sample transcribed texts with typical ASR issues
    sample_texts = [
        {
            "name": "Business Email",
            "text": "um okay so i think we should, you know, send the email tomorrow morning it's kind of important"
        },
        {
            "name": "Technical Instructions",
            "text": "run `npm install` and open https://foo.bar/docs um thanks"
        },
        {
            "name": "URL Preservation",
            "text": "check this link https://example.com and email john_doe@example.com um thanks"
        },
        {
            "name": "Casual Speech",
            "text": "i mean it's like really really slow"
        },
        {
            "name": "Repeated Words",
            "text": "the the quick brown fox jumped over over the the lazy dog"
        }
    ]

    # Configuration for cleanup
    config = {
        "cleanup": {
            "enabled": True,
            "mode": "standard",
            "engine": "rule"
        },
        "filler_words": [
            "um", "uh", "er", "ah", "like", "you know", "i mean",
            "sort of", "kind of", "right", "yeah", "yep", "yup",
            "hmm", "well", "so", "anyway", "basically"
        ],
        "preserve_patterns": {
            "urls": True, "emails": True, "code": True, "all_caps": True
        }
    }

    # Initialize cleanup manager
    manager = CleanupManager(config)

    print(f"🔧 Available engines: {', '.join(manager.get_available_engines())}")
    print(f"📊 Engine status: {manager.get_engine_status()}")
    print()

    # Test each sample with different modes
    for sample in sample_texts:
        print(f"📝 Sample: {sample['name']}")
        print(f"Original: {sample['text']}")
        print()

        modes = ["conservative", "standard", "rewrite"]
        for mode in modes:
            # Update config for this mode
            config["cleanup"]["mode"] = mode
            manager = CleanupManager(config)

            result = manager.clean_text(sample['text'], mode=mode)
            print(f"{mode.capitalize():12}: {result}")

        print("-" * 50)

    # Test bypass functionality
    print("🔄 Bypass Demo")
    print("Original: um hello world this is a test")
    normal_result = manager.clean_text("um hello world this is a test", bypass=False)
    bypass_result = manager.clean_text("um hello world this is a test", bypass=True)
    print(f"Normal:    {normal_result}")
    print(f"Bypass:    {bypass_result}")
    print()

    # Performance info
    print("⚡ Performance Note")
    print("Rule-based cleanup processes text in <1ms for typical inputs")
    print("Target: ≤40ms for 350-character texts")
    print()

    print("✅ Demo complete! Smart Cleanup is ready for integration.")


if __name__ == "__main__":
    demo_cleanup()
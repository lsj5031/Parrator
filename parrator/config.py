"""
Minimal configuration management.
"""

import json
import os
from typing import Any, Dict


class Config:
    """Simple configuration manager."""

    def __init__(self):
        self.config_path = self._get_config_path()
        self.defaults = {
            "hotkey": "ctrl+shift+;",
            "model_name": "nemo-parakeet-tdt-0.6b-v2",
            "backend": "onnx",
            # Inference mode: embedded (default) or http
            "inference_mode": "embedded",
            "inference_endpoint": "http://localhost:5005",
            # Secondary Mandarin (FunASR) hotkey and model (config-only fields)
            "hotkey_mandarin": "ctrl+alt+m",
            "mandarin_backend": "funasr",
            "mandarin_model_name": "funasr/paraformer-zh",
            "auto_paste": True,
            "auto_start_with_system": False,
            "enable_text_refinement": True,
            "remove_filler_words": True,
            "filler_words": [
                "uh",
                "um",
                "er",
                "ah",
                "like",
                "you know",
                "I mean",
                "sort of",
                "kind of",
                "right",
                "yeah",
                "yep",
                "yup",
                "hmm",
                "hmm",
                "well",
                "so",
                "anyway",
                "basically",
            ],
            "text_refinement_models": {
                "nemo-parakeet-tdt-0.6b-v2": True,
                "nvidia/parakeet-tdt-0.6b-v2": True,
                "openai/whisper-tiny": True,
                "openai/whisper-base": True,
                "openai/whisper-small": True,
                "funasr/paraformer-zh": True,
                "funasr/whisper-large-v3": True,
            },
        }
        self.config = self._load_config()

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value
        self._save_config()

    def _get_config_path(self) -> str:
        """Get path to config file."""
        if os.name == "nt":  # Windows
            config_dir = os.path.expandvars("%APPDATA%\\Parrator")
        else:  # macOS/Linux
            config_dir = os.path.expanduser("~/.config/parrator")

        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "config.json")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                # Ensure all defaults are present
                for key, value in self.defaults.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"Error loading config: {e}")

        # Create default config
        self._save_config_dict(self.defaults.copy())
        return self.defaults.copy()

    def _save_config(self):
        """Save current configuration to file."""
        self._save_config_dict(self.config)

    def _save_config_dict(self, config_dict: Dict[str, Any]):
        """Save configuration dictionary to file."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(config_dict, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

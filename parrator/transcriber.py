"""
Simplified transcription service using ONNX models.
"""

import os
from typing import Optional, Tuple

import onnxruntime as ort
from onnx_asr import load_model

from .config import Config


class Transcriber:
    """Handles speech-to-text transcription."""

    def __init__(self, config: Config):
        self.config = config
        self.model = None
        self.model_name = None

    def load_model(self) -> bool:
        """Load the transcription model."""
        try:
            model_name = self.config.get(
                'model_name', 'nemo-parakeet-tdt-0.6b-v2')

            # Get available ONNX providers
            providers = self._get_providers()

            print(f"Loading model: {model_name}")
            self.model = load_model(model_name, providers=providers)
            self.model_name = model_name

            print(f"Model '{model_name}' loaded successfully")
            return True

        except Exception as e:
            print(f"Failed to load model: {e}")
            return False

    def transcribe_file(self, audio_path: str) -> Tuple[bool, Optional[str]]:
        """Transcribe an audio file."""
        if not self.model:
            return False, None

        if not os.path.exists(audio_path):
            return False, None

        try:
            result = self.model.recognize(audio_path)

            # Handle different result formats
            if isinstance(result, str):
                text = result.strip()
            elif isinstance(result, list) and result:
                if isinstance(result[0], dict) and 'text' in result[0]:
                    text = ' '.join(s.get('text', '') for s in result).strip()
                else:
                    text = ' '.join(str(s) for s in result).strip()
            else:
                text = str(result).strip()

            return True, text if text else None

        except Exception as e:
            print(f"Transcription failed: {e}")
            return False, None

    def _get_providers(self):
        """Get ONNX runtime providers in preferred order."""
        available = ort.get_available_providers()
        preferred = [
            'DmlExecutionProvider',    # DirectML (Windows/WSL)
            'ROCMExecutionProvider',   # AMD GPU
            'CUDAExecutionProvider',   # NVIDIA GPU
            'CPUExecutionProvider'     # CPU fallback
        ]

        providers = [p for p in preferred if p in available]
        return providers or ['CPUExecutionProvider']

"""Transcription service supporting ONNX and optional FunASR backends."""

import os
from typing import Optional, Tuple

import onnxruntime as ort
from onnx_asr import load_model

try:
    import torch
    from funasr import AutoModel
except ImportError:  # pragma: no cover - optional dependency
    AutoModel = None  # type: ignore[assignment]
    torch = None  # type: ignore[assignment]
    FUNASR_AVAILABLE = False
else:
    FUNASR_AVAILABLE = True

from .config import Config


class Transcriber:
    """Handles speech-to-text transcription."""

    def __init__(
        self,
        config: Config,
        backend: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.config = config
        self._override_backend = backend
        self._override_model_name = model_name
        self.model = None
        self.model_name = None
        self.backend: Optional[str] = None

    def load_model(self) -> bool:
        """Load the transcription model."""
        try:
            model_name = self._override_model_name or self.config.get(
                "model_name", "nemo-parakeet-tdt-0.6b-v2"
            )
            backend = self._override_backend or self.config.get("backend", "onnx")

            if backend == "funasr":
                if FUNASR_AVAILABLE and AutoModel is not None and torch is not None:
                    if self._load_funasr_model(model_name):
                        return True
                    print("FunASR load failed, falling back to ONNX")
                else:
                    print("FunASR backend requested but dependencies are not installed")

                if self._override_backend:
                    return False

                fallback_model = self.config.defaults.get(
                    "model_name", "nemo-parakeet-tdt-0.6b-v2"
                )
                return self._load_onnx_model(fallback_model)

            return self._load_onnx_model(model_name)

        except Exception as e:
            print(f"Failed to load model: {e}")
            return False

    def _load_onnx_model(self, model_name: str) -> bool:
        try:
            providers = self._get_providers()

            if self._try_load_local_model(providers):
                return True

            print(f"Loading ONNX model: {model_name}")
            self.model = load_model(model_name, providers=providers)
            self.model_name = model_name
            self.backend = "onnx"

            print(f"Model '{model_name}' loaded successfully")
            return True

        except Exception as e:
            print(f"Failed to load ONNX model: {e}")
            return False

    def _load_funasr_model(self, model_name: str) -> bool:
        try:
            if not FUNASR_AVAILABLE or AutoModel is None or torch is None:
                print("FunASR not available, falling back to ONNX")
                return self._load_onnx_model(model_name)

            device = "cuda:0" if torch.cuda.is_available() else "cpu"

            print(f"Loading FunASR model: {model_name} on {device}")

            funasr_model_map = {
                "funasr/paraformer-zh": "paraformer-zh",
                "funasr/whisper-large-v3": "iic/Whisper-large-v3",
            }

            actual_model_name = funasr_model_map.get(model_name, model_name)

            self.model = AutoModel(
                model=actual_model_name, vad_model="fsmn-vad", device=device
            )
            self.model_name = f"{model_name} (FunASR)"
            self.backend = "funasr"

            print(f"FunASR model '{model_name}' loaded successfully")
            return True

        except Exception as e:
            print(f"Failed to load FunASR model: {e}")
            return False

    def get_device_info(self) -> str:
        try:
            backend = (
                self.backend
                or self._override_backend
                or self.config.get("backend", "onnx")
            )
            device = None
            if backend == "funasr" and FUNASR_AVAILABLE and torch is not None:
                device = "cuda:0" if torch.cuda.is_available() else "cpu"
            model_ref = (
                self.model_name
                or self._override_model_name
                or self.config.get("model_name")
            )
            return (
                f"backend={backend}, model={model_ref}, device={device or 'N/A'}"
            )
        except Exception:
            return "backend=unknown, model=unknown, device=unknown"

    def transcribe_file(self, audio_path: str) -> Tuple[bool, Optional[str]]:
        if not self.model or not os.path.exists(audio_path):
            return False, None

        try:
            backend = (
                self.backend
                or self._override_backend
                or self.config.get("backend", "onnx")
            )

            if backend == "funasr" and FUNASR_AVAILABLE and AutoModel is not None:
                result = self.model.generate(input=audio_path)
                if isinstance(result, list) and result:
                    text = result[0].get("text", "").strip()
                else:
                    text = str(result).strip()
            else:
                result = self.model.recognize(audio_path)
                if isinstance(result, str):
                    text = result.strip()
                elif isinstance(result, list) and result:
                    if isinstance(result[0], dict) and "text" in result[0]:
                        text = " ".join(s.get("text", "") for s in result).strip()
                    else:
                        text = " ".join(str(s) for s in result).strip()
                else:
                    text = str(result).strip()

            return True, text if text else None

        except Exception as e:
            print(f"Transcription failed: {e}")
            return False, None

    def _get_providers(self):
        available = ort.get_available_providers()
        preferred = [
            "DmlExecutionProvider",
            "ROCMExecutionProvider",
            "CUDAExecutionProvider",
            "CPUExecutionProvider",
        ]

        providers = [p for p in preferred if p in available]
        return providers or ["CPUExecutionProvider"]

    def _try_load_local_model(self, providers) -> bool:
        try:
            encoder_path = "encoder-model.onnx"
            decoder_path = "decoder_joint-model.onnx"
            vocab_path = "vocab.txt"

            if all(os.path.exists(f) for f in [encoder_path, decoder_path, vocab_path]):
                print("Loading model from local files...")
                self.model = load_model(
                    "nemo-parakeet-tdt-0.6b-v2",
                    encoder_path=encoder_path,
                    decoder_path=decoder_path,
                    vocab_path=vocab_path,
                    providers=providers,
                )
                self.model_name = "nemo-parakeet-tdt-0.6b-v2 (local)"
                self.backend = "onnx"
                print("Local model loaded successfully")
                return True
            return False
        except Exception as e:
            print(f"Failed to load local model: {e}")
            return False

    @staticmethod
    def funasr_supported() -> bool:
        return FUNASR_AVAILABLE

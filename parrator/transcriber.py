"""Transcription service supporting ONNX, HTTP, and optional FunASR backends."""

import os
from typing import Any, Optional, Tuple

import numpy as np
import onnxruntime as ort  # type: ignore[import]
from onnx_asr import load_model  # type: ignore[import]

from .engine_client import check_server_health, transcribe_http

try:
    import torch  # type: ignore[import]
    from funasr import AutoModel  # type: ignore[import-untyped]
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
        self.model: Optional[Any] = None
        self.model_name: Optional[str] = None
        self.backend: Optional[str] = None
        self._http_available = False

    def load_model(self) -> bool:
        """Load the transcription model."""
        try:
            inference_mode = self.config.get("inference_mode", "embedded")

            # Check if we should use HTTP mode
            if inference_mode == "http":
                endpoint = self.config.get(
                    "inference_endpoint", "http://localhost:5005"
                )
                if check_server_health(endpoint):
                    self._http_available = True
                    self.backend = "http"
                    self.model_name = f"HTTP server at {endpoint}"
                    print(f"Using HTTP inference mode: {endpoint}")
                    return True
                else:
                    print(
                        f"HTTP server not available at {endpoint}, "
                        "falling back to embedded mode"
                    )
                    self._http_available = False

            # Embedded mode (ONNX/FunASR)
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
            return f"backend={backend}, model={model_ref}, device={device or 'N/A'}"
        except Exception:
            return "backend=unknown, model=unknown, device=unknown"

    def transcribe_file(self, audio_path: str) -> Tuple[bool, Optional[str]]:
        if not os.path.exists(audio_path):
            return False, None

        try:
            backend = (
                self.backend
                or self._override_backend
                or self.config.get("backend", "onnx")
            )

            # HTTP mode
            if backend == "http" and self._http_available:
                endpoint = self.config.get(
                    "inference_endpoint", "http://localhost:5005"
                )

                # Read audio file as PCM bytes
                try:
                    import soundfile as sf

                    with sf.SoundFile(audio_path) as f:
                        audio_data = f.read(dtype=np.float32)
                        sr = f.samplerate
                except ImportError:
                    print("soundfile not available for HTTP mode")
                    return False, None

                # Convert to PCM16 bytes
                pcm_bytes = (audio_data * 32767).astype(np.int16).tobytes()

                return transcribe_http(pcm_bytes, int(sr), "en", endpoint)

            # Embedded mode
            if not self.model:
                return False, None

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
                model_dir = os.path.dirname(os.path.abspath(encoder_path))
                self.model = load_model(
                    "nemo-parakeet-tdt-0.6b-v2", path=model_dir, providers=providers
                )
                self.model_name = "nemo-parakeet-tdt-0.6b-v2 (local)"
                self.backend = "onnx"
                print("Local model loaded successfully")
                return True
            return False
        except Exception as e:
            print(f"Failed to load local model: {e}")
            return False

    def transcribe_pcm(
        self, pcm_bytes: bytes, sr: int = 16000
    ) -> Tuple[bool, Optional[str]]:
        """Transcribe raw PCM audio data."""
        try:
            backend = (
                self.backend
                or self._override_backend
                or self.config.get("backend", "onnx")
            )

            # HTTP mode
            if backend == "http" and self._http_available:
                endpoint = self.config.get(
                    "inference_endpoint", "http://localhost:5005"
                )
                return transcribe_http(pcm_bytes, sr, "en", endpoint)

            # Embedded mode - convert to temporary file
            if not self.model:
                return False, None

            import tempfile

            import soundfile as sf

            # Convert PCM bytes to numpy array
            audio_data = (
                np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            )

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                with sf.SoundFile(
                    temp_file.name, mode="w", samplerate=sr, channels=1
                ) as f:
                    f.write(audio_data)

                return self.transcribe_file(temp_file.name)

        except Exception as e:
            print(f"PCM transcription failed: {e}")
            return False, None

    @staticmethod
    def funasr_supported() -> bool:
        return FUNASR_AVAILABLE

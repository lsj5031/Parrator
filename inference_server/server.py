"""FastAPI inference server for ONNX models with DirectML support."""

import io
import os
import time
from typing import Optional

import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from onnx_asr import load_model
from pydantic import BaseModel
from soundfile import SoundFile

app = FastAPI(title="Parrator Inference Server", version="1.0.0")

# Global model instance
model = None
model_name = None
providers = None


class TranscribeRequest(BaseModel):
    sr: int = 16000
    lang: str = "en"
    format: str = "pcm_s16le"
    chunk_ms: Optional[int] = None


class TranscribeResponse(BaseModel):
    text: str
    latency_ms: float


class HealthResponse(BaseModel):
    status: str
    model: str
    backend: str


def get_providers():
    """Get available ONNX Runtime providers with DirectML priority."""
    available = ort.get_available_providers()
    preferred = [
        "DmlExecutionProvider",  # DirectML
        "ROCMExecutionProvider",
        "CUDAExecutionProvider",
        "CPUExecutionProvider",
    ]

    providers = [p for p in preferred if p in available]
    if not providers:
        providers = ["CPUExecutionProvider"]

    print(f"Available providers: {available}")
    print(f"Using providers: {providers}")
    return providers


def load_onnx_model(model_name_str: str = "nemo-parakeet-tdt-0.6b-v2"):
    """Load ONNX model with DirectML support."""
    global model, model_name, providers

    try:
        providers = get_providers()

        # Try local model first
        encoder_path = "encoder-model.onnx"
        decoder_path = "decoder_joint-model.onnx"
        vocab_path = "vocab.txt"

        if all(os.path.exists(f) for f in [encoder_path, decoder_path, vocab_path]):
            print("Loading model from local files...")
            model_dir = os.path.dirname(os.path.abspath(encoder_path))
            model = load_model(model_name_str, path=model_dir, providers=providers)
            model_name = f"{model_name_str} (local)"
        else:
            print(f"Loading ONNX model: {model_name_str}")
            model = load_model(model_name_str, providers=providers)
            model_name = model_name_str

        print(f"Model '{model_name}' loaded successfully")
        return True

    except Exception as e:
        print(f"Failed to load model: {e}")
        return False


@app.on_event("startup")
async def startup_event():
    """Initialize the model on server startup."""
    success = load_onnx_model()
    if not success:
        print("WARNING: Failed to load model on startup")


@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    backend = providers[0] if providers else "unknown"
    return HealthResponse(
        status="healthy", model=model_name or "unknown", backend=backend
    )


@app.post("/v1/transcribe", response_model=TranscribeResponse)
async def transcribe(request: TranscribeRequest, raw_data: bytes = b""):
    """Transcribe audio data."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    start_time = time.time()

    try:
        # Convert raw PCM bytes to numpy array
        if request.format == "pcm_s16le":
            # 16-bit little-endian PCM
            audio_data = (
                np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
            )
        elif request.format == "pcm_f32le":
            # 32-bit little-endian float PCM
            audio_data = np.frombuffer(raw_data, dtype=np.float32)
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported format: {request.format}"
            )

        # Resample if needed (basic implementation - you might want a better resampler)
        if request.sr != 16000:
            # Simple linear interpolation - replace with proper resampling if needed
            original_length = len(audio_data)
            target_length = int(original_length * 16000 / request.sr)
            audio_data = np.interp(
                np.linspace(0, 1, target_length),
                np.linspace(0, 1, original_length),
                audio_data,
            )

        # Create temporary WAV file in memory
        with io.BytesIO() as wav_buffer:
            with SoundFile(
                wav_buffer, mode="w", samplerate=16000, channels=1, format="WAV"
            ) as sf:
                sf.write(audio_data)

            wav_buffer.seek(0)
            # Save to temp file for onnx_asr compatibility
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(wav_buffer.getvalue())
                temp_path = temp_file.name

        try:
            # Transcribe using the model
            result = model.recognize(temp_path)

            if isinstance(result, str):
                text = result.strip()
            elif isinstance(result, list) and result:
                if isinstance(result[0], dict) and "text" in result[0]:
                    text = " ".join(s.get("text", "") for s in result).strip()
                else:
                    text = " ".join(str(s) for s in result).strip()
            else:
                text = str(result).strip()

        finally:
            # Clean up temp file
            import os

            try:
                os.unlink(temp_path)
            except:
                pass

        latency_ms = (time.time() - start_time) * 1000

        return TranscribeResponse(text=text if text else "", latency_ms=latency_ms)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.post("/v1/load_model")
async def load_model_endpoint(model_name_str: str = "nemo-parakeet-tdt-0.6b-v2"):
    """Load a different model."""
    success = load_onnx_model(model_name_str)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to load model")

    return {"status": "success", "model": model_name}


if __name__ == "__main__":
    import os
    import uvicorn

    # Load model on startup
    if not load_onnx_model():
        print("Failed to load model, exiting...")
        exit(1)

    # Run server
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5005))

    print(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

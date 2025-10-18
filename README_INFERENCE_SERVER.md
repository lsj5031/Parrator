# Parrator Inference Server (Optional GPU Acceleration)

This directory contains components for running Parrator's transcription engine in a separate Windows container with GPU acceleration via DirectML.

## Architecture

- **Tray App (Parrator.exe)**: Native Windows application with UI, hotkeys, and audio capture
- **Inference Server**: Optional Windows container running ONNX models with DirectML GPU acceleration
- **Communication**: HTTP API between tray app and inference server

## Quick Start

### 1. Build the Container Image

```powershell
# From project root
.\docker\build.ps1
```

### 2. Run with GPU Support

```powershell
# Create models directory if needed
mkdir C:\Parrator\Models

# Run the container
.\docker\run.ps1
```

### 3. Configure Parrator for HTTP Mode

Add to your Parrator config (`%APPDATA%\Parrator\config.json`):

```json
{
  "inference_mode": "http",
  "inference_endpoint": "http://localhost:5005"
}
```

Or use the Parrator UI to switch to "HTTP Mode" in settings.

## Container Features

- **GPU Acceleration**: DirectML execution provider for AMD/Intel/NVIDIA GPUs
- **HTTP API**: RESTful endpoints for transcription and health checks
- **Model Loading**: Supports local ONNX models or Hugging Face downloads
- **Health Monitoring**: `/healthz` endpoint for service availability

## API Endpoints

### Health Check
```
GET /healthz
```
Returns server status, loaded model, and backend provider.

### Transcription
```
POST /v1/transcribe
Content-Type: application/octet-stream

Parameters:
- sr: Sample rate (default: 16000)
- lang: Language code (default: "en") 
- format: Audio format (default: "pcm_s16le")

Body: Raw PCM audio data
```

Returns:
```json
{
  "text": "transcribed text",
  "latency_ms": 123.4
}
```

### Load Model
```
POST /v1/load_model?model_name=nemo-parakeet-tdt-0.6b-v2
```

## GPU Requirements

The container uses DirectML for GPU acceleration, which supports:
- **NVIDIA**: CUDA-capable GPUs
- **AMD**: DirectX 12-capable GPUs  
- **Intel**: DirectX 12-capable integrated/discrete GPUs

No vendor-specific SDKs required - DirectML is built into Windows.

## Docker Configuration

The container uses:
- **Process Isolation**: Required for GPU access
- **DirectX Device**: `--device class/5B45201D-F2F2-4F3B-85BB-30FF1F953599`
- **Port Mapping**: Host 5005 → Container 5005
- **Volume Mount**: Models directory (optional)

## Troubleshooting

### Container Won't Start
- Ensure Docker Desktop is running with Windows containers
- Check that your Windows version supports Windows containers
- Verify DirectX device class is available

### GPU Not Detected
- Confirm GPU supports DirectX 12
- Check DirectML provider availability in container logs
- Fall back to CPU execution if needed

### Connection Errors
- Verify port 5005 isn't blocked by firewall
- Check container is running: `docker ps`
- Test health endpoint: `curl http://localhost:5005/healthz`

## Development

### Local Testing
```bash
# Install dependencies
pip install -r inference_server/requirements.txt

# Run server locally
cd inference_server
python server.py
```

### Model Files
Place ONNX model files in `inference_server/models/`:
- `encoder-model.onnx`
- `decoder_joint-model.onnx` 
- `vocab.txt`

Or mount models directory via Docker volume.

## Performance

DirectML provides vendor-agnostic GPU acceleration with typical speedups:
- **NVIDIA**: 2-5x faster than CPU
- **AMD**: 2-4x faster than CPU  
- **Intel**: 1.5-3x faster than CPU

Actual performance depends on model size and GPU capabilities.
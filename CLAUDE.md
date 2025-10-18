# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Parrator is a Python-based speech-to-text desktop application that runs as a system tray application. It provides real-time speech transcription with global hotkey activation and automatic clipboard integration.

**Key Technologies:**
- Python 3.11+ with Poetry dependency management
- ONNX Runtime with DirectML GPU acceleration for Windows
- FunASR for Chinese speech recognition
- PyQt/pystray for system tray interface
- PyInstaller for executable creation

## Development Commands

### Setup and Installation
```bash
# Install dependencies
poetry install

# Install with optional features
poetry install --with textrefinement  # AI text refinement
poetry install --with funasr          # Chinese speech recognition
poetry install --with textrefinement,funasr  # All features

# Install development dependencies
poetry install --with dev
```

### Running the Application
```bash
# Run the application
poetry run python -m parrator

# Run with specific Python path
poetry run python -m parrator
```

### Code Quality and Testing
```bash
# Run linting
poetry run ruff check parrator/

# Run type checking
poetry run mypy parrator/ --ignore-missing-imports

# Compile check (syntax validation)
poetry run python -m py_compile parrator/*.py
```

### Building Executable
```bash
# Build Windows executable
poetry run pyinstaller Parrator.spec

# Test PyInstaller build (simplified)
poetry run pyinstaller --onefile --windowed --name=parrator-test --add-data="parrator/resources;resources" parrator/__main__.py
```

### Download Model Assets
```bash
# Download Parakeet ONNX models (required for first run)
poetry run python -c "from huggingface_hub import hf_hub_download; repo_id='istupakov/parakeet-tdt-0.6b-v2-onnx'; [hf_hub_download(repo_id=repo_id, filename=name, local_dir='.', local_dir_use_symlinks=False) for name in ['encoder-model.onnx','decoder_joint-model.onnx','vocab.txt']]"
```

## Architecture Overview

### Core Components

1. **System Tray Application** (`parrator/tray_app.py`)
   - Main application controller
   - Manages hotkeys, recording state, and user interactions
   - Coordinates between audio recording, transcription, and text refinement

2. **Transcription Engine** (`parrator/transcriber.py`)
   - Dual backend support: ONNX (default) and FunASR
   - Model loading and inference management
   - Backend switching and fallback logic

3. **Audio Recording** (`parrator/audio_recorder.py`)
   - Real-time audio capture using sounddevice
   - Voice Activity Detection (VAD) using webrtcvad
   - Audio format conversion and buffering

4. **Configuration System** (`parrator/config.py`)
   - JSON-based user settings
   - Model selection, hotkey configuration, feature toggles
   - Runtime configuration updates

5. **Text Refinement** (`parrator/text_refiner.py`)
   - Optional AI-powered post-processing
   - Grammar correction and filler word removal
   - Transformers-based text improvement

### Key Design Patterns

- **Async Model Loading**: Transcription models load in background to avoid blocking UI
- **Hotkey Management**: Separate hotkey managers for different languages/backends
- **Notification System**: User feedback via system notifications and tray icon updates
- **Error Handling**: Graceful fallbacks between backends and models

### Configuration Structure

The application uses a JSON configuration file with these key settings:
- `hotkey`: Global keyboard shortcut (default: "ctrl+shift+;")
- `backend`: Transcription backend ("onnx" or "funasr")
- `model_name`: Speech recognition model selection
- `auto_paste`: Automatic clipboard pasting
- `enable_text_refinement`: AI text improvement
- `remove_filler_words`: Filler word removal

### Model Support

**ONNX Backend Models:**
- `nemo-parakeet-tdt-0.6b-v2` (default, fast and accurate)
- `nvidia/parakeet-tdt-0.6b-v2`
- `openai/whisper-tiny`, `whisper-base`, `whisper-small`

**FunASR Backend Models:**
- `funasr/paraformer-zh` (Chinese speech recognition)
- `funasr/whisper-large-v3` (Chinese-optimized Whisper)

## Development Notes

### Platform Considerations
- **Windows**: Primary development platform with DirectML GPU support
- **Linux**: Requires additional audio libraries (`python3-dev`)
- **macOS**: Requires accessibility permissions for global hotkeys

### GPU Acceleration
- Windows: DirectML support via `onnxruntime-directml`
- FunASR: Automatic CUDA detection for GPU acceleration
- Models download automatically on first use via Hugging Face Hub

### Testing Infrastructure
- Currently minimal test coverage
- CI/CD runs syntax checks, linting, and type checking
- PyInstaller build testing in CI pipeline
- Manual testing required for audio functionality

### Common Development Tasks

When modifying transcription logic:
1. Check both ONNX and FunASR backend compatibility
2. Test model loading and fallback scenarios
3. Verify audio format compatibility
4. Test with different languages if modifying FunASR integration

When updating UI/hotkeys:
1. Test global hotkey registration across platforms
2. Verify system tray icon updates and notifications
3. Test configuration persistence and updates
4. Check accessibility permissions on macOS

When adding new models:
1. Update supported models list in documentation
2. Test model download and caching
3. Verify GPU acceleration compatibility
4. Update configuration validation
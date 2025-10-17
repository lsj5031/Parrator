# Parrator

Simple speech-to-text tray application with global hotkey activation.

<div align="center">
  <a href="https://github.com/NullSense/Parrator">
    <img src="./Parrator.png" alt="Parrator Banner" width="30%">
  </a>
</div>

Parrator is a lightweight, always-on speech-to-text application that runs in your system tray. Press a hotkey to record speech and get instant transcription with automatic clipboard integration.

## Features

- **Global Hotkey Recording**: Press `Ctrl+Shift+;` from anywhere to start/stop recording
- **Multiple Backends**: Choose between ONNX models (default) or FunASR for enhanced Chinese speech recognition
- **AI-Powered Text Refinement**: Automatic grammar correction and filler word removal using NLP models
- **Automatic Transcription**: Uses NVIDIA Parakeet ONNX models (AMD GPU supported) for fast, accurate speech-to-text
- **Clipboard Integration**: Transcriptions are automatically copied to clipboard with optional auto-paste
- **System Tray**: Runs silently in the background with minimal resource usage
- **Cross-Platform (WIP, looking for testers)**:
    - [x] Win11
    - [ ] Linux
    - [ ] Mac
- **Auto-Startup**: Optional system startup integration

## Quick Start

### Install

Simply install the .exe.
Other platform executables WIP.

### Prerequisites

- Python 3.11+
- Poetry for dependency management

### Optional Dependencies

For enhanced features, install optional dependency groups:

```bash
# AI-powered text refinement (grammar correction)
poetry install --with textrefinement

# FunASR Chinese speech recognition
poetry install --with funasr

# Install all optional features
poetry install --with textrefinement,funasr
```

### (dev) Installation

1. **Clone and install**:
   ```bash
   git clone https://github.com/yourusername/parrator.git
   cd parrator
   poetry install
   ```

2. **Run**:
   ```bash
   poetry run python -m parrator
   ```

### Usage

1. **Start the app** - Look for the Parrator icon in your system tray
2. **Record speech** - Press `Ctrl+Shift+;` to start recording, press again to stop
3. **Get transcription** - Text is automatically copied to clipboard and optionally pasted

## Configuration

Right-click the tray icon and select "Settings" to edit configuration:

```json
{
  "hotkey": "ctrl+shift+;",
  "model_name": "nemo-parakeet-tdt-0.6b-v2",
  "backend": "onnx",
  "auto_paste": true,
  "auto_start_with_system": false,
  "enable_text_refinement": true,
  "remove_filler_words": true
}
```

### Settings

- **hotkey**: Global keyboard shortcut (e.g., "ctrl+shift+;", "alt+space")
- **backend**: Transcription backend - `"onnx"` (default) or `"funasr"` for Chinese speech recognition
- **model_name**: Speech recognition model to use
- **auto_paste**: Automatically paste transcription after copying to clipboard
- **auto_start_with_system**: Launch Parrator when your computer starts
- **enable_text_refinement**: Enable AI-powered grammar correction and text improvement
- **remove_filler_words**: Automatically remove filler words (um, uh, like, etc.)

## Supported Models

### ONNX Backend (default)
- `nemo-parakeet-tdt-0.6b-v2` (default, fast and accurate)
- `nvidia/parakeet-tdt-0.6b-v2`
- `openai/whisper-tiny` (lightweight)
- `openai/whisper-base`
- `openai/whisper-small`

### FunASR Backend (Chinese speech recognition)
- `funasr/paraformer-zh` - Optimized for Chinese speech recognition
- `funasr/whisper-large-v3` - FunASR's implementation of Whisper with Chinese support

## System Requirements

- **Windows**: Windows 10/11 with DirectML support for GPU acceleration
- **macOS**: macOS 10.14+ (may require accessibility permissions for global hotkeys)
- **Linux**: Modern Linux distribution with audio support

## Troubleshooting

### Hotkey Not Working
- **Windows**: Run as administrator if needed
- **macOS**: Grant accessibility permissions in System Preferences
- **Linux**: Install `python3-dev` and audio libraries

### No Audio Input
```bash
# Check available audio devices
python -c "import sounddevice; print(sounddevice.query_devices())"
```

### GPU Acceleration (Windows)
- Update graphics drivers
- Install Windows Media Feature Pack
- Verify DirectML is available

## Building Executable

```bash
poetry run pyinstaller Parrator.spec
```

### Bundling FunASR Dependencies (Chinese Support)

1. Build on an environment with Python 3.11+ and Poetry (self-hosted runner or local workstation).
2. Install dependencies including FunASR before running PyInstaller:
   ```bash
   poetry install --with funasr
   ```
3. Run the build command from the same environment so PyInstaller picks up the installed `funasr`, `modelscope`, and `torch` packages.
4. Ship the generated `dist/Parrator.exe`; end users will not need Python or Poetry because the FunASR runtime is embedded.

## Changelog

### v0.2.0 (Current)

#### New Features
- **FunASR Integration**: Added support for FunASR backend with enhanced Chinese speech recognition
- **AI-Powered Text Refinement**: Automatic grammar correction and filler word removal using NLP models
- **Multiple Backend Support**: Choose between ONNX and FunASR backends
- **Enhanced Configuration**: New configuration options for text refinement and backend selection

#### Improvements
- **Better Chinese Support**: Paraformer-zh model provides excellent Chinese speech recognition
- **GPU Acceleration**: Automatic CUDA detection for FunASR models
- **Fallback System**: Graceful fallback between backends if model loading fails
- **Enhanced UI**: Improved tray app with better status indicators

#### Technical Changes
- Added `funasr` and `textrefinement` optional dependency groups
- Updated configuration system with new defaults
- Improved error handling and logging
- Enhanced Windows CI/CD workflows

### v0.0.13

Previous version features and improvements.

## Contributing

Pull requests welcome! Please ensure code follows the existing style and includes appropriate tests.


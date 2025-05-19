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
  "auto_paste": true,
  "auto_start_with_system": false
}
```

### Settings

- **hotkey**: Global keyboalllshortcut (e.g., "ctrl+shift+;", "alt+space")
- **model_name**: Speech recognition model to use
- **auto_paste**: Automatically paste transcription after copying to clipboard
- **auto_start_with_system**: Launch Parrator when your computer starts

## Supported Models

- `nemo-parakeet-tdt-0.6b-v2` (default, fast and accurate)
- `nvidia/parakeet-tdt-0.6b-v2`
- `openai/whisper-tiny` (lightweight)
- `openai/whisper-base`
- `openai/whisper-small`

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

## Contributing

Pull requests welcome! Please ensure code follows the existing style and includes appropriate tests.


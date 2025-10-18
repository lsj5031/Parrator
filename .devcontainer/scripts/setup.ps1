# Windows Dev Container Setup Script for Parrator
# This script initializes the development environment

param(
    [switch]$SkipModels,
    [switch]$Verbose
)

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $(
        switch ($Level) {
            "ERROR" { "Red" }
            "WARN" { "Yellow" }
            "INFO" { "Green" }
            "DEBUG" { "Cyan" }
            default { "White" }
        }
    )
}

function Test-DirectML {
    Write-Log "Testing DirectML availability..."
    try {
        $pythonCode = @"
import onnxruntime as ort
providers = ort.get_available_providers()
print('Available providers:', providers)
if 'DmlExecutionProvider' in providers:
    print('DirectML is available!')
    exit(0)
else:
    print('DirectML not found')
    exit(1)
"@
        $result = python -c $pythonCode
        if ($LASTEXITCODE -eq 0) {
            Write-Log "DirectML is available!" "INFO"
            return $true
        } else {
            Write-Log "DirectML not available, will use CPU" "WARN"
            return $false
        }
    } catch {
        Write-Log "Failed to test DirectML: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Initialize-Models {
    Write-Log "Initializing speech recognition models..."

    $modelsDir = "C:\app\models"
    if (-not (Test-Path $modelsDir)) {
        New-Item -ItemType Directory -Force -Path $modelsDir | Out-Null
    }

    # Check if models already exist
    $requiredModels = @("encoder-model.onnx", "decoder_joint-model.onnx", "vocab.txt")
    $modelsExist = $requiredModels | ForEach-Object { Test-Path (Join-Path $modelsDir $_) } | Where-Object { $_ -eq $false }

    if ($modelsExist) {
        Write-Log "Downloading required models..." "INFO"
        try {
            $pythonCode = @"
from huggingface_hub import hf_hub_download
import os

repo_id = 'istupakov/parakeet-tdt-0.6b-v2-onnx'
models_dir = 'C:\\app\\models'

required_files = ['encoder-model.onnx', 'decoder_joint-model.onnx', 'vocab.txt']
for filename in required_files:
    file_path = os.path.join(models_dir, filename)
    if not os.path.exists(file_path):
        print(f'Downloading {filename}...')
        hf_hub_download(repo_id=repo_id, filename=filename, local_dir=models_dir, local_dir_use_symlinks=False)
        print(f'Downloaded {filename}')
    else:
        print(f'{filename} already exists')

print('Model initialization complete!')
"@
            python -c $pythonCode
            if ($LASTEXITCODE -eq 0) {
                Write-Log "Models downloaded successfully!" "INFO"
            } else {
                Write-Log "Failed to download models" "ERROR"
            }
        } catch {
            Write-Log "Error downloading models: $($_.Exception.Message)" "ERROR"
        }
    } else {
        Write-Log "Models already exist in $modelsDir" "INFO"
    }
}

function Initialize-AudioDevices {
    Write-Log "Testing audio device availability..."
    try {
        $pythonCode = @"
import sounddevice as sd
print('Available audio devices:')
for i, device in enumerate(sd.query_devices()):
    print(f'  {i}: {device["name"]} ({"input" if device["max_input_channels"] > 0 else ""}{"output" if device["max_output_channels"] > 0 else ""})')

default_input = sd.default.device[0]
default_output = sd.default.device[1]
print(f'Default input device: {default_input}')
print(f'Default output device: {default_output}')
"@
        $result = python -c $pythonCode
        Write-Log "Audio devices initialized" "INFO"
    } catch {
        Write-Log "Warning: Could not initialize audio devices: $($_.Exception.Message)" "WARN"
    }
}

function Initialize-DevelopmentTools {
    Write-Log "Initializing development tools..."

    # Create necessary directories
    $directories = @(
        "C:\app\audio",
        "C:\app\logs",
        "C:\app\temp",
        "C:\app\tests",
        "C:\app\docs"
    )

    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Force -Path $dir | Out-Null
            Write-Log "Created directory: $dir" "DEBUG"
        }
    }

    # Set up environment variables
    $env:PYTHONPATH = "C:\app"
    $env:MODELS_PATH = "C:\app\models"
    $env:LOGS_PATH = "C:\app\logs"
    $env:AUDIO_PATH = "C:\app\audio"

    # Test Poetry installation
    try {
        $poetryVersion = poetry --version
        Write-Log "Poetry version: $poetryVersion" "INFO"
    } catch {
        Write-Log "Poetry not found or not working" "ERROR"
    }

    # Test Python packages
    $criticalPackages = @("onnxruntime", "sounddevice", "fastapi", "pystray")
    foreach ($package in $criticalPackages) {
        try {
            $result = python -c "import $($package.Replace('-', '_')); print('$package OK')"
            Write-Log "$package is available" "DEBUG"
        } catch {
            Write-Log "Warning: $package not available" "WARN"
        }
    }
}

function Start-DevelopmentServices {
    Write-Log "Starting development services..."

    # Start inference server in background
    $serverScript = "C:\app\scripts\start-inference-server.ps1"
    if (Test-Path $serverScript) {
        Write-Log "Starting inference server..." "INFO"
        Start-Job -ScriptBlock {
            param($ScriptPath)
            & $ScriptPath
        } -ArgumentList $serverScript | Out-Null
    } else {
        Write-Log "Inference server script not found at $serverScript" "WARN"
    }

    # Start Jupyter Lab if available
    try {
        $jupyterCheck = python -c "import jupyterlab; print('OK')" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Starting Jupyter Lab..." "INFO"
            Start-Job -ScriptBlock {
                jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''
            } | Out-Null
        }
    } catch {
        Write-Log "Jupyter Lab not available" "DEBUG"
    }
}

# Main setup execution
Write-Log "Starting Parrator Windows Dev Container setup..." "INFO"

try {
    # Initialize development tools
    Initialize-DevelopmentTools

    # Test DirectML availability
    $directmlAvailable = Test-DirectML

    # Initialize models (unless skipped)
    if (-not $SkipModels) {
        Initialize-Models
    } else {
        Write-Log "Skipping model initialization" "INFO"
    }

    # Initialize audio devices
    Initialize-AudioDevices

    # Start development services
    Start-DevelopmentServices

    Write-Log "Setup completed successfully!" "INFO"
    Write-Log "Development environment is ready." "INFO"
    Write-Log "Inference Server: http://localhost:5005" "INFO"
    Write-Log "Jupyter Lab: http://localhost:8888" "INFO"
    Write-Log "Health Check: http://localhost:5005/healthz" "INFO"

} catch {
    Write-Log "Setup failed: $($_.Exception.Message)" "ERROR"
    exit 1
}

exit 0
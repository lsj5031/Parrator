# escape=`
# Comprehensive Windows Dev Container for Parrator
# Uses Poetry for dependency management with integrated inference server

FROM python:3.11-windowsservercore-ltsc2022

SHELL ["pwsh", "-NoLogo", "-Command"]

# Set Windows environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8

# Install Chocolatey and system packages
RUN Write-Host "Installing Chocolatey and system packages..."; \
    Set-ExecutionPolicy Bypass -Scope Process -Force; \
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; \
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1')); \
    choco feature disable -n=showDownloadProgress

# Install system dependencies
RUN Write-Host "Installing system dependencies..."; \
    choco install -y --no-progress \
        ffmpeg \
        git \
        sysinternals \
        directx-sdk; \
    RefreshEnv

# Install Poetry and Python development tools
RUN Write-Host "Installing Poetry and Python development tools..."; \
    python -m pip install --upgrade pip setuptools wheel; \
    python -m pip install poetry==1.8.3; \
    $scriptDir = python -c "import sysconfig; print(sysconfig.get_path('scripts'))"; \
    [System.Environment]::SetEnvironmentVariable('PATH', "$env:PATH;$scriptDir", 'Machine')

# Install development-specific Python packages (not in Poetry)
RUN Write-Host "Installing development tools..."; \
    python -m pip install --upgrade \
        jupyterlab \
        ipython \
        pytest \
        pytest-cov \
        py-spy \
        memory-profiler \
        netron \
        tensorboard

# Create development directories
RUN Write-Host "Creating development directories..."; \
    New-Item -ItemType Directory -Force -Path C:\app; \
    New-Item -ItemType Directory -Force -Path C:\app\models; \
    New-Item -ItemType Directory -Force -Path C:\app\audio; \
    New-Item -ItemType Directory -Force -Path C:\app\logs; \
    New-Item -ItemType Directory -Force -Path C:\app\scripts

# Set working directory
WORKDIR C:/app

# Copy project files
COPY pyproject.toml poetry.lock* ./
COPY .devcontainer/scripts/ C:/app/scripts/

# Install Poetry dependencies
RUN Write-Host "Installing Poetry dependencies..."; \
    poetry config virtualenvs.create false; \
    poetry install --with dev,textrefinement,funasr

# Copy source code
COPY parrator/ ./parrator/
COPY inference_server/ ./inference_server/

# Create startup script
RUN Write-Host "Creating startup script..."; \
    @'
# Development container startup script
Write-Host "Starting Parrator Development Environment..."
Write-Host "Python version: $(python --version)"
Write-Host "Poetry version: $(poetry --version)"

# Set up environment
$env:PYTHONPATH = "C:\app"
$env:MODELS_PATH = "C:\app\models"
$env:LOGS_PATH = "C:\app\logs"

# Check DirectML availability
try {
    $pythonCode = @"
import onnxruntime as ort
providers = ort.get_available_providers()
print(f'Available providers: {providers}')
if 'DmlExecutionProvider' in providers:
    print('DirectML is available!')
else:
    print('DirectML not found, will use CPU')
"@
    python -c $pythonCode
} catch {
    Write-Host "Warning: Could not check DirectML availability"
}

Write-Host "Development environment ready!"
Write-Host "VS Code Server: Available on port 8000"
Write-Host "Inference Server: Available on port 5005"
Write-Host "Jupyter Lab: Available on port 8888"
'@ | Out-File -FilePath C:\app\startup.ps1 -Encoding UTF8

# Expose development ports
EXPOSE 8000 5005 8888

# Set entry point
ENTRYPOINT ["pwsh", "-NoLogo", "-Command", "& C:/app/startup.ps1"]

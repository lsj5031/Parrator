# PowerShell script to run Parrator inference container with GPU support

# Container configuration
$ImageName = "parrator-inference:win-ltsc2022"
$ContainerName = "parrator-ortdml"
$HostPort = 5005
$ContainerPort = 5005

# Paths (adjust these for your setup)
$ModelsHostPath = "C:\Parrator\Models"
$ModelsContainerPath = "C:\app\models"

Write-Host "Starting Parrator inference container with GPU support..." -ForegroundColor Green

# Check if container exists and remove it
if (docker ps -a --filter "name=$ContainerName" --format "{{.Names}}" | Select-String $ContainerName) {
    Write-Host "Removing existing container..." -ForegroundColor Yellow
    docker rm -f $ContainerName
}

# Run container with GPU support via DirectX device class
# This enables DirectML acceleration inside the container
docker run --isolation=process `
    --device class/5B45201D-F2F2-4F3B-85BB-30FF1F953599 `
    -p "${HostPort}:${ContainerPort}" `
    -v "${ModelsHostPath}:${ModelsContainerPath}" `
    --name $ContainerName `
    $ImageName

if ($LASTEXITCODE -eq 0) {
    Write-Host "Container started successfully!" -ForegroundColor Green
    Write-Host "API endpoint: http://localhost:${HostPort}" -ForegroundColor Cyan
    Write-Host "Health check: http://localhost:${HostPort}/healthz" -ForegroundColor Cyan
} else {
    Write-Host "Failed to start container!" -ForegroundColor Red
    exit 1
}
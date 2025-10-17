# PowerShell script to build Parrator inference container

$ImageName = "parrator-inference:win-ltsc2022"

Write-Host "Building Parrator inference container..." -ForegroundColor Green

# Build the Docker image
docker build -f docker/Dockerfile.win -t $ImageName .

if ($LASTEXITCODE -eq 0) {
    Write-Host "Image built successfully: $ImageName" -ForegroundColor Green
    Write-Host "Run with: .\docker\run.ps1" -ForegroundColor Cyan
} else {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}
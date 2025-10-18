# Start Inference Server Script
# This script starts the ONNX inference server with DirectML support

param(
    [switch]$Verbose,
    [switch]$Debug,
    [string]$ModelName = "nemo-parakeet-tdt-0.6b-v2",
    [int]$Port = 5005,
    [string]$Host = "0.0.0.0"
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

function Test-Environment {
    Write-Log "Testing inference server environment..." "INFO"

    # Test Python imports
    $requiredModules = @("fastapi", "uvicorn", "onnxruntime", "onnx_asr", "numpy", "soundfile")
    foreach ($module in $requiredModules) {
        try {
            $result = python -c "import $($module.Replace('-', '_')); print('OK')"
            Write-Log "$module is available" "DEBUG"
        } catch {
            Write-Log "ERROR: $module not available" "ERROR"
            return $false
        }
    }

    # Test DirectML availability
    try {
        $pythonCode = @"
import onnxruntime as ort
providers = ort.get_available_providers()
print('Available providers:', providers)
if 'DmlExecutionProvider' in providers:
    print('DirectML is available!')
    exit(0)
else:
    print('DirectML not found, will use CPU')
    exit(0)
"@
        $result = python -c $pythonCode
        Write-Log "ONNX Runtime providers checked" "INFO"
    } catch {
        Write-Log "Failed to check ONNX Runtime providers: $($_.Exception.Message)" "ERROR"
        return $false
    }

    return $true
}

function Start-Server {
    Write-Log "Starting inference server..." "INFO"
    Write-Log "Model: $ModelName" "INFO"
    Write-Log "Host: $Host" "INFO"
    Write-Log "Port: $Port" "INFO"

    $serverDir = "C:\app\inference_server"
    if (-not (Test-Path $serverDir)) {
        Write-Log "ERROR: Inference server directory not found: $serverDir" "ERROR"
        return $false
    }

    try {
        # Change to server directory
        Set-Location $serverDir

        # Set environment variables
        $env:HOST = $Host
        $env:PORT = $Port.ToString()
        $env:PYTHONPATH = "C:\app"

        if ($Debug) {
            $env:LOG_LEVEL = "DEBUG"
        } else {
            $env:LOG_LEVEL = "INFO"
        }

        # Build the command
        $pythonArgs = @("server.py")
        if ($Verbose) {
            $pythonArgs += "--verbose"
        }
        if ($Debug) {
            $pythonArgs += "--debug"
        }

        Write-Log "Starting server with: python $($pythonArgs -join ' ')" "DEBUG"

        # Start the server
        if ($Verbose -or $Debug) {
            python $pythonArgs
        } else {
            # Redirect output to suppress verbose logging
            python $pythonArgs 2>&1 | ForEach-Object {
                if ($_ -match "ERROR|WARN|INFO|DEBUG") {
                    Write-Log $_ "INFO"
                } elseif ($Verbose) {
                    Write-Log $_ "DEBUG"
                }
            }
        }

        return $true
    } catch {
        Write-Log "Failed to start inference server: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Wait-ForServer {
    param([int]$TimeoutSeconds = 30)

    Write-Log "Waiting for server to start..." "INFO"
    $healthUrl = "http://localhost:$Port/healthz"

    $startTime = Get-Date
    $timeout = [TimeSpan]::FromSeconds($TimeoutSeconds)

    while ((Get-Date) - $startTime -lt $timeout) {
        try {
            $response = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Log "Server is healthy and responding!" "INFO"
                return $true
            }
        } catch {
            # Server not ready yet, continue waiting
        }

        Start-Sleep -Seconds 1
        Write-Host "." -NoNewline
    }

    Write-Host ""
    Write-Log "Server did not become healthy within $TimeoutSeconds seconds" "WARN"
    return $false
}

function Show-ServerInfo {
    Write-Log "Server Information:" "INFO"
    Write-Log "==================" "INFO"
    Write-Log "Server URL: http://$Host`:$Port" "INFO"
    Write-Log "Health Check: http://localhost:$Port/healthz" "INFO"
    Write-Log "API Docs: http://localhost:$Port/docs" "INFO"
    Write-Log "Model: $ModelName" "INFO"

    # Show available endpoints
    try {
        $endpointsUrl = "http://localhost:$Port/docs"
        Write-Log "API documentation available at: $endpointsUrl" "INFO"
    } catch {
        Write-Log "API documentation not yet available" "DEBUG"
    }
}

# Main execution
Write-Log "Starting Parrator Inference Server..." "INFO"

try {
    # Test environment
    if (-not (Test-Environment)) {
        Write-Log "Environment test failed, exiting..." "ERROR"
        exit 1
    }

    # Start the server
    if (Start-Server) {
        # Wait for server to be healthy
        if (Wait-ForServer) {
            Show-ServerInfo
            Write-Log "Inference server started successfully!" "INFO"
        } else {
            Write-Log "Server started but health check failed" "WARN"
        }
    } else {
        Write-Log "Failed to start inference server" "ERROR"
        exit 1
    }

} catch {
    Write-Log "Inference server startup failed: $($_.Exception.Message)" "ERROR"
    exit 1
}
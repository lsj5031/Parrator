# Start Development Services Script
# This script starts all development services for Parrator

param(
    [switch]$Verbose,
    [string]$LogLevel = "INFO"
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

function Start-InferenceServer {
    Write-Log "Starting inference server..." "INFO"

    $serverScript = "C:\app\scripts\start-inference-server.ps1"
    if (Test-Path $serverScript) {
        try {
            # Start in background job
            $job = Start-Job -ScriptBlock {
                param($ScriptPath, $Verbose)
                if ($Verbose) {
                    & $ScriptPath -Verbose
                } else {
                    & $ScriptPath
                }
            } -ArgumentList $serverScript, $Verbose

            Write-Log "Inference server started (Job ID: $($job.Id))" "INFO"

            # Wait a moment and check if it's running
            Start-Sleep -Seconds 3
            $jobState = Get-Job -Id $job.Id
            if ($jobState.State -eq "Running") {
                Write-Log "Inference server is running" "INFO"
                return $job
            } else {
                Write-Log "Inference server failed to start" "ERROR"
                $jobState | Receive-Job | Write-Log "ERROR"
                return $null
            }
        } catch {
            Write-Log "Failed to start inference server: $($_.Exception.Message)" "ERROR"
            return $null
        }
    } else {
        Write-Log "Inference server script not found: $serverScript" "ERROR"
        return $null
    }
}

function Start-JupyterLab {
    Write-Log "Starting Jupyter Lab..." "INFO"

    try {
        # Check if Jupyter Lab is available
        $jupyterCheck = python -c "import jupyterlab; print('OK')" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Log "Jupyter Lab not available, skipping..." "WARN"
            return $null
        }

        # Start Jupyter Lab in background
        $job = Start-Job -ScriptBlock {
            jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password='' --NotebookApp.disable_check_xsrf=True
        }

        Write-Log "Jupyter Lab started (Job ID: $($job.Id))" "INFO"

        # Wait a moment and check if it's running
        Start-Sleep -Seconds 3
        $jobState = Get-Job -Id $job.Id
        if ($jobState.State -eq "Running") {
            Write-Log "Jupyter Lab is running" "INFO"
            return $job
        } else {
            Write-Log "Jupyter Lab failed to start" "ERROR"
            $jobState | Receive-Job | Write-Log "ERROR"
            return $null
        }
    } catch {
        Write-Log "Failed to start Jupyter Lab: $($_.Exception.Message)" "ERROR"
        return $null
    }
}

function Start-TensorBoard {
    Write-Log "Starting TensorBoard..." "INFO"

    try {
        # Check if TensorBoard is available
        $tensorboardCheck = python -c "import tensorboard; print('OK')" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Log "TensorBoard not available, skipping..." "WARN"
            return $null
        }

        # Create logs directory if it doesn't exist
        $logsDir = "C:\app\logs"
        if (-not (Test-Path $logsDir)) {
            New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
        }

        # Start TensorBoard in background
        $job = Start-Job -ScriptBlock {
            param($LogsDir)
            tensorboard --logdir=$LogsDir --host=0.0.0.0 --port=6006 --reload_interval=5
        } -ArgumentList $logsDir

        Write-Log "TensorBoard started (Job ID: $($job.Id))" "INFO"

        # Wait a moment and check if it's running
        Start-Sleep -Seconds 3
        $jobState = Get-Job -Id $job.Id
        if ($jobState.State -eq "Running") {
            Write-Log "TensorBoard is running" "INFO"
            return $job
        } else {
            Write-Log "TensorBoard failed to start" "ERROR"
            $jobState | Receive-Job | Write-Log "ERROR"
            return $null
        }
    } catch {
        Write-Log "Failed to start TensorBoard: $($_.Exception.Message)" "ERROR"
        return $null
    }
}

function Test-Services {
    Write-Log "Testing service availability..." "INFO"

    $services = @{
        "Inference Server" = @{ Port = 5005; Path = "/healthz" }
        "Jupyter Lab" = @{ Port = 8888; Path = "/" }
        "TensorBoard" = @{ Port = 6006; Path = "/" }
    }

    foreach ($serviceName in $services.Keys) {
        $service = $services[$serviceName]
        $url = "http://localhost:$($service.Port)$($service.Path)"

        try {
            $response = Invoke-WebRequest -Uri $url -TimeoutSec 5 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Log "$serviceName is responding (Port: $($service.Port))" "INFO"
            } else {
                Write-Log "$serviceName returned status $($response.StatusCode)" "WARN"
            }
        } catch {
            Write-Log "$serviceName is not responding: $($_.Exception.Message)" "WARN"
        }
    }
}

function Show-ServiceStatus {
    Write-Log "Development Services Status:" "INFO"
    Write-Log "========================" "INFO"

    $jobs = Get-Job
    if ($jobs.Count -eq 0) {
        Write-Log "No services are currently running" "WARN"
        return
    }

    foreach ($job in $jobs) {
        $jobInfo = Get-Job -Id $job.Id
        Write-Log "Job $($job.Id): $($jobInfo.Name) - State: $($jobInfo.State)" "INFO"

        if ($jobInfo.State -eq "Failed") {
            $errorOutput = $jobInfo | Receive-Job -ErrorAction SilentlyContinue
            if ($errorOutput) {
                Write-Log "Error output: $errorOutput" "ERROR"
            }
        }
    }
}

# Main execution
Write-Log "Starting Parrator development services..." "INFO"

# Store service jobs for management
$script:serviceJobs = @{}

try {
    # Start inference server
    $inferenceJob = Start-InferenceServer
    if ($inferenceJob) {
        $script:serviceJobs["InferenceServer"] = $inferenceJob
    }

    # Start Jupyter Lab
    $jupyterJob = Start-JupyterLab
    if ($jupyterJob) {
        $script:serviceJobs["JupyterLab"] = $jupyterJob
    }

    # Start TensorBoard
    $tensorboardJob = Start-TensorBoard
    if ($tensorboardJob) {
        $script:serviceJobs["TensorBoard"] = $tensorboardJob
    }

    # Wait a moment for services to start
    Start-Sleep -Seconds 5

    # Test services
    Test-Services

    # Show final status
    Show-ServiceStatus

    Write-Log "Development services startup completed!" "INFO"
    Write-Log "======================================" "INFO"
    Write-Log "Available services:" "INFO"
    Write-Log "- Inference Server: http://localhost:5005" "INFO"
    Write-Log "- Health Check: http://localhost:5005/healthz" "INFO"
    Write-Log "- Jupyter Lab: http://localhost:8888" "INFO"
    Write-Log "- TensorBoard: http://localhost:6006" "INFO"
    Write-Log "======================================" "INFO"

} catch {
    Write-Log "Failed to start development services: $($_.Exception.Message)" "ERROR"

    # Clean up any started jobs
    foreach ($job in $script:serviceJobs.Values) {
        try {
            Stop-Job -Id $job.Id -ErrorAction SilentlyContinue
            Remove-Job -Id $job.Id -ErrorAction SilentlyContinue
        } catch {
            # Ignore cleanup errors
        }
    }

    exit 1
}

# Keep the script running to maintain services
Write-Log "Services are running. Press Ctrl+C to stop all services." "INFO"

try {
    while ($true) {
        Start-Sleep -Seconds 30

        # Check if any jobs have failed
        $failedJobs = @()
        foreach ($serviceName in $script:serviceJobs.Keys) {
            $job = $script:serviceJobs[$serviceName]
            $jobInfo = Get-Job -Id $job.Id -ErrorAction SilentlyContinue
            if ($jobInfo -and $jobInfo.State -eq "Failed") {
                $failedJobs += $serviceName
            }
        }

        if ($failedJobs.Count -gt 0) {
            Write-Log "Warning: The following services have failed: $($failedJobs -join ', ')" "WARN"
            Show-ServiceStatus
        }
    }
} catch [System.Management.Automation.HaltCommandException] {
    Write-Log "Stopping all development services..." "INFO"
} finally {
    # Clean up all jobs
    foreach ($job in $script:serviceJobs.Values) {
        try {
            Write-Log "Stopping job $($job.Id)..." "DEBUG"
            Stop-Job -Id $job.Id -ErrorAction SilentlyContinue
            Remove-Job -Id $job.Id -ErrorAction SilentlyContinue
        } catch {
            Write-Log "Error stopping job $($job.Id): $($_.Exception.Message)" "WARN"
        }
    }

    Write-Log "All services stopped." "INFO"
}
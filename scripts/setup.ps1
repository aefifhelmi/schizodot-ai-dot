# ============================================
# SchizoDot AI - Setup Script (Windows PowerShell)
# ============================================
# Run this script in PowerShell as Administrator if needed

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SchizoDot AI - Development Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Function to print status
function Print-Status($message) {
    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host $message
}

function Print-Warning($message) {
    Write-Host "[WARN] " -ForegroundColor Yellow -NoNewline
    Write-Host $message
}

function Print-Error($message) {
    Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
    Write-Host $message
}

# Check if Docker is installed
Write-Host "Checking prerequisites..." -ForegroundColor White

try {
    $dockerVersion = docker --version
    Print-Status "Docker is installed: $dockerVersion"
} catch {
    Print-Error "Docker is not installed. Please install Docker Desktop first."
    Write-Host "  Download: https://docs.docker.com/desktop/install/windows-install/"
    Write-Host ""
    Write-Host "  IMPORTANT for Windows:" -ForegroundColor Yellow
    Write-Host "  - Enable WSL2 backend (recommended)"
    Write-Host "  - Or enable Hyper-V"
    exit 1
}

# Check if Docker is running
try {
    docker info | Out-Null
    Print-Status "Docker is running"
} catch {
    Print-Error "Docker is not running. Please start Docker Desktop."
    exit 1
}

# Check Docker Compose
try {
    docker compose version | Out-Null
    Print-Status "Docker Compose is available"
} catch {
    Print-Error "Docker Compose is not available."
    exit 1
}

Write-Host ""
Write-Host "Setting up project..." -ForegroundColor White

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Print-Warning ".env file created from .env.example"
        Write-Host "  Please edit .env and add your AWS credentials before running Docker."
    } else {
        Print-Error ".env.example not found!"
        exit 1
    }
} else {
    Print-Status ".env file exists"
}

# Create required directories
New-Item -ItemType Directory -Force -Path "uploads" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path "logs\nginx" | Out-Null
Print-Status "Created uploads\ and logs\ directories"

# Check for model files
Write-Host ""
Write-Host "Checking model files..." -ForegroundColor White

$emotionWeightsDir = "services\emotion-detection\schizodot_emotion_demo\ai\emotion\weights"
$pillModelsDir = "flask-styled-ui-main\models"

$audioModel = Join-Path $emotionWeightsDir "audio_model.pkl"
$audioEncoder = Join-Path $emotionWeightsDir "audio_label_encoder.pkl"
$pillModel = Join-Path $pillModelsDir "best.pt"

if ((Test-Path $audioModel) -and (Test-Path $audioEncoder)) {
    Print-Status "Emotion model weights found"
} else {
    Print-Error "Emotion model weights missing!"
    Write-Host "  Required files:"
    Write-Host "    - $audioModel"
    Write-Host "    - $audioEncoder"
    Write-Host "  Contact the team lead to obtain these files."
}

if (Test-Path $pillModel) {
    Print-Status "Pill detection model found"
} else {
    Print-Error "Pill detection model missing!"
    Write-Host "  Required file: $pillModel"
    Write-Host "  Contact the team lead to obtain this file."
}

# Windows-specific checks
Write-Host ""
Write-Host "Windows-specific checks..." -ForegroundColor White

# Check for port conflicts
$port80 = Get-NetTCPConnection -LocalPort 80 -ErrorAction SilentlyContinue
if ($port80) {
    Print-Warning "Port 80 is in use. You may need to stop IIS or other services."
    Write-Host "  To stop IIS: iisreset /stop"
    Write-Host "  Or change nginx port in docker-compose.yml"
}

$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    Print-Warning "Port 8000 is in use by another application."
}

# Check WSL2
try {
    $wslStatus = wsl --status 2>&1
    if ($wslStatus -match "Default Version: 2") {
        Print-Status "WSL2 is configured"
    } else {
        Print-Warning "WSL2 may not be the default. For best performance, use WSL2."
        Write-Host "  Run: wsl --set-default-version 2"
    }
} catch {
    Print-Warning "Could not check WSL status"
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Edit .env file with your AWS credentials"
Write-Host "  2. Run: docker compose build"
Write-Host "  3. Run: docker compose up -d"
Write-Host "  4. Check status: docker compose ps"
Write-Host ""
Write-Host "Service URLs after startup:" -ForegroundColor White
Write-Host "  - Backend API:        http://localhost:8000/api/v1"
Write-Host "  - API Docs:           http://localhost:8000/docs"
Write-Host "  - Emotion Service:    http://localhost:8001"
Write-Host "  - Pill Detection:     http://localhost:8003"
Write-Host "  - Proto Compliance:   http://localhost:5001"
Write-Host "  - Flower (Celery):    http://localhost:5555"
Write-Host ""
Write-Host "Frontend (run separately in new terminals):" -ForegroundColor White
Write-Host "  - Patient Portal:      cd frontend\patient-portal; python -m http.server 3000"
Write-Host "  - Clinician Dashboard: cd frontend\clinician-dashboard; python -m http.server 3001"
Write-Host ""
Write-Host "Troubleshooting:" -ForegroundColor Yellow
Write-Host "  - If services fail, check: docker compose logs <service-name>"
Write-Host "  - For port conflicts, modify ports in docker-compose.yml"
Write-Host "  - Ensure Docker Desktop has enough resources (Settings > Resources)"
Write-Host ""

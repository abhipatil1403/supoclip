# SupoClip - Quick Start Script for Windows PowerShell
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SupoClip - AI Video Clipping Tool" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "Error: .env file not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please create a .env file with your API keys:"
    Write-Host "  1. Copy the template: cp .env.example .env"
    Write-Host "  2. Edit .env and add your API keys:"
    Write-Host "     - Transcription: ASSEMBLY_AI_API_KEY (or TRANSCRIPTION_PROVIDER=whisper for local free)"
    Write-Host "     - LLM: GOOGLE_API_KEY, OPENROUTER_API_KEY, OPENAI_API_KEY, FASTROUTER_API_KEY, ANYROUTER_API_KEY, or local Ollama"
    Write-Host ""
    exit 1
}

# Check if Docker is running
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not running"
    }
} catch {
    Write-Host "Error: Docker Desktop is not running!" -ForegroundColor Red
    Write-Host "Please launch Docker Desktop from the Start menu and wait for the engine to start, then run this script again." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Determine docker compose command
$composeCmd = "docker compose"
try {
    docker compose version > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        $composeCmd = "docker-compose"
    }
} catch {
    $composeCmd = "docker-compose"
}

Write-Host "Starting SupoClip containers with $composeCmd..." -ForegroundColor Green
Write-Host "Building and launching frontend, backend, worker, postgres, and redis..." -ForegroundColor Gray
Write-Host ""

Invoke-Expression "$composeCmd up -d --build"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  SupoClip services are up and running!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Frontend:     http://localhost:3107" -ForegroundColor Cyan
    Write-Host "  Backend API:  http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  API Docs:     http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To view real-time logs, run: $composeCmd logs -f" -ForegroundColor Yellow
    Write-Host "To stop the stack, run:      $composeCmd down" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "Failed to start SupoClip containers. Please check error messages above." -ForegroundColor Red
}


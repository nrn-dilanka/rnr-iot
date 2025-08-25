# IoT Platform Management Script for Windows PowerShell
param(
    [Parameter(Position=0)]
    [ValidateSet("setup", "start", "stop", "status", "logs", "cleanup", "")]
    [string]$Command = ""
)

# Function to check prerequisites
function Test-Prerequisites {
    Write-Host "🔍 Checking prerequisites..." -ForegroundColor Cyan
    
    # Check Docker
    try {
        $dockerInfo = docker info 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Docker is not running. Please start Docker and try again." -ForegroundColor Red
            return $false
        }
        Write-Host "✅ Docker is running" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Docker is not installed or not accessible." -ForegroundColor Red
        return $false
    }
    
    # Check Node.js
    try {
        $nodeVersion = node --version 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Node.js is not installed. Please install Node.js and try again." -ForegroundColor Red
            return $false
        }
        Write-Host "✅ Node.js is installed: $nodeVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Node.js is not installed." -ForegroundColor Red
        return $false
    }
    
    # Check Python
    try {
        $pythonVersion = python --version 2>$null
        if ($LASTEXITCODE -ne 0) {
            $pythonVersion = python3 --version 2>$null
            if ($LASTEXITCODE -ne 0) {
                Write-Host "❌ Python is not installed. Please install Python and try again." -ForegroundColor Red
                return $false
            }
        }
        Write-Host "✅ Python is installed: $pythonVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Python is not installed." -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Function to setup the platform
function Setup-Platform {
    Write-Host "🚀 Setting up IoT Platform..." -ForegroundColor Cyan
    
    if (-not (Test-Prerequisites)) {
        return
    }
    
    Write-Host "📦 Setting up backend dependencies..." -ForegroundColor Yellow
    Set-Location backend
    
    try {
        python -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            python3 -m pip install -r requirements.txt
        }
    }
    catch {
        Write-Host "❌ Failed to install Python dependencies" -ForegroundColor Red
        Set-Location ..
        return
    }
    
    Set-Location ..
    
    Write-Host "📦 Setting up frontend dependencies..." -ForegroundColor Yellow
    Set-Location frontend
    
    try {
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Failed to install Node.js dependencies" -ForegroundColor Red
            Set-Location ..
            return
        }
    }
    catch {
        Write-Host "❌ Failed to install Node.js dependencies" -ForegroundColor Red
        Set-Location ..
        return
    }
    
    Set-Location ..
    
    Write-Host "🐳 Starting Docker services..." -ForegroundColor Yellow
    docker-compose up -d postgres rabbitmq
    
    Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    Write-Host "✅ Setup complete!" -ForegroundColor Green
}

# Function to start the platform
function Start-Platform {
    Write-Host "🚀 Starting IoT Platform..." -ForegroundColor Cyan
    
    Write-Host "🔧 Starting backend services..." -ForegroundColor Yellow
    docker-compose up -d
    
    Write-Host "🌐 Starting frontend development server..." -ForegroundColor Yellow
    Set-Location frontend
    
    # Start frontend in background
    $frontendJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD\frontend
        npm start
    }
    
    Set-Location ..
    
    Write-Host "✅ Platform started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📱 Frontend: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "🔧 Backend API: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "📊 RabbitMQ Management: http://localhost:15672 (guest/guest)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press Ctrl+C to stop the platform" -ForegroundColor Yellow
    
    try {
        # Wait for interrupt
        while ($true) {
            Start-Sleep -Seconds 1
        }
    }
    finally {
        Write-Host "🛑 Stopping platform..." -ForegroundColor Yellow
        Stop-Job $frontendJob -ErrorAction SilentlyContinue
        Remove-Job $frontendJob -ErrorAction SilentlyContinue
        docker-compose down
    }
}

# Function to show status
function Show-Status {
    Write-Host "📊 IoT Platform Status:" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "🐳 Docker Services:" -ForegroundColor Yellow
    docker-compose ps
    Write-Host ""
    
    # Check if frontend is running
    $frontendProcess = Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*npm start*" }
    if ($frontendProcess) {
        Write-Host "🌐 Frontend: ✅ Running" -ForegroundColor Green
    } else {
        Write-Host "🌐 Frontend: ❌ Not running" -ForegroundColor Red
    }
    
    # Check backend API
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
        Write-Host "🔧 Backend API: ✅ Running" -ForegroundColor Green
    }
    catch {
        Write-Host "🔧 Backend API: ❌ Not running" -ForegroundColor Red
    }
    
    # Check RabbitMQ
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:15672" -TimeoutSec 5 -ErrorAction Stop
        Write-Host "📡 RabbitMQ: ✅ Running" -ForegroundColor Green
    }
    catch {
        Write-Host "📡 RabbitMQ: ❌ Not running" -ForegroundColor Red
    }
}

# Function to stop the platform
function Stop-Platform {
    Write-Host "🛑 Stopping IoT Platform..." -ForegroundColor Yellow
    
    # Stop frontend processes
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*npm start*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    # Stop Docker services
    docker-compose down
    
    Write-Host "✅ Platform stopped" -ForegroundColor Green
}

# Function to show logs
function Show-Logs {
    Write-Host "📝 Showing platform logs..." -ForegroundColor Cyan
    docker-compose logs -f
}

# Function to cleanup
function Cleanup-Platform {
    Write-Host "🧹 Cleaning up IoT Platform..." -ForegroundColor Yellow
    
    Stop-Platform
    
    $response = Read-Host "Do you want to remove all data (database, etc.)? [y/N]"
    if ($response -eq "y" -or $response -eq "Y") {
        docker-compose down -v
        Write-Host "✅ All data removed" -ForegroundColor Green
    }
    
    # Clean up frontend
    if (Test-Path "frontend\node_modules") {
        Remove-Item -Path "frontend\node_modules" -Recurse -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path "frontend\package-lock.json") {
        Remove-Item -Path "frontend\package-lock.json" -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "✅ Cleanup complete" -ForegroundColor Green
}

# Main switch
switch ($Command) {
    "setup" {
        Setup-Platform
    }
    "start" {
        Start-Platform
    }
    "stop" {
        Stop-Platform
    }
    "status" {
        Show-Status
    }
    "logs" {
        Show-Logs
    }
    "cleanup" {
        Cleanup-Platform
    }
    default {
        Write-Host "🏭 IoT Platform Management Script" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Usage: .\manage_platform.ps1 [command]" -ForegroundColor White
        Write-Host ""
        Write-Host "Commands:" -ForegroundColor Yellow
        Write-Host "  setup     - Install dependencies and set up the platform" -ForegroundColor White
        Write-Host "  start     - Start the IoT platform" -ForegroundColor White
        Write-Host "  stop      - Stop the IoT platform" -ForegroundColor White
        Write-Host "  status    - Show platform status" -ForegroundColor White
        Write-Host "  logs      - Show platform logs" -ForegroundColor White
        Write-Host "  cleanup   - Clean up and remove all data" -ForegroundColor White
        Write-Host ""
        Write-Host "Example:" -ForegroundColor Yellow
        Write-Host "  .\manage_platform.ps1 setup    # First time setup" -ForegroundColor White
        Write-Host "  .\manage_platform.ps1 start    # Start the platform" -ForegroundColor White
        Write-Host ""
    }
}

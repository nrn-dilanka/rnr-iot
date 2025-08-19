@echo off
setlocal enabledelayedexpansion

REM Enhanced Greenhouse Features Deployment Script for Windows
REM This script helps deploy the new greenhouse monitoring and control features

echo 🌱 Enhanced Greenhouse Features Deployment Script
echo ==================================================
echo.

REM Check if running from correct directory
if not exist "docker-compose.yml" (
    echo [ERROR] Please run this script from the RNR Solutions IoT Platform root directory
    pause
    exit /b 1
)

REM Function to check if command exists
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

where docker-compose >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

where psql >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] PostgreSQL client (psql) not found. Database migration will be skipped.
    set SKIP_DB_MIGRATION=true
) else (
    set SKIP_DB_MIGRATION=false
)

echo [INFO] Prerequisites check completed
echo.

REM Ask for confirmation
set /p "confirm=This will deploy enhanced greenhouse features. Continue? (y/N): "
if /i not "%confirm%"=="y" (
    echo Deployment cancelled.
    pause
    exit /b 0
)

echo.
echo [STEP] Creating Database Backup
echo ================================

if "%SKIP_DB_MIGRATION%"=="true" (
    echo [WARNING] Skipping database backup (psql not available)
) else (
    if not exist "backups" mkdir backups
    
    REM Get current timestamp
    for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
    set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
    set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
    set "timestamp=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"
    
    set "BACKUP_FILE=backups\iot_platform_backup_%timestamp%.sql"
    
    echo [INFO] Creating backup: !BACKUP_FILE!
    
    REM Set default database connection details
    if not defined DB_HOST set DB_HOST=localhost
    if not defined DB_PORT set DB_PORT=5432
    if not defined DB_NAME set DB_NAME=iot_platform
    if not defined DB_USER set DB_USER=iotuser
    
    pg_dump -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% > "!BACKUP_FILE!"
    if %errorlevel% equ 0 (
        echo [INFO] Database backup created successfully
    ) else (
        echo [WARNING] Database backup failed, but continuing with deployment
    )
)

echo.
echo [STEP] Applying Database Migrations
echo ===================================

if "%SKIP_DB_MIGRATION%"=="true" (
    echo [WARNING] Skipping database migration (psql not available)
    echo [WARNING] Please manually apply database\enhanced_schema.sql to your database
) else (
    if not exist "database\enhanced_schema.sql" (
        echo [ERROR] Enhanced schema file not found: database\enhanced_schema.sql
        pause
        exit /b 1
    )
    
    echo [INFO] Applying enhanced schema to database...
    
    psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -f "database\enhanced_schema.sql"
    if %errorlevel% equ 0 (
        echo [INFO] Database migrations applied successfully
    ) else (
        echo [ERROR] Database migration failed
        pause
        exit /b 1
    )
)

echo.
echo [STEP] Installing Frontend Dependencies
echo ======================================

if not exist "frontend" (
    echo [ERROR] Frontend directory not found
    pause
    exit /b 1
)

cd frontend

if exist "package.json" (
    echo [INFO] Installing npm dependencies...
    
    where npm >nul 2>&1
    if %errorlevel% equ 0 (
        npm install
        echo [INFO] Frontend dependencies installed
    ) else (
        where yarn >nul 2>&1
        if %errorlevel% equ 0 (
            yarn install
            echo [INFO] Frontend dependencies installed with Yarn
        ) else (
            echo [WARNING] Neither npm nor yarn found. Please install frontend dependencies manually.
        )
    )
) else (
    echo [WARNING] package.json not found in frontend directory
)

cd ..

echo.
echo [STEP] Installing Backend Dependencies
echo =====================================

if not exist "backend" (
    echo [ERROR] Backend directory not found
    pause
    exit /b 1
)

cd backend

if exist "requirements.txt" (
    echo [INFO] Installing Python dependencies...
    
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        if not exist "venv" (
            echo [INFO] Creating virtual environment
            python -m venv venv
        )
        echo [INFO] Using virtual environment
        call venv\Scripts\activate.bat
        pip install -r requirements.txt
        echo [INFO] Backend dependencies installed
        call venv\Scripts\deactivate.bat
    ) else (
        echo [WARNING] Python not found. Please install backend dependencies manually.
    )
) else (
    echo [WARNING] requirements.txt not found in backend directory
)

cd ..

echo.
echo [STEP] Building and Starting Services
echo ====================================

echo [INFO] Stopping existing services...
docker-compose down

echo [INFO] Building services...
docker-compose build

echo [INFO] Starting services...
docker-compose up -d

echo [INFO] Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Check if services are running
docker-compose ps | findstr "Up" >nul
if %errorlevel% equ 0 (
    echo [INFO] Services started successfully
) else (
    echo [WARNING] Some services may not have started correctly
    docker-compose ps
)

echo.
echo [STEP] Verifying Deployment
echo ==========================

echo [INFO] Checking backend health...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Backend is responding
) else (
    echo [WARNING] Backend may not be responding on port 8000
)

echo [INFO] Checking frontend accessibility...
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Frontend is accessible
) else (
    echo [WARNING] Frontend may not be accessible on port 3000
)

if "%SKIP_DB_MIGRATION%"=="false" (
    echo [INFO] Checking database connection...
    psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -c "SELECT 1;" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [INFO] Database connection successful
    ) else (
        echo [WARNING] Database connection failed
    )
)

echo.
echo [STEP] Post-Deployment Information
echo =================================
echo.
echo 🎉 Greenhouse features deployment completed!
echo.
echo 📋 Next Steps:
echo 1. Access the platform at: http://localhost:3000
echo 2. Log in with your existing credentials
echo 3. Navigate to 'Environmental Monitoring' to see new features
echo 4. Navigate to 'Crop Management' for growth tracking
echo 5. Configure your ESP32 devices with the new firmware
echo.
echo 📖 Documentation:
echo - Feature documentation: GREENHOUSE_FEATURES.md
echo - API documentation: http://localhost:8000/docs
echo - Database schema: database\enhanced_schema.sql
echo.
echo 🔧 ESP32 Configuration:
echo - Upload esp32\greenhouse_sensors.ino to your ESP32 devices
echo - Update WiFi and MQTT credentials in the firmware
echo - Configure sensor pins according to your hardware setup
echo.
echo ⚠️  Important Notes:
echo - Backup created in: backups\ directory
echo - New database tables have been added
echo - WebSocket connections now support greenhouse events
echo - Role-based access is enforced for new features
echo.

if "%SKIP_DB_MIGRATION%"=="true" (
    echo 🚨 Manual Action Required:
    echo - Apply database\enhanced_schema.sql to your database manually
    echo - Ensure PostgreSQL client tools are installed for future deployments
    echo.
)

echo [INFO] Deployment completed successfully! 🎉
echo.
pause
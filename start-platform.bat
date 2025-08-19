@echo off
echo =================================================
echo     IoT Platform - Automatic IP Setup
echo =================================================
echo.

echo 🔍 Detecting and configuring IP address...
node auto-ip.js

if errorlevel 1 (
    echo ❌ IP detection failed. Please check your network connection.
    pause
    exit /b 1
)

echo.
echo 🚀 Starting IoT Platform containers...
docker-compose up --build -d

if errorlevel 1 (
    echo ❌ Failed to start containers. Please check Docker is running.
    pause
    exit /b 1
)

echo.
echo ✅ IoT Platform is now running!
echo.
echo 📋 Access your platform at:
echo   • Frontend: http://192.168.8.114:3000
echo   • API: http://192.168.8.114:8000
echo   • RabbitMQ Management: http://localhost:15672
echo.
pause

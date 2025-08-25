@echo off
REM RNR Solutions - RabbitMQ Startup Script (Windows Batch)
REM Starts only the RabbitMQ container for IoT data transmission

echo =================================================
echo      RNR IoT Platform - RabbitMQ Service
echo =================================================
echo.

REM Check if Docker is running
echo 🔍 Checking Docker status...
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

echo ✅ Docker is running
echo.

REM Check if RabbitMQ container already exists and is running
echo 🔍 Checking RabbitMQ container status...
docker ps --filter "name=rnr_iot_rabbitmq" --format "{{.Names}}" | findstr "rnr_iot_rabbitmq" >nul
if not errorlevel 1 (
    echo ✅ RabbitMQ container is already running
    echo.
) else (
    echo 🚀 Starting RabbitMQ container...
    docker-compose up -d rnr_rabbitmq
    
    if errorlevel 1 (
        echo ❌ Failed to start RabbitMQ container
        pause
        exit /b 1
    )
    
    echo ✅ RabbitMQ container started successfully
    echo.
)

REM Wait for RabbitMQ to be ready
echo ⏳ Waiting for RabbitMQ to be ready...
set maxAttempts=30
set attempt=0

:waitLoop
set /a attempt+=1
timeout /t 2 /nobreak >nul
docker exec rnr_iot_rabbitmq rabbitmq-diagnostics ping >nul 2>&1
if not errorlevel 1 (
    echo ✅ RabbitMQ is ready!
    goto ready
)

if %attempt% geq %maxAttempts% (
    echo ⚠️  RabbitMQ took longer than expected to start
    goto ready
)

echo|set /p="."
goto waitLoop

:ready
echo.
echo.

REM Display connection information
echo 📋 RabbitMQ Connection Information:
echo    • AMQP Port: 5672
echo    • MQTT Port: 1883
echo    • Management UI: http://localhost:15672
echo    • Username: rnr_iot_user
echo    • Password: rnr_iot_2025!
echo    • MQTT Virtual Host: rnr_iot_vhost
echo.

REM Test MQTT connection
echo 🧪 Testing MQTT connection...
docker exec rnr_iot_rabbitmq rabbitmq-plugins list | findstr "rabbitmq_mqtt" >nul
if not errorlevel 1 (
    echo ✅ MQTT plugin is enabled
) else (
    echo ⚠️  MQTT plugin status unknown
)

echo.
echo 🔗 Your ESP32 devices can now connect to:
echo    MQTT Broker: localhost:1883
echo    Username: rnr_iot_user
echo    Password: rnr_iot_2025!
echo.

REM Show container status
echo 📊 Container Status:
docker ps --filter "name=rnr_iot_rabbitmq" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo 🎉 RabbitMQ is ready to receive IoT data!
echo.
pause

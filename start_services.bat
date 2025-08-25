@echo off
echo Starting RabbitMQ IoT Platform Services...
echo.

echo Stopping any existing containers...
docker-compose down --remove-orphans

echo.
echo Starting RabbitMQ container...
docker-compose up -d rnr_rabbitmq

echo.
echo Waiting for RabbitMQ to initialize (60 seconds)...
timeout /t 60 /nobreak > nul

echo.
echo Checking RabbitMQ health...
docker exec rnr_iot_rabbitmq rabbitmq-diagnostics ping

echo.
echo Starting PostgreSQL database...
docker-compose up -d rnr_postgres

echo.
echo Waiting for database to initialize (30 seconds)...
timeout /t 30 /nobreak > nul

echo.
echo Starting API server...
docker-compose up -d rnr_api_server

echo.
echo Waiting for API server to start (20 seconds)...
timeout /t 20 /nobreak > nul

echo.
echo Checking all container status...
docker ps

echo.
echo ============================================
echo RabbitMQ Management UI: http://localhost:15672
echo Username: rnr_iot_user
echo Password: rnr_iot_2025!
echo ============================================
echo.

pause

#!/bin/bash
# RNR Solutions - Fix API Server and Restart Platform
# This script fixes the uvicorn command issue and restarts the platform

echo "=========================================="
echo "RNR IoT Platform - API Server Fix"
echo "Fixing uvicorn command and restarting services"
echo "=========================================="

# Stop all services
echo "Stopping all services..."
docker-compose down

# Remove the API server image to force rebuild
echo "Removing old API server image..."
docker rmi rnr-iot-rnr_api_server 2>/dev/null || true

# Build and start services
echo "Building and starting services..."
docker-compose up -d --build

# Wait for services to start
echo "Waiting for services to initialize..."
sleep 30

# Check service status
echo "=========================================="
echo "Service Status:"
echo "=========================================="
docker-compose ps

echo ""
echo "=========================================="
echo "API Server Logs (last 10 lines):"
echo "=========================================="
docker-compose logs rnr_api_server --tail=10

echo ""
echo "=========================================="
echo "Testing API endpoint..."
echo "=========================================="
sleep 5
curl -s http://localhost:8000/health 2>/dev/null || echo "API not yet ready"

echo ""
echo "=========================================="
echo "RNR IoT Platform Status:"
echo "=========================================="
echo "API Server: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "RabbitMQ Management: http://localhost:15672"
echo "Database: localhost:15432"
echo ""
echo "If all services show 'Up', the platform is ready!"
echo "=========================================="

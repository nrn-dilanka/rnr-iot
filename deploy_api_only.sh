#!/bin/bash
# RNR Solutions - API-Only Platform Deployment
# Optimized for 2GB RAM without frontend service

echo "=========================================="
echo "RNR IoT Platform - API-Only Deployment"
echo "Deploying backend services without frontend"
echo "=========================================="

# Stop all services
echo "Stopping all services..."
docker-compose down

# Remove old images to ensure clean build
echo "Cleaning old images..."
docker rmi rnr-iot-rnr_api_server 2>/dev/null || true

# Start only backend services
echo "Starting backend services..."
docker-compose up -d --build rnr_rabbitmq rnr_postgres rnr_api_server rnr_worker_service

# Wait for services to initialize
echo "Waiting for services to start..."
sleep 30

# Check service status
echo "=========================================="
echo "Backend Service Status:"
echo "=========================================="
docker-compose ps

echo ""
echo "=========================================="
echo "API Server Health Check:"
echo "=========================================="
sleep 5

# Test API endpoints
echo "Testing API server connectivity..."
curl -s http://localhost:8000/health 2>/dev/null && echo "✓ API Health: OK" || echo "✗ API Health: Failed"

echo ""
echo "=========================================="
echo "RNR IoT Platform - API-Only Mode:"
echo "=========================================="
echo "🚀 API Server: http://localhost:8000"
echo "📋 API Documentation: http://localhost:8000/docs"
echo "🔧 API Health Check: http://localhost:8000/health"
echo "🐰 RabbitMQ Management: http://localhost:15672"
echo "🗄️  Database: localhost:15432"
echo ""
echo "📡 External Access:"
echo "🌐 API Server: http://13.60.255.181/api"
echo "📚 API Docs: http://13.60.255.181/api/docs"
echo "💓 Health Check: http://13.60.255.181/health"
echo ""
echo "Memory Usage (optimized for 2GB):"
echo "- RabbitMQ: 300MB"
echo "- PostgreSQL: 384MB" 
echo "- API Server: 512MB"
echo "- Worker Service: 384MB"
echo "- Total: ~1.58GB (leaving 400MB+ for system)"
echo ""
echo "✅ API-only platform is ready!"
echo "=========================================="

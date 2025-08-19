#!/bin/bash

# RNR Solutions IoT Platform Setup Script
# Enterprise-grade IoT platform deployment and configuration
# © 2025 RNR Solutions. All rights reserved.

set -e

echo "🚀 Starting RNR Solutions IoT Platform Setup..."
echo "   Enterprise IoT Platform v2.0.0"
echo "   Developed by RNR Solutions"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads
mkdir -p data/postgres
mkdir -p data/rabbitmq

# Set permissions
chmod 755 uploads

echo "🔧 Starting RNR Solutions IoT Platform services..."

# Stop any existing containers
docker-compose down

# Pull latest images
echo "📥 Pulling Docker images for RNR IoT Platform..."
docker-compose pull

# Start services
echo "🚀 Starting all RNR IoT Platform services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for RNR IoT Platform services to initialize..."
sleep 30

# Check service health
echo "🏥 Checking RNR IoT Platform service health..."

# Check if PostgreSQL is ready
echo "Checking RNR PostgreSQL Database..."
if docker-compose exec -T rnr_postgres pg_isready -U rnr_iot_user > /dev/null 2>&1; then
    echo "✅ RNR PostgreSQL Database is ready"
else
    echo "❌ RNR PostgreSQL Database is not ready"
fi

# Check if RabbitMQ is ready
echo "Checking RNR RabbitMQ Message Broker..."
if curl -f http://localhost:15672 > /dev/null 2>&1; then
    echo "✅ RNR RabbitMQ Management UI is accessible"
else
    echo "⚠️ RNR RabbitMQ Management UI might not be ready yet"
fi

# Check if API server is ready
echo "Checking RNR API Server..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ RNR API Server is ready"
else
    echo "⚠️ RNR API Server might not be ready yet"
fi

# Check if Frontend is ready
echo "Checking RNR Frontend Dashboard..."
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ RNR Frontend Dashboard is ready"
else
    echo "⚠️ RNR Frontend Dashboard might not be ready yet"
fi

echo ""
echo "🎉 RNR Solutions IoT Platform Setup Complete!"
echo ""
echo "📋 RNR IoT Platform Service Information:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 RNR Web Dashboard:        http://localhost:3000"
echo "📚 RNR API Documentation:    http://localhost:8000/docs"
echo "🐰 RabbitMQ Management:      http://localhost:15672 (rnr_iot_user/rnr_iot_2025!)"
echo "🗄️  PostgreSQL Database:     localhost:15432 (rnr_iot_user/rnr_iot_2025!)"
echo "📡 MQTT Broker:              localhost:1883 (rnr_iot_user/rnr_iot_2025!)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 ESP32 Configuration for RNR IoT Platform:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Open firmware/src/main.cpp"
echo "2. Update WiFi credentials (ssid, password)"
echo "3. Set mqtt_server to your Docker host IP"
echo "4. Set mqtt_user to 'rnr_iot_user'"
echo "5. Set mqtt_password to 'rnr_iot_2025!'"
echo "6. Flash to ESP32 using PlatformIO"
echo ""
echo "🔍 RNR IoT Platform Monitoring:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "View logs:    docker-compose logs -f"
echo "Stop all:     docker-compose down"
echo "Restart:      docker-compose restart"
echo ""
echo "🎯 Welcome to RNR Solutions IoT Platform!"
echo "   Your enterprise IoT solution is ready."
echo ""
echo "© 2025 RNR Solutions. All rights reserved."
echo "For support: support@rnrsolutions.com"

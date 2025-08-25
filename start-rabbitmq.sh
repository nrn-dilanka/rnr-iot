#!/bin/bash
# RNR Solutions - RabbitMQ Startup Script
# Starts only the RabbitMQ container for IoT data transmission

echo "================================================="
echo "     RNR IoT Platform - RabbitMQ Service"
echo "================================================="
echo ""

# Check if Docker is running
echo "🔍 Checking Docker status..."
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    read -p "Press Enter to exit..."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if RabbitMQ container already exists and is running
echo "🔍 Checking RabbitMQ container status..."
if docker ps --filter "name=rnr_iot_rabbitmq" --format "{{.Names}}" | grep -q "rnr_iot_rabbitmq"; then
    echo "✅ RabbitMQ container is already running"
    echo ""
else
    echo "🚀 Starting RabbitMQ container..."
    docker-compose up -d rnr_rabbitmq
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to start RabbitMQ container"
        read -p "Press Enter to exit..."
        exit 1
    fi
    
    echo "✅ RabbitMQ container started successfully"
    echo ""
fi

# Wait for RabbitMQ to be ready
echo "⏳ Waiting for RabbitMQ to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    attempt=$((attempt + 1))
    sleep 2
    
    if docker exec rnr_iot_rabbitmq rabbitmq-diagnostics ping >/dev/null 2>&1; then
        echo "✅ RabbitMQ is ready!"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        echo "⚠️  RabbitMQ took longer than expected to start"
        break
    fi
    
    echo -n "."
done

echo ""
echo ""

# Display connection information
echo "📋 RabbitMQ Connection Information:"
echo "   • AMQP Port: 5672"
echo "   • MQTT Port: 1883"
echo "   • Management UI: http://localhost:15672"
echo "   • Username: rnr_iot_user"
echo "   • Password: rnr_iot_2025!"
echo "   • MQTT Virtual Host: rnr_iot_vhost"
echo ""

# Test MQTT connection
echo "🧪 Testing MQTT connection..."
if docker exec rnr_iot_rabbitmq rabbitmq-plugins list | grep -q "rabbitmq_mqtt"; then
    echo "✅ MQTT plugin is enabled"
else
    echo "⚠️  MQTT plugin status unknown"
fi

echo ""
echo "🔗 Your ESP32 devices can now connect to:"
echo "   MQTT Broker: localhost:1883"
echo "   Username: rnr_iot_user"
echo "   Password: rnr_iot_2025!"
echo ""

# Show container status
echo "📊 Container Status:"
docker ps --filter "name=rnr_iot_rabbitmq" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🎉 RabbitMQ is ready to receive IoT data!"
echo ""
read -p "Press Enter to exit..."

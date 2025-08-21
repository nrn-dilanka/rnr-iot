#!/bin/bash

echo "🚨 Error Log Analyzer - IoT Services"
echo "==================================="

# Function to analyze errors in a service
analyze_errors() {
    local service=$1
    local display_name=$2
    
    echo -e "\n🔍 Analyzing $display_name errors..."
    
    if ! docker ps --format "{{.Names}}" | grep -q "^${service}$"; then
        echo "❌ $service is not running"
        return
    fi
    
    # Get recent logs
    local logs=$(docker logs --tail=200 $service 2>&1)
    
    # Count different types of errors
    local error_count=$(echo "$logs" | grep -ci "error")
    local exception_count=$(echo "$logs" | grep -ci "exception")
    local failed_count=$(echo "$logs" | grep -ci "failed")
    local warning_count=$(echo "$logs" | grep -ci "warning")
    
    echo "📊 Error Summary:"
    echo "   Errors: $error_count"
    echo "   Exceptions: $exception_count"
    echo "   Failed: $failed_count"
    echo "   Warnings: $warning_count"
    
    if [ $error_count -gt 0 ] || [ $exception_count -gt 0 ] || [ $failed_count -gt 0 ]; then
        echo -e "\n🔥 Recent Critical Issues:"
        echo "$logs" | grep -i "error\|exception\|failed" | tail -5 | while read line; do
            echo "   ❌ $line"
        done
    else
        echo "   ✅ No critical errors found"
    fi
    
    if [ $warning_count -gt 0 ]; then
        echo -e "\n⚠️  Recent Warnings:"
        echo "$logs" | grep -i "warning" | tail -3 | while read line; do
            echo "   ⚠️  $line"
        done
    fi
}

# Analyze all services
analyze_errors "rnr_iot_api_server" "API Server"
analyze_errors "rnr_iot_postgres" "PostgreSQL Database"
analyze_errors "rnr_iot_rabbitmq" "RabbitMQ Message Broker"
analyze_errors "rnr_iot_worker_service" "Worker Service"

echo -e "\n🔍 Database Connection Test:"
timeout 5 docker exec rnr_iot_api_server python -c "
from api.database import get_db
try:
    db = next(get_db())
    db.execute('SELECT 1')
    print('✅ Database connection: OK')
except Exception as e:
    print(f'❌ Database connection: {e}')
" 2>/dev/null || echo "❌ Could not test database connection"

echo -e "\n🔍 MQTT Connection Test:"
timeout 5 docker logs --tail=20 rnr_iot_api_server | grep -i mqtt | tail -2 || echo "No recent MQTT logs"

echo -e "\n📋 Service Health Summary:"
docker-compose ps 2>/dev/null || docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo -e "\n🎯 Error analysis complete!"
echo ""
echo "💡 Quick Actions:"
echo "• Restart API server: docker-compose restart rnr_api_server"
echo "• Restart database: docker-compose restart postgres"
echo "• Restart RabbitMQ: docker-compose restart rabbitmq"
echo "• View specific logs: docker logs -f rnr_iot_api_server"
echo "• Monitor all logs: ./monitor_all_logs.sh"

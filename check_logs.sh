#!/bin/bash

echo "📋 RNR IoT Platform - Service Logs Monitor"
echo "=========================================="

# Function to display colored headers
print_header() {
    echo -e "\n🔍 $1"
    echo "$(printf '=%.0s' {1..50})"
}

# Function to check if container exists and is running
check_container() {
    local container_name=$1
    if docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
        echo "✅ ${container_name} - Running"
        return 0
    elif docker ps -a --format "table {{.Names}}" | grep -q "^${container_name}$"; then
        echo "⚠️  ${container_name} - Stopped"
        return 1
    else
        echo "❌ ${container_name} - Not Found"
        return 2
    fi
}

# Get number of log lines (default 50, or user specified)
LOG_LINES=${1:-50}
FOLLOW_MODE=${2:-""}

print_header "CONTAINER STATUS"
echo "Checking all IoT service containers..."

# Check all containers
check_container "rnr_iot_api_server"
API_STATUS=$?
check_container "rnr_iot_postgres"
DB_STATUS=$?
check_container "rnr_iot_rabbitmq"
RABBIT_STATUS=$?
check_container "rnr_iot_worker_service"
WORKER_STATUS=$?

print_header "API SERVER LOGS (Last $LOG_LINES lines)"
if [ $API_STATUS -eq 0 ]; then
    if [ "$FOLLOW_MODE" == "follow" ]; then
        echo "Following API server logs (Ctrl+C to stop)..."
        docker logs -f rnr_iot_api_server
    else
        docker logs --tail=$LOG_LINES rnr_iot_api_server
    fi
else
    echo "❌ API Server container not running - cannot show logs"
fi

if [ "$FOLLOW_MODE" != "follow" ]; then
    print_header "DATABASE LOGS (Last $LOG_LINES lines)"
    if [ $DB_STATUS -eq 0 ]; then
        docker logs --tail=$LOG_LINES rnr_iot_postgres
    else
        echo "❌ Database container not running - cannot show logs"
    fi

    print_header "RABBITMQ LOGS (Last $LOG_LINES lines)"
    if [ $RABBIT_STATUS -eq 0 ]; then
        docker logs --tail=$LOG_LINES rnr_iot_rabbitmq
    else
        echo "❌ RabbitMQ container not running - cannot show logs"
    fi

    if [ $WORKER_STATUS -eq 0 ]; then
        print_header "WORKER SERVICE LOGS (Last $LOG_LINES lines)"
        docker logs --tail=$LOG_LINES rnr_iot_worker_service
    fi

    print_header "ERROR SUMMARY"
    echo "🔍 Searching for errors in all services..."
    
    echo -e "\n📊 API Server Errors:"
    docker logs --tail=100 rnr_iot_api_server 2>/dev/null | grep -i "error\|exception\|failed" | tail -5 || echo "   No recent errors found"
    
    echo -e "\n📊 Database Errors:"
    docker logs --tail=100 rnr_iot_postgres 2>/dev/null | grep -i "error\|exception\|failed" | tail -5 || echo "   No recent errors found"
    
    echo -e "\n📊 RabbitMQ Errors:"
    docker logs --tail=100 rnr_iot_rabbitmq 2>/dev/null | grep -i "error\|exception\|failed" | tail -5 || echo "   No recent errors found"

    print_header "SYSTEM RESOURCE USAGE"
    echo "📊 Container Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null || echo "Could not get stats"

    print_header "RECENT CONTAINER EVENTS"
    echo "📅 Docker Events (Last 10):"
    docker events --since="10m" --until="now" --format="{{.Time}} {{.Type}} {{.Action}} {{.Actor.Attributes.name}}" 2>/dev/null | tail -10 || echo "No recent events"

    print_header "LOG MONITORING COMMANDS"
    echo "📝 Quick Commands for Log Monitoring:"
    echo ""
    echo "# Follow API server logs in real-time:"
    echo "docker logs -f rnr_iot_api_server"
    echo ""
    echo "# Get last 100 lines of API logs:"
    echo "docker logs --tail=100 rnr_iot_api_server"
    echo ""
    echo "# Follow all services (in separate terminals):"
    echo "docker-compose logs -f rnr_api_server"
    echo "docker-compose logs -f postgres"
    echo "docker-compose logs -f rabbitmq"
    echo ""
    echo "# Search for specific errors:"
    echo "docker logs rnr_iot_api_server 2>&1 | grep -i 'database'"
    echo "docker logs rnr_iot_api_server 2>&1 | grep -i 'mqtt'"
    echo ""
    echo "# Use this script:"
    echo "./check_logs.sh [number_of_lines] [follow]"
    echo "Example: ./check_logs.sh 100 follow"
fi

echo -e "\n🎯 Log check complete!"

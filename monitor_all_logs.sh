#!/bin/bash

echo "🔍 Real-time Log Monitor - All Services"
echo "======================================"

# Function to monitor logs in different terminals
monitor_service() {
    local service=$1
    local color=$2
    
    echo -e "\e[${color}m=== $service LOGS ===\e[0m"
    docker logs -f --tail=10 $service 2>&1 | while read line; do
        echo -e "\e[${color}m[$service]\e[0m $line"
    done &
}

# Start monitoring all services
echo "Starting real-time monitoring for all services..."
echo "Press Ctrl+C to stop"
echo ""

# Monitor each service with different colors
monitor_service "rnr_iot_api_server" "32"    # Green
monitor_service "rnr_iot_postgres" "34"      # Blue  
monitor_service "rnr_iot_rabbitmq" "35"      # Magenta
monitor_service "rnr_iot_worker_service" "36" # Cyan

# Wait for user interrupt
wait

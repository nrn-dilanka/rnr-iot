#!/bin/bash

# Real-time node monitoring dashboard
echo "🏭 Real-Time Node Monitoring Dashboard"
echo "====================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Function to get current timestamp
get_timestamp() {
    date "+%Y-%m-%d %H:%M:%S"
}

# Function to monitor nodes
monitor_nodes() {
    while true; do
        clear
        echo -e "${BLUE}🏭 Industrial IoT Node Dashboard${NC}"
        echo "================================="
        echo -e "📅 Last Update: $(get_timestamp)"
        echo ""
        
        # Get node status
        curl -s http://localhost:3005/api/nodes | python3 -c "
import json, sys
from datetime import datetime

try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        nodes = data
    else:
        nodes = data.get('nodes', [])
    
    online_count = 0
    offline_count = 0
    total_count = len(nodes)
    
    print('📊 SYSTEM OVERVIEW')
    print('==================')
    
    for node in nodes:
        node_id = node.get('id', 'N/A')
        name = node.get('name', 'Unknown')
        status = node.get('status', 'unknown')
        node_type = node.get('type', 'ESP32')
        location = node.get('location', 'Industrial Zone')
        
        if status == 'online':
            status_icon = '🟢 ONLINE '
            online_count += 1
        elif status == 'offline':
            status_icon = '🔴 OFFLINE'
            offline_count += 1
        else:
            status_icon = '🟡 UNKNOWN'
        
        print(f'{status_icon} | ID:{node_id:2} | {name:15} | {node_type:8} | {location}')
    
    print()
    print(f'📈 STATISTICS: {total_count} Total | {online_count} Online | {offline_count} Offline')
    
    # Calculate uptime percentage
    if total_count > 0:
        uptime_percent = (online_count / total_count) * 100
        if uptime_percent >= 80:
            health_status = '🟢 EXCELLENT'
        elif uptime_percent >= 60:
            health_status = '🟡 MODERATE'
        else:
            health_status = '🔴 CRITICAL'
        
        print(f'🏥 SYSTEM HEALTH: {health_status} ({uptime_percent:.1f}% uptime)')
    
except Exception as e:
    print(f'❌ Error fetching node data: {e}')
"
        
        echo ""
        echo -e "${CYAN}🔧 MANAGEMENT COMMANDS:${NC}"
        echo "======================"
        echo "• Press 'q' to quit"
        echo "• Press 'r' to refresh now"
        echo "• Press 'i' for interactive mode"
        echo "• Press 's' to show sensor data"
        echo ""
        echo "Auto-refresh in 5 seconds..."
        
        # Check for user input with timeout
        read -t 5 -n 1 input
        case $input in
            'q'|'Q')
                echo -e "\n👋 Monitoring stopped"
                exit 0
                ;;
            'r'|'R')
                echo -e "\n🔄 Refreshing..."
                continue
                ;;
            'i'|'I')
                echo -e "\n🎮 Starting interactive mode..."
                ./node_manager.sh --interactive
                exit 0
                ;;
            's'|'S')
                echo -e "\n🌡️ Sensor Data Overview:"
                curl -s http://localhost:3005/api/sensor-data/latest | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        sensors = data
    else:
        sensors = data.get('data', [])
    
    for sensor in sensors[:5]:  # Show last 5 readings
        node_id = sensor.get('node_id', 'Unknown')
        timestamp = sensor.get('timestamp', 'Unknown')
        reading = sensor.get('data', {})
        
        print(f'Node {node_id} ({timestamp}):')
        for key, value in reading.items():
            print(f'  {key}: {value}')
        print()
except:
    print('No sensor data available')
"
                read -p "Press Enter to continue monitoring..."
                ;;
        esac
    done
}

# Check if API is running
if ! curl -s http://localhost:3005/health > /dev/null 2>&1; then
    echo -e "${RED}❌ API server is not running${NC}"
    echo "Please start the API server first:"
    echo "  docker-compose up -d rnr_api_server"
    exit 1
fi

# Start monitoring
monitor_nodes

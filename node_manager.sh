#!/bin/bash

echo "🏭 Industrial IoT Node Management System"
echo "======================================="

# Color codes for better visibility
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Authentication token
get_auth_token() {
    TOKEN=$(curl -s -X POST "http://localhost:3005/api/auth/login" \
      -H "Content-Type: application/json" \
      -d '{"username": "admin", "password": "admin123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
    echo $TOKEN
}

# Get current node status
get_nodes() {
    echo -e "${BLUE}📊 Current Node Status:${NC}"
    echo "======================"
    
    curl -s http://localhost:3005/api/nodes | python3 -c "
import json, sys
from datetime import datetime
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        nodes = data
    else:
        nodes = data.get('nodes', [])
    
    print(f'📈 Total Nodes: {len(nodes)}')
    print(f'📅 Status as of: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')
    print()
    
    online_count = 0
    offline_count = 0
    
    for i, node in enumerate(nodes, 1):
        node_id = node.get('id', 'N/A')
        name = node.get('name', 'Unknown')
        status = node.get('status', 'unknown')
        node_type = node.get('type', 'ESP32')
        location = node.get('location', 'Not set')
        
        if status == 'online':
            status_icon = '🟢'
            online_count += 1
        elif status == 'offline':
            status_icon = '🔴'
            offline_count += 1
        else:
            status_icon = '🟡'
        
        print(f'{i:2d}. {status_icon} {name}')
        print(f'    ID: {node_id} | Type: {node_type} | Location: {location}')
        print(f'    Status: {status.upper()}')
        print()
    
    print(f'📊 Summary: {online_count} Online, {offline_count} Offline')
    
except Exception as e:
    print(f'❌ Error fetching nodes: {e}')
"
}

# Get detailed node information
get_node_details() {
    local node_id=$1
    echo -e "${CYAN}🔍 Node Details (ID: $node_id):${NC}"
    echo "========================="
    
    TOKEN=$(get_auth_token)
    if [ -z "$TOKEN" ]; then
        echo "❌ Authentication failed"
        return 1
    fi
    
    curl -s -H "Authorization: Bearer $TOKEN" http://localhost:3005/api/nodes/$node_id | python3 -c "
import json, sys
try:
    node = json.load(sys.stdin)
    print(f'📱 Name: {node.get(\"name\", \"Unknown\")}')
    print(f'🆔 ID: {node.get(\"id\", \"N/A\")}')
    print(f'🔧 Type: {node.get(\"type\", \"ESP32\")}')
    print(f'📍 Location: {node.get(\"location\", \"Not set\")}')
    print(f'🟢 Status: {node.get(\"status\", \"unknown\").upper()}')
    print(f'📡 IP Address: {node.get(\"ip_address\", \"Not available\")}')
    print(f'🔋 Last Seen: {node.get(\"last_seen\", \"Never\")}')
    print(f'📊 Firmware: {node.get(\"firmware_version\", \"Unknown\")}')
    
    # Sensor data if available
    if 'sensor_data' in node:
        print(f'\\n🌡️ Latest Sensor Data:')
        sensor_data = node['sensor_data']
        for key, value in sensor_data.items():
            print(f'   {key}: {value}')
            
except Exception as e:
    print(f'❌ Error: {e}')
"
}

# Activate a node
activate_node() {
    local node_id=$1
    echo -e "${GREEN}🚀 Activating Node $node_id...${NC}"
    
    TOKEN=$(get_auth_token)
    if [ -z "$TOKEN" ]; then
        echo "❌ Authentication failed"
        return 1
    fi
    
    RESULT=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        http://localhost:3005/api/nodes/$node_id/activate)
    
    echo "$RESULT" | python3 -c "
import json, sys
try:
    result = json.load(sys.stdin)
    if result.get('success', False):
        print('✅ Node activated successfully')
    else:
        print(f'❌ Activation failed: {result.get(\"message\", \"Unknown error\")}')
except:
    print('✅ Activation command sent')
"
}

# Deactivate a node
deactivate_node() {
    local node_id=$1
    echo -e "${YELLOW}⏸️ Deactivating Node $node_id...${NC}"
    
    TOKEN=$(get_auth_token)
    if [ -z "$TOKEN" ]; then
        echo "❌ Authentication failed"
        return 1
    fi
    
    RESULT=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        http://localhost:3005/api/nodes/$node_id/deactivate)
    
    echo "$RESULT" | python3 -c "
import json, sys
try:
    result = json.load(sys.stdin)
    if result.get('success', False):
        print('✅ Node deactivated successfully')
    else:
        print(f'❌ Deactivation failed: {result.get(\"message\", \"Unknown error\")}')
except:
    print('✅ Deactivation command sent')
"
}

# Send command to node
send_node_command() {
    local node_id=$1
    local command=$2
    echo -e "${PURPLE}📤 Sending command '$command' to Node $node_id...${NC}"
    
    TOKEN=$(get_auth_token)
    if [ -z "$TOKEN" ]; then
        echo "❌ Authentication failed"
        return 1
    fi
    
    RESULT=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"command\": \"$command\"}" \
        http://localhost:3005/api/nodes/$node_id/action)
    
    echo "$RESULT" | python3 -c "
import json, sys
try:
    result = json.load(sys.stdin)
    print(f'📨 Response: {result.get(\"message\", \"Command sent\")}')
except:
    print('📨 Command sent to node')
"
}

# Get sensor data from node
get_sensor_data() {
    local node_id=$1
    echo -e "${CYAN}🌡️ Sensor Data for Node $node_id:${NC}"
    echo "============================"
    
    curl -s http://localhost:3005/api/nodes/$node_id/sensor-data | python3 -c "
import json, sys
from datetime import datetime
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        readings = data
    else:
        readings = data.get('readings', [])
    
    print(f'📊 Total Readings: {len(readings)}')
    print()
    
    for i, reading in enumerate(readings[-5:], 1):  # Show last 5 readings
        timestamp = reading.get('timestamp', 'Unknown')
        sensor_data = reading.get('data', {})
        
        print(f'{i}. {timestamp}')
        for key, value in sensor_data.items():
            print(f'   {key}: {value}')
        print()
        
except Exception as e:
    print(f'❌ Error: {e}')
"
}

# Interactive menu
show_menu() {
    echo -e "${BLUE}🔧 Node Management Options:${NC}"
    echo "=========================="
    echo "1. 📊 View All Nodes"
    echo "2. 🔍 View Node Details"
    echo "3. 🚀 Activate Node"
    echo "4. ⏸️  Deactivate Node"
    echo "5. 📤 Send Command to Node"
    echo "6. 🌡️  Get Sensor Data"
    echo "7. 🔄 Refresh Node Status"
    echo "8. 🚪 Exit"
    echo ""
}

# Main execution
if [ "$1" == "--interactive" ]; then
    while true; do
        clear
        echo -e "${GREEN}🏭 Industrial IoT Node Management System${NC}"
        echo "======================================="
        echo ""
        
        get_nodes
        echo ""
        show_menu
        
        read -p "Select option (1-8): " choice
        
        case $choice in
            1)
                clear
                get_nodes
                read -p "Press Enter to continue..."
                ;;
            2)
                read -p "Enter Node ID: " node_id
                get_node_details $node_id
                read -p "Press Enter to continue..."
                ;;
            3)
                read -p "Enter Node ID to activate: " node_id
                activate_node $node_id
                read -p "Press Enter to continue..."
                ;;
            4)
                read -p "Enter Node ID to deactivate: " node_id
                deactivate_node $node_id
                read -p "Press Enter to continue..."
                ;;
            5)
                read -p "Enter Node ID: " node_id
                read -p "Enter Command: " command
                send_node_command $node_id "$command"
                read -p "Press Enter to continue..."
                ;;
            6)
                read -p "Enter Node ID: " node_id
                get_sensor_data $node_id
                read -p "Press Enter to continue..."
                ;;
            7)
                echo "🔄 Refreshing..."
                sleep 1
                ;;
            8)
                echo "👋 Goodbye!"
                exit 0
                ;;
            *)
                echo "❌ Invalid option"
                sleep 1
                ;;
        esac
    done
else
    # Command line mode
    case "$1" in
        "list"|"")
            get_nodes
            ;;
        "details")
            if [ -z "$2" ]; then
                echo "Usage: $0 details <node_id>"
                exit 1
            fi
            get_node_details $2
            ;;
        "activate")
            if [ -z "$2" ]; then
                echo "Usage: $0 activate <node_id>"
                exit 1
            fi
            activate_node $2
            ;;
        "deactivate")
            if [ -z "$2" ]; then
                echo "Usage: $0 deactivate <node_id>"
                exit 1
            fi
            deactivate_node $2
            ;;
        "command")
            if [ -z "$2" ] || [ -z "$3" ]; then
                echo "Usage: $0 command <node_id> <command>"
                exit 1
            fi
            send_node_command $2 "$3"
            ;;
        "sensors")
            if [ -z "$2" ]; then
                echo "Usage: $0 sensors <node_id>"
                exit 1
            fi
            get_sensor_data $2
            ;;
        *)
            echo "🏭 Node Management Commands:"
            echo "=========================="
            echo "$0                     - List all nodes"
            echo "$0 list                - List all nodes"
            echo "$0 details <id>        - Get node details"
            echo "$0 activate <id>       - Activate node"
            echo "$0 deactivate <id>     - Deactivate node"
            echo "$0 command <id> <cmd>  - Send command to node"
            echo "$0 sensors <id>        - Get sensor data"
            echo "$0 --interactive       - Interactive mode"
            ;;
    esac
fi

#!/bin/bash

echo "🌐 Starting Node Management Web Interface"
echo "========================================"

# Check if API is running
if ! curl -s http://localhost:3005/health > /dev/null; then
    echo "❌ API server is not running. Please start it first:"
    echo "   docker-compose up -d rnr_api_server"
    exit 1
fi

echo "✅ API server is running"
echo ""

# Get authentication token
echo "🔐 Getting authentication token..."
TOKEN=$(curl -s -X POST "http://localhost:3005/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ Authentication failed. Please check credentials."
    exit 1
fi

echo "✅ Authentication successful"
echo ""

# Available node management endpoints
echo "🔗 Node Management API Endpoints:"
echo "================================="
echo "GET    /api/nodes                 - List all nodes"
echo "GET    /api/nodes/{id}            - Get node details"
echo "POST   /api/nodes/{id}/activate   - Activate node"
echo "POST   /api/nodes/{id}/deactivate - Deactivate node"
echo "POST   /api/nodes/{id}/action     - Send command to node"
echo "GET    /api/nodes/{id}/sensor-data - Get sensor data"
echo ""

# Current node status
echo "📊 Current Node Status:"
echo "======================"
curl -s http://localhost:3005/api/nodes | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        nodes = data
    else:
        nodes = data.get('nodes', [])
    
    for node in nodes:
        node_id = node.get('id', 'N/A')
        name = node.get('name', 'Unknown')
        status = node.get('status', 'unknown')
        print(f'Node {node_id}: {name} - {status.upper()}')
except:
    print('Failed to get node data')
"

echo ""
echo "🎮 Node Management Commands:"
echo "==========================="

# Interactive management functions
function activate_node() {
    local node_id=$1
    echo "🚀 Activating Node $node_id..."
    
    RESULT=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        http://localhost:3005/api/nodes/$node_id/activate)
    
    echo "Result: $RESULT"
}

function deactivate_node() {
    local node_id=$1
    echo "⏸️ Deactivating Node $node_id..."
    
    RESULT=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        http://localhost:3005/api/nodes/$node_id/deactivate)
    
    echo "Result: $RESULT"
}

function send_command() {
    local node_id=$1
    local command=$2
    echo "📤 Sending command '$command' to Node $node_id..."
    
    RESULT=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"command\": \"$command\"}" \
        http://localhost:3005/api/nodes/$node_id/action)
    
    echo "Result: $RESULT"
}

function get_node_details() {
    local node_id=$1
    echo "🔍 Getting details for Node $node_id..."
    
    RESULT=$(curl -s -H "Authorization: Bearer $TOKEN" \
        http://localhost:3005/api/nodes/$node_id)
    
    echo "$RESULT" | python3 -c "
import json, sys
try:
    node = json.load(sys.stdin)
    print(f'Name: {node.get(\"name\", \"Unknown\")}')
    print(f'ID: {node.get(\"id\", \"N/A\")}')
    print(f'Status: {node.get(\"status\", \"unknown\")}')
    print(f'Type: {node.get(\"type\", \"ESP32\")}')
    print(f'Location: {node.get(\"location\", \"Not set\")}')
    print(f'IP Address: {node.get(\"ip_address\", \"Not available\")}')
except:
    print('Failed to parse node details')
"
}

echo "Available commands:"
echo "• activate_node <id>     - Activate a node"
echo "• deactivate_node <id>   - Deactivate a node"
echo "• send_command <id> <cmd> - Send command to node"
echo "• get_node_details <id>  - Get detailed node info"
echo ""

# Check if specific command was requested
if [ ! -z "$1" ]; then
    case "$1" in
        "activate")
            if [ ! -z "$2" ]; then
                activate_node $2
            else
                echo "Usage: $0 activate <node_id>"
            fi
            ;;
        "deactivate")
            if [ ! -z "$2" ]; then
                deactivate_node $2
            else
                echo "Usage: $0 deactivate <node_id>"
            fi
            ;;
        "command")
            if [ ! -z "$2" ] && [ ! -z "$3" ]; then
                send_command $2 "$3"
            else
                echo "Usage: $0 command <node_id> <command>"
            fi
            ;;
        "details")
            if [ ! -z "$2" ]; then
                get_node_details $2
            else
                echo "Usage: $0 details <node_id>"
            fi
            ;;
        *)
            echo "Unknown command: $1"
            echo "Available: activate, deactivate, command, details"
            ;;
    esac
else
    echo "💡 Examples:"
    echo "  $0 activate 1              - Activate node 1"
    echo "  $0 deactivate 2            - Deactivate node 2"
    echo "  $0 command 1 'restart'     - Send restart command to node 1"
    echo "  $0 details 1               - Get details for node 1"
    echo ""
    echo "🌐 For web interface, visit: http://localhost:3005/docs"
    echo "🔧 For interactive mode, use: ./node_manager.sh --interactive"
fi

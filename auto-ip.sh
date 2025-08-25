#!/bin/bash
# Auto IP Detection Script for RNR Solutions IoT Platform

echo "🔍 Detecting local IP address..."

# Function to detect local IP address
get_local_ip() {
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows (Git Bash, MSYS2, Cygwin)
        LOCAL_IP=$(ipconfig | grep -A 5 "Ethernet adapter" | grep "IPv4 Address" | head -1 | cut -d: -f2 | tr -d ' ')
        if [ -z "$LOCAL_IP" ]; then
            # Try Wi-Fi adapter
            LOCAL_IP=$(ipconfig | grep -A 5 "Wireless LAN adapter" | grep "IPv4 Address" | head -1 | cut -d: -f2 | tr -d ' ')
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        LOCAL_IP=$(hostname -I | awk '{print $1}')
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
    else
        # Default fallback
        LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || ifconfig | grep -E "inet.*broadcast" | awk '{print $2}' | head -1)
    fi
    
    # Remove any trailing characters
    LOCAL_IP=$(echo $LOCAL_IP | tr -d '\r\n')
    echo $LOCAL_IP
}

# Detect IP
DETECTED_IP=$(get_local_ip)

if [ -z "$DETECTED_IP" ]; then
    echo "❌ Could not detect IP address automatically"
    echo "📝 Please set IP manually in .env files"
    DETECTED_IP="localhost"
else
    echo "✅ Detected IP: $DETECTED_IP"
fi

# Update main .env file
echo "📝 Updating main .env file..."
sed -i.bak "s|REACT_APP_API_URL=http://.*:8000/api|REACT_APP_API_URL=http://$DETECTED_IP:8000/api|g" .env
sed -i.bak "s|REACT_APP_WS_URL=ws://.*:8000/ws|REACT_APP_WS_URL=ws://$DETECTED_IP:8000/ws|g" .env

# Update frontend .env file
echo "📝 Updating frontend/.env file..."
sed -i.bak "s|REACT_APP_API_URL=http://.*:8000/api|REACT_APP_API_URL=http://$DETECTED_IP:8000/api|g" frontend/.env
sed -i.bak "s|REACT_APP_WS_URL=ws://.*:8000/ws|REACT_APP_WS_URL=ws://$DETECTED_IP:8000/ws|g" frontend/.env

# Update docker-compose.yml
echo "📝 Updating docker-compose.yml..."
sed -i.bak "s|REACT_APP_API_URL: http://.*:8000/api|REACT_APP_API_URL: http://$DETECTED_IP:8000/api|g" docker-compose.yml
sed -i.bak "s|REACT_APP_WS_URL: ws://.*:8000/ws|REACT_APP_WS_URL: ws://$DETECTED_IP:8000/ws|g" docker-compose.yml
sed -i.bak "s|args:.*REACT_APP_API_URL: http://.*:8000/api|args:\n        REACT_APP_API_URL: http://$DETECTED_IP:8000/api|g" docker-compose.yml
sed -i.bak "s|REACT_APP_WS_URL: ws://.*:8000/ws|REACT_APP_WS_URL: ws://$DETECTED_IP:8000/ws|g" docker-compose.yml

echo "✅ IP configuration updated to: $DETECTED_IP"
echo "🚀 You can now run: docker-compose up --build -d"

#!/bin/bash

# RNR Solutions IoT Platform - Port Status Checker
# Shows all open ports and service mappings

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_section() {
    echo -e "${BLUE}=========================================="
    echo -e "$1"
    echo -e "==========================================${NC}"
}

print_section "RNR Solutions IoT Platform - Port Status"

# Check if running as root for some commands
if [ "$EUID" -eq 0 ]; then
    SUDO=""
else
    SUDO="sudo"
fi

print_section "System Network Ports"

print_status "All listening ports on the system:"
echo "Protocol | Local Address | State | Process"
echo "---------|---------------|-------|--------"
$SUDO netstat -tlnp 2>/dev/null | grep LISTEN | while read line; do
    proto=$(echo $line | awk '{print $1}')
    address=$(echo $line | awk '{print $4}')
    process=$(echo $line | awk '{print $7}' | cut -d'/' -f2)
    echo "$proto | $address | LISTEN | $process"
done

echo ""
print_section "Docker Container Ports"

if command -v docker &> /dev/null; then
    print_status "Docker containers and their port mappings:"
    docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}" 2>/dev/null || echo "No Docker containers running or Docker not accessible"
else
    print_warning "Docker not found or not accessible"
fi

echo ""
print_section "Expected RNR IoT Platform Ports"

echo "Service               | Internal Port | External Port | Protocol | Purpose"
echo "----------------------|---------------|---------------|----------|------------------"
echo "nginx                 | 80            | 80            | HTTP     | Web Server/Proxy"
echo "nginx (SSL)           | 443           | 443           | HTTPS    | Secure Web"
echo "Frontend (React)      | 3000          | 3000          | HTTP     | Web Application"
echo "API Server            | 8000          | 8000          | HTTP     | REST API"
echo "PostgreSQL            | 5432          | 15432         | TCP      | Database"
echo "RabbitMQ AMQP         | 5672          | 5672          | TCP      | Message Queue"
echo "RabbitMQ Management   | 15672         | 15672         | HTTP     | Web Management"
echo "RabbitMQ MQTT         | 1883          | 1883          | TCP      | IoT Devices"
echo "SSH                   | 22            | 22            | TCP      | Remote Access"

echo ""
print_section "Port Security Analysis"

# Check specific ports for RNR IoT Platform
declare -A rnr_ports=(
    ["80"]="nginx - Web Server"
    ["443"]="nginx - HTTPS (if SSL configured)"
    ["3000"]="Frontend - React Application"
    ["8000"]="API Server - Backend API"
    ["5672"]="RabbitMQ - AMQP Message Queue"
    ["15672"]="RabbitMQ - Management UI"
    ["1883"]="RabbitMQ - MQTT for IoT"
    ["15432"]="PostgreSQL - Database"
    ["22"]="SSH - System Access"
)

print_status "Checking RNR IoT Platform ports:"
for port in "${!rnr_ports[@]}"; do
    if $SUDO netstat -tln 2>/dev/null | grep -q ":$port "; then
        echo -e "${GREEN}✓${NC} Port $port is OPEN - ${rnr_ports[$port]}"
    else
        echo -e "${RED}✗${NC} Port $port is CLOSED - ${rnr_ports[$port]}"
    fi
done

echo ""
print_section "Firewall Status"

# Check UFW status
if command -v ufw &> /dev/null; then
    print_status "UFW Firewall status:"
    $SUDO ufw status 2>/dev/null || echo "UFW status unknown"
else
    print_warning "UFW not found"
fi

# Check iptables
echo ""
print_status "Basic iptables rules:"
$SUDO iptables -L INPUT -n 2>/dev/null | head -10 || echo "iptables not accessible"

echo ""
print_section "External Access Check"

# Try to get public IP
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "Unable to detect")
print_status "Public IP Address: $PUBLIC_IP"

if [ "$PUBLIC_IP" != "Unable to detect" ]; then
    echo ""
    print_status "External access URLs:"
    echo "Frontend:          http://$PUBLIC_IP"
    echo "API:               http://$PUBLIC_IP/api (via nginx)"
    echo "Direct API:        http://$PUBLIC_IP:8000"
    echo "RabbitMQ Mgmt:     http://$PUBLIC_IP:15672"
    echo "MQTT Endpoint:     $PUBLIC_IP:1883"
fi

echo ""
print_section "Port Usage Recommendations"

echo "🔒 SECURITY RECOMMENDATIONS:"
echo ""
echo "REQUIRED OPEN PORTS (for public access):"
echo "  ✅ Port 80 (HTTP) - Web traffic"
echo "  ✅ Port 443 (HTTPS) - Secure web traffic (when SSL configured)"
echo "  ✅ Port 1883 (MQTT) - IoT device connections"
echo "  ✅ Port 22 (SSH) - Administration (restrict to your IP)"
echo ""
echo "OPTIONAL OPEN PORTS (for development/monitoring):"
echo "  ⚠️  Port 3000 - Frontend (can be closed if using nginx proxy)"
echo "  ⚠️  Port 8000 - API (can be closed if using nginx proxy)"
echo "  ⚠️  Port 15672 - RabbitMQ Management (close for production)"
echo ""
echo "SHOULD BE CLOSED (internal only):"
echo "  🔒 Port 15432 - PostgreSQL (database should not be public)"
echo "  🔒 Port 5672 - RabbitMQ AMQP (use nginx proxy if needed)"

echo ""
print_section "AWS Security Group Configuration"

echo "For AWS EC2, configure your Security Group with these rules:"
echo ""
echo "INBOUND RULES:"
echo "Type        | Protocol | Port  | Source      | Description"
echo "------------|----------|-------|-------------|------------------"
echo "SSH         | TCP      | 22    | My IP       | SSH Access"
echo "HTTP        | TCP      | 80    | 0.0.0.0/0   | Web Traffic"
echo "HTTPS       | TCP      | 443   | 0.0.0.0/0   | Secure Web"
echo "Custom TCP  | TCP      | 1883  | 0.0.0.0/0   | MQTT IoT Devices"
echo "Custom TCP  | TCP      | 15672 | My IP       | RabbitMQ Mgmt (dev only)"
echo "Custom TCP  | TCP      | 3000  | My IP       | Frontend (dev only)"
echo "Custom TCP  | TCP      | 8000  | My IP       | API (dev only)"

echo ""
echo "OUTBOUND RULES:"
echo "All traffic | All | All | 0.0.0.0/0 | Allow all outbound"

echo ""
print_section "Quick Commands"

echo "🔧 USEFUL COMMANDS:"
echo ""
echo "Check specific port:"
echo "  sudo netstat -tlnp | grep :PORT_NUMBER"
echo ""
echo "Test port connectivity:"
echo "  telnet YOUR_SERVER_IP PORT_NUMBER"
echo "  nc -zv YOUR_SERVER_IP PORT_NUMBER"
echo ""
echo "Check Docker container ports:"
echo "  docker port CONTAINER_NAME"
echo ""
echo "Monitor network connections:"
echo "  sudo netstat -tuln"
echo "  ss -tuln"

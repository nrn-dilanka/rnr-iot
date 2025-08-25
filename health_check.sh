#!/bin/bash

# RNR Solutions IoT Platform - Health Check Script
# Quick verification that all services are running properly

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

echo "=========================================="
echo "RNR Solutions IoT Platform Health Check"
echo "=========================================="

# Check if Docker is running
if systemctl is-active --quiet docker; then
    print_status "Docker is running"
else
    print_error "Docker is not running"
    exit 1
fi

# Check if nginx is running
if systemctl is-active --quiet nginx; then
    print_status "Nginx is running"
else
    print_error "Nginx is not running"
fi

# Check Docker containers
echo ""
print_info "Checking Docker containers..."

containers=("rnr_iot_postgres" "rnr_iot_rabbitmq" "rnr_iot_api_server" "rnr_iot_worker_service" "rnr_iot_frontend")

for container in "${containers[@]}"; do
    if docker ps --format "table {{.Names}}" | grep -q "^$container$"; then
        print_status "$container is running"
    else
        print_error "$container is not running"
    fi
done

# Check port connectivity
echo ""
print_info "Checking port connectivity..."

ports=("80:nginx" "3000:frontend" "8000:api" "5672:rabbitmq" "15432:postgres" "1883:mqtt")

for port_service in "${ports[@]}"; do
    port=$(echo $port_service | cut -d: -f1)
    service=$(echo $port_service | cut -d: -f2)
    
    if netstat -tln | grep -q ":$port "; then
        print_status "Port $port ($service) is listening"
    else
        print_error "Port $port ($service) is not listening"
    fi
done

# Check API health
echo ""
print_info "Checking API health..."

if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "API health check passed"
else
    print_warning "API health check failed (might still be starting)"
fi

# Check frontend
if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    print_status "Frontend is responding"
else
    print_warning "Frontend not responding (might still be starting)"
fi

# Check nginx config
echo ""
print_info "Checking nginx configuration..."

if nginx -t > /dev/null 2>&1; then
    print_status "Nginx configuration is valid"
else
    print_error "Nginx configuration has errors"
fi

# Check disk space
echo ""
print_info "System resources:"

disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$disk_usage" -lt 80 ]; then
    print_status "Disk usage: ${disk_usage}%"
else
    print_warning "Disk usage high: ${disk_usage}%"
fi

memory_usage=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
memory_check=$(echo "$memory_usage < 80" | bc -l)
if [ "$memory_check" -eq 1 ]; then
    print_status "Memory usage: ${memory_usage}%"
else
    print_warning "Memory usage high: ${memory_usage}%"
fi

echo ""
echo "=========================================="
print_info "Health check completed"

# Show access URLs
echo ""
print_info "Access URLs:"
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_EC2_IP")
echo "Frontend:     http://$PUBLIC_IP"
echo "API:          http://$PUBLIC_IP/api"
echo "RabbitMQ UI:  http://$PUBLIC_IP/rabbitmq"
echo ""

print_info "For detailed logs: docker-compose logs [service_name]"
print_info "For monitoring: ./monitor_platform.sh"

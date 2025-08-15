#!/bin/bash

# Fix nginx configuration for API docs MIME type issues
# RNR Solutions IoT Platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_section() {
    echo -e "${BLUE}=========================================="
    echo -e "$1"
    echo -e "==========================================${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo)"
    exit 1
fi

print_section "Fixing Nginx Configuration for API Docs"

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Backup current nginx config
print_status "Backing up current nginx configuration..."
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)

# Copy new nginx configuration
print_status "Installing updated nginx configuration..."
cp nginx.conf /etc/nginx/nginx.conf

# Test nginx configuration
print_status "Testing nginx configuration..."
nginx -t
if [ $? -ne 0 ]; then
    print_error "Nginx configuration test failed!"
    print_warning "Restoring backup configuration..."
    cp /etc/nginx/nginx.conf.backup.* /etc/nginx/nginx.conf
    exit 1
fi

# Reload nginx
print_status "Reloading nginx..."
systemctl reload nginx

# Restart API containers to apply FastAPI changes
print_status "Restarting API containers..."
docker-compose restart rnr_api_server

print_section "Fix Complete!"
print_status "Nginx configuration updated successfully"
print_status "API documentation should now load properly"

echo ""
print_status "Test the API docs at:"
echo "http://$(curl -s ifconfig.me || echo 'YOUR_IP')/api/docs"
echo "http://$(curl -s ifconfig.me || echo 'YOUR_IP')/docs"

echo ""
print_status "If issues persist, check logs with:"
echo "sudo tail -f /var/log/nginx/error.log"
echo "docker-compose logs rnr_api_server"

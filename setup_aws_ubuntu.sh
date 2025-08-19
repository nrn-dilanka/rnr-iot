#!/bin/bash

# RNR Solutions IoT Platform - AWS EC2 Ubuntu Setup Script
# This script sets up nginx and the complete IoT platform on Ubuntu

set -e

echo "=========================================="
echo "RNR Solutions IoT Platform Setup"
echo "AWS EC2 Ubuntu Installation"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo)"
    exit 1
fi

# Update system
print_status "Updating system packages..."
apt update && apt upgrade -y

# Remove any existing Docker packages that might conflict
print_status "Removing any existing Docker packages..."
apt remove -y docker docker-engine docker.io containerd runc containerd.io || true
apt autoremove -y

# Install basic required packages first
print_status "Installing basic required packages..."
apt install -y \
    curl \
    wget \
    git \
    ufw \
    htop \
    net-tools \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Install nginx separately
print_status "Installing nginx..."
apt install -y nginx

# Add Docker's official GPG key and repository
print_status "Adding Docker repository..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package index
print_status "Updating package index with Docker repository..."
apt update

# Install Docker Engine
print_status "Installing Docker Engine..."
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin

# Install Docker Compose v2 (plugin)
print_status "Installing Docker Compose v2..."
apt install -y docker-compose-plugin

# Create symlink for docker-compose command compatibility
ln -sf /usr/libexec/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose || true

# Add current user to docker group (if not root)
if [ "$SUDO_USER" ]; then
    usermod -aG docker $SUDO_USER
    print_status "Added $SUDO_USER to docker group"
fi

# Start and enable services
print_status "Starting and enabling services..."
systemctl start docker
systemctl enable docker
systemctl start nginx
systemctl enable nginx

# Configure firewall
print_status "Configuring UFW firewall..."
ufw --force enable
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 1883/tcp  # MQTT
ufw allow 8000/tcp  # API (optional - can be removed in production)
ufw allow 3000/tcp  # Frontend (optional - can be removed in production)

# Backup default nginx config
print_status "Backing up default nginx configuration..."
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup

# Create nginx directory structure
mkdir -p /etc/nginx/conf.d
mkdir -p /var/log/nginx

# Set up log rotation for nginx
cat > /etc/logrotate.d/nginx << 'EOF'
/var/log/nginx/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data adm
    sharedscripts
    prerotate
        if [ -d /etc/logrotate.d/httpd-prerotate ]; then \
            run-parts /etc/logrotate.d/httpd-prerotate; \
        fi
    endscript
    postrotate
        invoke-rc.d nginx rotate >/dev/null 2>&1
    endscript
}
EOF

# Create .env file template if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file template..."
    cat > .env << 'EOF'
# RNR Solutions IoT Platform Environment Variables

# Database Configuration
DATABASE_URL=postgresql://rnr_iot_user:rnr_iot_2025!@localhost:15432/rnr_iot_platform

# RabbitMQ Configuration
RABBITMQ_URL=amqp://rnr_iot_user:rnr_iot_2025!@localhost:5672/rnr_iot_vhost

# API Configuration
API_URL=http://localhost:8000

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000/ws

# Gemini AI Configuration
GEMINI_API_KEY=AIzaSyAs2JqPjvUcWeg5K2Vxeto7j37GzUzABUY

# Company Branding
RNR_COMPANY_NAME="RNR Solutions"
RNR_PLATFORM_VERSION="2.0.0"
EOF
    print_warning "Created .env file with default values. Please update with your actual configuration."
fi

print_status "=========================================="
print_status "Setup completed successfully!"
print_status "=========================================="

echo ""
print_status "Next steps:"
echo "1. Copy your project files to the server"
echo "2. Update the nginx configuration with your domain/IP"
echo "3. Configure SSL certificates (recommended for production)"
echo "4. Update .env file with your actual values"
echo "5. Deploy the platform using docker-compose"

echo ""
print_status "To deploy the platform:"
echo "sudo ./deploy_aws_platform.sh"

echo ""
print_warning "Don't forget to:"
echo "- Update security groups in AWS to allow ports 80, 443, 1883"
echo "- Configure a domain name and SSL certificate for production"
echo "- Review and update the nginx configuration with your domain"

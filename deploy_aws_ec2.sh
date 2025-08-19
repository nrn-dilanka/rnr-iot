#!/bin/bash

# RNR Solutions IoT Platform - AWS EC2 Deployment Script
# This script sets up the RNR IoT Platform on AWS EC2 Ubuntu instance

set -e

echo "🚀 RNR Solutions IoT Platform - AWS EC2 Deployment"
echo "=================================================="

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io
    sudo usermod -aG docker $USER
    echo "✅ Docker installed successfully"
else
    echo "✅ Docker is already installed"
fi

# Install Docker Compose
echo "🔧 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose installed successfully"
else
    echo "✅ Docker Compose is already installed"
fi

# Install Nginx
echo "🌐 Installing and configuring Nginx..."
sudo apt install -y nginx

# Stop default nginx service
sudo systemctl stop nginx

# Copy our nginx configuration
sudo cp nginx.conf /etc/nginx/nginx.conf

# Test nginx configuration
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration error"
    exit 1
fi

# Configure firewall (UFW)
echo "🔒 Configuring firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 80/tcp          # HTTP
sudo ufw allow 443/tcp         # HTTPS
sudo ufw allow 3005/tcp        # API Server
sudo ufw allow 15672/tcp       # RabbitMQ Management (optional)
sudo ufw allow 1883/tcp        # MQTT
sudo ufw allow 5672/tcp        # RabbitMQ AMQP

echo "✅ Firewall configured"

# Start Docker service
echo "🐳 Starting Docker service..."
sudo systemctl enable docker
sudo systemctl start docker

# Deploy the IoT Platform
echo "🚀 Deploying RNR IoT Platform..."
docker-compose down || true
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 30

# Check service status
echo "📊 Checking service status..."
docker-compose ps

# Start Nginx
echo "🌐 Starting Nginx..."
sudo systemctl enable nginx
sudo systemctl start nginx

# Get EC2 public IP
EC2_PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")

echo ""
echo "🎉 RNR Solutions IoT Platform Deployment Complete!"
echo "=================================================="
echo ""
echo "📡 Access Points:"
echo "  • API Server: http://$EC2_PUBLIC_IP:3005"
echo "  • API Documentation: http://$EC2_PUBLIC_IP/api/docs"
echo "  • Health Check: http://$EC2_PUBLIC_IP/health"
echo "  • Nginx Proxy: http://$EC2_PUBLIC_IP"
echo ""
echo "🔧 Management:"
echo "  • RabbitMQ Management: http://$EC2_PUBLIC_IP:15672"
echo "    (Username: rnr_iot_user, Password: rnr_iot_2025!)"
echo ""
echo "📋 Useful Commands:"
echo "  • Check services: docker-compose ps"
echo "  • View logs: docker-compose logs"
echo "  • Restart services: docker-compose restart"
echo "  • Stop platform: docker-compose down"
echo ""
echo "🔒 Security Notes:"
echo "  • Change default passwords in production"
echo "  • Configure SSL certificates for HTTPS"
echo "  • Update EC2 security groups as needed"
echo ""

# Test API connectivity
echo "🧪 Testing API connectivity..."
if curl -f http://localhost:3005/health > /dev/null 2>&1; then
    echo "✅ API server is responding"
else
    echo "❌ API server is not responding"
fi

if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ Nginx proxy is working"
else
    echo "❌ Nginx proxy is not working"
fi

echo ""
echo "✅ Deployment script completed!"

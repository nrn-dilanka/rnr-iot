#!/bin/bash

# RNR Solutions - Docker Troubleshooting and Cleanup Script
# Resolves common Docker installation issues on Ubuntu

set -e

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

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
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

print_section "Docker Installation Troubleshooting"

# Step 1: Complete cleanup of existing Docker installations
print_status "Step 1: Removing all existing Docker packages..."
apt remove -y docker docker-engine docker.io containerd runc containerd.io docker-ce docker-ce-cli docker-buildx-plugin docker-compose-plugin || true

# Remove any snap Docker installations
print_status "Removing snap Docker packages..."
snap remove docker || true

# Clean up package cache
print_status "Cleaning package cache..."
apt autoremove -y
apt autoclean

# Step 2: Clean up any leftover files
print_status "Step 2: Cleaning up leftover Docker files..."
rm -rf /var/lib/docker || true
rm -rf /etc/docker || true
rm -f /etc/apt/sources.list.d/docker.list || true
rm -f /usr/share/keyrings/docker-archive-keyring.gpg || true

# Step 3: Hold any problematic packages
print_status "Step 3: Checking for held packages..."
apt-mark showhold

# Step 4: Update system
print_status "Step 4: Updating system..."
apt update
apt upgrade -y

# Step 5: Install prerequisites
print_status "Step 5: Installing prerequisites..."
apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    software-properties-common \
    apt-transport-https

# Step 6: Add Docker's official GPG key
print_status "Step 6: Adding Docker's GPG key..."
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Step 7: Add Docker repository
print_status "Step 7: Adding Docker repository..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Step 8: Update package index
print_status "Step 8: Updating package index..."
apt update

# Step 9: Install Docker CE
print_status "Step 9: Installing Docker CE..."
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Step 10: Verify installation
print_status "Step 10: Verifying Docker installation..."
systemctl start docker
systemctl enable docker

# Test Docker
if docker --version; then
    print_status "✓ Docker installed successfully: $(docker --version)"
else
    print_error "✗ Docker installation failed"
    exit 1
fi

# Test Docker Compose
if docker compose version; then
    print_status "✓ Docker Compose installed successfully: $(docker compose version)"
else
    print_error "✗ Docker Compose installation failed"
    exit 1
fi

# Step 11: Create docker-compose symlink for compatibility
print_status "Creating docker-compose symlink for compatibility..."
ln -sf /usr/libexec/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose || true

# Step 12: Test Docker functionality
print_status "Step 12: Testing Docker functionality..."
if docker run --rm hello-world > /dev/null 2>&1; then
    print_status "✓ Docker is working correctly"
else
    print_warning "Docker test failed, but installation appears successful"
fi

# Step 13: Set up user permissions (if not root)
if [ "$SUDO_USER" ]; then
    print_status "Adding $SUDO_USER to docker group..."
    usermod -aG docker $SUDO_USER
    print_warning "Please log out and log back in for group changes to take effect"
fi

print_section "Docker Installation Complete"

print_status "Next steps:"
echo "1. Log out and log back in (if you added user to docker group)"
echo "2. Run: docker --version"
echo "3. Run: docker compose version"
echo "4. Continue with platform deployment"

print_status "If you still have issues, check:"
echo "- System requirements (Ubuntu 18.04+ recommended)"
echo "- Available disk space (at least 10GB free)"
echo "- Network connectivity to Docker Hub"
echo "- No conflicting virtualization software"

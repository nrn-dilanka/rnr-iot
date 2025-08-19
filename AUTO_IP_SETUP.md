# 🚀 IoT Platform - Automatic IP Setup

This guide explains how to automatically detect and configure your local IP address for the IoT Platform.

## 🎯 Quick Setup (Automatic IP Detection)

### Method 1: Using npm scripts (Recommended)
```bash
# Install and setup with automatic IP detection
npm run setup
```

### Method 2: Manual automatic IP detection
```bash
# Run automatic IP detection
node auto-ip.js

# Then start the platform
docker-compose up --build -d
```

### Method 3: PowerShell (Windows)
```powershell
# Run PowerShell script
powershell -ExecutionPolicy Bypass -File auto-ip.ps1

# Then start the platform
docker-compose up --build -d
```

### Method 4: Bash script (Linux/Mac/Git Bash)
```bash
# Make script executable
chmod +x auto-ip.sh

# Run the script
./auto-ip.sh
```

## 📋 Available Scripts

```bash
# Detect and set IP automatically
npm run auto-ip

# Complete setup (auto-IP + build + start)
npm run setup

# Start the platform (containers must be built first)
npm run start

# Stop the platform
npm run stop

# Restart all services
npm run restart

# View logs from all services
npm run logs

# Check status of all containers
npm run status

# Clean up (stop and remove volumes)
npm run clean
```

## 🔧 How Automatic IP Detection Works

The automatic IP detection script:

1. **Detects your local IP address** using the system's network interfaces
2. **Updates configuration files** with the detected IP:
   - `.env` (main environment file)
   - `frontend/.env` (frontend configuration)
   - `docker-compose.yml` (container configuration)
3. **Provides feedback** on the detected IP and updated configuration

### Detection Priority
1. **Ethernet adapter** (wired connection)
2. **Wi-Fi adapter** (wireless connection)
3. **Any active network interface** (fallback)

### Updated URLs
After running the script, your platform will be accessible at:
- **Frontend**: `http://[YOUR_IP]:3000`
- **API Server**: `http://[YOUR_IP]:8000`
- **WebSocket**: `ws://[YOUR_IP]:8000/ws`
- **RabbitMQ Management**: `http://localhost:15672`

## 🌐 Manual IP Configuration

If automatic detection doesn't work, you can manually update these files:

### 1. Main `.env` file:
```bash
REACT_APP_API_URL=http://YOUR_IP:8000/api
REACT_APP_WS_URL=ws://YOUR_IP:8000/ws
```

### 2. Frontend `.env` file:
```bash
REACT_APP_API_URL=http://YOUR_IP:8000/api
REACT_APP_WS_URL=ws://YOUR_IP:8000/ws
```

### 3. Docker Compose file:
```yaml
frontend:
  environment:
    REACT_APP_API_URL: http://YOUR_IP:8000/api
    REACT_APP_WS_URL: ws://YOUR_IP:8000/ws
```

## 🔍 Finding Your IP Address Manually

### Windows:
```cmd
ipconfig | findstr IPv4
```

### Linux/Mac:
```bash
hostname -I
# or
ifconfig | grep inet
```

## 🚨 Troubleshooting

### Issue: IP detection fails
**Solution**: Run manual IP detection commands above and update files manually

### Issue: Cannot access platform from other devices
**Solution**: 
1. Ensure your firewall allows connections on ports 3000, 8000
2. Verify the IP address is correct for your network
3. Check that Docker containers are running: `docker-compose ps`

### Issue: WebSocket connection fails
**Solution**: 
1. Verify WebSocket URL is correct in browser dev tools
2. Check if any proxy or firewall is blocking WebSocket connections
3. Ensure API server is running and accessible

## 📊 Current Configuration

After running the auto-IP script, you'll see output like:
```
✅ Detected IP: 192.168.1.100
📋 Current Configuration:
  • Frontend URL: http://192.168.1.100:3000
  • API URL: http://192.168.1.100:8000
  • WebSocket URL: ws://192.168.1.100:8000/ws
  • RabbitMQ Management: http://localhost:15672
```

## 🔄 Re-running IP Detection

If your IP changes (e.g., switching networks), simply run:
```bash
npm run auto-ip
```

Then restart the containers:
```bash
npm run restart
```

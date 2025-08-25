# 🏭 Industrial IoT Node Management System

## 📊 Current System Status

**Total Nodes**: 5 ESP32 devices  
**Status**: All offline (system ready for activation)  
**System Health**: Ready for node deployment

### 🔗 Connected Nodes
1. **ESP32-F9456C** (ID: 1) - Industrial monitoring device
2. **Endpoint Test Node** (ID: 5) - Testing and validation device  
3. **ESP32-D3E4F5** (ID: 2) - Environmental sensor hub
4. **ESP32-4D5E6F** (ID: 3) - Equipment monitoring unit
5. **ESP32-C3B4A5** (ID: 4) - Process control device

## 🎮 Management Tools

### 1. **Interactive Node Manager** (Recommended)
```bash
./node_manager.sh --interactive
```
**Features**:
- Visual menu-driven interface
- Real-time node status
- Easy activation/deactivation
- Command sending capabilities
- Sensor data viewing

### 2. **Real-Time Monitoring Dashboard**
```bash
./monitor_nodes.sh
```
**Features**:
- Live node status updates
- System health monitoring
- Uptime statistics
- Auto-refresh every 5 seconds

### 3. **Command Line Management**
```bash
# List all nodes
./node_manager.sh list

# Get node details
./node_manager.sh details <node_id>

# Activate a node
./node_manager.sh activate <node_id>

# Deactivate a node
./node_manager.sh deactivate <node_id>

# Send command to node
./node_manager.sh command <node_id> <command>

# Get sensor data
./node_manager.sh sensors <node_id>
```

### 4. **Web API Management**
```bash
# Quick operations
./manage_nodes.sh activate 1      # Activate node 1
./manage_nodes.sh details 2       # Get details for node 2
./manage_nodes.sh command 3 reset # Send reset command to node 3
```

## 🌐 Web Interface Access

### FastAPI Documentation
- **URL**: http://localhost:3005/docs
- **Features**: Interactive API testing, endpoint documentation
- **Authentication**: Use admin/admin123 for testing

### Available API Endpoints
- `GET /api/nodes` - List all nodes
- `GET /api/nodes/{id}` - Get specific node details
- `POST /api/nodes/{id}/activate` - Activate node
- `POST /api/nodes/{id}/deactivate` - Deactivate node
- `POST /api/nodes/{id}/action` - Send commands
- `GET /api/nodes/{id}/sensor-data` - Get sensor readings

## 🔧 Node Operations

### Activation Process
```bash
# Activate node 1
./manage_nodes.sh activate 1

# Or using interactive mode
./node_manager.sh --interactive
# Then select option 3 and enter node ID
```

### Sending Commands
```bash
# Send restart command
./manage_nodes.sh command 1 restart

# Send configuration update
./manage_nodes.sh command 1 "update_config"

# Send sensor calibration
./manage_nodes.sh command 1 "calibrate_sensors"
```

### Monitoring Sensor Data
```bash
# Get latest sensor readings
./node_manager.sh sensors 1

# Monitor all sensors in real-time
./monitor_nodes.sh
# Press 's' to view sensor data
```

## 📡 Node Communication

### MQTT Integration
- **Broker**: RabbitMQ with MQTT plugin
- **Queue**: `device_data`
- **Routing**: Topic exchange with `devices.*.data` pattern
- **Protocol**: MQTT over port 1883

### Message Flow
1. ESP32 devices publish sensor data
2. RabbitMQ routes messages to `device_data` queue
3. Backend processes and stores data
4. Web interface displays real-time updates

## 🔒 Security & Authentication

### Access Control
- **Authentication**: JWT tokens required for node operations
- **Roles**: Admin users can manage all nodes
- **Permissions**: Operators can view and control assigned nodes

### Default Credentials
- **Username**: admin
- **Password**: admin123
- **Role**: superuser (full access)

## 🏥 System Health Monitoring

### Health Indicators
- **Green (🟢)**: Node online and responsive
- **Red (🔴)**: Node offline or unreachable
- **Yellow (🟡)**: Node status unknown or degraded

### Monitoring Commands
```bash
# System overview
./node_manager.sh list

# Real-time dashboard
./monitor_nodes.sh

# Health check
curl http://localhost:3005/health
```

## 🚀 Quick Start Guide

### 1. Start Node Management
```bash
# Interactive mode (recommended for beginners)
./node_manager.sh --interactive

# Real-time monitoring
./monitor_nodes.sh
```

### 2. Activate Your First Node
```bash
# Option 1: Command line
./manage_nodes.sh activate 1

# Option 2: Interactive menu
./node_manager.sh --interactive
# Choose option 3, enter node ID 1
```

### 3. Monitor Node Status
```bash
# Check if activation worked
./node_manager.sh list

# View detailed information
./manage_nodes.sh details 1
```

### 4. Send Commands (When Node is Online)
```bash
# Test communication
./manage_nodes.sh command 1 "ping"

# Request sensor reading
./manage_nodes.sh command 1 "read_sensors"
```

## 🔄 Troubleshooting

### Common Issues
1. **All nodes offline**: Normal state - activate them individually
2. **Authentication failed**: Check admin credentials
3. **API not responding**: Restart with `docker-compose up -d`
4. **Commands not working**: Ensure node is activated first

### Debug Commands
```bash
# Check API status
curl http://localhost:3005/health

# Check authentication
./manage_nodes.sh details 1

# Check RabbitMQ queues
./queue_manager.sh
```

---

**Your industrial IoT node management system is ready!** Use the interactive tools to start managing your ESP32 devices. 🏭✨

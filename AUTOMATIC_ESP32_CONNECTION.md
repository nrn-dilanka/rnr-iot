# Automatic ESP32 Connection System

## 🚀 Overview

The IoT Platform now features **automatic ESP32 device discovery and management**. When ESP32 devices connect to the MQTT broker and start sending data, they are automatically detected, registered, and managed by the system.

## ✨ Key Features

### **1. Automatic Device Discovery**
- **Zero Configuration**: ESP32 devices are auto-detected when they first connect
- **Real-time Registration**: New devices appear in the system immediately
- **Unique Identification**: Each device gets a unique ID based on MAC address
- **Capability Detection**: System automatically detects device capabilities (temperature, humidity, servo control)

### **2. Device Management**
- **Live Status Monitoring**: Real-time connection status for all devices
- **Remote Control**: Send commands to devices via web interface
- **Servo Control**: Direct servo motor control with angle specification
- **Device Information**: Edit device names, locations, and settings
- **Health Monitoring**: Track device uptime, memory usage, and signal strength

### **3. Enhanced Web Interface**
- **ESP32 Manager Dashboard**: Dedicated interface for ESP32 device management
- **Statistics Overview**: Total, connected, active, and offline device counts
- **Real-time Updates**: Live device status updates via WebSocket
- **Command Center**: Send reboot, status, and servo commands
- **Device Configuration**: Update device information through the UI

## 🔧 How It Works

### **1. Device Discovery Process**
```
ESP32 Device Powers On
        ↓
Connects to WiFi Network
        ↓
Connects to MQTT Broker
        ↓
Publishes First Data Message
        ↓
System Detects New Device
        ↓
Auto-Registration in Database
        ↓
Welcome Message Sent to Device
        ↓
Device Appears in Web Interface
```

### **2. MQTT Topic Structure**
- **Data Publishing**: `devices/{MAC_ADDRESS}/data`
- **Command Receiving**: `devices/{MAC_ADDRESS}/commands`
- **Auto-Discovery**: System listens to `devices/+/data` for new devices

### **3. Device Registration**
When a new ESP32 device is detected:
```json
{
  "device_id": "AABBCCDDEEFF",
  "name": "ESP32-DDEEFF",
  "device_type": "ESP32",
  "location": "Unknown",
  "capabilities": ["temperature", "humidity", "servo_control"],
  "is_active": true,
  "last_seen": "2025-07-21T14:30:15.123Z"
}
```

## 🎮 Web Interface Features

### **ESP32 Manager Dashboard**

#### **Statistics Cards**
- **Total Devices**: Count of all registered ESP32 devices
- **Connected**: Number of currently online devices  
- **Active**: Number of active devices in system
- **Offline**: Number of devices that are registered but not connected

#### **Device Table**
| Column | Description |
|--------|-------------|
| Status | Live connection indicator (Connected/Offline) |
| Device | Device name and MAC address |
| Type | Device type (ESP32) |
| Location | Configurable device location |
| Capabilities | Available features (temperature, humidity, servo_control) |
| Last Seen | Timestamp of last communication |
| Actions | Control buttons for device management |

#### **Available Actions**
- 🎛️ **Servo Control**: Set servo angle (0-180°) for devices with servo capability
- ℹ️ **Status Request**: Request immediate status update from device
- 🔄 **Reboot Device**: Remotely restart the ESP32
- ⚙️ **Edit Device**: Update device name, location, and type
- 🗑️ **Delete Device**: Remove device from system

### **Real-time Features**
- **Live Updates**: Device status updates automatically via WebSocket
- **Auto-refresh**: Device list refreshes every 30 seconds
- **Instant Notifications**: Toast messages for new device registrations
- **Connection Status**: Real-time connection indicators

## 📡 API Endpoints

### **Device Management**
```bash
# Get all ESP32 devices
GET /api/esp32/devices

# Get connected devices
GET /api/esp32/connected

# Get system statistics
GET /api/esp32/stats

# Update device information
PUT /api/esp32/device/{device_id}

# Delete device
DELETE /api/esp32/device/{device_id}
```

### **Device Control**
```bash
# Send custom command
POST /api/esp32/command/{device_id}
Body: {"action": "CUSTOM_COMMAND", "param": "value"}

# Control servo motor
POST /api/esp32/servo/{device_id}?angle=90

# Reboot device
POST /api/esp32/reboot/{device_id}

# Request status
POST /api/esp32/status/{device_id}

# Broadcast to all devices
POST /api/esp32/command/broadcast
Body: {"action": "STATUS_REQUEST"}
```

## 🔌 ESP32 Configuration

### **Required Network Settings**
Your ESP32 firmware is already configured for:
```cpp
// WiFi Configuration
const char* ssid = "RNR SOLUTIONS 4G";
const char* password = "Rnrs1100";

// MQTT Configuration  
const char* mqtt_server = "192.168.8.115";
const int mqtt_port = 1883;
const char* mqtt_user = "iotuser";
const char* mqtt_password = "iotpassword";
```

### **Automatic Features**
- ✅ **MAC Address ID**: Unique device ID generated from MAC address
- ✅ **Topic Generation**: Automatic MQTT topic creation
- ✅ **Capability Reporting**: Device reports available features
- ✅ **Health Monitoring**: Continuous status and metrics reporting

## 🚀 Getting Started

### **1. Hardware Setup**
1. Connect ESP32 to power
2. Connect servo to GPIO16 (if using servo control)
3. Ensure ESP32 is within WiFi range

### **2. Firmware Upload**
```bash
# Using PlatformIO
cd /home/robotics/test/IoT-Platform/firmware
pio run --target upload

# Using Arduino IDE
# Open IoT_Platform_Node.ino and upload
```

### **3. Verify Connection**
1. Open Serial Monitor (115200 baud)
2. Watch for connection messages:
```
=== IoT Platform ESP32 Node ===
Connecting to WiFi: RNR SOLUTIONS 4G
WiFi connected!
MQTT connected!
```

### **4. Check Web Interface**
1. Open http://localhost:3000
2. Navigate to "ESP32 Manager"
3. Device should appear automatically in the table

## 🔍 Troubleshooting

### **Device Not Appearing**
1. **Check Serial Monitor**: Verify WiFi and MQTT connections
2. **Network Connectivity**: Ensure ESP32 and server are on same network
3. **MQTT Broker**: Verify MQTT broker is running (`docker compose ps`)
4. **Firewall**: Check if port 1883 is accessible

### **Device Shows Offline**
1. **Power Cycle**: Restart the ESP32 device
2. **WiFi Signal**: Check WiFi signal strength
3. **MQTT Credentials**: Verify MQTT username/password
4. **Broker Status**: Check MQTT broker health

### **Commands Not Working**
1. **Device Connection**: Ensure device shows as "Connected"
2. **MQTT Topics**: Verify topic structure in logs
3. **Payload Format**: Check command JSON format
4. **Device Logs**: Monitor ESP32 serial output

## 🎯 Advanced Features

### **Custom Commands**
Send custom commands to devices:
```json
{
  "action": "CUSTOM_ACTION",
  "parameter1": "value1",
  "parameter2": 123
}
```

### **Bulk Operations**
Broadcast commands to all connected devices:
```bash
curl -X POST http://localhost:8000/api/esp32/command/broadcast \
  -H "Content-Type: application/json" \
  -d '{"action": "STATUS_REQUEST"}'
```

### **Device Configuration**
Update multiple device properties:
```json
{
  "name": "Living Room Sensor",
  "location": "Living Room",
  "device_type": "Environmental Monitor"
}
```

## 📊 Monitoring and Analytics

### **Real-time Metrics**
- Device connection status
- Last communication timestamps
- System resource usage (memory, WiFi signal)
- Command success/failure rates

### **Historical Data**
- Device registration timeline
- Connection uptime statistics
- Command execution history
- Error and disconnect logs

Your IoT Platform now provides complete automatic ESP32 device management with zero manual configuration required! 🎉

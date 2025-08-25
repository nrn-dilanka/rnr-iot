# RNR IoT Platform - RabbitMQ Integration Summary

## 🎯 Project Updates Completed

Your RNR IoT Platform has been successfully updated to support RabbitMQ for reliable MQTT data transmission from ESP32 devices. Here's what has been added and modified:

## 📁 New Files Created

### 1. RabbitMQ Startup Scripts

- **`start-rabbitmq.ps1`** - PowerShell script for Windows users
- **`start-rabbitmq.sh`** - Bash script for Linux/macOS users
- **`start-rabbitmq.bat`** - Windows batch file alternative

### 2. Documentation

- **`RABBITMQ_SETUP_GUIDE.md`** - Comprehensive RabbitMQ setup and troubleshooting guide
- **`test_rabbitmq_mqtt_connection.py`** - Python script to test MQTT connection to RabbitMQ

### 3. Updated Files

- **`README.md`** - Added RabbitMQ quick start section
- **`firmware/IoT_Platform_Node/IoT_Platform_Node.ino`** - Enhanced ESP32 firmware with RabbitMQ optimization

## 🚀 How to Use the Updated Project

### Step 1: Start RabbitMQ Only

Choose your preferred method:

**Windows PowerShell:**

```powershell
.\start-rabbitmq.ps1
```

**Windows Command Prompt:**

```batch
start-rabbitmq.bat
```

**Linux/macOS:**

```bash
chmod +x start-rabbitmq.sh
./start-rabbitmq.sh
```

**Manual Docker Compose:**

```bash
docker-compose up -d rnr_rabbitmq
```

### Step 2: Configure Your ESP32

Update the ESP32 firmware with your RabbitMQ server IP:

```cpp
// In IoT_Platform_Node.ino, line ~45
const char* mqtt_server = "YOUR_RABBITMQ_SERVER_IP"; // e.g., "192.168.1.100"
```

### Step 3: Upload Firmware to ESP32

1. Open the firmware file in Arduino IDE or PlatformIO
2. Update the MQTT server IP address to match your RabbitMQ server
3. Upload the firmware to your ESP32 device

### Step 4: Verify Data Transmission

1. **Access RabbitMQ Management Interface:**

   - URL: http://localhost:15672
   - Username: `rnr_iot_user`
   - Password: `rnr_iot_2025!`

2. **Test MQTT Connection:**

   ```bash
   pip install paho-mqtt
   python test_rabbitmq_mqtt_connection.py
   ```

3. **Monitor ESP32 Serial Output:**
   - Look for "Connected to RabbitMQ MQTT broker!" messages
   - Check for "Data sent to RabbitMQ" confirmations

## 📊 Data Flow Architecture

```
ESP32 Device → WiFi → MQTT (Port 1883) → RabbitMQ Container → Data Processing
     ↓                                           ↓
 Sensor Data                              Management UI
(Temperature,                           (http://localhost:15672)
 Humidity, Gas,
 Device Controls)
```

## 🔧 Key Features Added

### Enhanced ESP32 Firmware

- **RabbitMQ-optimized MQTT connection** with detailed error reporting
- **Improved retry logic** for reliable data transmission
- **Enhanced debugging output** for troubleshooting
- **Larger MQTT buffer size** (1024 bytes) for RabbitMQ compatibility

### Startup Scripts

- **Automatic Docker status checking**
- **RabbitMQ health verification**
- **Clear connection information display**
- **Cross-platform compatibility** (Windows, Linux, macOS)

### Test and Monitoring Tools

- **Python MQTT test script** that simulates ESP32 data
- **Comprehensive documentation** with troubleshooting guides
- **Container status monitoring**

## 📋 RabbitMQ Configuration

Your RabbitMQ container is configured with:

- **AMQP Port:** 5672
- **MQTT Port:** 1883 (for ESP32 connections)
- **Management UI:** 15672
- **Username:** rnr_iot_user
- **Password:** rnr_iot_2025!
- **Virtual Host:** rnr_iot_vhost

## 🔍 Topics Structure

Your ESP32 devices will use these MQTT topics:

- **Data Publishing:** `devices/{MAC_ADDRESS}/data`
- **Command Reception:** `devices/{MAC_ADDRESS}/commands`
- **Status Updates:** `devices/{MAC_ADDRESS}/status`

Example: For an ESP32 with MAC address `AA:BB:CC:DD:EE:FF`, the data topic would be:
`devices/AABBCCDDEEFF/data`

## 🛠️ Troubleshooting

### Common Issues

1. **ESP32 Cannot Connect:**

   - Verify RabbitMQ container is running: `docker ps`
   - Check IP address in ESP32 firmware
   - Ensure ESP32 and RabbitMQ are on same network

2. **Docker Not Running:**

   - Start Docker Desktop
   - Wait for Docker to fully initialize before running scripts

3. **Authentication Errors:**
   - Verify credentials in ESP32 firmware match RabbitMQ settings
   - Check RabbitMQ management interface for user permissions

### Debug Commands

```bash
# Check RabbitMQ container status
docker ps --filter "name=rnr_iot_rabbitmq"

# View RabbitMQ logs
docker logs rnr_iot_rabbitmq

# Test RabbitMQ health
docker exec rnr_iot_rabbitmq rabbitmq-diagnostics ping
```

## 🎯 Next Steps

1. **Start Docker Desktop** if not already running
2. **Run the appropriate startup script** for your operating system
3. **Update ESP32 firmware** with your RabbitMQ server IP
4. **Upload firmware** to ESP32 devices
5. **Monitor data transmission** via RabbitMQ management interface
6. **Test with the Python script** to verify everything works

## 📚 Additional Resources

- **Detailed Setup Guide:** [RABBITMQ_SETUP_GUIDE.md](RABBITMQ_SETUP_GUIDE.md)
- **Docker Compose File:** `docker-compose.yml` (RabbitMQ configuration)
- **RabbitMQ Config:** `rabbitmq/rabbitmq.conf`
- **ESP32 Firmware:** `firmware/IoT_Platform_Node/IoT_Platform_Node.ino`

Your RNR IoT Platform is now ready for reliable data transmission using RabbitMQ! 🚀

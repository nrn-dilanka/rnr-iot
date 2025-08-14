# IoT Platform Testing Guide

This guide walks you through testing the complete IoT platform functionality.

## 🧪 Testing Overview

The platform can be tested in multiple ways:
1. **Full Integration Test**: Using real ESP32 devices
2. **Simulation Test**: Using MQTT test clients
3. **API Testing**: Direct API endpoint testing
4. **Frontend Testing**: UI interaction testing

## 🚀 Quick Start Testing

### 1. Start the Platform

```bash
cd /home/robotics/test/IoT-Platform
./setup.sh
```

Wait for all services to start (about 2-3 minutes).

### 2. Verify Services

Check that all services are running:
```bash
docker-compose ps
```

All services should show "Up" status.

### 3. Access the Web Dashboard

Open your browser and navigate to: http://localhost:3000

You should see the IoT Platform dashboard with:
- Navigation sidebar (Dashboard, Device Management, Firmware Management)
- Header showing connection status
- Empty dashboard (no devices registered yet)

## 📱 Testing with Simulated Device

Since you might not have an ESP32 device immediately available, you can simulate device data using MQTT commands.

### Install MQTT Client

```bash
# Install mosquitto client tools
sudo apt-get update
sudo apt-get install mosquitto-clients
```

### Simulate Device Registration and Data

1. **Register a simulated device** via the web interface:
   - Go to http://localhost:3000/devices
   - Click "Add Node"
   - Enter Node ID: `TEST001122334455`
   - Enter Name: `Test Sensor`
   - Enter MAC Address: `00:11:22:33:44:55`
   - Click OK

2. **Publish simulated sensor data**:

```bash
# Publish temperature and sensor data
mosquitto_pub -h localhost -p 1883 -u iotuser -P iotpassword \
  -t "devices/TEST001122334455/data" \
  -m '{"timestamp": '$(date +%s)', "temperature": 23.5, "humidity": 65, "status": "online", "uptime": 12345}'

# Wait a few seconds and publish another data point
sleep 5
mosquitto_pub -h localhost -p 1883 -u iotuser -P iotpassword \
  -t "devices/TEST001122334455/data" \
  -m '{"timestamp": '$(date +%s)', "temperature": 24.1, "humidity": 63, "status": "online", "uptime": 12350}'
```

3. **Check the dashboard**:
   - Go back to http://localhost:3000
   - You should see the device appear as "Online"
   - Charts should show the temperature and humidity data
   - Metrics should update to show 1 online device

### Test Device Commands

1. **Send commands to the device**:
   - Go to Device Management page
   - Click "Control" button for your test device
   - Click "Request Status Update"
   - You should see a success message

2. **Monitor commands** (simulate ESP32 receiving commands):

```bash
# Subscribe to commands for the test device
mosquitto_sub -h localhost -p 1883 -u iotuser -P iotpassword \
  -t "devices/TEST001122334455/commands"
```

When you send commands from the web interface, you should see them appear in this terminal.

## 🔧 ESP32 Hardware Testing

If you have an ESP32 device:

### 1. Set up PlatformIO

```bash
# Install PlatformIO Core
pip install platformio

# Navigate to firmware directory
cd /home/robotics/test/IoT-Platform/firmware
```

### 2. Configure the Firmware

Edit `src/main.cpp` and update:
```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqtt_server = "YOUR_COMPUTER_IP";  // IP address of your Docker host
```

### 3. Flash the Firmware

```bash
# Connect ESP32 via USB and flash
pio run --target upload

# Monitor serial output
pio device monitor
```

### 4. Observe Device Behavior

The ESP32 should:
1. Connect to WiFi
2. Connect to MQTT broker
3. Start sending sensor data every 30 seconds
4. Appear as "Online" in the web dashboard
5. Respond to commands sent from the web interface

## 🧩 API Testing

Test the REST API endpoints directly:

### 1. Test Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected response: `{"status":"healthy"}`

### 2. Test Node Management

```bash
# List all nodes
curl http://localhost:8000/api/nodes

# Create a new node
curl -X POST http://localhost:8000/api/nodes \
  -H "Content-Type: application/json" \
  -d '{"node_id": "API_TEST_001", "name": "API Test Device"}'

# Get specific node
curl http://localhost:8000/api/nodes/API_TEST_001

# Send command to node
curl -X POST http://localhost:8000/api/nodes/API_TEST_001/actions \
  -H "Content-Type: application/json" \
  -d '{"action": "STATUS_REQUEST"}'
```

### 3. Test Firmware Management

```bash
# List firmware versions
curl http://localhost:8000/api/firmware

# Upload firmware (create a dummy file first)
echo "dummy firmware content" > test_firmware.bin
curl -X POST http://localhost:8000/api/firmware/upload \
  -F "version=1.0.1" \
  -F "file=@test_firmware.bin"
```

## 📊 Database Testing

Access the PostgreSQL database to verify data storage:

```bash
# Connect to database
docker-compose exec postgres psql -U iotuser -d iot_platform

# Check tables and data
\dt
SELECT * FROM nodes;
SELECT * FROM sensor_data ORDER BY received_at DESC LIMIT 10;
SELECT * FROM firmware;
```

## 🔌 RabbitMQ Testing

Access RabbitMQ Management Interface:

1. Open http://localhost:15672
2. Login with `iotuser` / `iotpassword`
3. Check:
   - **Queues**: Should see `device_data` queue
   - **Exchanges**: Should see `amq.topic`
   - **Connections**: Should see connections from worker service and any ESP32 devices

## 🌐 WebSocket Testing

Test real-time communication:

1. Open browser developer tools (F12)
2. Go to Network tab
3. Navigate to http://localhost:3000
4. Look for WebSocket connection (WS)
5. Send some MQTT data using mosquitto_pub
6. Observe real-time updates in the web interface

## 📋 Test Scenarios

### Scenario 1: Complete Device Lifecycle

1. Register device via web interface
2. Device comes online (simulated with MQTT)
3. Device sends sensor data
4. Monitor data in dashboard
5. Send commands to device
6. Device goes offline (stop sending data)
7. Verify offline status in dashboard

### Scenario 2: Firmware Update Flow

1. Upload firmware via web interface
2. Select online device for update
3. Trigger OTA update
4. Monitor command sent via MQTT
5. Simulate successful update response

### Scenario 3: Multiple Device Management

1. Register multiple devices
2. Generate data from all devices
3. Verify dashboard shows aggregated metrics
4. Test batch operations

## 🐛 Troubleshooting Tests

### Common Issues and Solutions

1. **Services not starting**:
   ```bash
   docker-compose logs -f
   ```

2. **MQTT connection fails**:
   - Check if port 1883 is accessible
   - Verify credentials (iotuser/iotpassword)
   - Check RabbitMQ logs

3. **WebSocket not connecting**:
   - Verify API server is running on port 8000
   - Check browser console for errors
   - Ensure CORS is properly configured

4. **Database connection issues**:
   - Check if PostgreSQL is running
   - Verify database initialization completed
   - Check database logs

### Log Analysis

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api_server
docker-compose logs -f worker_service
docker-compose logs -f postgres
docker-compose logs -f rabbitmq
```

## ✅ Success Criteria

Your platform is working correctly if:

- [ ] All Docker services start without errors
- [ ] Web dashboard loads and shows connection status
- [ ] You can register devices via the web interface
- [ ] MQTT messages are received and processed
- [ ] Sensor data appears in real-time charts
- [ ] Device status updates correctly (online/offline)
- [ ] Commands can be sent to devices
- [ ] Firmware can be uploaded
- [ ] Database stores all data correctly
- [ ] WebSocket connection is stable

## 📈 Performance Testing

For load testing:

1. **Multiple Device Simulation**:
   ```bash
   # Script to simulate multiple devices
   for i in {1..10}; do
     mosquitto_pub -h localhost -p 1883 -u iotuser -P iotpassword \
       -t "devices/TEST$(printf %012d $i)/data" \
       -m "{\"timestamp\": $(date +%s), \"temperature\": $((20 + RANDOM % 20)), \"humidity\": $((40 + RANDOM % 40))}" &
   done
   ```

2. **API Load Testing** (install Apache Bench):
   ```bash
   ab -n 1000 -c 10 http://localhost:8000/api/nodes
   ```

3. **Database Performance**:
   ```sql
   -- Check query performance
   EXPLAIN ANALYZE SELECT * FROM sensor_data WHERE node_id = 'TEST001122334455' ORDER BY received_at DESC LIMIT 100;
   ```

## 🎯 Next Steps

After successful testing:

1. **Deploy to production** with proper security configurations
2. **Scale services** using Docker Swarm or Kubernetes
3. **Add monitoring** with Prometheus and Grafana
4. **Implement alerting** for device failures
5. **Add authentication** and user management
6. **Optimize database** for large-scale deployments

Happy testing! 🚀

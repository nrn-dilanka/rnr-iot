# RNR IoT Platform - RabbitMQ MQTT Integration

This document explains how to set up and use RabbitMQ as the MQTT broker for the RNR IoT Platform to enable reliable data transmission from ESP32 devices.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- ESP32 development environment
- Network connectivity between ESP32 and RabbitMQ server

### 1. Start RabbitMQ Only

**Windows (PowerShell):**

```powershell
.\start-rabbitmq.ps1
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

### 2. Verify RabbitMQ is Running

Check container status:

```bash
docker ps --filter "name=rnr_iot_rabbitmq"
```

Test RabbitMQ health:

```bash
docker exec rnr_iot_rabbitmq rabbitmq-diagnostics ping
```

### 3. Access RabbitMQ Management Interface

Open your browser and navigate to:

- **URL:** http://localhost:15672
- **Username:** rnr_iot_user
- **Password:** rnr_iot_2025!

## 📡 ESP32 Configuration

### MQTT Connection Settings

Update your ESP32 firmware with these settings:

```cpp
// MQTT Configuration - RabbitMQ MQTT Broker
const char* mqtt_server = "YOUR_RABBITMQ_SERVER_IP"; // e.g., "192.168.1.100"
const int mqtt_port = 1883;
const char* mqtt_user = "rnr_iot_user";
const char* mqtt_password = "rnr_iot_2025!";
```

### Data Topics Structure

Your ESP32 devices will publish data to:

- **Data Topic:** `devices/{MAC_ADDRESS}/data`
- **Command Topic:** `devices/{MAC_ADDRESS}/commands`
- **Status Topic:** `devices/{MAC_ADDRESS}/status`

### Sample Data Format

```json
{
  "timestamp": "14:30:25",
  "temperature": 24.5,
  "humidity": 65.3,
  "humidity_mq": 58.2,
  "humidity_mq_raw": 2456,
  "gas_sensor": 1234,
  "status": "online",
  "node_id": "AABBCCDDEEFF",
  "servo_angle": 90,
  "light_state": false,
  "fan_state": true,
  "wifi_rssi": -45,
  "uptime": 123456
}
```

## 🔧 Configuration Details

### RabbitMQ Container Configuration

```yaml
services:
  rnr_rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: rnr_iot_rabbitmq
    ports:
      - "5672:5672" # AMQP port
      - "15672:15672" # Management UI
      - "1883:1883" # MQTT port
    environment:
      RABBITMQ_DEFAULT_USER: rnr_iot_user
      RABBITMQ_DEFAULT_PASS: rnr_iot_2025!
      RABBITMQ_DEFAULT_VHOST: rnr_iot_vhost
```

### MQTT Plugin Configuration

The following plugins are enabled:

- `rabbitmq_management` - Web management interface
- `rabbitmq_mqtt` - MQTT protocol support

### Memory Optimization

RabbitMQ is configured for low-memory environments:

- Memory high watermark: 40% of available RAM
- Connection limit: 100 concurrent connections
- Channel limit: 256 channels per connection

## 📊 Monitoring and Troubleshooting

### Check RabbitMQ Logs

```bash
docker logs rnr_iot_rabbitmq
```

### Monitor MQTT Connections

In the RabbitMQ Management interface:

1. Go to **Connections** tab
2. Look for ESP32 client connections
3. Monitor message rates and queues

### Test MQTT Publishing

You can test MQTT publishing using mosquitto tools:

```bash
# Publish test message
mosquitto_pub -h localhost -p 1883 -u rnr_iot_user -P rnr_iot_2025! -t "test/topic" -m "Hello RabbitMQ"

# Subscribe to all device messages
mosquitto_sub -h localhost -p 1883 -u rnr_iot_user -P rnr_iot_2025! -t "devices/+/data"
```

### Common Issues and Solutions

#### 1. ESP32 Cannot Connect to RabbitMQ

**Symptoms:**

- MQTT connection failed errors in ESP32 serial output
- Connection timeout messages

**Solutions:**

- Verify RabbitMQ server IP address in ESP32 code
- Check network connectivity between ESP32 and RabbitMQ server
- Ensure RabbitMQ container is running: `docker ps`
- Check firewall settings on RabbitMQ server

#### 2. Authentication Failures

**Symptoms:**

- "Bad credentials" errors
- "Not authorized" messages

**Solutions:**

- Verify username and password in ESP32 code
- Check RabbitMQ user permissions in management interface
- Ensure virtual host is correctly configured

#### 3. Messages Not Appearing in RabbitMQ

**Symptoms:**

- ESP32 reports successful publishing but no data in RabbitMQ
- Empty queues in management interface

**Solutions:**

- Check topic naming consistency
- Verify MQTT exchange configuration
- Enable message tracing in RabbitMQ management interface

#### 4. High Memory Usage

**Symptoms:**

- RabbitMQ container consuming too much memory
- Container restarts due to memory limits

**Solutions:**

- Reduce message retention time
- Implement message acknowledgments
- Monitor queue lengths and purge old messages

## 🔄 Data Flow Architecture

```
ESP32 Device --> MQTT (Port 1883) --> RabbitMQ --> Backend API --> Database
     ↓                                    ↓              ↓
Temperature/                        Message Queue    WebSocket
Humidity/Gas                       (Topic Exchange)  (Real-time)
Sensor Data                             ↓
                                  Management UI
                                 (Port 15672)
```

## 📈 Production Considerations

### Security

For production deployment:

1. Change default credentials
2. Enable TLS/SSL for MQTT connections
3. Configure proper firewall rules
4. Use certificates for client authentication

### Scalability

- Monitor connection counts and message rates
- Consider clustering RabbitMQ for high availability
- Implement load balancing for multiple ESP32 devices
- Set up monitoring and alerting

### Backup and Recovery

- Regular backups of RabbitMQ data volume
- Document configuration changes
- Test disaster recovery procedures

## 📞 Support

For issues related to RabbitMQ MQTT integration:

1. Check the logs: `docker logs rnr_iot_rabbitmq`
2. Verify network connectivity
3. Review ESP32 serial output for error messages
4. Use RabbitMQ management interface for debugging

## 🔗 Related Files

- `docker-compose.yml` - Main container configuration
- `rabbitmq/rabbitmq.conf` - RabbitMQ server configuration
- `rabbitmq/enabled_plugins` - Enabled plugins list
- `firmware/IoT_Platform_Node/IoT_Platform_Node.ino` - ESP32 firmware
- `start-rabbitmq.ps1` - Windows startup script
- `start-rabbitmq.sh` - Linux startup script

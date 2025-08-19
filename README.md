# RNR Solutions IoT Platform - Enterprise Monitoring & Management System

**Developed by RNR Solutions**

A comprehensive enterprise-grade IoT platform for registering, monitoring, controlling, and managing remote hardware devices with real-time dashboards, remote action control, and Over-the-Air (OTA) firmware updates.

## 🏢 About RNR Solutions

RNR Solutions is a leading technology company specializing in innovative IoT solutions and enterprise software development. Our cutting-edge IoT platform empowers businesses to seamlessly connect, monitor, and manage their device ecosystems with unprecedented efficiency and reliability.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ESP32 Nodes   │    │   RabbitMQ      │    │   PostgreSQL    │
│   (MQTT Client) │◄──►│   (MQTT Broker) │◄──►│   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                          │
                              ▼                          ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Web     │◄──►│   FastAPI       │◄──►│   Worker        │
│   Frontend      │    │   Backend       │    │   Service       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Features

### Device Management
- **Automatic Registration**: Devices auto-register using MAC address as unique identifier
- **Real-time Monitoring**: Live sensor data collection and visualization
- **Remote Control**: Send commands (reboot, status request) to devices
- **Status Tracking**: Online/offline status with last-seen timestamps

### Firmware Management
- **OTA Updates**: Over-the-Air firmware deployment to devices
- **Version Control**: Manage multiple firmware versions
- **Batch Deployment**: Update multiple devices simultaneously
- **Progress Tracking**: Monitor update status and handle failures

### Real-time Dashboard
- **Live Charts**: Temperature, humidity, and other sensor data visualization
- **Device Overview**: Current status of all registered devices
- **WebSocket Integration**: Real-time data streaming
- **Responsive Design**: Works on desktop and mobile devices

## 🛠️ Technology Stack

### Embedded System
- **Platform**: ESP32 Microcontroller
- **Framework**: Arduino with PlatformIO
- **Communication**: MQTT over WiFi
- **OTA**: ESP32 HTTP Update library

### Backend Services
- **API Server**: Python FastAPI
- **Worker Service**: Python with Pika (RabbitMQ client)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Message Broker**: RabbitMQ with MQTT plugin

### Frontend
- **Framework**: React 18
- **UI Library**: Ant Design
- **Charts**: Recharts
- **Real-time**: WebSocket connection

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Networking**: Internal Docker network
- **Storage**: Persistent volumes for database and file uploads

## 📋 Prerequisites

- Docker and Docker Compose
- PlatformIO (for ESP32 development)
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd RNR-IoT-Platform
```

### 2. Start the RNR IoT Platform Services

```bash
# Start all RNR IoT Platform services using Docker Compose
docker-compose up -d

# Check service status
docker-compose ps
```

### 3. Access the RNR IoT Platform

- **RNR Web Dashboard**: http://localhost:3000
- **RNR API Documentation**: http://localhost:8000/docs
- **RabbitMQ Management**: http://localhost:15672 (iotuser/iotpassword)
- **Database**: localhost:15432 (iotuser/iotpassword)

### 4. Configure ESP32 Firmware

1. Open `firmware/src/main.cpp`
2. Update WiFi credentials:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   const char* mqtt_server = "YOUR_MQTT_BROKER_IP";
   ```
3. Flash to ESP32 using PlatformIO

## 📡 ESP32 Node Setup

### Hardware Requirements
- ESP32 development board
- Sensors (optional - code includes simulated data)
- WiFi network access

### Firmware Features
- **Auto-identification**: Uses MAC address as unique node ID
- **MQTT Communication**: Publishes sensor data and subscribes to commands
- **Sensor Simulation**: Generates realistic temperature and humidity data
- **OTA Support**: Can receive and install firmware updates remotely
- **Command Processing**: Handles reboot, status, and update commands

### MQTT Topics
- **Data Publishing**: `devices/{node_id}/data`
- **Command Subscription**: `devices/{node_id}/commands`

### Example Sensor Data
```json
{
  "timestamp": 1677610000,
  "temperature": 25.4,
  "humidity": 65,
  "status": "online",
  "uptime": 12345,
  "free_heap": 123456,
  "wifi_rssi": -45
}
```

## 🔧 API Endpoints

### Node Management
- `POST /api/nodes` - Register new node
- `GET /api/nodes` - List all nodes
- `GET /api/nodes/{node_id}` - Get node details
- `PUT /api/nodes/{node_id}` - Update node
- `DELETE /api/nodes/{node_id}` - Delete node
- `POST /api/nodes/{node_id}/actions` - Send command to node

### Firmware Management
- `POST /api/firmware/upload` - Upload firmware file
- `GET /api/firmware` - List firmware versions
- `POST /api/firmware/deploy` - Deploy firmware to nodes

### Supported Commands
```json
{"action": "REBOOT"}
{"action": "STATUS_REQUEST"}
{"action": "FIRMWARE_UPDATE", "url": "http://..."}
```

## 🗄️ Database Schema

### Tables
- **nodes**: Device registration and metadata
- **firmware**: Firmware version management
- **node_firmware**: Device-firmware assignments
- **sensor_data**: Time-series sensor data storage

### Relationships
- One-to-many: Node → Sensor Data
- Many-to-many: Node ↔ Firmware (through node_firmware)

## 🔄 Real-time Communication

### WebSocket Events
- `sensor_data`: New sensor readings from devices
- `node_status`: Device online/offline status changes

### Message Flow
1. ESP32 publishes data to MQTT topic
2. Worker service receives and processes message
3. Data stored in PostgreSQL database
4. WebSocket broadcasts update to connected clients
5. Frontend updates charts and device status in real-time

## 🐳 Docker Services

### RabbitMQ
- **Ports**: 5672 (AMQP), 1883 (MQTT), 15672 (Management)
- **Plugins**: rabbitmq_management, rabbitmq_mqtt
- **Credentials**: iotuser/iotpassword

### PostgreSQL
- **Port**: 5432
- **Database**: iot_platform
- **Credentials**: iotuser/iotpassword
- **Initialization**: Runs `database/init.sql` on first start

### API Server
- **Port**: 8000
- **Framework**: FastAPI with Uvicorn
- **Features**: REST API, WebSocket server, file uploads

### Worker Service
- **No external ports**: Internal service only
- **Function**: MQTT message processing and database updates

### Frontend
- **Port**: 3000
- **Framework**: React with Ant Design
- **Build**: Production-optimized build served by nginx

## 🛡️ Security Considerations

### Production Deployment
- Change default passwords for RabbitMQ and PostgreSQL
- Use environment variables for sensitive configuration
- Enable SSL/TLS for MQTT and HTTP communications
- Implement authentication and authorization
- Use secure WiFi connections for ESP32 devices
- Validate and sanitize all user inputs

### Network Security
- Place ESP32 devices on isolated VLAN if possible
- Use firewall rules to restrict unnecessary network access
- Monitor device connections and detect anomalies

## 🔧 Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

### ESP32 Development
```bash
cd firmware
pio run --target upload --target monitor
```

## 📊 Monitoring and Debugging

### Logs
```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api_server
docker-compose logs -f worker_service
```

### Database Access
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U iotuser -d iot_platform
```

### RabbitMQ Management
- Access http://localhost:15672
- Monitor queues, exchanges, and message flow
- Debug MQTT connections and message routing

## 🚨 Troubleshooting

### Common Issues

1. **ESP32 won't connect to WiFi**
   - Check SSID and password in firmware
   - Ensure WiFi network is accessible
   - Check serial monitor for connection logs

2. **No sensor data appearing**
   - Verify MQTT broker IP address in firmware
   - Check RabbitMQ logs for connection issues
   - Ensure worker service is running

3. **WebSocket connection fails**
   - Check if API server is running on port 8000
   - Verify frontend is configured with correct WebSocket URL
   - Check browser console for connection errors

4. **Docker services won't start**
   - Check if ports 3000, 5432, 5672, 8000, 15672 are available
   - Ensure Docker daemon is running
   - Check Docker logs for specific error messages

## 📈 Performance Optimization

### Database
- Indexes on frequently queried columns (node_id, timestamp)
- Periodic cleanup of old sensor data
- Connection pooling for high load scenarios

### Message Processing
- Adjust RabbitMQ prefetch settings for worker service
- Implement message batching for high-frequency data
- Use Redis for WebSocket connection management in multi-instance deployments

### Frontend
- Implement data pagination for large datasets
- Use React.memo for expensive components
- Implement virtual scrolling for large tables

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section
- Review Docker Compose logs for error details

---

**RNR Solutions IoT Platform** - Powering the Future of Connected Devices

© 2025 RNR Solutions. All rights reserved.

For enterprise inquiries and support, contact: support@rnrsolutions.com

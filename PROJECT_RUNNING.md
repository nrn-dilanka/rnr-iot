# 🚀 RNR Solutions IoT Platform - Running Status

**Enterprise IoT Platform Deployment Guide**  
**© 2025 RNR Solutions. All rights reserved.**

## 📊 Platform Status

The RNR Solutions IoT Platform is successfully deployed and operational with the following enterprise-grade services:

### 🏢 Core Services Status

| Service | Status | Port | Description |
|---------|--------|------|-------------|
| **RNR Frontend Dashboard** | ✅ Running | 3000 | Enterprise web interface |
| **RNR API Server** | ✅ Running | 8000 | RESTful API and WebSocket server |
| **RNR PostgreSQL Database** | ✅ Running | 15432 | Enterprise database |
| **RNR RabbitMQ Broker** | ✅ Running | 1883/15672 | MQTT message broker |
| **RNR Worker Service** | ✅ Running | Internal | Background processing |

## 🔗 Access Points

### Primary Access URLs
- **Enterprise Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Management Interface**: http://localhost:15672

### Credentials
- **Database**: `rnr_iot_user` / `rnr_iot_2025!`
- **MQTT Broker**: `rnr_iot_user` / `rnr_iot_2025!`
- **RabbitMQ Management**: `rnr_iot_user` / `rnr_iot_2025!`

## 🎯 Platform Features

✅ **Real-time Device Monitoring**  
✅ **ESP32 Device Management**  
✅ **OTA Firmware Updates**  
✅ **Enterprise Dashboard**  
✅ **RESTful API**  
✅ **MQTT Communication**  
✅ **WebSocket Real-time Updates**  
✅ **Data Analytics**  

## 📱 ESP32 Configuration

Update your ESP32 firmware with:
```cpp
const char* mqtt_server = "YOUR_SERVER_IP";
const char* mqtt_user = "rnr_iot_user";
const char* mqtt_password = "rnr_iot_2025!";
```

## 🛠️ Management Commands

```bash
# View all service logs
docker-compose logs -f

# Check service status
docker-compose ps

# Restart all services
docker-compose restart

# Stop platform
docker-compose down

# Start platform
docker-compose up -d
```

---

**RNR Solutions IoT Platform** - Enterprise IoT Excellence  
For technical support: support@rnrsolutions.com
# 🔧 RNR Solutions IoT Platform Configuration Guide

**Enterprise Configuration and Setup Manual**  
**© 2025 RNR Solutions. All rights reserved.**

This comprehensive guide provides detailed instructions for configuring and customizing the RNR Solutions IoT Platform's advanced features for enterprise deployment.

## 📋 Table of Contents

1. [Environment Configuration](#environment-configuration)
2. [Database Setup](#database-setup)
3. [ESP32 Device Configuration](#esp32-device-configuration)
4. [Sensor Calibration](#sensor-calibration)
5. [Automation Rules Setup](#automation-rules-setup)
6. [User Roles and Permissions](#user-roles-and-permissions)
7. [AI Integration Setup](#ai-integration-setup)
8. [Weather Service Integration](#weather-service-integration)
9. [Mobile Responsiveness](#mobile-responsiveness)
10. [Troubleshooting](#troubleshooting)

## 🌍 Environment Configuration

### RNR IoT Platform Backend Environment Variables

Create or update your `backend/.env` file with the following RNR Solutions configuration:

```bash
# RNR Solutions Database Configuration
DATABASE_URL=postgresql://rnr_iot_user:rnr_iot_2025!@localhost:15432/rnr_iot_platform
DB_HOST=localhost
DB_PORT=15432
DB_NAME=rnr_iot_platform
DB_USER=rnr_iot_user
DB_PASSWORD=your_password

# MQTT Configuration
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=mqtt_user
MQTT_PASSWORD=mqtt_password

# AI Integration
GEMINI_API_KEY=your_gemini_api_key_here
AI_ENABLED=true
AI_MODEL=gemini-pro

# Weather Services
OPENWEATHER_API_KEY=your_openweather_api_key
WEATHER_UPDATE_INTERVAL=3600  # seconds

# Greenhouse Features
GREENHOUSE_FEATURES_ENABLED=true
MAX_ZONES_PER_USER=10
SENSOR_DATA_RETENTION_DAYS=365
ALERT_EMAIL_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Security
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Upload
MAX_UPLOAD_SIZE=10485760  # 10MB
UPLOAD_DIRECTORY=uploads/
ALLOWED_IMAGE_EXTENSIONS=jpg,jpeg,png,gif

# Performance
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=300  # seconds
```

### Frontend Environment Variables

Create or update your `frontend/.env` file:

```bash
# API Configuration
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws

# Feature Flags
REACT_APP_GREENHOUSE_FEATURES=true
REACT_APP_AI_FEATURES=true
REACT_APP_WEATHER_INTEGRATION=true
REACT_APP_MOBILE_RESPONSIVE=true

# UI Configuration
REACT_APP_THEME=light
REACT_APP_LANGUAGE=en
REACT_APP_TIMEZONE=UTC

# Map Integration (if using location features)
REACT_APP_GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Analytics (optional)
REACT_APP_GOOGLE_ANALYTICS_ID=your_ga_id
```

## 🗄️ Database Setup

### Initial Setup

1. **Create Database** (if not exists):
```sql
CREATE DATABASE iot_platform;
CREATE USER iotuser WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE iot_platform TO iotuser;
```

2. **Install TimescaleDB Extension** (recommended for time-series data):
```sql
-- Connect to your database
\c iot_platform

-- Create TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Convert sensor data table to hypertable (after running enhanced_schema.sql)
SELECT create_hypertable('enhanced_sensor_data', 'timestamp');
```

3. **Apply Enhanced Schema**:
```bash
# Using psql
psql -U iotuser -d iot_platform -f database/enhanced_schema.sql

# Or using the deployment script
./deploy_greenhouse_features.sh  # Linux/Mac
deploy_greenhouse_features.bat   # Windows
```

### Database Optimization

Add these indexes for better performance:

```sql
-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_sensor_data_zone_timestamp 
ON enhanced_sensor_data (zone_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_crop_growth_zone_date 
ON crop_growth_tracking (zone_id, measurement_date DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_zone_status 
ON system_alerts (zone_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_automation_rules_zone_active 
ON automation_rules (zone_id, is_active);

-- Partial indexes for active records
CREATE INDEX IF NOT EXISTS idx_active_zones 
ON greenhouse_zones (id) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_unresolved_alerts 
ON system_alerts (zone_id, created_at) WHERE status = 'active';
```

## 🔌 ESP32 Device Configuration

### Hardware Requirements

**Minimum Setup:**
- ESP32 Development Board
- DHT22 (Temperature & Humidity)
- Soil Moisture Sensor
- Relay Module (4-channel recommended)

**Advanced Setup:**
- BH1750 Light Sensor
- pH Sensor (analog)
- EC/TDS Sensor (analog)
- CO2 Sensor (MH-Z19 or similar)
- DS18B20 Soil Temperature Sensor
- Water pump and solenoid valves
- Ventilation fan
- Grow lights
- Heating element

### Pin Configuration

Update the pin definitions in `esp32/greenhouse_sensors.ino`:

```cpp
// Pin Definitions - Customize based on your hardware
#define DHT_PIN 4              // DHT22 data pin
#define SOIL_MOISTURE_PIN A0   // Analog soil moisture sensor
#define SOIL_TEMP_PIN 2        // DS18B20 soil temperature
#define PH_SENSOR_PIN A1       // Analog pH sensor
#define EC_SENSOR_PIN A2       // Analog EC/TDS sensor
#define CO2_SENSOR_RX 16       // CO2 sensor RX pin
#define CO2_SENSOR_TX 17       // CO2 sensor TX pin

// Relay Control Pins
#define RELAY_WATER 5          // Water pump relay
#define RELAY_FAN 18           // Ventilation fan relay
#define RELAY_HEATER 19        // Heater relay
#define RELAY_LIGHTS 21        // Grow lights relay

#define STATUS_LED 2           // Status LED pin
```

### WiFi and MQTT Configuration

Update the network configuration in the firmware:

```cpp
// WiFi Configuration
const char* ssid = "Your_WiFi_Network";
const char* password = "Your_WiFi_Password";

// MQTT Configuration
const char* mqtt_server = "192.168.1.100";  // Your MQTT broker IP
const int mqtt_port = 1883;
const char* mqtt_user = "mqtt_user";
const char* mqtt_password = "mqtt_password";

// Device Configuration
const char* device_id = "greenhouse_node_01";  // Unique device ID
const char* zone_id = "zone_1";                // Zone assignment
```

### Firmware Upload Process

1. **Install Arduino IDE** and required libraries:
   - ESP32 Board Package
   - PubSubClient (MQTT)
   - ArduinoJson
   - DHT sensor library
   - OneWire and DallasTemperature
   - BH1750 library

2. **Configure Arduino IDE**:
   - Board: "ESP32 Dev Module"
   - Upload Speed: "921600"
   - CPU Frequency: "240MHz (WiFi/BT)"
   - Flash Frequency: "80MHz"
   - Flash Mode: "QIO"
   - Flash Size: "4MB (32Mb)"

3. **Upload Firmware**:
   - Open `esp32/greenhouse_sensors.ino`
   - Update configuration variables
   - Verify and upload to ESP32

## 🎯 Sensor Calibration

### Soil Moisture Sensor

```cpp
// Calibration values (update based on your sensor)
int soil_moisture_dry = 4095;    // Reading in dry soil
int soil_moisture_wet = 1500;    // Reading in wet soil

// In the readAllSensors() function:
int soilMoistureRaw = analogRead(SOIL_MOISTURE_PIN);
currentData.soil_moisture = map(soilMoistureRaw, soil_moisture_dry, soil_moisture_wet, 0, 100);
currentData.soil_moisture = constrain(currentData.soil_moisture, 0, 100);
```

### pH Sensor Calibration

```cpp
// pH sensor calibration (update based on calibration solutions)
float ph_4_voltage = 3.0;   // Voltage reading at pH 4.0
float ph_7_voltage = 2.5;   // Voltage reading at pH 7.0
float ph_10_voltage = 2.0;  // Voltage reading at pH 10.0

// Calibration function
float calibratePH(int raw_reading) {
    float voltage = (raw_reading / 4095.0) * 3.3;
    
    // Linear interpolation based on calibration points
    if (voltage > ph_4_voltage) {
        return 4.0 - ((voltage - ph_4_voltage) / (ph_7_voltage - ph_4_voltage)) * 3.0;
    } else {
        return 7.0 + ((ph_7_voltage - voltage) / (ph_7_voltage - ph_10_voltage)) * 3.0;
    }
}
```

### Light Sensor Configuration

```cpp
// BH1750 sensor modes
// BH1750::CONTINUOUS_HIGH_RES_MODE   - 1 lx resolution
// BH1750::CONTINUOUS_HIGH_RES_MODE_2 - 0.5 lx resolution
// BH1750::CONTINUOUS_LOW_RES_MODE    - 4 lx resolution

void initializeLightSensor() {
    if (lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
        Serial.println("BH1750 initialized successfully");
    } else {
        Serial.println("Error initializing BH1750");
    }
}
```

## ⚙️ Automation Rules Setup

### Creating Automation Rules via API

```javascript
// Example: Create temperature control rule
const temperatureRule = {
    name: "Temperature Control",
    zone_id: "zone_1",
    conditions: [
        {
            sensor_type: "air_temperature",
            operator: "less_than",
            value: 20.0,
            logic_operator: "AND"
        }
    ],
    actions: [
        {
            device_type: "heater",
            action: "turn_on",
            duration: 300  // 5 minutes
        }
    ],
    priority: 1,
    is_active: true
};

// Create rule via API
fetch('/api/greenhouse/automation-rules', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(temperatureRule)
});
```

### Complex Automation Example

```javascript
// Multi-condition irrigation rule
const irrigationRule = {
    name: "Smart Irrigation",
    zone_id: "zone_1",
    conditions: [
        {
            sensor_type: "soil_moisture",
            operator: "less_than",
            value: 30.0,
            logic_operator: "AND"
        },
        {
            sensor_type: "air_temperature",
            operator: "greater_than",
            value: 25.0,
            logic_operator: "AND"
        },
        {
            sensor_type: "light_intensity",
            operator: "greater_than",
            value: 1000.0,
            logic_operator: "OR"
        }
    ],
    actions: [
        {
            device_type: "water_pump",
            action: "turn_on",
            duration: 30
        },
        {
            device_type: "notification",
            action: "send_alert",
            message: "Irrigation activated for Zone 1"
        }
    ],
    schedule: {
        enabled: true,
        start_time: "06:00",
        end_time: "20:00",
        days: ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    },
    priority: 2,
    is_active: true
};
```

## 👥 User Roles and Permissions

### Role Configuration

Update the role permissions in your backend configuration:

```python
# backend/api/auth.py

ROLE_PERMISSIONS = {
    "student": [
        "greenhouse:read",
        "greenhouse:zones:read",
        "greenhouse:sensors:read",
        "greenhouse:crop_management:read",
        "greenhouse:crop_management:write",
        "greenhouse:growth_tracking:write",
        "greenhouse:data_export:read"
    ],
    "admin": [
        "greenhouse:*",  # All greenhouse permissions
        "automation:*",  # All automation permissions
        "users:read",
        "system:read"
    ],
    "superuser": [
        "*"  # All permissions
    ]
}

def check_permission(user_role: str, permission: str) -> bool:
    """Check if user role has specific permission"""
    if user_role not in ROLE_PERMISSIONS:
        return False
    
    permissions = ROLE_PERMISSIONS[user_role]
    
    # Check for wildcard permissions
    if "*" in permissions:
        return True
    
    # Check for specific permission
    if permission in permissions:
        return True
    
    # Check for wildcard in permission category
    permission_parts = permission.split(":")
    if len(permission_parts) > 1:
        wildcard_permission = f"{permission_parts[0]}:*"
        if wildcard_permission in permissions:
            return True
    
    return False
```

### Frontend Role-Based Access

```javascript
// frontend/src/utils/permissions.js

export const checkPermission = (userRole, permission) => {
    const rolePermissions = {
        student: [
            'greenhouse:read',
            'greenhouse:zones:read',
            'greenhouse:sensors:read',
            'greenhouse:crop_management:read',
            'greenhouse:crop_management:write',
            'greenhouse:growth_tracking:write',
            'greenhouse:data_export:read'
        ],
        admin: [
            'greenhouse:*',
            'automation:*',
            'users:read',
            'system:read'
        ],
        superuser: ['*']
    };

    const permissions = rolePermissions[userRole] || [];
    
    if (permissions.includes('*')) return true;
    if (permissions.includes(permission)) return true;
    
    const [category] = permission.split(':');
    if (permissions.includes(`${category}:*`)) return true;
    
    return false;
};

// Usage in components
import { checkPermission } from '../utils/permissions';

const MyComponent = () => {
    const { user } = useAuth();
    
    const canManageAutomation = checkPermission(user.role, 'automation:write');
    
    return (
        <div>
            {canManageAutomation && (
                <Button onClick={handleAutomationSetup}>
                    Setup Automation
                </Button>
            )}
        </div>
    );
};
```

## 🤖 AI Integration Setup

### Gemini AI Configuration

1. **Get API Key**:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Add it to your environment variables

2. **Configure AI Features**:

```python
# backend/api/ai_service.py

import google.generativeai as genai
from typing import Dict, List, Any

class GreenhouseAI:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def analyze_environmental_conditions(
        self, 
        sensor_data: Dict[str, Any],
        crop_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze environmental conditions and provide recommendations"""
        
        prompt = f"""
        Analyze the following greenhouse environmental data for {crop_profile['name']}:
        
        Environmental Data:
        - Temperature: {sensor_data['air_temperature']}°C
        - Humidity: {sensor_data['air_humidity']}%
        - Soil Moisture: {sensor_data['soil_moisture']}%
        - Light Intensity: {sensor_data['light_intensity']} lux
        - pH Level: {sensor_data['ph_level']}
        - CO2 Level: {sensor_data['co2_level']} ppm
        
        Crop Information:
        - Growth Stage: {crop_profile['current_stage']}
        - Optimal Temperature Range: {crop_profile['optimal_temp_min']}-{crop_profile['optimal_temp_max']}°C
        - Optimal Humidity Range: {crop_profile['optimal_humidity_min']}-{crop_profile['optimal_humidity_max']}%
        
        Provide analysis and recommendations in JSON format with:
        1. Overall health score (0-100)
        2. Issues identified
        3. Specific recommendations
        4. Priority actions
        5. Predicted yield impact
        """
        
        response = self.model.generate_content(prompt)
        return self._parse_ai_response(response.text)
    
    async def predict_yield(
        self,
        historical_data: List[Dict[str, Any]],
        crop_profile: Dict[str, Any],
        current_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict crop yield based on historical and current data"""
        
        # Implementation for yield prediction
        # This would involve more complex analysis of historical patterns
        pass
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response and extract structured data"""
        try:
            # Extract JSON from response
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback parsing
                return {"raw_response": response_text}
        except Exception as e:
            return {"error": str(e), "raw_response": response_text}
```

## 🌤️ Weather Service Integration

### OpenWeatherMap Setup

1. **Get API Key**:
   - Sign up at [OpenWeatherMap](https://openweathermap.org/api)
   - Get your free API key
   - Add to environment variables

2. **Configure Weather Service**:

```python
# backend/api/weather_service.py

import aiohttp
import asyncio
from typing import Dict, Any, Optional

class WeatherService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    async def get_current_weather(
        self, 
        latitude: float, 
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        """Get current weather data"""
        
        url = f"{self.base_url}/weather"
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "metric"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._format_current_weather(data)
                return None
    
    async def get_forecast(
        self, 
        latitude: float, 
        longitude: float,
        days: int = 5
    ) -> Optional[List[Dict[str, Any]]]:
        """Get weather forecast"""
        
        url = f"{self.base_url}/forecast"
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "metric",
            "cnt": days * 8  # 8 forecasts per day (3-hour intervals)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._format_forecast(data)
                return None
    
    def _format_current_weather(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format current weather data"""
        return {
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "description": data["weather"][0]["description"],
            "wind_speed": data["wind"]["speed"],
            "wind_direction": data["wind"].get("deg", 0),
            "clouds": data["clouds"]["all"],
            "visibility": data.get("visibility", 0) / 1000,  # Convert to km
            "uv_index": data.get("uvi", 0),
            "timestamp": data["dt"]
        }
    
    def _format_forecast(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format forecast data"""
        forecasts = []
        for item in data["list"]:
            forecasts.append({
                "timestamp": item["dt"],
                "temperature": item["main"]["temp"],
                "humidity": item["main"]["humidity"],
                "pressure": item["main"]["pressure"],
                "description": item["weather"][0]["description"],
                "wind_speed": item["wind"]["speed"],
                "precipitation": item.get("rain", {}).get("3h", 0),
                "clouds": item["clouds"]["all"]
            })
        return forecasts
```

## 📱 Mobile Responsiveness

### CSS Media Queries

Add responsive styles to your components:

```css
/* frontend/src/components/AdvancedEnvironmentalDashboard.css */

.environmental-dashboard {
    padding: 20px;
}

.sensor-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.chart-container {
    height: 400px;
    margin-bottom: 30px;
}

/* Tablet styles */
@media (max-width: 768px) {
    .environmental-dashboard {
        padding: 15px;
    }
    
    .sensor-grid {
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 15px;
    }
    
    .chart-container {
        height: 300px;
    }
    
    .ant-card-body {
        padding: 16px;
    }
}

/* Mobile styles */
@media (max-width: 480px) {
    .environmental-dashboard {
        padding: 10px;
    }
    
    .sensor-grid {
        grid-template-columns: 1fr;
        gap: 10px;
    }
    
    .chart-container {
        height: 250px;
    }
    
    .ant-card-body {
        padding: 12px;
    }
    
    .sensor-card .ant-statistic-title {
        font-size: 12px;
    }
    
    .sensor-card .ant-statistic-content {
        font-size: 18px;
    }
}
```

### Responsive React Components

```javascript
// frontend/src/hooks/useResponsive.js

import { useState, useEffect } from 'react';

export const useResponsive = () => {
    const [screenSize, setScreenSize] = useState({
        width: window.innerWidth,
        height: window.innerHeight,
        isMobile: window.innerWidth < 768,
        isTablet: window.innerWidth >= 768 && window.innerWidth < 1024,
        isDesktop: window.innerWidth >= 1024
    });

    useEffect(() => {
        const handleResize = () => {
            const width = window.innerWidth;
            const height = window.innerHeight;
            
            setScreenSize({
                width,
                height,
                isMobile: width < 768,
                isTablet: width >= 768 && width < 1024,
                isDesktop: width >= 1024
            });
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return screenSize;
};

// Usage in components
import { useResponsive } from '../hooks/useResponsive';

const EnvironmentalDashboard = () => {
    const { isMobile, isTablet } = useResponsive();
    
    const chartHeight = isMobile ? 250 : isTablet ? 300 : 400;
    const gridCols = isMobile ? 1 : isTablet ? 2 : 3;
    
    return (
        <div className="environmental-dashboard">
            <Row gutter={[16, 16]}>
                {sensorData.map((sensor, index) => (
                    <Col 
                        key={sensor.id}
                        xs={24}
                        sm={12}
                        md={8}
                        lg={6}
                    >
                        <SensorCard sensor={sensor} />
                    </Col>
                ))}
            </Row>
            
            <div style={{ height: chartHeight }}>
                <ResponsiveChart data={chartData} />
            </div>
        </div>
    );
};
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. ESP32 Connection Issues

**Problem**: ESP32 not connecting to WiFi
```
Solution:
1. Check WiFi credentials in firmware
2. Ensure WiFi network is 2.4GHz (ESP32 doesn't support 5GHz)
3. Check signal strength at device location
4. Verify firewall settings
```

**Problem**: MQTT connection fails
```
Solution:
1. Verify MQTT broker is running: docker-compose ps
2. Check MQTT credentials in firmware
3. Ensure MQTT broker port (1883) is accessible
4. Check device_id uniqueness
```

#### 2. Database Issues

**Problem**: Database migration fails
```
Solution:
1. Check PostgreSQL is running: docker-compose ps
2. Verify database credentials in .env
3. Ensure user has sufficient privileges
4. Check for existing table conflicts
```

**Problem**: Slow query performance
```
Solution:
1. Ensure indexes are created (see Database Optimization section)
2. Consider partitioning large tables
3. Optimize queries with EXPLAIN ANALYZE
4. Consider upgrading to TimescaleDB for time-series data
```

#### 3. Frontend Issues

**Problem**: Components not loading
```
Solution:
1. Check browser console for errors
2. Verify API endpoints are accessible
3. Check authentication tokens
4. Clear browser cache and localStorage
```

**Problem**: WebSocket connection fails
```
Solution:
1. Verify WebSocket URL in frontend .env
2. Check backend WebSocket endpoint
3. Ensure no proxy/firewall blocking WebSocket connections
4. Check browser WebSocket support
```

#### 4. Sensor Reading Issues

**Problem**: Inconsistent sensor readings
```
Solution:
1. Check sensor wiring and connections
2. Verify power supply stability
3. Calibrate sensors according to manufacturer instructions
4. Add filtering/averaging in firmware
5. Check for electromagnetic interference
```

**Problem**: Sensor not detected
```
Solution:
1. Verify sensor is properly connected
2. Check I2C address for digital sensors
3. Test sensor with simple Arduino sketch
4. Check sensor power requirements
5. Verify pin assignments in firmware
```

### Debug Mode

Enable debug logging in your environment:

```bash
# Backend debug mode
DEBUG=true
LOG_LEVEL=DEBUG

# Frontend debug mode
REACT_APP_DEBUG=true
```

### Log Analysis

Check logs for troubleshooting:

```bash
# Docker container logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs database

# Follow logs in real-time
docker-compose logs -f backend

# ESP32 serial monitor
# Use Arduino IDE Serial Monitor or PlatformIO
```

### Performance Monitoring

Monitor system performance:

```bash
# Check system resources
docker stats

# Monitor database performance
docker-compose exec database psql -U iotuser -d iot_platform -c "
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public'
ORDER BY tablename, attname;
"

# Check MQTT broker status
docker-compose exec mqtt mosquitto_sub -h localhost -t '$SYS/#' -C 10
```

---

## 📞 Support

For additional support:

1. **Check Documentation**: Review GREENHOUSE_FEATURES.md
2. **Search Issues**: Look for similar problems in project issues
3. **Create Issue**: Submit detailed bug report with logs
4. **Community**: Join project discussions and forums

**Remember**: Always backup your data before making configuration changes!

---

*This configuration guide is part of the Enhanced Greenhouse Management System. For the latest updates, check the project repository.*
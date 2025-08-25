# ESP32 to Message Broker Communication Guide

## 📡 How ESP32 Sends Messages to RabbitMQ MQTT Broker

This guide explains exactly how your ESP32 sends messages to the RabbitMQ message broker and what you need to know about this communication.

---

## 🔧 **Current ESP32 Message Sending Setup**

### **1. MQTT Connection Configuration**

```cpp
// MQTT Broker Settings (in IoT_Platform_Node.ino)
const char* mqtt_server = "192.168.8.114";    // Your RabbitMQ server IP
const int mqtt_port = 1883;                    // MQTT port
const char* mqtt_user = "rnr_iot_user";        // MQTT username
const char* mqtt_password = "rnr_iot_2025!";   // MQTT password

// Persistent Session Settings
PubSubClient client(espClient);
client.connect(clientId, mqtt_user, mqtt_password, NULL, 0, false, NULL, false); // cleanSession=false
```

### **2. Message Topics**

Your ESP32 sends messages to these topics:

```cpp
String data_topic = "devices/" + node_id + "/data";        // Sensor data
String command_topic = "devices/" + node_id + "/commands"; // Command responses
String last_topic = "devices/" + node_id + "/last";        // Last will message
```

---

## 📊 **Types of Messages ESP32 Sends**

### **1. Sensor Data Messages (Every 1 Second)**

```json
{
  "timestamp": "14:30:25",
  "temperature": 25.6,
  "humidity": 65.2,
  "humidity_mq": 62.8,
  "humidity_mq_raw": 2450,
  "gas_sensor": 1234,
  "status": "online",
  "node_id": "AABBCCDDEEFF",
  "servo_angle": 90,
  "light_state": false,
  "fan_state": true,
  "relay3_state": false,
  "relay4_state": false,
  "real_model_state": false,
  "smart_mode": false,
  "uptime": 123456789,
  "wifi_rssi": -45
}
```

**Sent to topic**: `devices/AABBCCDDEEFF/data`

### **2. Status Messages**

```json
{
  "node_id": "AABBCCDDEEFF",
  "status": "connected",
  "timestamp": "14:30:25",
  "message": "ESP32 connected and ready"
}
```

### **3. Heartbeat Messages**

```json
{
  "node_id": "AABBCCDDEEFF",
  "timestamp": "14:30:25",
  "uptime": 123456789,
  "status": "alive",
  "wifi_rssi": -45
}
```

### **4. Command Response Messages**

```json
{
  "node_id": "AABBCCDDEEFF",
  "action": "LIGHT_CONTROL",
  "result": "success",
  "new_state": true,
  "timestamp": "14:30:25"
}
```

---

## 🚀 **How Message Sending Works**

### **Step 1: ESP32 Connects to RabbitMQ**

```cpp
void connectMQTT() {
  while (!client.connected()) {
    Serial.print("🔄 Attempting RabbitMQ MQTT connection...");

    String clientId = "ESP32-" + node_id;

    // Connect with persistent session (cleanSession=false)
    if (client.connect(clientId.c_str(), mqtt_user, mqtt_password,
                       last_topic.c_str(), 1, true, "offline", false)) {

      Serial.println(" ✅ Connected to RabbitMQ MQTT broker with persistent session!");
      Serial.println("📦 Persistent session enabled - queued messages will be received on reconnect");

      // Subscribe to commands with QoS=1
      client.subscribe(command_topic.c_str(), 1);
      Serial.println("Subscribed to: " + command_topic + " (qos=1, persistent)");

    } else {
      Serial.print(" ❌ Connection failed, rc=");
      Serial.println(client.state());
      delay(5000);
    }
  }
}
```

### **Step 2: ESP32 Creates Message**

```cpp
void readAndPublishSensors() {
  // Read sensor values
  temperature = 25.6;  // Example temperature
  humidity = 65.2;     // Example humidity
  gasSensorValue = analogRead(gasSensorPin);

  // Create JSON message
  StaticJsonDocument<250> doc;
  doc["timestamp"] = "14:30:25";
  doc["temperature"] = temperature;
  doc["humidity"] = humidity;
  doc["gas_sensor"] = gasSensorValue;
  doc["node_id"] = node_id;
  doc["status"] = "online";

  String payload;
  serializeJson(doc, payload);
```

### **Step 3: ESP32 Sends Message to Broker**

```cpp
  // Send message with retry logic
  bool published = false;
  for (int attempt = 0; attempt < 3 && !published; attempt++) {
    if (client.connected() && client.publish(data_topic.c_str(),
                                           (const uint8_t*)payload.c_str(),
                                           payload.length(), false)) {
      published = true;
      Serial.println("✅ Data sent to RabbitMQ (attempt " + String(attempt + 1) + "):");
      Serial.println(payload);
    } else {
      Serial.println("❌ RabbitMQ publish attempt " + String(attempt + 1) + " failed");
    }
  }
}
```

### **Step 4: Message Reaches RabbitMQ Broker**

- RabbitMQ receives the message on topic `devices/AABBCCDDEEFF/data`
- Message is queued in RabbitMQ
- Backend services can subscribe to receive the message
- Web dashboard can display the data

---

## ⚙️ **Configuration You Need to Know**

### **1. Update MQTT Broker IP Address**

In `IoT_Platform_Node.ino`, update this line:

```cpp
const char* mqtt_server = "192.168.8.114"; // Change to your RabbitMQ server IP
```

### **2. WiFi Configuration**

Your ESP32 creates a WiFi AP for configuration:

- **AP Name**: `IoTPlatform-Setup`
- **Setup URL**: `http://192.168.4.1`
- Enter your WiFi credentials through web interface

### **3. Device ID Configuration**

```cpp
// Device ID is auto-generated from MAC address
node_id = WiFi.macAddress();
node_id.replace(":", "");  // Remove colons: "AABBCCDDEEFF"
```

---

## 📋 **Message Sending Frequency**

### **Current Settings:**

```cpp
#define SENSOR_INTERVAL 1000    // Send data every 1 second
#define HEARTBEAT_INTERVAL 30000 // Send heartbeat every 30 seconds
```

### **In main loop():**

```cpp
void loop() {
  static unsigned long lastSensorTime = 0;

  // Send sensor data every 1 second
  if (millis() - lastSensorTime >= SENSOR_INTERVAL) {
    if (client.connected()) {
      readAndPublishSensors();  // This sends your message!
    }
    lastSensorTime = millis();
  }

  client.loop(); // Handle MQTT communication
}
```

---

## 🔍 **How to Monitor Message Sending**

### **1. Serial Monitor Output**

Connect ESP32 to computer and open serial monitor (115200 baud):

```
✅ Data sent to RabbitMQ (attempt 1):
{"timestamp":"14:30:25","temperature":25.6,"humidity":65.2,"gas_sensor":1234,"node_id":"AABBCCDDEEFF","status":"online"}
```

### **2. RabbitMQ Management Interface**

- Open: `http://your-server-ip:15672`
- Login: `rnr_iot_user` / `rnr_iot_2025!`
- Check **Queues** tab to see messages

### **3. MQTT Client Tools**

Use MQTT client to subscribe and see messages:

```bash
# Subscribe to all device messages
mosquitto_sub -h your-server-ip -p 1883 -u rnr_iot_user -P rnr_iot_2025! -t "devices/+/data"
```

---

## 🚨 **Troubleshooting Message Sending**

### **Problem: No Messages Sent**

**Check:**

1. WiFi connection: ESP32 connected to internet?
2. MQTT broker IP: Is `mqtt_server` IP correct?
3. MQTT credentials: Username/password correct?
4. Firewall: Port 1883 open?

**Solution:**

```cpp
// Add debug output in readAndPublishSensors()
Serial.print("MQTT Connected: ");
Serial.println(client.connected() ? "Yes" : "No");
Serial.print("WiFi Status: ");
Serial.println(WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected");
```

### **Problem: Messages Not Reaching Backend**

**Check:**

1. RabbitMQ service running?
2. Backend subscribed to correct topic?
3. Message format correct?

**Test:**

```bash
# Check if RabbitMQ is receiving messages
docker logs rabbitmq-container
```

### **Problem: Intermittent Message Loss**

**Check:**

1. WiFi signal strength (RSSI)
2. Network stability
3. MQTT QoS settings

**Solution:**

```cpp
// Add QoS=1 for reliable delivery
client.publish(data_topic.c_str(), payload.c_str(), true); // retained=true
```

---

## 📝 **Custom Message Types**

### **Send Custom Data**

Add to `readAndPublishSensors()`:

```cpp
// Add custom sensor data
doc["custom_sensor"] = analogRead(A0);
doc["button_state"] = digitalRead(buttonPin);
doc["custom_message"] = "Hello from ESP32!";
```

### **Send Alert Messages**

```cpp
void sendAlert(String alertType, String message) {
  StaticJsonDocument<150> doc;
  doc["node_id"] = node_id;
  doc["type"] = "alert";
  doc["alert_type"] = alertType;
  doc["message"] = message;
  doc["timestamp"] = getTimeString();
  doc["priority"] = "high";

  String payload;
  serializeJson(doc, payload);

  if (client.connected()) {
    client.publish(data_topic.c_str(), payload.c_str());
    Serial.println("🚨 Alert sent: " + message);
  }
}

// Usage
sendAlert("temperature", "Temperature above 30°C!");
sendAlert("gas", "Gas levels critical!");
```

### **Send Status Updates**

```cpp
void sendStatusUpdate(String status, String details) {
  StaticJsonDocument<120> doc;
  doc["node_id"] = node_id;
  doc["type"] = "status";
  doc["status"] = status;
  doc["details"] = details;
  doc["timestamp"] = getTimeString();

  String payload;
  serializeJson(doc, payload);

  client.publish(data_topic.c_str(), payload.c_str());
}

// Usage
sendStatusUpdate("startup", "ESP32 booted successfully");
sendStatusUpdate("error", "Sensor reading failed");
sendStatusUpdate("maintenance", "Starting self-test");
```

---

## 🎯 **Message Flow Summary**

```
ESP32 Sensor Reading → JSON Creation → MQTT Publish → RabbitMQ Broker → Backend API → Web Dashboard
```

**Detailed Flow:**

1. **ESP32** reads sensors every 1 second
2. **ESP32** creates JSON message with sensor data
3. **ESP32** publishes message to `devices/DEVICEID/data` topic
4. **RabbitMQ** receives message and queues it
5. **Backend API** subscribes to topic and receives message
6. **Backend API** processes data and stores in database
7. **Web Dashboard** displays real-time data to user

---

## 🔧 **Quick Configuration Checklist**

- [ ] Update `mqtt_server` IP address in firmware
- [ ] Ensure RabbitMQ is running on port 1883
- [ ] Configure WiFi credentials via ESP32 AP mode
- [ ] Verify ESP32 MAC address for device ID
- [ ] Check serial monitor for message sending confirmation
- [ ] Test message reception in RabbitMQ management interface
- [ ] Verify backend API receives messages
- [ ] Confirm web dashboard shows real-time data

**Your ESP32 is now sending messages to the message broker every 1 second!** 🚀

For any issues, check the serial monitor output and RabbitMQ logs for debugging information.

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <HTTPUpdate.h>
#include <WiFiClient.h>
#include <time.h>
#include <ESP32Servo.h>

/*
 * RNR Solutions IoT Platform - ESP32 Firmware
 * Enterprise IoT Device Management System
 * © 2025 RNR Solutions. All rights reserved.
 * 
 * This firmware enables ESP32 devices to connect to the RNR IoT Platform
 * for real-time monitoring, control, and OTA firmware updates.
 */

// Function declarations
void connectWiFi();
void connectMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int length);
void readAndPublishSensors();
void publishStatus(String status);
void handleReboot();
void handleStatusRequest();
void handleFirmwareUpdate(String url);
void handleServoAngle(int angle);

// WiFi Configuration - Update with your network credentials
const char* ssid = "YOUR_WIFI_SSID";           // Replace with your WiFi SSID
const char* password = "YOUR_WIFI_PASSWORD";   // Replace with your WiFi password

// RNR Solutions IoT Platform MQTT Configuration
const char* mqtt_server = "192.168.1.100";     // Replace with your RNR IoT Platform server IP
const int mqtt_port = 1883;
const char* mqtt_user = "rnr_iot_user";        // RNR IoT Platform MQTT username
const char* mqtt_password = "rnr_iot_2025!";   // RNR IoT Platform MQTT password

// NTP Configuration
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 5.5 * 3600; // UTC+5:30 for India
const int daylightOffset_sec = 0;

// Device Configuration
String node_id;
String data_topic;
String command_topic;

// MQTT and WiFi clients
WiFiClient espClient;
PubSubClient client(espClient);

// Servo Configuration
Servo servo;
const int servoPin = 16; // GPIO16 for servo signal
int servoAngle = 90; // Initial servo position (middle)

// Sensor simulation variables
float temperature = 20.0;
float humidity = 50.0;
unsigned long lastSensorRead = 0;
unsigned long lastMqttReconnect = 0;
unsigned long lastServoDisplay = 0; // For periodic servo angle display
const unsigned long SENSOR_INTERVAL = 30000; // 30 seconds
const unsigned long MQTT_RECONNECT_INTERVAL = 5000; // 5 seconds
const unsigned long SERVO_DISPLAY_INTERVAL = 5000; // 5 seconds for servo angle display

void setup() {
  Serial.begin(115200);
  delay(1000); // Allow time for Serial Monitor to connect

  Serial.println("\n╔══════════════════════════════════════════════════════╗");
  Serial.println("║           RNR Solutions IoT Platform                ║");
  Serial.println("║           ESP32 Enterprise Node                     ║");
  Serial.println("║           Firmware v2.0.0                           ║");
  Serial.println("║           © 2025 RNR Solutions                      ║");
  Serial.println("╚══════════════════════════════════════════════════════╝");
  Serial.println();

  // Initialize servo
  servo.attach(servoPin);
  servo.write(servoAngle); // Set initial position
  Serial.print("Initial servo angle: ");
  Serial.println(servoAngle);

  // Connect to WiFi
  connectWiFi();

  // Generate and display MAC address after WiFi connection
  String macAddress = WiFi.macAddress();
  node_id = macAddress;
  node_id.replace(":", "");
  Serial.print("MAC Address: ");
  Serial.println(macAddress); // Explicitly display MAC address
  if (macAddress == "" || macAddress == "00:00:00:00:00:00") {
    Serial.println("Warning: Failed to retrieve valid MAC address");
  }

  // Setup MQTT topics
  data_topic = "devices/" + node_id + "/data";
  command_topic = "devices/" + node_id + "/commands";

  Serial.println("Node ID: " + node_id);
  Serial.println("Data Topic: " + data_topic);
  Serial.println("Command Topic: " + command_topic);

  // Initialize NTP
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  Serial.println("Waiting for NTP time sync...");
  delay(2000);

  // Setup MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqttCallback);

  connectMQTT();

  Serial.println("=== Setup Complete ===\n");
}

void loop() {
  // Maintain MQTT connection
  if (!client.connected()) {
    if (millis() - lastMqttReconnect > MQTT_RECONNECT_INTERVAL) {
      lastMqttReconnect = millis();
      connectMQTT();
    }
  }
  client.loop();

  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  // Read and publish sensor data
  if (millis() - lastSensorRead > SENSOR_INTERVAL) {
    lastSensorRead = millis();
    readAndPublishSensors();
  }

  // Continuously display servo angle
  if (millis() - lastServoDisplay > SERVO_DISPLAY_INTERVAL) {
    lastServoDisplay = millis();
    Serial.print("Current servo angle: ");
    Serial.println(servoAngle);
  }

  delay(100);
}

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println("\nWiFi connection failed!");
  }
}

void connectMQTT() {
  if (client.connected()) {
    return;
  }

  Serial.print("Connecting to MQTT broker: ");
  Serial.print(mqtt_server);
  Serial.print(":");
  Serial.println(mqtt_port);

  String clientId = "ESP32-" + node_id;

  if (client.connect(clientId.c_str(), mqtt_user, mqtt_password)) {
    Serial.println("MQTT connected!");

    // Subscribe to command topic with QoS=1 so commands are queued for offline devices
    if (client.subscribe(command_topic.c_str(), 1)) {
      Serial.println("Subscribed to: " + command_topic + " (qos=1)");
    } else {
      Serial.println("Failed to subscribe to: " + command_topic);
    }

    // Subscribe to retained last-command topic as a fallback to receive the
    // most recent command if it was published with retain flag while this
    // device was offline. Use QoS=1 to ensure delivery.
    String last_cmd_topic = command_topic + "/last";
    if (client.subscribe(last_cmd_topic.c_str(), 1)) {
      Serial.println("Subscribed to retained fallback: " + last_cmd_topic + " (qos=1)");
    } else {
      Serial.println("Failed to subscribe to retained fallback: " + last_cmd_topic);
    }

    // Publish initial status
    publishStatus("online");
  } else {
    Serial.print("MQTT connection failed, rc=");
    Serial.println(client.state());
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message received on topic: ");
  Serial.println(topic);

  // Convert payload to string
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("Message: ");
  Serial.println(message);

  // Parse JSON command
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, message);

  if (error) {
    Serial.print("JSON parsing failed: ");
    Serial.println(error.c_str());
    return;
  }

  String action = doc["action"];
  Serial.print("Action: ");
  Serial.println(action);

  // If this message came from the retained fallback topic, strip '/last' suffix
  String t = String(topic);
  if (t.endsWith("/last")) {
    Serial.println("Received retained last-command fallback topic");
    // treat payload the same as a live command
  }

  // Handle different commands
  if (action == "REBOOT") {
    handleReboot();
  } else if (action == "STATUS_REQUEST") {
    handleStatusRequest();
  } else if (action == "FIRMWARE_UPDATE") {
    String url = doc["url"];
    handleFirmwareUpdate(url);
  } else if (action == "SERVO_ANGLE") {
    int angle = doc["angle"];
    handleServoAngle(angle);
  } else {
    Serial.println("Unknown action: " + action);
  }
}

void readAndPublishSensors() {
  // Simulate sensor readings with some variation
  temperature += random(-50, 51) / 100.0; // ±0.5°C variation
  humidity += random(-200, 201) / 100.0;  // ±2% variation

  // Keep values in realistic ranges
  temperature = constrain(temperature, 15.0, 35.0);
  humidity = constrain(humidity, 30.0, 80.0);

  // Create JSON payload
  StaticJsonDocument<300> doc;

  // Get current time
  time_t now;
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    Serial.println("Failed to obtain time");
    doc["timestamp"] = "unknown";
  } else {
    char timeString[25];
    strftime(timeString, sizeof(timeString), "%Y-%m-%d %H:%M:%S", &timeinfo);
    doc["timestamp"] = timeString;
  }

  doc["temperature"] = round(temperature * 10) / 10.0;
  doc["humidity"] = round(humidity * 10) / 10.0;
  doc["status"] = "online";
  doc["uptime"] = millis();
  doc["free_heap"] = ESP.getFreeHeap();
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["node_id"] = node_id;
  doc["servo_angle"] = servoAngle;

  String payload;
  serializeJson(doc, payload);

  // Publish to MQTT and display to Serial Monitor
  if (client.publish(data_topic.c_str(), payload.c_str())) {
    Serial.println("Sensor data published:");
    Serial.println(payload);
    Serial.print("Current servo angle: ");
    Serial.println(servoAngle);
  } else {
    Serial.println("Failed to publish sensor data");
    Serial.print("Current servo angle: ");
    Serial.println(servoAngle);
  }
}

void publishStatus(String status) {
  StaticJsonDocument<200> doc;

  // Get current time
  time_t now;
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    Serial.println("Failed to obtain time");
    doc["timestamp"] = "unknown";
  } else {
    char timeString[25];
    strftime(timeString, sizeof(timeString), "%Y-%m-%d %H:%M:%S", &timeinfo);
    doc["timestamp"] = timeString;
  }

  doc["status"] = status;
  doc["uptime"] = millis();
  doc["free_heap"] = ESP.getFreeHeap();
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["node_id"] = node_id;
  doc["servo_angle"] = servoAngle;

  String payload;
  serializeJson(doc, payload);

  // Publish to MQTT and display to Serial Monitor
  if (client.publish(data_topic.c_str(), payload.c_str())) {
    Serial.println("Status published: " + status);
    Serial.println(payload);
    Serial.print("Current servo angle: ");
    Serial.println(servoAngle);
  } else {
    Serial.println("Failed to publish status");
    Serial.print("Current servo angle: ");
    Serial.println(servoAngle);
  }
}

void handleReboot() {
  Serial.println("Reboot command received. Restarting in 2 seconds...");
  publishStatus("rebooting");
  delay(2000);
  ESP.restart();
}

void handleStatusRequest() {
  Serial.println("Status request received. Publishing current status...");
  publishStatus("online");
}

void handleFirmwareUpdate(String url) {
  Serial.println("Firmware update command received.");
  Serial.println("Update URL: " + url);

  publishStatus("updating");

  WiFiClient client;

  Serial.println("Starting OTA update...");

  t_httpUpdate_return ret = httpUpdate.update(client, url);

  switch (ret) {
    case HTTP_UPDATE_FAILED:
      Serial.printf("HTTP_UPDATE_FAILED Error (%d): %s\n",
                    httpUpdate.getLastError(),
                    httpUpdate.getLastErrorString().c_str());
      publishStatus("update_failed");
      break;

    case HTTP_UPDATE_NO_UPDATES:
      Serial.println("HTTP_UPDATE_NO_UPDATES");
      publishStatus("no_update_needed");
      break;

    case HTTP_UPDATE_OK:
      Serial.println("HTTP_UPDATE_OK");
      publishStatus("update_success");
      break;
  }
}

void handleServoAngle(int angle) {
  Serial.print("Servo angle command received: ");
  Serial.println(angle);

  // Validate angle (0–180 degrees)
  angle = constrain(angle, 0, 180);
  servoAngle = angle;
  servo.write(angle);

  // Display updated servo angle
  Serial.print("Servo moved to angle: ");
  Serial.println(servoAngle);

  // Publish updated status
  publishStatus("servo_updated");
}

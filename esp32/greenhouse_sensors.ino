/*
 * Enhanced Greenhouse Monitoring ESP32 Firmware
 * Supports multiple sensor types for comprehensive environmental monitoring
 * Compatible with the enhanced IoT Platform greenhouse features
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Wire.h>
#include <BH1750.h>
#include <SoftwareSerial.h>

// WiFi and MQTT Configuration
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqtt_server = "YOUR_MQTT_BROKER_IP";
const int mqtt_port = 1883;
const char* mqtt_user = "YOUR_MQTT_USER";
const char* mqtt_password = "YOUR_MQTT_PASSWORD";

// Device Configuration
const char* device_id = "greenhouse_node_01";
const char* zone_id = "zone_1";
const int firmware_version = 2;

// Pin Definitions
#define DHT_PIN 4
#define DHT_TYPE DHT22
#define SOIL_MOISTURE_PIN A0
#define SOIL_TEMP_PIN 2
#define PH_SENSOR_PIN A1
#define EC_SENSOR_PIN A2
#define CO2_SENSOR_RX 16
#define CO2_SENSOR_TX 17
#define RELAY_WATER 5
#define RELAY_FAN 18
#define RELAY_HEATER 19
#define RELAY_LIGHTS 21
#define STATUS_LED 2

// Sensor Objects
DHT dht(DHT_PIN, DHT_TYPE);
OneWire oneWire(SOIL_TEMP_PIN);
DallasTemperature soilTempSensor(&oneWire);
BH1750 lightMeter;
SoftwareSerial co2Serial(CO2_SENSOR_RX, CO2_SENSOR_TX);

// Network Objects
WiFiClient espClient;
PubSubClient client(espClient);

// Timing Variables
unsigned long lastSensorRead = 0;
unsigned long lastHeartbeat = 0;
unsigned long lastWiFiCheck = 0;
const unsigned long SENSOR_INTERVAL = 30000;  // 30 seconds
const unsigned long HEARTBEAT_INTERVAL = 60000;  // 1 minute
const unsigned long WIFI_CHECK_INTERVAL = 300000;  // 5 minutes

// Sensor Data Structure
struct SensorData {
  float air_temperature;
  float air_humidity;
  float soil_temperature;
  float soil_moisture;
  float ph_level;
  float ec_level;
  float light_intensity;
  int co2_level;
  float battery_voltage;
  int wifi_signal_strength;
  bool sensor_status[8];  // Status for each sensor type
  unsigned long timestamp;
};

SensorData currentData;

// Control State
struct ControlState {
  bool water_pump;
  bool ventilation_fan;
  bool heater;
  bool grow_lights;
  bool auto_mode;
  float target_temperature;
  float target_humidity;
  float target_soil_moisture;
};

ControlState controlState = {false, false, false, false, true, 25.0, 60.0, 50.0};

void setup() {
  Serial.begin(115200);
  Serial.println("Enhanced Greenhouse Monitor Starting...");
  
  // Initialize pins
  pinMode(STATUS_LED, OUTPUT);
  pinMode(RELAY_WATER, OUTPUT);
  pinMode(RELAY_FAN, OUTPUT);
  pinMode(RELAY_HEATER, OUTPUT);
  pinMode(RELAY_LIGHTS, OUTPUT);
  
  // Initialize all relays to OFF
  digitalWrite(RELAY_WATER, LOW);
  digitalWrite(RELAY_FAN, LOW);
  digitalWrite(RELAY_HEATER, LOW);
  digitalWrite(RELAY_LIGHTS, LOW);
  
  // Initialize sensors
  initializeSensors();
  
  // Connect to WiFi
  setupWiFi();
  
  // Setup MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqttCallback);
  
  // Initial sensor reading
  readAllSensors();
  
  Serial.println("Greenhouse Monitor Ready!");
  digitalWrite(STATUS_LED, HIGH);
}

void loop() {
  unsigned long currentTime = millis();
  
  // Maintain MQTT connection
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();
  
  // Check WiFi connection periodically
  if (currentTime - lastWiFiCheck >= WIFI_CHECK_INTERVAL) {
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi disconnected, reconnecting...");
      setupWiFi();
    }
    lastWiFiCheck = currentTime;
  }
  
  // Read sensors at regular intervals
  if (currentTime - lastSensorRead >= SENSOR_INTERVAL) {
    readAllSensors();
    publishSensorData();
    lastSensorRead = currentTime;
  }
  
  // Send heartbeat
  if (currentTime - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    publishHeartbeat();
    lastHeartbeat = currentTime;
  }
  
  // Execute automatic control logic
  if (controlState.auto_mode) {
    executeAutomaticControl();
  }
  
  // Update status LED
  updateStatusLED();
  
  delay(1000);  // Small delay to prevent watchdog issues
}

void initializeSensors() {
  Serial.println("Initializing sensors...");
  
  // Initialize DHT sensor
  dht.begin();
  
  // Initialize soil temperature sensor
  soilTempSensor.begin();
  
  // Initialize light sensor
  Wire.begin();
  if (lightMeter.begin()) {
    Serial.println("BH1750 Light sensor initialized");
  } else {
    Serial.println("Error initializing BH1750");
  }
  
  // Initialize CO2 sensor serial communication
  co2Serial.begin(9600);
  
  Serial.println("Sensor initialization complete");
}

void setupWiFi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("");
    Serial.println("WiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("Failed to connect to WiFi");
  }
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    if (client.connect(device_id, mqtt_user, mqtt_password)) {
      Serial.println("connected");
      
      // Subscribe to control topics
      String controlTopic = "greenhouse/" + String(zone_id) + "/control";
      String configTopic = "greenhouse/" + String(zone_id) + "/config";
      
      client.subscribe(controlTopic.c_str());
      client.subscribe(configTopic.c_str());
      
      // Publish device info
      publishDeviceInfo();
      
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  Serial.println(message);
  
  // Parse JSON message
  DynamicJsonDocument doc(1024);
  deserializeJson(doc, message);
  
  String topicStr = String(topic);
  
  if (topicStr.endsWith("/control")) {
    handleControlCommand(doc);
  } else if (topicStr.endsWith("/config")) {
    handleConfigUpdate(doc);
  }
}

void handleControlCommand(DynamicJsonDocument& doc) {
  if (doc.containsKey("water_pump")) {
    controlState.water_pump = doc["water_pump"];
    digitalWrite(RELAY_WATER, controlState.water_pump ? HIGH : LOW);
  }
  
  if (doc.containsKey("ventilation_fan")) {
    controlState.ventilation_fan = doc["ventilation_fan"];
    digitalWrite(RELAY_FAN, controlState.ventilation_fan ? HIGH : LOW);
  }
  
  if (doc.containsKey("heater")) {
    controlState.heater = doc["heater"];
    digitalWrite(RELAY_HEATER, controlState.heater ? HIGH : LOW);
  }
  
  if (doc.containsKey("grow_lights")) {
    controlState.grow_lights = doc["grow_lights"];
    digitalWrite(RELAY_LIGHTS, controlState.grow_lights ? HIGH : LOW);
  }
  
  if (doc.containsKey("auto_mode")) {
    controlState.auto_mode = doc["auto_mode"];
  }
  
  // Publish control state confirmation
  publishControlState();
}

void handleConfigUpdate(DynamicJsonDocument& doc) {
  if (doc.containsKey("target_temperature")) {
    controlState.target_temperature = doc["target_temperature"];
  }
  
  if (doc.containsKey("target_humidity")) {
    controlState.target_humidity = doc["target_humidity"];
  }
  
  if (doc.containsKey("target_soil_moisture")) {
    controlState.target_soil_moisture = doc["target_soil_moisture"];
  }
  
  Serial.println("Configuration updated");
}

void readAllSensors() {
  currentData.timestamp = millis();
  
  // Read DHT22 (Air Temperature & Humidity)
  currentData.air_temperature = dht.readTemperature();
  currentData.air_humidity = dht.readHumidity();
  currentData.sensor_status[0] = !isnan(currentData.air_temperature) && !isnan(currentData.air_humidity);
  
  // Read soil temperature
  soilTempSensor.requestTemperatures();
  currentData.soil_temperature = soilTempSensor.getTempCByIndex(0);
  currentData.sensor_status[1] = currentData.soil_temperature != DEVICE_DISCONNECTED_C;
  
  // Read soil moisture (analog sensor)
  int soilMoistureRaw = analogRead(SOIL_MOISTURE_PIN);
  currentData.soil_moisture = map(soilMoistureRaw, 0, 4095, 0, 100);
  currentData.sensor_status[2] = true;  // Analog sensors typically always work
  
  // Read pH sensor
  int phRaw = analogRead(PH_SENSOR_PIN);
  currentData.ph_level = map(phRaw, 0, 4095, 0, 14);  // Basic mapping, calibrate as needed
  currentData.sensor_status[3] = true;
  
  // Read EC sensor
  int ecRaw = analogRead(EC_SENSOR_PIN);
  currentData.ec_level = map(ecRaw, 0, 4095, 0, 5000);  // Basic mapping, calibrate as needed
  currentData.sensor_status[4] = true;
  
  // Read light intensity
  currentData.light_intensity = lightMeter.readLightLevel();
  currentData.sensor_status[5] = currentData.light_intensity >= 0;
  
  // Read CO2 sensor (if available)
  currentData.co2_level = readCO2Sensor();
  currentData.sensor_status[6] = currentData.co2_level > 0;
  
  // Read system status
  currentData.battery_voltage = readBatteryVoltage();
  currentData.wifi_signal_strength = WiFi.RSSI();
  currentData.sensor_status[7] = true;  // System status always available
}

int readCO2Sensor() {
  // Simple CO2 sensor reading (implement based on your specific sensor)
  // This is a placeholder - implement according to your CO2 sensor protocol
  if (co2Serial.available()) {
    String data = co2Serial.readString();
    // Parse CO2 data based on sensor protocol
    return data.toInt();  // Simplified parsing
  }
  return 400;  // Default atmospheric CO2 level
}

float readBatteryVoltage() {
  // Read battery voltage if using battery power
  // This is a placeholder - implement based on your power setup
  return 3.7;  // Default for Li-ion battery
}

void publishSensorData() {
  DynamicJsonDocument doc(2048);
  
  doc["device_id"] = device_id;
  doc["zone_id"] = zone_id;
  doc["timestamp"] = currentData.timestamp;
  doc["firmware_version"] = firmware_version;
  
  // Environmental data
  doc["air_temperature"] = currentData.air_temperature;
  doc["air_humidity"] = currentData.air_humidity;
  doc["soil_temperature"] = currentData.soil_temperature;
  doc["soil_moisture"] = currentData.soil_moisture;
  doc["ph_level"] = currentData.ph_level;
  doc["ec_level"] = currentData.ec_level;
  doc["light_intensity"] = currentData.light_intensity;
  doc["co2_level"] = currentData.co2_level;
  
  // System status
  doc["battery_voltage"] = currentData.battery_voltage;
  doc["wifi_signal_strength"] = currentData.wifi_signal_strength;
  
  // Sensor status array
  JsonArray sensorStatus = doc.createNestedArray("sensor_status");
  for (int i = 0; i < 8; i++) {
    sensorStatus.add(currentData.sensor_status[i]);
  }
  
  // Data quality score (0-100)
  int qualityScore = calculateDataQuality();
  doc["data_quality_score"] = qualityScore;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  String topic = "greenhouse/" + String(zone_id) + "/sensors";
  client.publish(topic.c_str(), jsonString.c_str());
  
  Serial.println("Sensor data published: " + jsonString);
}

int calculateDataQuality() {
  int workingSensors = 0;
  for (int i = 0; i < 8; i++) {
    if (currentData.sensor_status[i]) {
      workingSensors++;
    }
  }
  
  int baseScore = (workingSensors * 100) / 8;
  
  // Adjust based on WiFi signal strength
  if (currentData.wifi_signal_strength > -50) {
    baseScore += 5;
  } else if (currentData.wifi_signal_strength < -80) {
    baseScore -= 10;
  }
  
  return constrain(baseScore, 0, 100);
}

void publishControlState() {
  DynamicJsonDocument doc(1024);
  
  doc["device_id"] = device_id;
  doc["zone_id"] = zone_id;
  doc["timestamp"] = millis();
  
  doc["water_pump"] = controlState.water_pump;
  doc["ventilation_fan"] = controlState.ventilation_fan;
  doc["heater"] = controlState.heater;
  doc["grow_lights"] = controlState.grow_lights;
  doc["auto_mode"] = controlState.auto_mode;
  
  doc["target_temperature"] = controlState.target_temperature;
  doc["target_humidity"] = controlState.target_humidity;
  doc["target_soil_moisture"] = controlState.target_soil_moisture;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  String topic = "greenhouse/" + String(zone_id) + "/status";
  client.publish(topic.c_str(), jsonString.c_str());
}

void publishHeartbeat() {
  DynamicJsonDocument doc(512);
  
  doc["device_id"] = device_id;
  doc["zone_id"] = zone_id;
  doc["timestamp"] = millis();
  doc["status"] = "online";
  doc["uptime"] = millis() / 1000;
  doc["free_heap"] = ESP.getFreeHeap();
  doc["wifi_rssi"] = WiFi.RSSI();
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  String topic = "greenhouse/" + String(zone_id) + "/heartbeat";
  client.publish(topic.c_str(), jsonString.c_str());
}

void publishDeviceInfo() {
  DynamicJsonDocument doc(1024);
  
  doc["device_id"] = device_id;
  doc["zone_id"] = zone_id;
  doc["firmware_version"] = firmware_version;
  doc["chip_id"] = ESP.getChipRevision();
  doc["mac_address"] = WiFi.macAddress();
  doc["ip_address"] = WiFi.localIP().toString();
  
  // Supported sensors
  JsonArray sensors = doc.createNestedArray("supported_sensors");
  sensors.add("air_temperature");
  sensors.add("air_humidity");
  sensors.add("soil_temperature");
  sensors.add("soil_moisture");
  sensors.add("ph_level");
  sensors.add("ec_level");
  sensors.add("light_intensity");
  sensors.add("co2_level");
  
  // Supported controls
  JsonArray controls = doc.createNestedArray("supported_controls");
  controls.add("water_pump");
  controls.add("ventilation_fan");
  controls.add("heater");
  controls.add("grow_lights");
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  String topic = "greenhouse/" + String(zone_id) + "/device_info";
  client.publish(topic.c_str(), jsonString.c_str());
}

void executeAutomaticControl() {
  // Automatic temperature control
  if (!isnan(currentData.air_temperature)) {
    if (currentData.air_temperature < controlState.target_temperature - 2.0) {
      if (!controlState.heater) {
        controlState.heater = true;
        digitalWrite(RELAY_HEATER, HIGH);
        publishControlState();
      }
    } else if (currentData.air_temperature > controlState.target_temperature + 2.0) {
      if (controlState.heater) {
        controlState.heater = false;
        digitalWrite(RELAY_HEATER, LOW);
      }
      if (!controlState.ventilation_fan) {
        controlState.ventilation_fan = true;
        digitalWrite(RELAY_FAN, HIGH);
        publishControlState();
      }
    } else {
      // Temperature in acceptable range
      if (controlState.heater) {
        controlState.heater = false;
        digitalWrite(RELAY_HEATER, LOW);
        publishControlState();
      }
      if (controlState.ventilation_fan && currentData.air_temperature < controlState.target_temperature + 1.0) {
        controlState.ventilation_fan = false;
        digitalWrite(RELAY_FAN, LOW);
        publishControlState();
      }
    }
  }
  
  // Automatic irrigation control
  if (currentData.soil_moisture < controlState.target_soil_moisture - 5.0) {
    if (!controlState.water_pump) {
      controlState.water_pump = true;
      digitalWrite(RELAY_WATER, HIGH);
      publishControlState();
      
      // Set timer to turn off water pump after 30 seconds
      // (In a real implementation, you'd want a more sophisticated approach)
    }
  }
  
  // Turn off water pump after irrigation cycle
  static unsigned long waterStartTime = 0;
  if (controlState.water_pump) {
    if (waterStartTime == 0) {
      waterStartTime = millis();
    } else if (millis() - waterStartTime > 30000) {  // 30 seconds
      controlState.water_pump = false;
      digitalWrite(RELAY_WATER, LOW);
      waterStartTime = 0;
      publishControlState();
    }
  }
}

void updateStatusLED() {
  static unsigned long lastBlink = 0;
  static bool ledState = false;
  
  if (WiFi.status() != WL_CONNECTED || !client.connected()) {
    // Fast blink for connection issues
    if (millis() - lastBlink > 250) {
      ledState = !ledState;
      digitalWrite(STATUS_LED, ledState);
      lastBlink = millis();
    }
  } else {
    // Slow blink for normal operation
    if (millis() - lastBlink > 1000) {
      ledState = !ledState;
      digitalWrite(STATUS_LED, ledState);
      lastBlink = millis();
    }
  }
}
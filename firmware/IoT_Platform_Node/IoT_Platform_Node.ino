#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <HTTPUpdate.h>
#include <WiFiClient.h>
#include <time.h>
#include <ESP32Servo.h>
#include <HTTPClient.h>
#include <WebServer.h>    // For the configuration web server
#include <DNSServer.h>    // For the captive portal
#include <Preferences.h>  // For saving WiFi credentials

// Function declarations
void connectWiFi();
void connectMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int length);
void readAndPublishSensors();
void publishHeartbeat();
void publishStatus(String status);
void handleReboot();
void handleStatusRequest();
void handleFirmwareUpdate(String url);
void handleServoAngle(int angle);
void handleRelayControl(int relayNumber, bool state);
void handleLightControl(bool state);
void handleFanControl(bool state);
void handleRealModelControl(bool state);
void handleSmartAutomation();
void testMQTTPublish(); // New test function
// WiFi Configuration Functions
bool connectToWiFi(bool initialAttempt = false);
void startAPMode();
void handleRoot();
void handleSave();
void checkButtonAndSendWebhook();
void sendGetRequest();

// WiFi Configuration - Dynamic credentials (web-based only)
char actual_ssid[33] = "";                          // Empty - requires web configuration
char actual_password[65] = "";                      // Empty - requires web configuration

// Push button pin definition for webhook
const int buttonPin = 4;  // GPIO4 for push button (in addition to existing pins)
const int LEDPin = 2;     // GPIO2 for LED (often built-in ESP32 dev board LED)

// Webhook URL
const char* webhookURL = "https://webhook.site/739356a7-2da8-4a56-a6f3-4acf162aaecb";

// AP Mode Configuration
const char* apConfigSsid = "IoTPlatform-Setup"; // Name of the AP created by ESP32
WebServer webServer(80);
DNSServer dnsServer;
bool apModeActive = false;

// Preferences for WiFi storage
Preferences preferences;
const char* PREF_NAMESPACE = "wifi-config";
const char* PREF_KEY_SSID = "ssid";
const char* PREF_KEY_PASS = "password";

// WiFi and Button State Management
bool wifiEverConnected = false;
int lastStableButtonState = HIGH;
int lastFlickerButtonState = HIGH;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;
int staReconnectFailures = 0;

// MQTT Configuration
const char* mqtt_server = "51.20.42.126";
const int mqtt_port = 1883;
const char* mqtt_user = "rnr_iot_user";
const char* mqtt_password = "rnr_iot_2025!";

// MQTT retry configuration
int mqtt_retry_count = 0;
const int MAX_MQTT_RETRIES = 3;

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

// Servo 
Servo servo;
const int servoPin = 16; // GPIO16 for servo signal
int servoAngle = 90; // Initial servo position (middle)

// Relay/Switch Configuration for intelligent control
const int relay1Pin = 2;  // GPIO2 for Relay 1 (Light control)
const int relay2Pin = 4;  // GPIO4 for Relay 2 (Fan control)
const int relay3Pin = 5;  // GPIO5 for Relay 3 (General purpose)
const int relay4Pin = 18; // GPIO18 for Relay 4 (General purpose)
const int realModelPin = 27; // GPIO27 for Real Model connection

// Device states
bool lightState = false;    // Light is OFF by default
bool fanState = false;      // Fan is OFF by default
bool relay3State = false;   // Relay 3 is OFF by default
bool relay4State = false;   // Relay 4 is OFF by default
bool realModelState = false; // Real Model is OFF by default

// Smart automation settings
bool smartModeEnabled = true;
int lightOnHour = 18;   // Turn on lights at 6 PM
int lightOffHour = 6;   // Turn off lights at 6 AM
float fanTempThreshold = 28.0; // Turn on fan if temperature > 28°C

// Gas Sensor Configuration
const int gasSensorPin = 34; // GPIO 34 for MQ gas sensor (ADC input)

// Humidity MQ Sensor Configuration
const int humidityMQPin = 25; // GPIO 25 for MQ humidity sensor (ADC input)

// Sensor simulation variables
float temperature = 20.0;
float humidity = 50.0;
int gasSensorValue = 0; // Variable to store gas sensor reading
int humidityMQValue = 0; // Variable to store MQ humidity sensor reading
float humidityMQPercent = 0.0; // Converted humidity percentage from MQ sensor
unsigned long lastSensorRead = 0;
unsigned long lastMqttReconnect = 0;
unsigned long lastServoDisplay = 0; // For periodic servo angle display
unsigned long lastHeartbeat = 0; // For periodic heartbeat/status updates
const unsigned long SENSOR_INTERVAL = 2000; // 2 seconds - reduced load
const unsigned long MQTT_RECONNECT_INTERVAL = 5000; // 5 seconds
const unsigned long SERVO_DISPLAY_INTERVAL = 10000; // 10 seconds for status display
const unsigned long HEARTBEAT_INTERVAL = 5000; // 5 seconds for connection heartbeat

// Additional sensor variables for more realistic data
float baseTemperature = 20.0;
float baseHumidity = 50.0;
unsigned long systemStartTime = 0;

void setup() {
  Serial.begin(115200);
  delay(1000); // Allow time for Serial Monitor to connect

  Serial.println("\n=== IoT Platform ESP32 Node with Smart Device Control ===");

  // Initialize button and LED pins for WiFi configuration
  pinMode(buttonPin, INPUT_PULLUP);
  pinMode(LEDPin, OUTPUT);
  digitalWrite(LEDPin, LOW); // Start with LED off

  // Initialize GPIO pins for relays
  pinMode(relay1Pin, OUTPUT);
  pinMode(relay2Pin, OUTPUT);
  pinMode(relay3Pin, OUTPUT);
  pinMode(relay4Pin, OUTPUT);
  pinMode(realModelPin, OUTPUT);
  
  // Set initial relay states (all OFF)
  digitalWrite(relay1Pin, LOW);
  digitalWrite(relay2Pin, LOW);
  digitalWrite(relay3Pin, LOW);
  digitalWrite(relay4Pin, LOW);
  digitalWrite(realModelPin, LOW);
  
  Serial.println("🔌 Relay configuration:");
  Serial.println("   - Relay 1 (Light): GPIO2 - OFF");
  Serial.println("   - Relay 2 (Fan): GPIO4 - OFF");
  Serial.println("   - Relay 3 (General): GPIO5 - OFF");
  Serial.println("   - Relay 4 (General): GPIO18 - OFF");
  Serial.println("   - Real Model: GPIO27 - OFF");

  // Initialize servo
  servo.attach(servoPin);
  servo.write(servoAngle); // Set initial position
  Serial.print("🔄 Initial servo angle: ");
  Serial.println(servoAngle);
  
  // Initialize MQ sensors
  Serial.println("📡 Initializing sensors:");
  Serial.println("   - Gas sensor on GPIO 34");
  Serial.println("   - MQ Humidity sensor on GPIO 25");
  
  // Take initial readings
  gasSensorValue = analogRead(gasSensorPin);
  humidityMQValue = analogRead(humidityMQPin);
  humidityMQPercent = map(humidityMQValue, 0, 4095, 0, 100);
  
  Serial.print("📊 Initial readings - Gas: ");
  Serial.print(gasSensorValue);
  Serial.print(", MQ Humidity: ");
  Serial.print(humidityMQPercent);
  Serial.println("%");

  // Initialize WiFi with stored credentials or AP mode
  WiFi.mode(WIFI_STA); // Start in STA mode by default

  preferences.begin(PREF_NAMESPACE, false); // false = read/write
  String stored_ssid = preferences.getString(PREF_KEY_SSID, "");
  String stored_pass = preferences.getString(PREF_KEY_PASS, "");
  preferences.end();

  if (stored_ssid.length() > 0) {
    Serial.println("Found saved WiFi credentials.");
    strncpy(actual_ssid, stored_ssid.c_str(), sizeof(actual_ssid) - 1);
    strncpy(actual_password, stored_pass.c_str(), sizeof(actual_password) - 1);
    actual_ssid[sizeof(actual_ssid) - 1] = '\0'; // Ensure null termination
    actual_password[sizeof(actual_password) - 1] = '\0';

    if (!connectToWiFi(true)) { // true = initial attempt from setup
      Serial.println("Failed to connect with saved credentials. Starting AP mode.");
      startAPMode();
    } else {
      Serial.println("Connected using saved credentials during setup.");
    }
  } else {
    Serial.println("No saved credentials found. Using default or starting AP mode.");
    if (!connectToWiFi(true)) {
      Serial.println("Failed to connect with default credentials. Starting AP mode.");
      startAPMode();
    }
  }

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

  // Setup MQTT only if WiFi is connected and not in AP mode
  if (WiFi.status() == WL_CONNECTED && !apModeActive) {
    client.setServer(mqtt_server, mqtt_port);
    client.setCallback(mqttCallback);
    client.setBufferSize(512); // Increase buffer size for larger payloads
    client.setKeepAlive(15); // Keep alive interval

    connectMQTT();

    // Test MQTT publishing immediately after connection
    delay(1000);
    testMQTTPublish();
  }

  Serial.println("=== Setup Complete ===\n");
}

void loop() {
  // Handle AP mode for WiFi configuration
  if (apModeActive) {
    dnsServer.processNextRequest();
    webServer.handleClient();
    // AP mode LED pattern: slow blink
    digitalWrite(LEDPin, (millis() / 700) % 2);
    delay(10); // Allow AP tasks to run
    return;    // Don't do STA tasks if in AP mode
  }

  // STA Mode Logic - WiFi connection management
  if (WiFi.status() != WL_CONNECTED) {
    if (wifiEverConnected) {
      Serial.println("WiFi disconnected.");
    }
    wifiEverConnected = false;
    digitalWrite(LEDPin, LOW); // Turn off LED during reconnection attempts

    static unsigned long lastTryConnectTime = 0;
    // Try to reconnect every 30 seconds if disconnected
    if (millis() - lastTryConnectTime > 30000 || lastTryConnectTime == 0) {
      Serial.println("Attempting to reconnect to WiFi...");
      if (!connectToWiFi()) { // Regular attempt, not initial
        Serial.println("Reconnect attempt failed.");
        staReconnectFailures++;
        if (staReconnectFailures > 3 && strlen(actual_ssid) > 0) { // After 3*30s fails with known creds
          Serial.println("Too many reconnection failures. Switching to AP mode to allow reconfiguration.");
          startAPMode();
          staReconnectFailures = 0; // Reset for next time
          lastTryConnectTime = millis(); // Reset timer to avoid immediate retry after AP exit
          return; // Exit loop early
        } else if (strlen(actual_ssid) == 0) { // Should not happen if logic is correct, but as a safeguard
          Serial.println("No credentials, forcing AP mode.");
          startAPMode();
          staReconnectFailures = 0;
          lastTryConnectTime = millis();
          return;
        }
      } else {
        // Successfully reconnected in loop
        staReconnectFailures = 0; // Reset on success
      }
      lastTryConnectTime = millis();
    }
  } else { // WiFi.status() == WL_CONNECTED
    staReconnectFailures = 0; // Reset failure count if connected
    if (!wifiEverConnected) {
      Serial.println("\n(Re)Connected to WiFi!");
      Serial.print("IP address: ");
      Serial.println(WiFi.localIP());
      wifiEverConnected = true;
      digitalWrite(LEDPin, HIGH); // Indicate connection success
      delay(1000);
      if (digitalRead(buttonPin) == HIGH && lastStableButtonState == HIGH) {
        digitalWrite(LEDPin, LOW); // Turn off if button not active
      }
    }
  }

  // Only proceed with MQTT and sensor operations if WiFi is connected
  if (WiFi.status() == WL_CONNECTED) {
    // Maintain MQTT connection
    if (!client.connected()) {
      if (millis() - lastMqttReconnect > MQTT_RECONNECT_INTERVAL) {
        lastMqttReconnect = millis();
        connectMQTT();
      }
    }
    client.loop();

    // Read and publish sensor data
    if (millis() - lastSensorRead > SENSOR_INTERVAL) {
      lastSensorRead = millis();
      readAndPublishSensors();
      
      // Execute smart automation after sensor readings
      if (smartModeEnabled) {
        handleSmartAutomation();
      }
    }

    // Send periodic heartbeat for real-time connection status
    if (millis() - lastHeartbeat > HEARTBEAT_INTERVAL) {
      lastHeartbeat = millis();
      publishHeartbeat();
    }

    // Handle webhook button functionality
    checkButtonAndSendWebhook();
  }

  // Continuously display servo angle and gas sensor value
  if (millis() - lastServoDisplay > SERVO_DISPLAY_INTERVAL) {
    lastServoDisplay = millis();
    Serial.println("📊 === Device Status ===");
    Serial.print("🔧 Servo angle: ");
    Serial.println(servoAngle);
    Serial.print("🌬️  Gas sensor: ");
    Serial.println(gasSensorValue);
    Serial.print("💧 MQ Humidity (GPIO25): ");
    Serial.print(humidityMQPercent);
    Serial.print("% (Raw: ");
    Serial.print(humidityMQValue);
    Serial.println(")");
    Serial.print("📡 WiFi: ");
    Serial.print(WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected");
    Serial.print(" (RSSI: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm)");
    Serial.print("🔗 MQTT: ");
    Serial.print(client.connected() ? "Connected" : "Disconnected");
    Serial.print(" (State: ");
    Serial.print(client.state());
    Serial.println(")");
    Serial.print("⏱️  Uptime: ");
    Serial.print(millis() / 1000);
    Serial.println(" seconds");
    Serial.println("========================");
  }

  delay(10); // Small delay for main loop responsiveness
}

bool connectToWiFi(bool initialAttempt) {
  if (strlen(actual_ssid) == 0) {
    if (!initialAttempt) Serial.println("connectToWiFi: No SSID configured to connect to.");
    return false;
  }

  Serial.print("Connecting to: "); 
  Serial.println(actual_ssid);
  
  // Blinking LED pattern during connection attempt
  for(int i=0; i<3; ++i) {
      digitalWrite(LEDPin, HIGH); delay(150);
      digitalWrite(LEDPin, LOW);  delay(150);
  }

  WiFi.disconnect(true); // Disconnect previous session and clear config
  WiFi.mode(WIFI_STA);   // Ensure STA mode
  WiFi.begin(actual_ssid, actual_password);

  int connectionAttempts = 0;
  // Wait up to ~15 seconds for connection
  while (WiFi.status() != WL_CONNECTED && connectionAttempts < 60) { // 60 * 250ms = 15 seconds
    digitalWrite(LEDPin, !digitalRead(LEDPin)); // Fast toggle LED
    delay(250);
    Serial.print(".");
    connectionAttempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi Connected successfully!");
    Serial.print("IP address: "); 
    Serial.println(WiFi.localIP());
    wifiEverConnected = true;
    digitalWrite(LEDPin, HIGH); // Solid LED for good connection
    return true;
  } else {
    Serial.println("\nFailed to connect to WiFi.");
    digitalWrite(LEDPin, LOW);
    WiFi.disconnect(true); // Clean up
    return false;
  }
}

void connectWiFi() {
  // Legacy function - now calls the new connectToWiFi function
  connectToWiFi(false);
}

void connectMQTT() {
  if (client.connected()) {
    mqtt_retry_count = 0; // Reset retry count on successful connection
    return;
  }

  Serial.print("Connecting to MQTT broker: ");
  Serial.print(mqtt_server);
  Serial.print(":");
  Serial.println(mqtt_port);

  String clientId = "ESP32-" + node_id;

  // Try to connect with retry logic
  if (client.connect(clientId.c_str(), mqtt_user, mqtt_password)) {
    Serial.println("MQTT connected!");
    mqtt_retry_count = 0; // Reset retry count on successful connection

    // Subscribe to command topic with QoS=1 so commands sent while device
    // is offline will be queued by the broker and delivered on reconnect.
    if (client.subscribe(command_topic.c_str(), 1)) {
      Serial.println("Subscribed to: " + command_topic + " (qos=1)");
    } else {
      Serial.println("Failed to subscribe to: " + command_topic);
    }

    // Publish initial status
    publishStatus("online");
  } else {
    mqtt_retry_count++;
    Serial.print("MQTT connection failed, rc=");
    Serial.print(client.state());
    Serial.print(", retry count: ");
    Serial.println(mqtt_retry_count);
    
    // If max retries reached, restart ESP32
    if (mqtt_retry_count >= MAX_MQTT_RETRIES) {
      Serial.println("Max MQTT retries reached. Restarting ESP32...");
      delay(2000);
      ESP.restart();
    }
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

  // Handle different commands
  if (action == "REBOOT") {
    handleReboot();
  } else if (action == "STATUS_REQUEST") {
    handleStatusRequest();
  } else if (action == "FIRMWARE_UPDATE") {
    String url = doc["url"];
    handleFirmwareUpdate(url);
  } else if (action == "SERVO_CONTROL" || action == "SERVO_ANGLE") {
    int angle = doc["angle"];
    Serial.println("🔧 Received servo control command via WiFi/MQTT");
    handleServoAngle(angle);
  } else if (action == "LIGHT_CONTROL") {
    bool state = doc["state"];
    Serial.println("💡 Received light control command via MQTT");
    handleLightControl(state);
  } else if (action == "FAN_CONTROL") {
    bool state = doc["state"];
    Serial.println("🌀 Received fan control command via MQTT");
    handleFanControl(state);
  } else if (action == "RELAY_CONTROL") {
    int relayNumber = doc["relay"];
    bool state = doc["state"];
    Serial.println("🔌 Received relay control command via MQTT");
    handleRelayControl(relayNumber, state);
  } else if (action == "REAL_MODEL_CONTROL") {
    bool state = doc["state"];
    Serial.println("🎯 Received real model control command via MQTT");
    handleRealModelControl(state);
  } else if (action == "SMART_MODE") {
    smartModeEnabled = doc["enabled"];
    Serial.print("🤖 Smart mode ");
    Serial.println(smartModeEnabled ? "ENABLED" : "DISABLED");
  } else if (action == "SET_LIGHT_SCHEDULE") {
    lightOnHour = doc["on_hour"];
    lightOffHour = doc["off_hour"];
    Serial.print("⏰ Light schedule updated: ON at ");
    Serial.print(lightOnHour);
    Serial.print(":00, OFF at ");
    Serial.print(lightOffHour);
    Serial.println(":00");
  } else {
    Serial.println("Unknown action: " + action);
  }
}

void readAndPublishSensors() {
  // Enhanced sensor simulation with more dynamic variations for fast updates
  temperature += random(-25, 26) / 100.0; // ±0.25°C variation for faster changes
  humidity += random(-100, 101) / 100.0;  // ±1% variation for more dynamic updates
  
  // Read actual gas sensor value (real data from MQ sensor)
  gasSensorValue = analogRead(gasSensorPin); // Raw analog reading from GPIO 34
  
  // Read MQ humidity sensor from GPIO 25
  humidityMQValue = analogRead(humidityMQPin); // Raw analog reading from GPIO 25
  
  // Convert MQ humidity sensor reading to percentage (0-100%)
  humidityMQPercent = map(humidityMQValue, 0, 4095, 0, 100); // Basic linear conversion
  humidityMQPercent = constrain(humidityMQPercent, 0.0, 100.0);

  // Keep simulated values in realistic ranges
  temperature = constrain(temperature, 15.0, 35.0);
  humidity = constrain(humidity, 30.0, 80.0);
  gasSensorValue = constrain(gasSensorValue, 0, 4095); // ESP32 ADC range

  // Create JSON payload
  StaticJsonDocument<250> doc; // Increased size for additional sensor data

  // Get current time
  time_t now;
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    doc["timestamp"] = "unknown";
  } else {
    char timeString[20];
    strftime(timeString, sizeof(timeString), "%H:%M:%S", &timeinfo); // Shorter timestamp
    doc["timestamp"] = timeString;
  }

  // Core sensor data - TEMPERATURE IS INCLUDED HERE
  doc["temperature"] = round(temperature * 10) / 10.0; // This is your temperature data
  doc["humidity"] = round(humidity * 10) / 10.0; // Simulated humidity
  doc["humidity_mq"] = round(humidityMQPercent * 10) / 10.0; // MQ humidity sensor from GPIO 25
  doc["humidity_mq_raw"] = humidityMQValue; // Raw ADC value from MQ sensor
  doc["gas_sensor"] = gasSensorValue;
  doc["status"] = "online";
  doc["node_id"] = node_id;
  doc["servo_angle"] = servoAngle;
  
  // Device control states
  doc["light_state"] = lightState;
  doc["fan_state"] = fanState;
  doc["relay3_state"] = relay3State;
  doc["relay4_state"] = relay4State;
  doc["real_model_state"] = realModelState;
  doc["smart_mode"] = smartModeEnabled;
  
  doc["uptime"] = millis();
  doc["wifi_rssi"] = WiFi.RSSI();

  String payload;
  serializeJson(doc, payload);

  // Check payload size
  if (payload.length() > 300) { // Increased from 256 to accommodate MQ humidity data
    Serial.println("⚠️ Payload too large: " + String(payload.length()) + " bytes");
    return;
  }

  // Publish to MQTT with multiple attempts
  bool published = false;
  for (int attempt = 0; attempt < 3 && !published; attempt++) {
    if (client.connected() && client.publish(data_topic.c_str(), payload.c_str())) {
      published = true;
      Serial.println("✅ Sensor data published (attempt " + String(attempt + 1) + "):");
      Serial.println(payload);
    } else {
      Serial.println("❌ Publish attempt " + String(attempt + 1) + " failed");
      Serial.print("MQTT Connected: ");
      Serial.println(client.connected() ? "Yes" : "No");
      Serial.print("MQTT State: ");
      Serial.println(client.state());
      
      if (!client.connected()) {
        Serial.println("🔄 Reconnecting MQTT...");
        connectMQTT();
        delay(100); // Small delay between attempts
      }
    }
  }
  
  if (!published) {
    Serial.println("❌ All publish attempts failed for sensor data");
  }
}

void publishHeartbeat() {
  // Ultra-lightweight heartbeat message
  StaticJsonDocument<100> doc; // Even smaller buffer

  doc["type"] = "heartbeat";
  doc["status"] = "online";
  doc["node_id"] = node_id;
  doc["uptime"] = millis();

  String payload;
  serializeJson(doc, payload);

  // Publish heartbeat with retry
  bool published = false;
  for (int attempt = 0; attempt < 2 && !published; attempt++) {
    if (client.connected() && client.publish(data_topic.c_str(), payload.c_str())) {
      published = true;
      Serial.println("💓 Heartbeat sent - Device Online");
    } else {
      Serial.println("❌ Heartbeat attempt " + String(attempt + 1) + " failed");
      if (!client.connected()) {
        connectMQTT();
        delay(50);
      }
    }
  }
}

void publishStatus(String status) {
  StaticJsonDocument<250> doc;

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
  doc["gas_sensor"] = gasSensorValue; // Include current gas sensor reading
  doc["signal_strength"] = map(WiFi.RSSI(), -100, -30, 0, 100); // Signal strength

  String payload;
  serializeJson(doc, payload);

  // Publish to MQTT and display to Serial Monitor
  if (client.connected() && client.publish(data_topic.c_str(), payload.c_str())) {
    Serial.println("✅ Status published: " + status);
    Serial.println(payload);
    Serial.print("Current servo angle: ");
    Serial.println(servoAngle);
    Serial.print("Gas Sensor Analog Value: ");
    Serial.println(gasSensorValue);
  } else {
    Serial.println("❌ Failed to publish status");
    Serial.print("MQTT Connected: ");
    Serial.println(client.connected() ? "Yes" : "No");
    Serial.print("MQTT State: ");
    Serial.println(client.state());
    Serial.print("Current servo angle: ");
    Serial.println(servoAngle);
    Serial.print("Gas Sensor Analog Value: ");
    Serial.println(gasSensorValue);
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
  Serial.print("🔧 Servo angle command received via WiFi: ");
  Serial.println(angle);

  // Validate angle (0–180 degrees)
  angle = constrain(angle, 0, 180);
  servoAngle = angle;
  servo.write(angle);

  // Display updated servo angle with enhanced feedback
  Serial.print("✅ Servo successfully moved to angle: ");
  Serial.print(servoAngle);
  Serial.println("° (wireless control)");

  // Publish updated status with servo confirmation
  publishStatus("servo_updated_wifi");
}

void testMQTTPublish() {
  // Simple test message to verify MQTT publishing works
  StaticJsonDocument<50> doc;
  doc["test"] = "ping";
  doc["node_id"] = node_id;
  
  String payload;
  serializeJson(doc, payload);
  
  Serial.println("🧪 Testing MQTT publish...");
  Serial.print("Payload: ");
  Serial.println(payload);
  Serial.print("Topic: ");
  Serial.println(data_topic);
  Serial.print("Client connected: ");
  Serial.println(client.connected());
  Serial.print("Client state: ");
  Serial.println(client.state());
  
  if (client.connected()) {
    if (client.publish(data_topic.c_str(), payload.c_str())) {
      Serial.println("✅ Test message published successfully");
    } else {
      Serial.println("❌ Test message publish failed");
    }
  } else {
    Serial.println("❌ MQTT client not connected");
  }
}

// === SMART DEVICE CONTROL FUNCTIONS ===

void handleLightControl(bool state) {
  lightState = state;
  digitalWrite(relay1Pin, state ? HIGH : LOW);
  Serial.print("💡 Light ");
  Serial.println(state ? "turned ON" : "turned OFF");
  
  // Publish device state update
  publishStatus(state ? "light_on" : "light_off");
}

void handleFanControl(bool state) {
  fanState = state;
  digitalWrite(relay2Pin, state ? HIGH : LOW);
  Serial.print("🌀 Fan ");
  Serial.println(state ? "turned ON" : "turned OFF");
  
  // Publish device state update
  publishStatus(state ? "fan_on" : "fan_off");
}

void handleRelayControl(int relayNumber, bool state) {
  int relayPin = -1;
  String deviceName = "";
  
  switch (relayNumber) {
    case 1:
      relayPin = relay1Pin;
      deviceName = "Light";
      lightState = state;
      break;
    case 2:
      relayPin = relay2Pin;
      deviceName = "Fan";
      fanState = state;
      break;
    case 3:
      relayPin = relay3Pin;
      deviceName = "Relay 3";
      relay3State = state;
      break;
    case 4:
      relayPin = relay4Pin;
      deviceName = "Relay 4";
      relay4State = state;
      break;
    case 5:
      relayPin = realModelPin;
      deviceName = "Real Model";
      realModelState = state;
      break;
    default:
      Serial.println("❌ Invalid relay number: " + String(relayNumber));
      return;
  }
  
  digitalWrite(relayPin, state ? HIGH : LOW);
  Serial.print("🔌 ");
  Serial.print(deviceName);
  Serial.print(" (Relay ");
  Serial.print(relayNumber);
  Serial.print(") ");
  Serial.println(state ? "turned ON" : "turned OFF");
  
  // Publish device state update
  publishStatus("relay" + String(relayNumber) + (state ? "_on" : "_off"));
}

void handleRealModelControl(bool state) {
  realModelState = state;
  digitalWrite(realModelPin, state ? HIGH : LOW);
  Serial.print("🎯 Real Model ");
  Serial.println(state ? "turned ON" : "turned OFF");
  
  // Publish device state update
  publishStatus(state ? "real_model_on" : "real_model_off");
}

void handleSmartAutomation() {
  if (!smartModeEnabled) return;
  
  // Get current time
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    return; // Skip automation if time is not available
  }
  
  int currentHour = timeinfo.tm_hour;
  
  // Smart light control based on time
  bool shouldLightBeOn = false;
  if (lightOnHour <= lightOffHour) {
    // Normal case: turn on at 18:00, off at 6:00 next day
    shouldLightBeOn = (currentHour >= lightOnHour || currentHour < lightOffHour);
  } else {
    // Edge case: spans midnight
    shouldLightBeOn = (currentHour >= lightOnHour && currentHour < lightOffHour);
  }
  
  if (shouldLightBeOn != lightState) {
    handleLightControl(shouldLightBeOn);
    Serial.print("🤖 Smart Light Control: Auto ");
    Serial.print(shouldLightBeOn ? "ON" : "OFF");
    Serial.print(" at ");
    Serial.print(currentHour);
    Serial.println(":00");
  }
  
  // Smart fan control based on temperature and humidity
  bool shouldFanBeOn = (temperature > fanTempThreshold);

  if (shouldFanBeOn != fanState) {
    handleFanControl(shouldFanBeOn);
    Serial.print("🤖 Smart Fan Control: Auto ");
    Serial.print(shouldFanBeOn ? "ON" : "OFF");
    Serial.print(" (Temp: ");
    Serial.print(temperature);
    Serial.print("°C, Humidity: ");
    Serial.print(humidity);
    Serial.println("%)");
  }
  
  // Smart gas safety control
  if (gasSensorValue > 100) { // High gas level detected
    if (!fanState) {
      handleFanControl(true);
      Serial.println("🚨 Smart Gas Safety: Fan turned ON due to high gas level!");
    }
  }
}

void sendTemperatureOnly() {
  // Update temperature value
  temperature += random(-25, 26) / 100.0;
  temperature = constrain(temperature, 15.0, 35.0);

  // Create minimal JSON with just temperature
  StaticJsonDocument<100> doc;
  doc["temperature"] = round(temperature * 10) / 10.0;
  doc["node_id"] = node_id;
  doc["timestamp"] = millis();

  String payload;
  serializeJson(doc, payload);

  // Publish to MQTT
  if (client.connected()) {
    client.publish(data_topic.c_str(), payload.c_str());
    Serial.println("🌡️ Temperature sent: " + String(temperature) + "°C");
  }
}

// === WiFi CONFIGURATION AND WEBHOOK FUNCTIONS ===

void startAPMode() {
  apModeActive = true;
  Serial.println("Starting AP Mode...");
  digitalWrite(LEDPin, LOW); // Ensure LED is off before AP pattern starts

  WiFi.disconnect(true);    // Disconnect from any STA connection
  WiFi.mode(WIFI_AP);       // Switch to AP mode
  WiFi.softAP(apConfigSsid, NULL); // SSID, NULL for an open network

  IPAddress apIP = WiFi.softAPIP();
  Serial.print("AP IP address: "); 
  Serial.println(apIP);

  // Start DNS server for captive portal
  dnsServer.setErrorReplyCode(DNSReplyCode::NoError);
  dnsServer.start(53, "*", apIP); // Port 53, domain *, resolve to AP's IP

  // Web server routes
  webServer.on("/", HTTP_GET, handleRoot);
  webServer.on("/save", HTTP_POST, handleSave);
  // For captive portal detection on various OS
  webServer.on("/generate_204", HTTP_GET, handleRoot); 
  webServer.on("/fwlink", HTTP_GET, handleRoot);       
  webServer.on("/ncsi.txt", HTTP_GET, handleRoot);     
  webServer.onNotFound(handleRoot); // Catch all

  webServer.begin();
  Serial.print("Web Server started. Connect to SSID: '");
  Serial.print(apConfigSsid);
  Serial.println("' to configure WiFi.");
}

void handleRoot() {
  String html = R"rawliteral(
<!DOCTYPE HTML><html><head>
<title>IoT Platform WiFi Setup</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f0f8ff; display: flex; justify-content: center; align-items: center; min-height: 100vh; text-align: center;}
  .container { background-color: #fff; padding: 25px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.15); max-width: 450px; width: 90%; }
  h1 { color: #005a9c; margin-bottom: 20px; }
  label { display: block; margin-bottom: 8px; font-weight: bold; color: #333; text-align: left; }
  input[type="text"], input[type="password"] { width: calc(100% - 22px); padding: 12px; margin-bottom: 20px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
  input[type="submit"] { background-color: #007bff; color: white; padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%; transition: background-color 0.3s; }
  input[type="submit"]:hover { background-color: #0056b3; }
</style>
</head><body>
<div class="container">
  <h1>IoT Platform WiFi Setup</h1>
  <form method="POST" action="/save">
    <label for="ssid">WiFi Network Name (SSID):</label>
    <input type="text" id="ssid" name="ssid" placeholder="Enter WiFi SSID" required><br>
    <label for="password">Password:</label>
    <input type="password" id="password" name="password" placeholder="Enter WiFi Password"><br>
    <input type="submit" value="Save & Connect">
  </form>
</div>
</body></html>
)rawliteral";
  webServer.send(200, "text/html", html);
}

void handleSave() {
  String new_ssid_str = webServer.arg("ssid");
  String new_pass_str = webServer.arg("password");

  Serial.println("Received new WiFi credentials via web form:");
  Serial.print("SSID: '"); Serial.print(new_ssid_str); Serial.println("'");
  Serial.println(new_pass_str.length() > 0 ? "Password: [set]" : "Password: [not set]");

  if (new_ssid_str.length() == 0 || new_ssid_str.length() > sizeof(actual_ssid) - 1) {
    String err_html = R"rawliteral(
    <!DOCTYPE HTML><html><head><title>Error</title></head><body>
    <h1>Error: Invalid SSID. It cannot be empty or too long.</h1><a href="/">Try again</a>
    </body></html>)rawliteral";
    webServer.send(400, "text/html", err_html);
    return;
  }
   if (new_pass_str.length() > sizeof(actual_password) - 1) {
    String err_html = R"rawliteral(
    <!DOCTYPE HTML><html><head><title>Error</title></head><body>
    <h1>Error: Password too long.</h1><a href="/">Try again</a>
    </body></html>)rawliteral";
    webServer.send(400, "text/html", err_html);
    return;
  }

  // Update global variables
  strncpy(actual_ssid, new_ssid_str.c_str(), sizeof(actual_ssid) - 1);
  actual_ssid[sizeof(actual_ssid) - 1] = '\0';
  strncpy(actual_password, new_pass_str.c_str(), sizeof(actual_password) - 1);
  actual_password[sizeof(actual_password) - 1] = '\0';

  // Save to Preferences
  preferences.begin(PREF_NAMESPACE, false); // false for read/write
  preferences.putString(PREF_KEY_SSID, new_ssid_str);
  preferences.putString(PREF_KEY_PASS, new_pass_str);
  preferences.end();

  Serial.println("Credentials saved to Preferences.");

  String ok_html = R"rawliteral(
<!DOCTYPE HTML><html><head><title>IoT Platform Setup</title>
<meta http-equiv="refresh" content="7;url=http://connectivitycheck.gstatic.com/generate_204">
<style> body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #e6f7ff; color: #004085;} h1 {color: #007bff;} p {font-size: 1.1em;} </style>
</head><body>
<h1>Credentials Saved!</h1><p>Attempting to connect to '<b>)rawliteral" + new_ssid_str + R"rawliteral(</b>'.</p>
<p>If connection is successful, this device will exit setup mode. You may need to reconnect your phone/computer to your regular WiFi network.</p>
<p>This page will attempt to redirect in 7 seconds to help your device recognize the network change...</p>
</body></html>
)rawliteral";
  webServer.send(200, "text/html", ok_html);
  delay(200); // Allow server to send response fully

  // Stop AP mode components
  Serial.println("Stopping AP Mode...");
  webServer.stop();
  dnsServer.stop();
  WiFi.softAPdisconnect(true); // Disconnect clients and turn off AP
  apModeActive = false;
  digitalWrite(LEDPin, LOW); // Turn off AP LED pattern

  Serial.println("Attempting to connect with new credentials...");
  staReconnectFailures = 0; // Reset as we are trying fresh credentials
  connectToWiFi(true); // Attempt connection immediately
}

void checkButtonAndSendWebhook() {
  int currentButtonReading = digitalRead(buttonPin);

  if (currentButtonReading != lastFlickerButtonState) {
    lastDebounceTime = millis();
  }
  lastFlickerButtonState = currentButtonReading;

  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (currentButtonReading != lastStableButtonState) {
      lastStableButtonState = currentButtonReading;

      if (lastStableButtonState == LOW) { // Button is pressed
        Serial.println("Button pressed!");
        if (WiFi.status() == WL_CONNECTED) {
          digitalWrite(LEDPin, HIGH); // Turn LED ON to indicate action
          sendGetRequest();
        } else {
          Serial.println("WiFi not connected. Cannot send webhook.");
          for(int i=0; i<3; ++i) { 
            digitalWrite(LEDPin, HIGH); delay(80); 
            digitalWrite(LEDPin, LOW); delay(80); 
          } // Error blink
        }
      } else { // Button is released
        Serial.println("Button released.");
        if (WiFi.status() == WL_CONNECTED) { 
            digitalWrite(LEDPin, LOW);
        }
      }
    }
  }
}

void sendGetRequest() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("sendGetRequest: WiFi not connected. Aborting.");
    return;
  }

  HTTPClient http;
  Serial.print("Sending GET request to: "); 
  Serial.println(webhookURL);

  http.begin(webhookURL); // HTTP
  int httpResponseCode = http.GET();

  if (httpResponseCode > 0) {
    Serial.print("HTTP Response code: "); 
    Serial.println(httpResponseCode);
    String payload = http.getString();
    Serial.println("Response payload: "); 
    Serial.println(payload);
  } else {
    Serial.print("Error on sending GET request. HTTP Response code: "); 
    Serial.println(httpResponseCode);
    Serial.printf("HTTPClient error: %s\n", http.errorToString(httpResponseCode).c_str());
  }
  http.end();
}
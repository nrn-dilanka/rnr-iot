# Data Queue Communication Guide

## 📨 Send Data to Queue and Retrieve from Other Side

This guide shows you how to implement reliable message queuing between your ESP32 and backend services using RabbitMQ queues.

---

## 🔄 **Queue-Based Communication Flow**

```
ESP32 → RabbitMQ Queue → Backend Consumer → Process Data → Response Queue → ESP32
```

### **Bidirectional Queue Communication:**

1. **ESP32 sends data** → Queue A → **Backend receives**
2. **Backend processes** → Queue B → **ESP32 receives response**

---

## 🚀 **Implementation: ESP32 Side**

### **1. Enhanced ESP32 Queue Publisher**

Add this to your `IoT_Platform_Node.ino`:

```cpp
// Queue Configuration
const char* data_queue = "esp32_sensor_data";
const char* command_queue = "esp32_commands";
const char* response_queue = "esp32_responses";

// Queue message structure
struct QueueMessage {
  String messageId;
  String timestamp;
  String data;
  String queueName;
  int priority;
};

// Send data to specific queue
bool sendToQueue(String queueName, String data, int priority = 1) {
  StaticJsonDocument<300> doc;

  // Generate unique message ID
  String messageId = "msg_" + String(millis()) + "_" + String(random(1000, 9999));

  // Create queue message
  doc["message_id"] = messageId;
  doc["timestamp"] = getTimeString();
  doc["queue_name"] = queueName;
  doc["priority"] = priority;
  doc["sender"] = "ESP32_" + node_id;
  doc["data"] = data;

  String payload;
  serializeJson(doc, payload);

  // Send to RabbitMQ queue topic
  String queueTopic = "queue/" + queueName;

  bool sent = false;
  for (int attempt = 0; attempt < 3; attempt++) {
    if (client.connected() && client.publish(queueTopic.c_str(), payload.c_str(), true)) {
      sent = true;
      Serial.println("📤 Sent to queue '" + queueName + "': " + messageId);
      Serial.println("📋 Data: " + data);
      break;
    } else {
      Serial.println("❌ Queue send attempt " + String(attempt + 1) + " failed");
      delay(1000);
    }
  }

  return sent;
}

// Send sensor data to queue
void sendSensorDataToQueue() {
  // Create sensor data payload
  StaticJsonDocument<200> sensorDoc;
  sensorDoc["temperature"] = temperature;
  sensorDoc["humidity"] = humidity;
  sensorDoc["gas_sensor"] = gasSensorValue;
  sensorDoc["node_id"] = node_id;
  sensorDoc["wifi_rssi"] = WiFi.RSSI();
  sensorDoc["uptime"] = millis();

  String sensorData;
  serializeJson(sensorDoc, sensorData);

  // Send to sensor data queue
  sendToQueue("sensor_data", sensorData, 1);
}

// Send alert to high-priority queue
void sendAlertToQueue(String alertType, String message) {
  StaticJsonDocument<150> alertDoc;
  alertDoc["alert_type"] = alertType;
  alertDoc["message"] = message;
  alertDoc["severity"] = "high";
  alertDoc["node_id"] = node_id;

  String alertData;
  serializeJson(alertDoc, alertData);

  // Send to high-priority alert queue
  sendToQueue("alerts", alertData, 10); // High priority
}

// Request data from backend via queue
void requestDataFromQueue(String requestType) {
  StaticJsonDocument<100> requestDoc;
  requestDoc["request_type"] = requestType;
  requestDoc["node_id"] = node_id;
  requestDoc["response_queue"] = "esp32_responses_" + node_id;

  String requestData;
  serializeJson(requestDoc, requestData);

  sendToQueue("data_requests", requestData, 5);
}
```

### **2. Enhanced MQTT Callback for Queue Responses**

Update your MQTT callback to handle queue responses:

```cpp
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.println("📨 Message received on topic: " + String(topic));
  Serial.println("📏 Message length: " + String(length) + " bytes");
  Serial.println("📋 Message content: " + message);

  // Check if this is a queue response
  if (String(topic).startsWith("queue/responses/")) {
    handleQueueResponse(message);
    return;
  }

  // Handle regular commands
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, message);

  if (error) {
    Serial.println("❌ JSON parsing failed: " + String(error.c_str()));
    return;
  }

  String action = doc["action"];

  if (action == "LIGHT_CONTROL") {
    bool state = doc["state"];
    handleLightControl(state);
  }
  // ... other command handlers
}

// Handle responses from backend queues
void handleQueueResponse(String response) {
  StaticJsonDocument<300> doc;
  DeserializationError error = deserializeJson(doc, response);

  if (error) {
    Serial.println("❌ Queue response parsing failed");
    return;
  }

  String messageId = doc["message_id"];
  String responseType = doc["response_type"];
  String data = doc["data"];

  Serial.println("📬 Queue response received:");
  Serial.println("🆔 Message ID: " + messageId);
  Serial.println("📂 Type: " + responseType);
  Serial.println("📄 Data: " + data);

  // Process different response types
  if (responseType == "config_update") {
    // Update ESP32 configuration
    processConfigUpdate(data);
  } else if (responseType == "command_batch") {
    // Process batch of commands
    processBatchCommands(data);
  } else if (responseType == "status_request") {
    // Send status update
    sendStatusToQueue();
  }
}
```

### **3. Enhanced Setup for Queue Subscriptions**

Update your MQTT connection to subscribe to response queues:

```cpp
void connectMQTT() {
  while (!client.connected()) {
    Serial.print("🔄 Attempting RabbitMQ MQTT connection...");

    String clientId = "ESP32-" + node_id;

    if (client.connect(clientId.c_str(), mqtt_user, mqtt_password,
                       last_topic.c_str(), 1, true, "offline", false)) {

      Serial.println(" ✅ Connected to RabbitMQ MQTT broker!");

      // Subscribe to regular commands
      client.subscribe(command_topic.c_str(), 1);
      Serial.println("📡 Subscribed to: " + command_topic);

      // Subscribe to queue responses
      String responseQueue = "queue/responses/" + node_id;
      client.subscribe(responseQueue.c_str(), 1);
      Serial.println("📨 Subscribed to queue responses: " + responseQueue);

      // Subscribe to broadcast queue
      client.subscribe("queue/broadcast", 1);
      Serial.println("📢 Subscribed to broadcast queue");

    } else {
      Serial.print(" ❌ Connection failed, rc=");
      Serial.println(client.state());
      delay(5000);
    }
  }
}
```

---

## 🖥️ **Backend Queue Consumer Implementation**

### **1. Enhanced RabbitMQ Queue Manager**

Create `backend/api/queue_manager.py`:

```python
import pika
import json
import time
from datetime import datetime
import threading
import logging

class QueueManager:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queues = {
            'sensor_data': {'durable': True, 'priority': False},
            'alerts': {'durable': True, 'priority': True},
            'data_requests': {'durable': True, 'priority': True},
            'esp32_responses': {'durable': True, 'priority': False},
            'broadcast': {'durable': True, 'priority': False}
        }
        self.consumers = {}

    def connect(self):
        """Connect to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials('rnr_iot_user', 'rnr_iot_2025!')
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost', 5672, '/', credentials)
            )
            self.channel = self.connection.channel()

            # Declare all queues
            for queue_name, config in self.queues.items():
                self.channel.queue_declare(
                    queue=queue_name,
                    durable=config['durable'],
                    arguments={'x-max-priority': 10} if config['priority'] else None
                )

            print("✅ Connected to RabbitMQ for queue management")
            return True

        except Exception as e:
            print(f"❌ Failed to connect to RabbitMQ: {e}")
            return False

    def send_to_queue(self, queue_name, data, priority=1):
        """Send data to specific queue"""
        try:
            if not self.channel:
                self.connect()

            message = {
                'message_id': f"backend_{int(time.time())}_{priority}",
                'timestamp': datetime.now().isoformat(),
                'queue_name': queue_name,
                'priority': priority,
                'sender': 'backend_api',
                'data': data
            }

            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    priority=priority,
                    delivery_mode=2  # Make message persistent
                )
            )

            print(f"📤 Sent to queue '{queue_name}': {message['message_id']}")
            return True

        except Exception as e:
            print(f"❌ Failed to send to queue '{queue_name}': {e}")
            return False

    def consume_queue(self, queue_name, callback):
        """Start consuming from specific queue"""
        try:
            if not self.channel:
                self.connect()

            def wrapper(ch, method, properties, body):
                try:
                    data = json.loads(body.decode())
                    print(f"📨 Received from queue '{queue_name}': {data.get('message_id', 'unknown')}")

                    # Process message
                    result = callback(data)

                    # Acknowledge message
                    ch.basic_ack(delivery_tag=method.delivery_tag)

                    if result:
                        print(f"✅ Successfully processed message from '{queue_name}'")
                    else:
                        print(f"⚠️ Message processing returned false for '{queue_name}'")

                except Exception as e:
                    print(f"❌ Error processing message from '{queue_name}': {e}")
                    # Reject message and requeue
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(queue=queue_name, on_message_callback=wrapper)

            print(f"📡 Started consuming from queue: {queue_name}")

            # Start consuming in separate thread
            def consume_loop():
                self.channel.start_consuming()

            consumer_thread = threading.Thread(target=consume_loop)
            consumer_thread.daemon = True
            consumer_thread.start()

            self.consumers[queue_name] = consumer_thread
            return True

        except Exception as e:
            print(f"❌ Failed to start consuming from '{queue_name}': {e}")
            return False

    def send_response_to_esp32(self, node_id, response_type, data):
        """Send response back to ESP32"""
        response_queue = f"esp32_responses_{node_id}"

        response_data = {
            'response_type': response_type,
            'target_node': node_id,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }

        return self.send_to_queue(response_queue, response_data, priority=5)

    def broadcast_to_all_esp32(self, message_type, data):
        """Broadcast message to all ESP32 devices"""
        broadcast_data = {
            'message_type': message_type,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'sender': 'backend_broadcast'
        }

        return self.send_to_queue('broadcast', broadcast_data, priority=3)

# Global queue manager instance
queue_manager = QueueManager()
```

### **2. Queue Message Processors**

Create `backend/api/queue_processors.py`:

```python
import json
from datetime import datetime
from queue_manager import queue_manager

def process_sensor_data(message):
    """Process sensor data from ESP32"""
    try:
        data = message.get('data', {})
        node_id = data.get('node_id', 'unknown')

        print(f"🌡️ Processing sensor data from {node_id}:")
        print(f"   Temperature: {data.get('temperature', 'N/A')}°C")
        print(f"   Humidity: {data.get('humidity', 'N/A')}%")
        print(f"   Gas Sensor: {data.get('gas_sensor', 'N/A')}")

        # Store in database (implement your database logic here)
        # save_sensor_data_to_db(data)

        # Send acknowledgment back to ESP32
        response_data = {
            'status': 'received',
            'message_id': message.get('message_id'),
            'processed_at': datetime.now().isoformat()
        }

        queue_manager.send_response_to_esp32(node_id, 'data_ack', response_data)

        return True

    except Exception as e:
        print(f"❌ Error processing sensor data: {e}")
        return False

def process_alert(message):
    """Process alert from ESP32"""
    try:
        data = message.get('data', {})
        node_id = data.get('node_id', 'unknown')
        alert_type = data.get('alert_type', 'unknown')
        alert_message = data.get('message', 'No message')

        print(f"🚨 ALERT from {node_id}:")
        print(f"   Type: {alert_type}")
        print(f"   Message: {alert_message}")

        # Handle different alert types
        if alert_type == 'temperature':
            handle_temperature_alert(data)
        elif alert_type == 'gas':
            handle_gas_alert(data)

        # Send alert response
        response_data = {
            'alert_received': True,
            'action_taken': 'logged_and_processed',
            'timestamp': datetime.now().isoformat()
        }

        queue_manager.send_response_to_esp32(node_id, 'alert_ack', response_data)

        return True

    except Exception as e:
        print(f"❌ Error processing alert: {e}")
        return False

def process_data_request(message):
    """Process data request from ESP32"""
    try:
        data = message.get('data', {})
        node_id = data.get('node_id', 'unknown')
        request_type = data.get('request_type', 'unknown')

        print(f"📝 Data request from {node_id}: {request_type}")

        # Handle different request types
        if request_type == 'config':
            config_data = get_esp32_config(node_id)
            queue_manager.send_response_to_esp32(node_id, 'config_update', config_data)

        elif request_type == 'commands':
            pending_commands = get_pending_commands(node_id)
            queue_manager.send_response_to_esp32(node_id, 'command_batch', pending_commands)

        elif request_type == 'status':
            status_data = {'requested_status': 'send_full_status'}
            queue_manager.send_response_to_esp32(node_id, 'status_request', status_data)

        return True

    except Exception as e:
        print(f"❌ Error processing data request: {e}")
        return False

def handle_temperature_alert(data):
    """Handle temperature alerts"""
    temp = data.get('temperature', 0)
    if temp > 30:
        print("🔥 High temperature detected - activating cooling")
        # Send cooling command
        cooling_command = {
            'action': 'FAN_CONTROL',
            'state': True,
            'reason': 'temperature_alert'
        }
        node_id = data.get('node_id')
        queue_manager.send_response_to_esp32(node_id, 'command', cooling_command)

def handle_gas_alert(data):
    """Handle gas sensor alerts"""
    gas_level = data.get('gas_sensor', 0)
    if gas_level > 2000:
        print("💨 High gas levels detected - activating ventilation")
        # Send ventilation command
        ventilation_command = {
            'action': 'FAN_CONTROL',
            'state': True,
            'reason': 'gas_alert'
        }
        node_id = data.get('node_id')
        queue_manager.send_response_to_esp32(node_id, 'command', ventilation_command)

def get_esp32_config(node_id):
    """Get configuration for specific ESP32"""
    return {
        'sensor_interval': 1000,
        'heartbeat_interval': 30000,
        'alert_thresholds': {
            'temperature_max': 30,
            'gas_max': 2000,
            'humidity_max': 80
        }
    }

def get_pending_commands(node_id):
    """Get pending commands for ESP32"""
    return [
        {'action': 'LIGHT_CONTROL', 'state': True},
        {'action': 'SERVO_CONTROL', 'angle': 45}
    ]
```

### **3. Start Queue Consumers**

Create `backend/api/start_queue_consumers.py`:

```python
#!/usr/bin/env python3
"""
Start all queue consumers for processing ESP32 messages
"""
from queue_manager import queue_manager
from queue_processors import process_sensor_data, process_alert, process_data_request
import time

def main():
    print("🚀 Starting Queue Consumers...")

    # Connect to RabbitMQ
    if not queue_manager.connect():
        print("❌ Failed to connect to RabbitMQ")
        return

    # Start consumers for different queues
    consumers = [
        ('sensor_data', process_sensor_data),
        ('alerts', process_alert),
        ('data_requests', process_data_request)
    ]

    for queue_name, processor in consumers:
        if queue_manager.consume_queue(queue_name, processor):
            print(f"✅ Started consumer for queue: {queue_name}")
        else:
            print(f"❌ Failed to start consumer for queue: {queue_name}")

    print("\n📡 All queue consumers started. Waiting for messages...")
    print("Press Ctrl+C to stop")

    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n⚠️ Stopping queue consumers...")

if __name__ == "__main__":
    main()
```

---

## 🎯 **Usage Examples**

### **1. ESP32 Sending Sensor Data to Queue**

```cpp
// In your main loop
void loop() {
  static unsigned long lastQueueSend = 0;

  if (millis() - lastQueueSend >= 5000) { // Every 5 seconds
    sendSensorDataToQueue();
    lastQueueSend = millis();
  }
}
```

### **2. ESP32 Sending High-Priority Alert**

```cpp
// When temperature is too high
if (temperature > 30.0) {
  sendAlertToQueue("temperature", "Temperature critical: " + String(temperature) + "°C");
}

// When gas levels are dangerous
if (gasSensorValue > 2000) {
  sendAlertToQueue("gas", "Gas levels dangerous: " + String(gasSensorValue));
}
```

### **3. ESP32 Requesting Data from Backend**

```cpp
// Request configuration update
requestDataFromQueue("config");

// Request pending commands
requestDataFromQueue("commands");

// Request status update
requestDataFromQueue("status");
```

### **4. Backend Sending Response to ESP32**

```python
# Send configuration to ESP32
config_data = {
    'sensor_interval': 2000,
    'alert_thresholds': {'temp_max': 35}
}
queue_manager.send_response_to_esp32("AABBCCDDEEFF", "config_update", config_data)

# Send command to ESP32
command_data = {
    'action': 'LIGHT_CONTROL',
    'state': True,
    'duration': 5000
}
queue_manager.send_response_to_esp32("AABBCCDDEEFF", "command", command_data)
```

---

## 🔧 **How to Run the Queue System**

### **1. Start RabbitMQ**

```bash
docker-compose up -d
```

### **2. Start Backend Queue Consumers**

```bash
cd backend/api
python start_queue_consumers.py
```

### **3. Flash ESP32 with Enhanced Firmware**

Upload the enhanced `IoT_Platform_Node.ino` with queue functions

### **4. Monitor Queue Activity**

- **RabbitMQ Management**: `http://localhost:15672`
- **Backend Console**: Shows queue processing messages
- **ESP32 Serial**: Shows queue sending/receiving messages

---

## 📊 **Queue Message Flow**

```
ESP32 Sensor Data → sensor_data Queue → Backend Processor → Database
ESP32 Alert → alerts Queue → Backend Processor → Response Queue → ESP32
ESP32 Request → data_requests Queue → Backend Processor → Response Queue → ESP32
Backend Command → esp32_responses Queue → ESP32 Command Handler
```

This queue-based system provides **reliable, persistent message delivery** between your ESP32 and backend services! 🚀📨

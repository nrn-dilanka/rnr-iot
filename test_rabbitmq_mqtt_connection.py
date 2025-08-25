#!/usr/bin/env python3
"""
RNR Solutions - RabbitMQ MQTT Connection Test
This script tests the MQTT connection to RabbitMQ and simulates ESP32 data transmission.
"""

import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime

# RabbitMQ MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USERNAME = "rnr_iot_user"
MQTT_PASSWORD = "rnr_iot_2025!"
MQTT_KEEPALIVE = 60

# Test device configuration
TEST_NODE_ID = "TEST_ESP32_001"
DATA_TOPIC = f"devices/{TEST_NODE_ID}/data"
COMMAND_TOPIC = f"devices/{TEST_NODE_ID}/commands"
STATUS_TOPIC = f"devices/{TEST_NODE_ID}/status"

def on_connect(client, userdata, flags, rc):
    """Callback for when the client receives a CONNECT response from the server."""
    if rc == 0:
        print("✅ Connected to RabbitMQ MQTT broker successfully!")
        print(f"📡 Connection flags: {flags}")
        
        # Subscribe to command topic to test bidirectional communication
        client.subscribe(COMMAND_TOPIC, qos=1)
        print(f"📥 Subscribed to: {COMMAND_TOPIC}")
        
        # Publish initial status
        status_payload = {
            "status": "online",
            "node_id": TEST_NODE_ID,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "test_mode": True
        }
        client.publish(STATUS_TOPIC, json.dumps(status_payload), qos=1, retain=True)
        print(f"📤 Published initial status to: {STATUS_TOPIC}")
        
    else:
        print(f"❌ Failed to connect to RabbitMQ MQTT broker. Return code: {rc}")
        error_messages = {
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorized"
        }
        if rc in error_messages:
            print(f"   Error: {error_messages[rc]}")

def on_message(client, userdata, msg):
    """Callback for when a PUBLISH message is received from the server."""
    print(f"📨 Received message on topic: {msg.topic}")
    try:
        payload = json.loads(msg.payload.decode())
        print(f"   Message: {json.dumps(payload, indent=2)}")
    except json.JSONDecodeError:
        print(f"   Raw message: {msg.payload.decode()}")

def on_publish(client, userdata, mid):
    """Callback for when a message is published."""
    print(f"✅ Message published successfully (Message ID: {mid})")

def on_disconnect(client, userdata, rc):
    """Callback for when the client disconnects from the server."""
    if rc != 0:
        print(f"⚠️  Unexpected disconnection from RabbitMQ MQTT broker. RC: {rc}")
    else:
        print("👋 Disconnected from RabbitMQ MQTT broker.")

def generate_sensor_data():
    """Generate simulated sensor data similar to ESP32."""
    return {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "temperature": round(random.uniform(18.0, 32.0), 1),
        "humidity": round(random.uniform(40.0, 80.0), 1),
        "humidity_mq": round(random.uniform(35.0, 75.0), 1),
        "humidity_mq_raw": random.randint(1500, 3500),
        "gas_sensor": random.randint(100, 2000),
        "status": "online",
        "node_id": TEST_NODE_ID,
        "servo_angle": random.choice([0, 45, 90, 135, 180]),
        "light_state": random.choice([True, False]),
        "fan_state": random.choice([True, False]),
        "relay3_state": random.choice([True, False]),
        "relay4_state": random.choice([True, False]),
        "real_model_state": random.choice([True, False]),
        "smart_mode": True,
        "uptime": random.randint(10000, 500000),
        "wifi_rssi": random.randint(-80, -30),
        "test_data": True
    }

def main():
    print("=" * 60)
    print("    RNR IoT Platform - RabbitMQ MQTT Test")
    print("=" * 60)
    print()
    
    # Create MQTT client
    client = mqtt.Client(client_id=f"TestClient_{TEST_NODE_ID}")
    
    # Set username and password
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    
    try:
        print(f"🔗 Connecting to RabbitMQ MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
        
        # Start the network loop in a separate thread
        client.loop_start()
        
        print("🧪 Starting sensor data simulation...")
        print("📊 Publishing test data every 3 seconds...")
        print("🛑 Press Ctrl+C to stop")
        print()
        
        message_count = 0
        
        while True:
            # Generate and publish sensor data
            sensor_data = generate_sensor_data()
            payload = json.dumps(sensor_data)
            
            result = client.publish(DATA_TOPIC, payload, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                message_count += 1
                print(f"📤 Message #{message_count} sent to RabbitMQ:")
                print(f"   Topic: {DATA_TOPIC}")
                print(f"   Temperature: {sensor_data['temperature']}°C")
                print(f"   Humidity: {sensor_data['humidity']}%")
                print(f"   Gas Sensor: {sensor_data['gas_sensor']}")
                print(f"   Light: {'ON' if sensor_data['light_state'] else 'OFF'}")
                print(f"   Fan: {'ON' if sensor_data['fan_state'] else 'OFF'}")
                print()
            else:
                print(f"❌ Failed to publish message. Error code: {result.rc}")
            
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
    except ConnectionRefusedError:
        print("❌ Connection refused. Is RabbitMQ running?")
        print("   Try: docker-compose up -d rnr_rabbitmq")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        print("🧹 Cleaning up...")
        
        # Publish offline status
        offline_status = {
            "status": "offline",
            "node_id": TEST_NODE_ID,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "test_mode": True
        }
        client.publish(STATUS_TOPIC, json.dumps(offline_status), qos=1, retain=True)
        
        client.loop_stop()
        client.disconnect()
        print("✅ Test completed")

if __name__ == "__main__":
    main()

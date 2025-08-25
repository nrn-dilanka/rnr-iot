#!/usr/bin/env python3
"""
Simple MQTT test script to verify connectivity and debug ESP32 issues
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

# MQTT Configuration
MQTT_BROKER = "16.171.30.3"
MQTT_PORT = 1883
MQTT_USER = "rnr_iot_user"
MQTT_PASSWORD = "rnr_iot_2025!"
TOPIC = "devices/441793F9456C/data"

def on_connect(client, userdata, flags, rc):
    print(f"🔗 Connected to MQTT broker with result code {rc}")
    if rc == 0:
        print(f"✅ Successfully connected to {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(TOPIC)
        print(f"📡 Subscribed to topic: {TOPIC}")
    else:
        print(f"❌ Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        # Decode message
        payload = msg.payload.decode()
        data = json.loads(payload)
        
        # Get timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Parse message type
        msg_type = data.get('type', 'sensor_data')
        node_id = data.get('node_id', 'unknown')
        status = data.get('status', 'unknown')
        
        if msg_type == 'heartbeat':
            print(f"💓 [{timestamp}] HEARTBEAT from {node_id} - Status: {status}")
            print(f"   ⏱️ Uptime: {data.get('uptime', 0)/1000:.1f}s, RSSI: {data.get('wifi_rssi', 0)} dBm")
        else:
            print(f"📊 [{timestamp}] SENSOR DATA from {node_id} - Status: {status}")
            print(f"   🌡️ Temp: {data.get('temperature', 'N/A')}°C, 💧 Humidity: {data.get('humidity', 'N/A')}%")
            print(f"   🌬️ Gas: {data.get('gas_sensor', 'N/A')}, 🔧 Servo: {data.get('servo_angle', 'N/A')}°")
            print(f"   📡 RSSI: {data.get('wifi_rssi', 'N/A')} dBm, 🔋 Heap: {data.get('free_heap', 'N/A')} bytes")
        
        print(f"   📨 Raw: {payload}")
        print("-" * 80)
        
    except json.JSONDecodeError:
        print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] Invalid JSON: {msg.payload.decode()}")
    except Exception as e:
        print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] Error processing message: {e}")

def on_disconnect(client, userdata, rc):
    print(f"🔌 Disconnected from MQTT broker with result code {rc}")

def main():
    print("🚀 Starting MQTT Test Client for ESP32 Debugging")
    print(f"🎯 Target: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"📡 Topic: {TOPIC}")
    print("=" * 80)
    
    # Create MQTT client
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    try:
        # Connect to broker
        print(f"🔗 Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Start loop
        print("👂 Listening for messages... Press Ctrl+C to stop")
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping MQTT test client...")
        client.disconnect()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test MQTT command publishing to ESP32
"""
import paho.mqtt.client as mqtt
import json
import time

# MQTT settings
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_USER = "iotuser"
MQTT_PASSWORD = "iotpassword"
NODE_ID = "441793F9456C"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT broker")
        
        # Send firmware update command
        command_topic = f"devices/{NODE_ID}/commands"
        command = {
            "action": "FIRMWARE_UPDATE",
            "url": "http://192.168.8.108:8000/uploads/firmware_v1.1.2.bin"
        }
        
        result = client.publish(command_topic, json.dumps(command))
        print(f"📤 Sent firmware update command to {command_topic}")
        print(f"🔗 URL: {command['url']}")
        print(f"📊 Result: {result}")
        
        # Send a simple reboot command too
        time.sleep(2)
        reboot_command = {"action": "REBOOT"}
        result2 = client.publish(command_topic, json.dumps(reboot_command))
        print(f"📤 Sent reboot command: {result2}")
        
    else:
        print(f"❌ Failed to connect to MQTT broker: {rc}")

def on_publish(client, userdata, mid):
    print(f"✅ Message {mid} published successfully")

# Create MQTT client
client = mqtt.Client()
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_publish = on_publish

print("🔄 Connecting to MQTT broker...")
client.connect(MQTT_HOST, MQTT_PORT, 60)

# Keep connected for a few seconds
client.loop_start()
time.sleep(5)
client.loop_stop()
client.disconnect()
print("🔌 Disconnected from MQTT broker")

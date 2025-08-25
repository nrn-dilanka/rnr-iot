"""
Enhanced ESP32 Firmware Deployment Script
This script provides a working firmware deployment mechanism using MQTT directly.
"""
import paho.mqtt.client as mqtt
import json
import time
import requests

# Configuration
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_USER = "iotuser"
MQTT_PASSWORD = "iotpassword"
API_BASE_URL = "http://localhost:8000"

def send_firmware_update(device_id, firmware_version):
    """Send firmware update command via MQTT"""
    
    # Get firmware information from API
    response = requests.get(f"{API_BASE_URL}/api/firmware")
    firmwares = response.json()
    
    # Find the requested firmware
    firmware = None
    for fw in firmwares:
        if fw["version"] == firmware_version:
            firmware = fw
            break
    
    if not firmware:
        print(f"❌ Firmware version {firmware_version} not found")
        return False
    
    # Prepare the command with the correct URL
    firmware_url = f"http://192.168.8.108:8000{firmware['file_url']}"
    command = {
        "action": "FIRMWARE_UPDATE",
        "url": firmware_url
    }
    
    print(f"📦 Firmware: {firmware['file_name']}")
    print(f"🔗 URL: {firmware_url}")
    
    # Setup MQTT client
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connected to MQTT broker")
            
            # Send firmware update command
            topic = f"devices/{device_id}/commands"
            message = json.dumps(command)
            
            result = client.publish(topic, message, qos=1)
            print(f"📤 Firmware update command sent to device {device_id}")
            print(f"📊 MQTT Result: {result}")
            
            # Disconnect after sending
            client.disconnect()
            
        else:
            print(f"❌ Failed to connect to MQTT broker: {rc}")
    
    def on_publish(client, userdata, mid):
        print(f"✅ Message {mid} published successfully")
    
    client.on_connect = on_connect
    client.on_publish = on_publish
    
    print("🔄 Connecting to MQTT broker...")
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_forever()
    
    return True

def list_available_firmware():
    """List all available firmware versions"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/firmware")
        firmwares = response.json()
        
        print("📦 Available Firmware Versions:")
        for fw in firmwares:
            print(f"  - Version: {fw['version']}")
            print(f"    File: {fw['file_name']}")
            print(f"    Uploaded: {fw['uploaded_at']}")
            print()
            
        return firmwares
    except Exception as e:
        print(f"❌ Error fetching firmware: {e}")
        return []

def list_nodes():
    """List all registered nodes"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/nodes")
        nodes = response.json()
        
        print("🔌 Registered Nodes:")
        for node in nodes:
            print(f"  - ID: {node['node_id']}")
            print(f"    Name: {node['name']}")
            print(f"    Last Seen: {node.get('last_seen', 'Never')}")
            print()
            
        return nodes
    except Exception as e:
        print(f"❌ Error fetching nodes: {e}")
        return []

if __name__ == "__main__":
    print("=== ESP32 Firmware Deployment Tool ===\n")
    
    # List available resources
    firmwares = list_available_firmware()
    nodes = list_nodes()
    
    if not firmwares:
        print("❌ No firmware versions available")
        exit(1)
    
    if not nodes:
        print("❌ No nodes registered")
        exit(1)
    
    # Deploy firmware
    device_id = "441793F9456C"  # Your ESP32 device ID
    firmware_version = "1.1.2"  # The firmware version to deploy
    
    print(f"🚀 Deploying firmware v{firmware_version} to device {device_id}...")
    success = send_firmware_update(device_id, firmware_version)
    
    if success:
        print("✅ Firmware deployment command sent successfully!")
        print("📡 Check your ESP32 serial monitor for update progress.")
    else:
        print("❌ Firmware deployment failed!")

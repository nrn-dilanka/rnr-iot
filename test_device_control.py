#!/usr/bin/env python3
"""
Test script for ESP32 intelligent device control
"""
import requests
import time
import json

API_BASE = "http://localhost:8000/api"

def test_device_control():
    """Test ESP32 device control commands"""
    
    print("🤖 Testing ESP32 Intelligent Device Control")
    print("=" * 50)
    
    # Device ID from your ESP32
    device_id = "441793F9456C"
    
    test_commands = [
        {
            "name": "Light ON",
            "command": {"action": "LIGHT_CONTROL", "state": True}
        },
        {
            "name": "Light OFF", 
            "command": {"action": "LIGHT_CONTROL", "state": False}
        },
        {
            "name": "Fan ON",
            "command": {"action": "FAN_CONTROL", "state": True}
        },
        {
            "name": "Fan OFF",
            "command": {"action": "FAN_CONTROL", "state": False}
        },
        {
            "name": "Relay 3 ON",
            "command": {"action": "RELAY_CONTROL", "relay": 3, "state": True}
        },
        {
            "name": "Relay 3 OFF",
            "command": {"action": "RELAY_CONTROL", "relay": 3, "state": False}
        },
        {
            "name": "Enable Smart Mode",
            "command": {"action": "SMART_MODE", "enabled": True}
        },
        {
            "name": "Set Light Schedule",
            "command": {"action": "SET_LIGHT_SCHEDULE", "on_hour": 18, "off_hour": 6}
        },
        {
            "name": "Servo Control",
            "command": {"action": "SERVO_CONTROL", "angle": 45}
        }
    ]
    
    for test in test_commands:
        print(f"\n🔧 Testing: {test['name']}")
        print(f"Command: {json.dumps(test['command'], indent=2)}")
        
        try:
            response = requests.post(
                f"{API_BASE}/esp32/command/{device_id}",
                json=test['command'],
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SUCCESS: {result.get('message', 'Command sent')}")
            else:
                print(f"❌ FAILED: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ CONNECTION ERROR: {e}")
        
        # Wait between commands
        time.sleep(2)
    
    print("\n🔍 Checking device status...")
    try:
        response = requests.get(f"{API_BASE}/sensor-data?limit=5")
        if response.status_code == 200:
            data = response.json()
            if data:
                latest = data[0]['data']
                print(f"Latest device states:")
                print(f"  💡 Light: {'ON' if latest.get('light_state') else 'OFF'}")
                print(f"  🌀 Fan: {'ON' if latest.get('fan_state') else 'OFF'}")
                print(f"  🔌 Relay 3: {'ON' if latest.get('relay3_state') else 'OFF'}")
                print(f"  🔌 Relay 4: {'ON' if latest.get('relay4_state') else 'OFF'}")
                print(f"  🤖 Smart Mode: {'ENABLED' if latest.get('smart_mode') else 'DISABLED'}")
                print(f"  🌡️  Temperature: {latest.get('temperature', 'N/A')}°C")
                print(f"  💧 Humidity: {latest.get('humidity', 'N/A')}%")
        else:
            print(f"❌ Failed to get sensor data: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting sensor data: {e}")

if __name__ == "__main__":
    test_device_control()

#!/usr/bin/env python3
"""
Real-time Sensor Data Generator for IoT Dashboard Testing
Generates simulated sensor data and sends it via MQTT to the platform.
This script mimics the data sent by an ESP32 device.
"""

import asyncio
import json
import random
import time
from datetime import datetime
import paho.mqtt.client as mqtt
import requests

class SensorDataGenerator:
    def __init__(self):
        # Using the node ID from the user's example
        self.nodes = [
            {"node_id": "441793F9456C", "name": "Test Device 1"},
            {"node_id": "ESP32_SIM_002", "name": "Test Device 2"},
        ]
        self.running = False
        self.api_url = "http://13.60.169.17:3005/api"
        self.mqtt_host = "13.60.169.17"
        self.mqtt_port = 1883
        self.mqtt_user = "rnr_iot_user"
        self.mqtt_password = "rnr_iot_2025!"
        
    def generate_sensor_data(self, node_id):
        """Generate realistic sensor data that mimics the ESP32 firmware payload."""
        temperature = round(22 + random.uniform(-3, 8), 1)
        humidity = round(45 + random.uniform(-15, 25), 1)
        humidity_mq_value = random.randint(0, 4095)
        humidity_mq_percent = round((humidity_mq_value / 4095) * 100, 1)

        return {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "temperature": temperature,
            "humidity": humidity,
            "humidity_mq": humidity_mq_percent,
            "humidity_mq_raw": humidity_mq_value,
            "gas_sensor": random.randint(50, 300),
            "status": "online",
            "node_id": node_id,
            "servo_angle": 90,  # Static value for simulation
            "light_state": False,
            "fan_state": False,
            "relay3_state": False,
            "relay4_state": False,
            "real_model_state": False,
            "smart_mode": True,
            "uptime": int(time.time() * 1000),
            "wifi_rssi": random.randint(-80, -40)
        }
    
    def register_nodes_via_api(self):
        """Register test nodes via API if they don't exist."""
        print(f"Checking node registration at {self.api_url}/nodes...")
        for node in self.nodes:
            try:
                # Check if node exists
                response = requests.get(f"{self.api_url}/nodes")
                if response.status_code == 200:
                    existing_nodes = response.json()
                    node_exists = any(n.get('node_id') == node['node_id'] for n in existing_nodes)
                else:
                    print(f"⚠️ Could not fetch existing nodes, assuming they don't exist. Status: {response.status_code}")
                    node_exists = False

                if not node_exists:
                    print(f"Node {node['node_id']} not found. Registering...")
                    node_data = {
                        "node_id": node['node_id'],
                        "name": node['name'],
                        "location": "Simulated Location",
                        "sensor_types": ["temperature", "humidity", "gas_sensor"]
                    }
                    
                    response = requests.post(f"{self.api_url}/nodes", json=node_data)
                    if response.status_code == 200:
                        print(f"✅ Registered node: {node['node_id']}")
                    else:
                        print(f"❌ Failed to register node {node['node_id']}: {response.text}")
                else:
                    print(f"📋 Node {node['node_id']} already exists.")
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Error connecting to API to register node {node['node_id']}: {e}")
    
    def send_via_mqtt(self, data):
        """Send data via MQTT to the remote broker."""
        try:
            client = mqtt.Client()
            client.username_pw_set(self.mqtt_user, self.mqtt_password)
            client.connect(self.mqtt_host, self.mqtt_port, 60)
            
            topic = f"devices/{data['node_id']}/data"
            payload = json.dumps(data)
            
            result = client.publish(topic, payload, qos=1)
            result.wait_for_publish() # Wait for publish to complete
            
            if result.is_published():
                print(f"📡 MQTT sent to {topic}: {data['node_id']} - T:{data['temperature']}°C H:{data['humidity']}%")
            else:
                print(f"❌ MQTT publish failed to topic {topic}")

            client.disconnect()
            
        except Exception as e:
            print(f"❌ MQTT error: {e}")
    
    async def run_simulation(self, duration_minutes=30):
        """Run the sensor data simulation."""
        print(f"🚀 Starting Real-time Sensor Data Simulation for {duration_minutes} minutes...")
        print(f"   Broker: {self.mqtt_host}:{self.mqtt_port}")
        print("-" * 60)
        
        # Register nodes first
        self.register_nodes_via_api()
        print("-" * 60)
        
        self.running = True
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        while self.running and time.time() < end_time:
            for node in self.nodes:
                # Generate sensor data
                sensor_data = self.generate_sensor_data(node['node_id'])
                
                # Send via MQTT
                self.send_via_mqtt(sensor_data)
                
                # Minimal delay between nodes (0.1s)
                await asyncio.sleep(0.1)
            
            # Wait 1 second before next round
            wait_time = 1
            print(f"⏱️  Data sent. Next in {wait_time}s... (Uptime: {int(time.time() - start_time)}s)")
            await asyncio.sleep(wait_time)
        
        print("✅ Simulation completed!")
    
    def stop(self):
        """Stop the simulation"""
        self.running = False

async def main():
    generator = SensorDataGenerator()
    
    try:
        print("🌟 IoT Real-time Data Simulator")
        print("=" * 50)
        print("This script will:")
        print("1. Register simulated ESP32 nodes via API (if needed).")
        print("2. Generate sensor data mimicking the firmware.")
        print("3. Send data via MQTT to the cloud platform.")
        print()
        
        await generator.run_simulation(duration_minutes=30)
        
    except KeyboardInterrupt:
        print("\n⏹️  Stopping simulation...")
        generator.stop()
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Real-time Sensor Data Generator for IoT Dashboard Testing
Generates simulated sensor data and sends it via WebSocket and MQTT to test the real-time dashboard.
"""

import asyncio
import json
import random
import time
from datetime import datetime
import websockets
import paho.mqtt.client as mqtt
import requests

class SensorDataGenerator:
    def __init__(self):
        self.nodes = [
            {"node_id": "ESP32_001", "name": "Living Room Sensor"},
            {"node_id": "ESP32_002", "name": "Kitchen Sensor"},
            {"node_id": "ESP32_003", "name": "Bedroom Sensor"},
            {"node_id": "441793F9456C", "name": "abcd"},
        ]
        self.running = False
        
    def generate_sensor_data(self, node_id):
        """Generate realistic sensor data"""
        # Base values with some variation
        base_temp = 22 + random.uniform(-3, 8)  # 19-30°C
        base_humidity = 45 + random.uniform(-15, 25)  # 30-70%
        base_pressure = 1013 + random.uniform(-20, 20)  # Atmospheric pressure
        base_light = random.uniform(100, 1000)  # Light intensity
        
        return {
            "node_id": node_id,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "temperature": round(base_temp, 1),
                "humidity": round(base_humidity, 1),
                "pressure": round(base_pressure, 1),
                "light": round(base_light, 1)
            }
        }
    
    def register_nodes_via_api(self):
        """Register test nodes via API"""
        api_url = "http://localhost:8000/api"
        
        for node in self.nodes:
            try:
                # Check if node exists
                response = requests.get(f"{api_url}/nodes")
                existing_nodes = response.json()
                
                # Check if node already exists
                node_exists = any(n.get('node_id') == node['node_id'] for n in existing_nodes)
                
                if not node_exists:
                    # Create new node
                    node_data = {
                        "node_id": node['node_id'],
                        "name": node['name'],
                        "location": "Test Location",
                        "sensor_types": ["temperature", "humidity", "pressure", "light"]
                    }
                    
                    response = requests.post(f"{api_url}/nodes", json=node_data)
                    if response.status_code == 200:
                        print(f"✅ Registered node: {node['node_id']}")
                    else:
                        print(f"❌ Failed to register node {node['node_id']}: {response.text}")
                else:
                    print(f"📋 Node {node['node_id']} already exists")
                    
            except Exception as e:
                print(f"❌ Error registering node {node['node_id']}: {e}")
    
    async def send_via_websocket(self, data):
        """Send data via WebSocket"""
        try:
            uri = "ws://localhost:8000/ws"
            async with websockets.connect(uri) as websocket:
                message = {
                    "type": "sensor_data",
                    **data
                }
                await websocket.send(json.dumps(message))
                print(f"📡 WebSocket sent: {data['node_id']} - T:{data['data']['temperature']}°C H:{data['data']['humidity']}%")
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
    
    def send_via_mqtt(self, data):
        """Send data via MQTT using the correct routing that the worker expects"""
        try:
            # Connect to RabbitMQ directly for better reliability
            import pika
            
            connection = pika.BlockingConnection(
                pika.URLParameters("amqp://iotuser:iotpassword@localhost:5672/iot_vhost")
            )
            channel = connection.channel()
            
            # Send to the topic exchange with the routing key the worker listens for
            routing_key = f"devices.{data['node_id']}.data"
            
            # Format the message as expected by the worker
            message = {
                "timestamp": data["timestamp"],
                "temperature": data["data"]["temperature"],
                "humidity": data["data"]["humidity"], 
                "pressure": data["data"]["pressure"],
                "light_level": data["data"]["light"]
            }
            
            channel.basic_publish(
                exchange='amq.topic',
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            
            connection.close()
            print(f"📡 MQTT sent: {data['node_id']} - T:{data['data']['temperature']}°C H:{data['data']['humidity']}%")
            
        except Exception as e:
            print(f"❌ MQTT error: {e}")
            # Fallback to old MQTT method
            try:
                client = mqtt.Client()
                client.connect("localhost", 1883, 60)
                
                topic = f"sensors/{data['node_id']}/data"
                payload = json.dumps(data)
                
                client.publish(topic, payload)
                client.disconnect()
            except Exception as e2:
                print(f"❌ MQTT fallback error: {e2}")
    
    async def run_simulation(self, duration_minutes=30):
        """Run the sensor data simulation"""
        print(f"🚀 Starting Real-time Sensor Data Simulation for {duration_minutes} minutes...")
        print("📊 This will generate data for the IoT Dashboard to display in real-time")
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
                
                # Send via MQTT - the backend worker will handle WebSocket broadcasting
                self.send_via_mqtt(sensor_data)
                
                # Small delay between nodes
                await asyncio.sleep(1)
            
            # Wait 10 seconds before next round of data
            print(f"⏱️  Next batch in 10 seconds... (Running for {int(time.time() - start_time)}s)")
            await asyncio.sleep(10)
        
        print("✅ Simulation completed!")
    
    def stop(self):
        """Stop the simulation"""
        self.running = False

async def main():
    generator = SensorDataGenerator()
    
    try:
        print("🌟 IoT Dashboard Real-time Data Generator")
        print("=" * 50)
        print("This script will:")
        print("1. Register test ESP32 nodes via API")
        print("2. Generate realistic sensor data")
        print("3. Send data via WebSocket for real-time dashboard updates")
        print("4. Send data via MQTT for device communication")
        print()
        print("🔍 Open your dashboard at: http://localhost:3000")
        print("📊 You should see real-time updates in the charts and metrics")
        print()
        
        # Run simulation for 30 minutes
        await generator.run_simulation(duration_minutes=30)
        
    except KeyboardInterrupt:
        print("\n⏹️  Stopping simulation...")
        generator.stop()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Quick RabbitMQ Queue Test and Data Generator
This script tests RabbitMQ connectivity and generates test data to populate queues
"""

import json
import time
import random
from datetime import datetime
import paho.mqtt.client as mqtt
import requests
import threading

class QuickRabbitMQTest:
    def __init__(self):
        # Configuration (adjust these based on your setup)
        self.mqtt_host = "localhost"  # Change to your RabbitMQ host
        self.mqtt_port = 1883
        self.mqtt_user = "rnr_iot_user"
        self.mqtt_password = "rnr_iot_2025!"
        
        # Test configuration
        self.test_node_id = "TEST_NODE_001"
        self.messages_sent = 0
        self.messages_received = 0
        self.client = None
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            print(f"✅ Connected to RabbitMQ MQTT broker")
            # Subscribe to test topics
            client.subscribe(f"devices/{self.test_node_id}/data")
            client.subscribe("devices/+/data")  # Subscribe to all device data
            print(f"📡 Subscribed to device data topics")
        else:
            print(f"❌ Failed to connect to MQTT broker: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback for received MQTT messages"""
        self.messages_received += 1
        try:
            data = json.loads(msg.payload.decode())
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"📨 [{timestamp}] Message #{self.messages_received}")
            print(f"   Topic: {msg.topic}")
            print(f"   Temperature: {data.get('temperature', 'N/A')}°C")
            print(f"   Humidity: {data.get('humidity', 'N/A')}%")
            print(f"   Node ID: {data.get('node_id', 'N/A')}")
            print("-" * 50)
        except Exception as e:
            print(f"❌ Error parsing message: {e}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        print(f"🔌 Disconnected from MQTT broker")
    
    def generate_test_data(self):
        """Generate realistic test sensor data"""
        return {
            "node_id": self.test_node_id,
            "timestamp": datetime.now().isoformat(),
            "temperature": round(20 + random.uniform(-5, 15), 1),
            "humidity": round(50 + random.uniform(-20, 30), 1),
            "gas_sensor": random.randint(50, 500),
            "status": "online",
            "battery_level": random.randint(20, 100),
            "signal_strength": random.randint(-80, -30),
            "test_message": True
        }
    
    def publish_test_data(self, duration_seconds=60):
        """Publish test data for a specified duration"""
        print(f"🚀 Starting data generation for {duration_seconds} seconds...")
        
        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            try:
                # Generate test data
                data = self.generate_test_data()
                
                # Publish to MQTT topic
                topic = f"devices/{self.test_node_id}/data"
                payload = json.dumps(data)
                
                result = self.client.publish(topic, payload, qos=1)
                
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    self.messages_sent += 1
                    print(f"📤 Sent message #{self.messages_sent}: T={data['temperature']}°C, H={data['humidity']}%")
                else:
                    print(f"❌ Failed to publish message: {result.rc}")
                
                # Wait before next message
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error generating data: {e}")
                break
    
    def check_rabbitmq_management(self):
        """Check RabbitMQ management interface"""
        print("🔍 Checking RabbitMQ Management Interface...")
        
        management_url = "http://localhost:15672/api/overview"
        auth = (self.mqtt_user, self.mqtt_password)
        
        try:
            response = requests.get(management_url, auth=auth, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Management interface accessible")
                print(f"   RabbitMQ Version: {data.get('rabbitmq_version', 'unknown')}")
                print(f"   Management Version: {data.get('management_version', 'unknown')}")
                return True
            else:
                print(f"❌ Management interface returned: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot access management interface: {e}")
            return False
    
    def check_queues(self):
        """Check current queue status"""
        print("📊 Checking Queue Status...")
        
        queues_url = "http://localhost:15672/api/queues"
        auth = (self.mqtt_user, self.mqtt_password)
        
        try:
            response = requests.get(queues_url, auth=auth, timeout=10)
            if response.status_code == 200:
                queues = response.json()
                print(f"📋 Found {len(queues)} queues:")
                
                for queue in queues:
                    name = queue.get('name', 'unknown')
                    messages = queue.get('messages', 0)
                    consumers = queue.get('consumers', 0)
                    print(f"   📦 {name}: {messages} messages, {consumers} consumers")
                
                return True
            else:
                print(f"❌ Cannot fetch queues: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error checking queues: {e}")
            return False
    
    def run_complete_test(self):
        """Run complete RabbitMQ test"""
        print("🐰 RabbitMQ Quick Test and Data Generator")
        print("=" * 60)
        
        # Step 1: Check management interface
        if not self.check_rabbitmq_management():
            print("❌ Cannot proceed without management interface")
            return
        
        # Step 2: Setup MQTT client
        print("\n🔧 Setting up MQTT client...")
        self.client = mqtt.Client()
        self.client.username_pw_set(self.mqtt_user, self.mqtt_password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        try:
            # Step 3: Connect to MQTT broker
            print(f"🔗 Connecting to {self.mqtt_host}:{self.mqtt_port}...")
            self.client.connect(self.mqtt_host, self.mqtt_port, 60)
            
            # Step 4: Start MQTT loop in background
            self.client.loop_start()
            time.sleep(3)  # Give time for connection
            
            # Step 5: Check initial queue status
            print("\n📊 Initial queue status:")
            self.check_queues()
            
            # Step 6: Generate test data
            print(f"\n🎯 Generating test data (30 seconds)...")
            self.publish_test_data(30)
            
            # Step 7: Check final queue status
            print("\n📊 Final queue status:")
            self.check_queues()
            
            # Step 8: Summary
            print(f"\n📈 Test Summary:")
            print(f"   Messages sent: {self.messages_sent}")
            print(f"   Messages received: {self.messages_received}")
            
            if self.messages_sent > 0 and self.messages_received > 0:
                print("✅ RabbitMQ is working correctly!")
            elif self.messages_sent > 0:
                print("⚠️ Messages sent but none received - check queue bindings")
            else:
                print("❌ No messages were sent - check MQTT connection")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        finally:
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
            
            print("\n🎬 Test completed!")

def main():
    tester = QuickRabbitMQTest()
    
    try:
        tester.run_complete_test()
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()

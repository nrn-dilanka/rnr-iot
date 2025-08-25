#!/usr/bin/env python3
"""
Test RabbitMQ MQTT broker connectivity
"""
import paho.mqtt.client as mqtt
import json
import time
import threading
from datetime import datetime

# RabbitMQ MQTT Configuration
RABBITMQ_HOST = "localhost"
RABBITMQ_MQTT_PORT = 1883
TOPIC = "devices/441793F9456C/data"

# Global variables for tracking
messages_sent = 0
messages_received = 0

def on_connect(client, userdata, flags, rc):
    print(f"🔗 Connected to RabbitMQ MQTT with result code {rc}")
    if rc == 0:
        print("✅ Successfully connected to RabbitMQ MQTT broker")
        client.subscribe(TOPIC)
        print(f"📡 Subscribed to topic: {TOPIC}")
    else:
        print(f"❌ Failed to connect to RabbitMQ MQTT broker: {rc}")

def on_message(client, userdata, msg):
    global messages_received
    messages_received += 1
    try:
        data = json.loads(msg.payload.decode())
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"📨 [{timestamp}] Received message #{messages_received}")
        print(f"   Topic: {msg.topic}")
        print(f"   Data: {data}")
        print("-" * 60)
    except Exception as e:
        print(f"❌ Error parsing message: {e}")
        print(f"   Raw payload: {msg.payload}")

def on_disconnect(client, userdata, rc):
    print(f"🔌 Disconnected from RabbitMQ MQTT broker with result code {rc}")

def publish_test_messages(client):
    """Publish test messages to verify broker functionality"""
    global messages_sent
    
    # Wait a bit for connection to establish
    time.sleep(2)
    
    print("🚀 Starting to publish test messages...")
    
    for i in range(5):
        test_data = {
            "node_id": "441793F9456C",
            "temperature": 20.5 + i * 0.1,
            "humidity": 50.0 + i,
            "gas_sensor": 100 + i * 10,
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "test_message": True,
            "message_number": i + 1
        }
        
        try:
            result = client.publish(TOPIC, json.dumps(test_data))
            messages_sent += 1
            print(f"📤 Published test message #{messages_sent}: {test_data}")
            time.sleep(1)
        except Exception as e:
            print(f"❌ Error publishing message: {e}")
            break

def main():
    print("🚀 Starting RabbitMQ MQTT Test Client")
    print(f"🎯 Target: {RABBITMQ_HOST}:{RABBITMQ_MQTT_PORT}")
    print(f"📡 Topic: {TOPIC}")
    print("=" * 80)
    
    # Create MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    try:
        print(f"🔗 Connecting to {RABBITMQ_HOST}:{RABBITMQ_MQTT_PORT}...")
        client.connect(RABBITMQ_HOST, RABBITMQ_MQTT_PORT, 60)
        
        # Start publisher thread
        publisher_thread = threading.Thread(target=publish_test_messages, args=(client,))
        publisher_thread.daemon = True
        publisher_thread.start()
        
        print("👂 Listening for messages... Press Ctrl+C to stop")
        
        # Keep the client running
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping test client...")
        client.disconnect()
        
        print(f"\n📊 Summary:")
        print(f"   Messages sent: {messages_sent}")
        print(f"   Messages received: {messages_received}")
        
        if messages_received > 0:
            print("✅ RabbitMQ MQTT broker is working correctly!")
        else:
            print("❌ RabbitMQ MQTT broker test failed - no messages received")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

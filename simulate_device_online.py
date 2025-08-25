import pika
import json
import time
from datetime import datetime

def send_sensor_data():
    """Send simulated sensor data for device 441793F9456C"""
    
    # Connection parameters
    rabbitmq_url = "amqp://iotuser:iotpassword@localhost:5672/iot_vhost"
    
    try:
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
        channel = connection.channel()
        
        # Sensor data for device 441793F9456C
        sensor_data = {
            "node_id": "441793F9456C",
            "timestamp": datetime.utcnow().isoformat(),
            "temperature": 23.5,
            "humidity": 45.2,
            "pressure": 1013.25,
            "light_level": 350,
            "heat_index": 24.1,
            "air_quality": 85,
            "signal_strength": -65
        }
        
        # Publish to the topic the worker service is listening to
        routing_key = f"devices.441793F9456C.data"
        
        channel.basic_publish(
            exchange='amq.topic',
            routing_key=routing_key,
            body=json.dumps(sensor_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
            )
        )
        
        print(f"✅ Sent sensor data for device 441793F9456C")
        print(f"📊 Data: {json.dumps(sensor_data, indent=2)}")
        
        connection.close()
        
    except Exception as e:
        print(f"❌ Error sending sensor data: {e}")

if __name__ == "__main__":
    print("🚀 Sending sensor data to mark device as online...")
    send_sensor_data()

import os
import pika
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RabbitMQClient:
    def __init__(self, rabbitmq_url: str = None):
        self.rabbitmq_url = rabbitmq_url or os.getenv("RABBITMQ_URL", "amqp://iotuser:iotpassword@localhost:5672/iot_vhost")
        self.connection = None
        self.channel = None
    
    def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            self.channel = self.connection.channel()
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    def disconnect(self):
        """Close connection to RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Disconnected from RabbitMQ")
    
    def publish_command(self, node_id: str, command: Dict[str, Any]):
        """Publish a command to a specific node"""
        if not self.channel:
            self.connect()
        
        topic = f"devices/{node_id}/commands"
        message = json.dumps(command)
        
        try:
            # For MQTT clients, use the MQTT exchange
            # RabbitMQ MQTT plugin maps MQTT topics to AMQP routing keys
            self.channel.exchange_declare(
                exchange='amq.topic',
                exchange_type='topic',
                durable=True
            )
            
            # Publish the message with proper MQTT routing
            self.channel.basic_publish(
                exchange='amq.topic',
                routing_key=topic,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                )
            )
            
            logger.info(f"Published command to {topic}: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish command to {topic}: {e}")
            return False
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

# Global RabbitMQ client instance
rabbitmq_client = RabbitMQClient()

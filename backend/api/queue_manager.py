"""
Enhanced RabbitMQ Queue Manager for ESP32 Communication
Handles bidirectional message queuing between ESP32 devices and backend services
"""
import pika
import json
import time
from datetime import datetime
import threading
import logging

class QueueManager:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queues = {
            'sensor_data': {'durable': True, 'priority': False},
            'alerts': {'durable': True, 'priority': True},
            'data_requests': {'durable': True, 'priority': True},
            'esp32_responses': {'durable': True, 'priority': False},
            'broadcast': {'durable': True, 'priority': False},
            'commands': {'durable': True, 'priority': True},
            'status_updates': {'durable': True, 'priority': False}
        }
        self.consumers = {}
        self.is_connected = False
        
    def connect(self):
        """Connect to RabbitMQ with persistent connection"""
        try:
            credentials = pika.PlainCredentials('rnr_iot_user', 'rnr_iot_2025!')
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host='localhost', 
                    port=5672, 
                    virtual_host='/', 
                    credentials=credentials,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
            )
            self.channel = self.connection.channel()
            
            # Declare all queues with proper configuration
            for queue_name, config in self.queues.items():
                queue_args = {}
                if config['priority']:
                    queue_args['x-max-priority'] = 10
                
                self.channel.queue_declare(
                    queue=queue_name, 
                    durable=config['durable'],
                    arguments=queue_args
                )
            
            self.is_connected = True
            print("✅ Connected to RabbitMQ for queue management")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to RabbitMQ: {e}")
            self.is_connected = False
            return False
    
    def ensure_connection(self):
        """Ensure connection is active, reconnect if needed"""
        if not self.is_connected or self.connection.is_closed:
            print("🔄 Reconnecting to RabbitMQ...")
            return self.connect()
        return True
    
    def send_to_queue(self, queue_name, data, priority=1, persistent=True):
        """Send data to specific queue with retry logic"""
        for attempt in range(3):
            try:
                if not self.ensure_connection():
                    continue
                
                message = {
                    'message_id': f"backend_{int(time.time())}_{priority}_{attempt}",
                    'timestamp': datetime.now().isoformat(),
                    'queue_name': queue_name,
                    'priority': priority,
                    'sender': 'backend_api',
                    'attempt': attempt + 1,
                    'data': data
                }
                
                properties = pika.BasicProperties(
                    priority=priority,
                    delivery_mode=2 if persistent else 1,  # Persistent or transient
                    timestamp=int(time.time()),
                    message_id=message['message_id']
                )
                
                self.channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=json.dumps(message),
                    properties=properties
                )
                
                print(f"📤 Sent to queue '{queue_name}': {message['message_id']} (attempt {attempt + 1})")
                return True
                
            except Exception as e:
                print(f"❌ Failed to send to queue '{queue_name}' (attempt {attempt + 1}): {e}")
                self.is_connected = False
                time.sleep(1)
        
        return False
    
    def consume_queue(self, queue_name, callback, auto_ack=False):
        """Start consuming from specific queue with error handling"""
        try:
            if not self.ensure_connection():
                return False
            
            def wrapper(ch, method, properties, body):
                try:
                    data = json.loads(body.decode())
                    message_id = data.get('message_id', 'unknown')
                    
                    print(f"📨 Received from queue '{queue_name}': {message_id}")
                    
                    # Process message
                    result = callback(data)
                    
                    # Acknowledge message if processing successful
                    if not auto_ack:
                        if result:
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                            print(f"✅ Successfully processed message from '{queue_name}'")
                        else:
                            print(f"⚠️ Message processing failed for '{queue_name}' - rejecting")
                            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON in message from '{queue_name}': {e}")
                    if not auto_ack:
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                        
                except Exception as e:
                    print(f"❌ Error processing message from '{queue_name}': {e}")
                    if not auto_ack:
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
            # Configure QoS for fair distribution
            self.channel.basic_qos(prefetch_count=1)
            
            # Start consuming
            self.channel.basic_consume(
                queue=queue_name, 
                on_message_callback=wrapper,
                auto_ack=auto_ack
            )
            
            print(f"📡 Started consuming from queue: {queue_name}")
            
            # Start consuming in separate thread
            def consume_loop():
                try:
                    self.channel.start_consuming()
                except Exception as e:
                    print(f"❌ Consumer error for '{queue_name}': {e}")
            
            consumer_thread = threading.Thread(target=consume_loop, name=f"Consumer-{queue_name}")
            consumer_thread.daemon = True
            consumer_thread.start()
            
            self.consumers[queue_name] = consumer_thread
            return True
            
        except Exception as e:
            print(f"❌ Failed to start consuming from '{queue_name}': {e}")
            return False
    
    def send_response_to_esp32(self, node_id, response_type, data, priority=5):
        """Send response back to specific ESP32 device"""
        response_queue = f"esp32_responses_{node_id}"
        
        response_data = {
            'response_type': response_type,
            'target_node': node_id,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'sender': 'backend_queue_manager'
        }
        
        return self.send_to_queue(response_queue, response_data, priority=priority)
    
    def send_command_to_esp32(self, node_id, action, parameters, priority=7):
        """Send command to specific ESP32 device"""
        command_data = {
            'node_id': node_id,
            'action': action,
            'parameters': parameters,
            'timestamp': datetime.now().isoformat(),
            'command_id': f"cmd_{int(time.time())}_{node_id}"
        }
        
        command_queue = f"commands_{node_id}"
        return self.send_to_queue(command_queue, command_data, priority=priority)
    
    def broadcast_to_all_esp32(self, message_type, data, priority=3):
        """Broadcast message to all ESP32 devices"""
        broadcast_data = {
            'message_type': message_type,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'sender': 'backend_broadcast',
            'broadcast_id': f"broadcast_{int(time.time())}"
        }
        
        return self.send_to_queue('broadcast', broadcast_data, priority=priority)
    
    def get_queue_info(self, queue_name):
        """Get information about specific queue"""
        try:
            if not self.ensure_connection():
                return None
                
            method = self.channel.queue_declare(queue=queue_name, passive=True)
            return {
                'queue': queue_name,
                'message_count': method.method.message_count,
                'consumer_count': method.method.consumer_count
            }
            
        except Exception as e:
            print(f"❌ Failed to get queue info for '{queue_name}': {e}")
            return None
    
    def purge_queue(self, queue_name):
        """Purge all messages from queue"""
        try:
            if not self.ensure_connection():
                return False
                
            self.channel.queue_purge(queue=queue_name)
            print(f"🗑️ Purged queue: {queue_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to purge queue '{queue_name}': {e}")
            return False
    
    def close(self):
        """Close connection gracefully"""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.stop_consuming()
                self.channel.close()
            
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                
            self.is_connected = False
            print("✅ Queue manager connection closed")
            
        except Exception as e:
            print(f"⚠️ Error closing queue manager: {e}")

# Global queue manager instance
queue_manager = QueueManager()

# Convenience functions
def send_sensor_data_to_queue(data):
    """Convenience function to send sensor data"""
    return queue_manager.send_to_queue('sensor_data', data, priority=1)

def send_alert_to_queue(data):
    """Convenience function to send alert"""
    return queue_manager.send_to_queue('alerts', data, priority=10)

def send_status_to_queue(data):
    """Convenience function to send status update"""
    return queue_manager.send_to_queue('status_updates', data, priority=3)

# Export main components
__all__ = ['QueueManager', 'queue_manager', 'send_sensor_data_to_queue', 'send_alert_to_queue', 'send_status_to_queue']

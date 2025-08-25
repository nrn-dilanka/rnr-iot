import os
import pika
import json
import logging
from typing import Dict, Any, Optional, Callable, List
import threading
import time
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class EnhancedRabbitMQClient:
    """Enhanced RabbitMQ client with improved reliability and performance"""
    
    def __init__(self, rabbitmq_url: str = None):
        self.rabbitmq_url = rabbitmq_url or os.getenv("RABBITMQ_URL", "amqp://rnr_iot_user:rnr_iot_2025!@localhost:5672/rnr_iot_vhost")
        self.connection = None
        self.channel = None
        self.consuming = False
        self.consumer_thread = None
        self.connection_lock = threading.Lock()
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5
        
        # Performance optimizations for persistent sessions
        self.heartbeat_interval = 600
        self.blocked_connection_timeout = 300
        self.socket_timeout = 10
        self.connection_attempts = 3
        self.retry_delay = 2
        
        # Message tracking for reliability
        self.message_count = 0
        self.failed_messages = []
        self.persistent_delivery_enabled = True
        
        logger.info("🚀 Enhanced RabbitMQ Client initialized")
        logger.info(f"   - URL: {self._mask_credentials(self.rabbitmq_url)}")
        logger.info(f"   - Persistent delivery: {self.persistent_delivery_enabled}")
        logger.info(f"   - Heartbeat: {self.heartbeat_interval}s")
        
    def connect(self):
        """Establish connection to RabbitMQ with enhanced reliability"""
        with self.connection_lock:
            if self.is_connected and self.connection and not self.connection.is_closed:
                return True
                
            for attempt in range(self.max_reconnect_attempts):
                try:
                    logger.info(f"🔗 Connecting to RabbitMQ (attempt {attempt + 1}/{self.max_reconnect_attempts})")
                    
                    # Enhanced connection parameters
                    params = pika.URLParameters(self.rabbitmq_url)
                    params.heartbeat = self.heartbeat_interval
                    params.blocked_connection_timeout = self.blocked_connection_timeout
                    params.socket_timeout = self.socket_timeout
                    params.connection_attempts = 3
                    params.retry_delay = 2
                    
                    self.connection = pika.BlockingConnection(params)
                    self.channel = self.connection.channel()
                    
                    # Enable publisher confirms for reliability
                    self.channel.confirm_delivery()
                    
                    # Set QoS for better message distribution
                    self.channel.basic_qos(prefetch_count=10)
                    
                    # Setup exchanges and queues
                    self.setup_exchanges_and_queues()
                    
                    self.is_connected = True
                    self.reconnect_attempts = 0
                    
                    logger.info(f"✅ Connected to RabbitMQ successfully!")
                    logger.info(f"📊 Connection details:")
                    logger.info(f"   - Heartbeat: {self.heartbeat_interval}s")
                    logger.info(f"   - Socket timeout: {self.socket_timeout}s")
                    logger.info(f"   - Virtual host: {params.virtual_host}")
                    
                    return True
                    
                except Exception as e:
                    self.reconnect_attempts = attempt + 1
                    logger.error(f"❌ Failed to connect to RabbitMQ (attempt {attempt + 1}): {e}")
                    
                    if attempt < self.max_reconnect_attempts - 1:
                        delay = min(self.reconnect_delay * (2 ** attempt), 60)  # Exponential backoff, max 60s
                        logger.info(f"⏳ Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        logger.error("💥 All RabbitMQ connection attempts failed")
                        self.is_connected = False
                        raise
    
    def setup_exchanges_and_queues(self):
        """Setup required exchanges and queues with enhanced configuration"""
        if not self.channel:
            return
            
        try:
            # Declare topic exchange for MQTT with durability
            self.channel.exchange_declare(
                exchange='amq.topic',
                exchange_type='topic',
                durable=True
            )
            
            # Declare enhanced IoT data exchange
            self.channel.exchange_declare(
                exchange='iot_data',
                exchange_type='topic',
                durable=True
            )
            
            # Declare device management exchange
            self.channel.exchange_declare(
                exchange='device_management',
                exchange_type='topic',
                durable=True
            )
            
            # Enhanced sensor data queue with TTL and DLX
            self.channel.queue_declare(
                queue='sensor_data',
                durable=True,
                arguments={
                    'x-message-ttl': 3600000,  # 1 hour TTL
                    'x-max-length': 10000,     # Max 10k messages
                    'x-dead-letter-exchange': 'dlx',
                    'x-dead-letter-routing-key': 'sensor_data.failed'
                }
            )
            
            # Enhanced commands queue with priority support
            self.channel.queue_declare(
                queue='device_commands',
                durable=True,
                arguments={
                    'x-max-priority': 10,      # Priority queue
                    'x-message-ttl': 300000,   # 5 minutes TTL
                }
            )
            
            # Status updates queue for real-time monitoring
            self.channel.queue_declare(
                queue='device_status',
                durable=True,
                arguments={
                    'x-message-ttl': 60000,    # 1 minute TTL
                }
            )
            
            # Dead letter exchange for failed messages
            self.channel.exchange_declare(
                exchange='dlx',
                exchange_type='topic',
                durable=True
            )
            
            self.channel.queue_declare(
                queue='failed_messages',
                durable=True
            )
            
            # Enhanced queue bindings
            queue_bindings = [
                ('sensor_data', 'amq.topic', 'devices.*.data'),
                ('sensor_data', 'iot_data', 'devices.*.data'),
                ('device_commands', 'amq.topic', 'devices.*.commands'),
                ('device_commands', 'device_management', 'commands.*'),
                ('device_status', 'amq.topic', 'devices.*.status'),
                ('device_status', 'device_management', 'status.*'),
                ('failed_messages', 'dlx', '#'),
            ]
            
            for queue, exchange, routing_key in queue_bindings:
                self.channel.queue_bind(
                    exchange=exchange,
                    queue=queue,
                    routing_key=routing_key
                )
            
            logger.info("✅ Successfully setup enhanced exchanges and queues")
            logger.info(f"📋 Configured queues:")
            logger.info(f"   - sensor_data: TTL=1h, Max=10k messages")
            logger.info(f"   - device_commands: Priority queue, TTL=5min") 
            logger.info(f"   - device_status: Real-time, TTL=1min")
            logger.info(f"   - failed_messages: Dead letter queue")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup exchanges and queues: {e}")

    def disconnect(self):
        """Gracefully close connection to RabbitMQ"""
        with self.connection_lock:
            self.consuming = False
            self.is_connected = False
            
            if self.consumer_thread and self.consumer_thread.is_alive():
                logger.info("🛑 Stopping consumer thread...")
                self.consumer_thread.join(timeout=10)
            
            if self.channel and not self.channel.is_closed:
                try:
                    self.channel.close()
                    logger.info("📢 RabbitMQ channel closed")
                except:
                    pass
            
            if self.connection and not self.connection.is_closed:
                try:
                    self.connection.close()
                    logger.info("🔌 Disconnected from RabbitMQ")
                except:
                    pass
    
    def ensure_connection(self):
        """Ensure connection is active, reconnect if necessary"""
        if not self.is_connected or not self.connection or self.connection.is_closed:
            logger.info("🔄 Connection lost, attempting to reconnect...")
            self.connect()
    
    def publish_command(self, node_id: str, command: Dict[str, Any], priority: int = 5) -> bool:
        """Publish a command to a specific node with enhanced reliability"""
        try:
            self.ensure_connection()
            
            topic = f"devices/{node_id}/commands"
            
            # Enhance command with metadata
            enhanced_command = {
                **command,
                'message_id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat(),
                'node_id': node_id,
                'retry_count': 0
            }
            
            message = json.dumps(enhanced_command)
            
            # Publish with enhanced properties
            properties = pika.BasicProperties(
                delivery_mode=2,  # Persistent message
                priority=priority,
                timestamp=int(time.time()),
                message_id=enhanced_command['message_id'],
                headers={
                    'node_id': node_id,
                    'message_type': 'command',
                    'action': command.get('action', 'unknown'),
                    'source': 'api_server'
                },
                expiration=str(300000)  # 5 minutes expiration
            )
            
            # Publish to multiple exchanges for redundancy
            exchanges_topics = [
                ('amq.topic', topic),
                ('device_management', f"commands.{node_id}")
            ]
            
            success_count = 0
            for exchange, routing_key in exchanges_topics:
                try:
                    confirmed = self.channel.basic_publish(
                        exchange=exchange,
                        routing_key=routing_key,
                        body=message,
                        properties=properties,
                        mandatory=True
                    )
                    
                    if confirmed:
                        success_count += 1
                        
                except Exception as e:
                    logger.error(f"❌ Failed to publish to {exchange}: {e}")
            
            if success_count > 0:
                self.message_count += 1
                logger.info(f"📤 Command published to {node_id} (ID: {enhanced_command['message_id'][:8]}...)")
                logger.info(f"   Action: {command.get('action', 'unknown')}")
                logger.info(f"   Priority: {priority}")
                logger.info(f"   Published to {success_count}/{len(exchanges_topics)} exchanges")
                return True
            else:
                self.failed_messages.append({
                    'node_id': node_id,
                    'command': command,
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': 'All publish attempts failed'
                })
                logger.error(f"❌ Failed to publish command to {node_id}")
                return False
                
        except Exception as e:
            logger.error(f"💥 Error publishing command to {node_id}: {e}")
            self.failed_messages.append({
                'node_id': node_id,
                'command': command,
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            })
            return False
    
    def publish_sensor_data(self, node_id: str, sensor_data: Dict[str, Any]) -> bool:
        """Publish sensor data with enhanced reliability and performance"""
        try:
            self.ensure_connection()
            
            topic = f"devices/{node_id}/data"
            
            # Enhance sensor data with metadata
            enhanced_data = {
                **sensor_data,
                'message_id': str(uuid.uuid4()),
                'received_at': datetime.utcnow().isoformat(),
                'node_id': node_id
            }
            
            message = json.dumps(enhanced_data)
            
            # Enhanced message properties
            properties = pika.BasicProperties(
                delivery_mode=1,  # Non-persistent for sensor data (performance)
                timestamp=int(time.time()),
                message_id=enhanced_data['message_id'],
                headers={
                    'node_id': node_id,
                    'message_type': 'sensor_data',
                    'data_type': 'telemetry',
                    'source': 'iot_device'
                }
            )
            
            # Publish to multiple exchanges
            exchanges_topics = [
                ('amq.topic', topic),
                ('iot_data', topic)
            ]
            
            success_count = 0
            for exchange, routing_key in exchanges_topics:
                try:
                    self.channel.basic_publish(
                        exchange=exchange,
                        routing_key=routing_key,
                        body=message,
                        properties=properties
                    )
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Failed to publish sensor data to {exchange}: {e}")
            
            if success_count > 0:
                self.message_count += 1
                temp = sensor_data.get('temperature', 'N/A')
                humidity = sensor_data.get('humidity', 'N/A')
                logger.debug(f"📊 Sensor data published for {node_id}: {temp}°C, {humidity}%")
                return True
            else:
                logger.error(f"❌ Failed to publish sensor data for {node_id}")
                return False
                
        except Exception as e:
            logger.error(f"💥 Error publishing sensor data for {node_id}: {e}")
            return False
    
    def publish_status_update(self, node_id: str, status: str, metadata: Dict[str, Any] = None) -> bool:
        """Publish device status updates"""
        try:
            self.ensure_connection()
            
            status_data = {
                'node_id': node_id,
                'status': status,
                'timestamp': datetime.utcnow().isoformat(),
                'message_id': str(uuid.uuid4()),
                **(metadata or {})
            }
            
            message = json.dumps(status_data)
            
            properties = pika.BasicProperties(
                delivery_mode=2,  # Persistent for status updates
                timestamp=int(time.time()),
                headers={
                    'node_id': node_id,
                    'message_type': 'status_update',
                    'status': status
                }
            )
            
            # Publish to status topics
            topics = [
                f"devices/{node_id}/status",
                f"status.{status}.{node_id}"
            ]
            
            success_count = 0
            for topic in topics:
                try:
                    self.channel.basic_publish(
                        exchange='amq.topic',
                        routing_key=topic,
                        body=message,
                        properties=properties
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"❌ Failed to publish status to {topic}: {e}")
            
            if success_count > 0:
                logger.info(f"📡 Status update published: {node_id} -> {status}")
                return True
            else:
                logger.error(f"❌ Failed to publish status update for {node_id}")
                return False
                
        except Exception as e:
            logger.error(f"💥 Error publishing status update: {e}")
            return False
    
    def consume_sensor_data(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Start consuming sensor data with enhanced reliability"""
        try:
            self.ensure_connection()
            
            def enhanced_callback(ch, method, properties, body):
                try:
                    # Parse message data
                    data = json.loads(body.decode())
                    
                    # Extract node_id from routing key or headers
                    node_id = None
                    if properties.headers:
                        node_id = properties.headers.get('node_id')
                    
                    if not node_id:
                        # Extract from routing key: devices.{node_id}.data
                        routing_parts = method.routing_key.split('.')
                        if len(routing_parts) >= 3:
                            node_id = routing_parts[1]
                    
                    if node_id:
                        # Call the provided callback
                        callback(node_id, data)
                        
                        # Acknowledge successful processing
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        
                        logger.debug(f"✅ Processed sensor data from {node_id}")
                    else:
                        logger.error("❌ Could not extract node_id from message")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                        
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Invalid JSON in sensor data: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing sensor data: {e}")
                    # Requeue the message for retry (up to a limit)
                    requeue = getattr(method, 'redelivered', False) == False
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=requeue)
            
            # Set up consumer with QoS
            self.channel.basic_qos(prefetch_count=10)
            self.channel.basic_consume(
                queue='sensor_data',
                on_message_callback=enhanced_callback
            )
            
            self.consuming = True
            logger.info("🎯 Started consuming sensor data with enhanced reliability")
            
            # Enhanced consume loop with reconnection handling
            def enhanced_consume_loop():
                while self.consuming:
                    try:
                        if self.is_connected and self.connection and not self.connection.is_closed:
                            self.connection.process_data_events(time_limit=1)
                        else:
                            logger.warning("⚠️ Connection lost in consume loop, attempting reconnection...")
                            self.ensure_connection()
                            time.sleep(1)
                    except Exception as e:
                        logger.error(f"💥 Error in enhanced consume loop: {e}")
                        self.ensure_connection()
                        time.sleep(2)
            
            self.consumer_thread = threading.Thread(target=enhanced_consume_loop, daemon=True)
            self.consumer_thread.start()
            
        except Exception as e:
            logger.error(f"💥 Failed to start enhanced sensor data consumer: {e}")
    
    def get_queue_info(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive information about a specific queue"""
        try:
            self.ensure_connection()
            
            method = self.channel.queue_declare(queue=queue_name, passive=True)
            
            return {
                'name': queue_name,
                'message_count': method.method.message_count,
                'consumer_count': method.method.consumer_count,
                'status': 'active' if method.method.message_count >= 0 else 'unknown'
            }
        except Exception as e:
            logger.error(f"❌ Failed to get queue info for {queue_name}: {e}")
            return {
                'name': queue_name,
                'message_count': 0,
                'consumer_count': 0,
                'status': 'error',
                'error': str(e)
            }
    
    def get_all_queue_info(self) -> List[Dict[str, Any]]:
        """Get information about all monitored queues"""
        queues = ['sensor_data', 'device_commands', 'device_status', 'failed_messages']
        queue_info = []
        
        for queue_name in queues:
            info = self.get_queue_info(queue_name)
            if info:
                queue_info.append(info)
        
        return queue_info
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection and performance statistics"""
        return {
            'is_connected': self.is_connected,
            'reconnect_attempts': self.reconnect_attempts,
            'messages_published': self.message_count,
            'failed_messages_count': len(self.failed_messages),
            'consuming': self.consuming,
            'heartbeat_interval': self.heartbeat_interval,
            'socket_timeout': self.socket_timeout,
            'connection_url': self.rabbitmq_url.split('@')[1] if '@' in self.rabbitmq_url else 'unknown'
        }
    
    def get_failed_messages(self) -> List[Dict[str, Any]]:
        """Get list of failed messages for debugging"""
        return self.failed_messages.copy()
    
    def clear_failed_messages(self):
        """Clear the failed messages list"""
        self.failed_messages.clear()
        logger.info("🧹 Cleared failed messages list")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check"""
        health_status = {
            'status': 'unknown',
            'timestamp': datetime.utcnow().isoformat(),
            'connection': {
                'connected': self.is_connected,
                'url': self.rabbitmq_url.split('@')[1] if '@' in self.rabbitmq_url else 'unknown'
            },
            'queues': [],
            'performance': {
                'messages_published': self.message_count,
                'failed_messages': len(self.failed_messages),
                'consuming': self.consuming
            }
        }
        
        try:
            # Test connection
            if not self.is_connected:
                self.connect()
            
            # Get queue information
            health_status['queues'] = self.get_all_queue_info()
            
            # Test publishing (dry run)
            test_message = {
                'type': 'health_check',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Don't actually publish, just verify we can prepare the message
            json.dumps(test_message)
            
            health_status['status'] = 'healthy'
            logger.info("✅ RabbitMQ health check passed")
            
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
            logger.error(f"❌ RabbitMQ health check failed: {e}")
        
        return health_status
    
    def _mask_credentials(self, url: str) -> str:
        """Mask credentials in URL for logging"""
        try:
            if '@' in url:
                parts = url.split('@')
                if len(parts) == 2:
                    protocol_user = parts[0]
                    if '://' in protocol_user:
                        protocol, user_pass = protocol_user.split('://', 1)
                        if ':' in user_pass:
                            user, _ = user_pass.split(':', 1)
                            return f"{protocol}://{user}:***@{parts[1]}"
            return url
        except:
            return "***"
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

# Global enhanced RabbitMQ client instance
rabbitmq_client = EnhancedRabbitMQClient()

# Backwards compatibility alias
RabbitMQClient = EnhancedRabbitMQClient

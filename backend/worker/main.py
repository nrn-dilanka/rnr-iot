import os
import json
import logging
import asyncio
import threading
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any

import pika
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set up enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedWorkerService:
    """Enhanced Worker Service with improved RabbitMQ communication and performance"""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql://rnr_iot_user:rnr_iot_2025!@localhost:5432/rnr_iot_platform")
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://rnr_iot_user:rnr_iot_2025!@localhost:5672/rnr_iot_vhost")
        self.api_url = os.getenv("API_URL", "http://localhost:3005")
        
        # Database connection with connection pooling
        self.engine = create_engine(
            self.database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Enhanced RabbitMQ connection
        self.connection = None
        self.channel = None
        self.is_connected = False
        
        # Performance tracking
        self.message_count = 0
        self.error_count = 0
        self.start_time = datetime.utcnow()
        
        # Enhanced node status tracking
        self.node_status = {}  # {node_id: {'status': 'online/offline', 'last_seen': datetime}}
        self.offline_threshold = timedelta(seconds=15)  # More reasonable offline detection
        
        # Connection retry settings
        self.max_retries = 15
        self.retry_delay = 2
        self.heartbeat_interval = 600
        self.socket_timeout = 10
    
    def connect_rabbitmq(self):
        """Enhanced RabbitMQ connection with better reliability"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"🔗 Connecting to RabbitMQ (attempt {attempt + 1}/{self.max_retries})")
                
                # Enhanced connection parameters
                params = pika.URLParameters(self.rabbitmq_url)
                params.heartbeat = self.heartbeat_interval
                params.blocked_connection_timeout = 300
                params.socket_timeout = self.socket_timeout
                params.connection_attempts = 3
                params.retry_delay = 2
                
                self.connection = pika.BlockingConnection(params)
                self.channel = self.connection.channel()
                
                # Enable publisher confirms for reliability
                self.channel.confirm_delivery()
                
                # Set QoS for better performance
                self.channel.basic_qos(prefetch_count=10)
                
                # Setup enhanced exchanges and queues
                self.setup_enhanced_infrastructure()
                
                self.is_connected = True
                logger.info("✅ Connected to RabbitMQ with enhanced configuration")
                logger.info(f"📊 Connection details:")
                logger.info(f"   - Heartbeat: {self.heartbeat_interval}s")
                logger.info(f"   - Socket timeout: {self.socket_timeout}s")
                logger.info(f"   - Prefetch count: 10")
                
                return self.setup_consumers()
                
            except Exception as e:
                logger.error(f"❌ Failed to connect to RabbitMQ (attempt {attempt + 1}): {e}")
                
                if attempt < self.max_retries - 1:
                    delay = min(self.retry_delay * (2 ** attempt), 60)  # Exponential backoff
                    logger.info(f"⏳ Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logger.error("💥 All RabbitMQ connection attempts failed")
                    raise
    
    def setup_enhanced_infrastructure(self):
        """Setup enhanced RabbitMQ infrastructure"""
        try:
            # Declare exchanges
            exchanges = [
                ('amq.topic', 'topic'),
                ('iot_data', 'topic'),
                ('device_management', 'topic'),
                ('dlx', 'topic')  # Dead letter exchange
            ]
            
            for exchange_name, exchange_type in exchanges:
                self.channel.exchange_declare(
                    exchange=exchange_name,
                    exchange_type=exchange_type,
                    durable=True
                )
            
            # Enhanced queue declarations with advanced features
            queue_configs = [
                {
                    'name': 'sensor_data_enhanced',
                    'args': {
                        'x-message-ttl': 3600000,  # 1 hour TTL
                        'x-max-length': 50000,     # Max 50k messages
                        'x-dead-letter-exchange': 'dlx',
                        'x-dead-letter-routing-key': 'sensor_data.failed'
                    }
                },
                {
                    'name': 'device_commands_enhanced',
                    'args': {
                        'x-max-priority': 10,      # Priority queue
                        'x-message-ttl': 300000,   # 5 minutes TTL
                    }
                },
                {
                    'name': 'device_status_enhanced',
                    'args': {
                        'x-message-ttl': 60000,    # 1 minute TTL
                    }
                },
                {
                    'name': 'failed_messages',
                    'args': {}
                }
            ]
            
            for queue_config in queue_configs:
                self.channel.queue_declare(
                    queue=queue_config['name'],
                    durable=True,
                    arguments=queue_config['args']
                )
            
            # Enhanced queue bindings
            bindings = [
                ('sensor_data_enhanced', 'amq.topic', 'devices.*.data'),
                ('sensor_data_enhanced', 'iot_data', 'devices.*.data'),
                ('device_commands_enhanced', 'amq.topic', 'devices.*.commands'),
                ('device_commands_enhanced', 'device_management', 'commands.*'),
                ('device_status_enhanced', 'amq.topic', 'devices.*.status'),
                ('device_status_enhanced', 'device_management', 'status.*'),
                ('failed_messages', 'dlx', '#'),
            ]
            
            for queue, exchange, routing_key in bindings:
                self.channel.queue_bind(
                    exchange=exchange,
                    queue=queue,
                    routing_key=routing_key
                )
            
            logger.info("✅ Enhanced RabbitMQ infrastructure setup complete")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup enhanced infrastructure: {e}")
            raise
    
    def setup_consumers(self):
        """Setup enhanced message consumers"""
        try:
            # Set up enhanced sensor data consumer
            self.channel.basic_consume(
                queue='sensor_data_enhanced',
                on_message_callback=self.process_sensor_data_enhanced
            )
            
            # Set up command consumer (for monitoring/debugging)
            self.channel.basic_consume(
                queue='device_commands_enhanced',
                on_message_callback=self.process_device_command
            )
            
            # Set up status consumer
            self.channel.basic_consume(
                queue='device_status_enhanced', 
                on_message_callback=self.process_status_update
            )
            
            logger.info("✅ Enhanced consumers setup complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup consumers: {e}")
            return False
    def process_sensor_data_enhanced(self, ch, method, properties, body):
        """Enhanced sensor data processing with better error handling and performance"""
        try:
            # Parse the message
            data = json.loads(body.decode('utf-8'))
            
            # Extract node_id with multiple fallback methods
            node_id = self.extract_node_id(method.routing_key, properties, data)
            
            if not node_id:
                logger.error(f"❌ Could not extract node_id from message")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            
            # Enhanced logging with message metadata
            message_id = properties.message_id or 'unknown'
            logger.info(f"📊 Processing sensor data from {node_id} (msg_id: {message_id[:8]}...)")
            
            # Store data with enhanced error handling
            success = self.store_sensor_data_enhanced(node_id, data, properties)
            
            if success:
                # Update node status
                self.update_node_status_enhanced(node_id, data)
                
                # Track performance metrics
                self.message_count += 1
                
                # Broadcast to WebSocket clients with enhanced data
                self.broadcast_sensor_data_enhanced(node_id, data, properties)
                
                # Acknowledge successful processing
                ch.basic_ack(delivery_tag=method.delivery_tag)
                
                logger.debug(f"✅ Successfully processed sensor data from {node_id}")
            else:
                # Failed to store data, reject without requeue
                logger.error(f"❌ Failed to store sensor data from {node_id}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                self.error_count += 1
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in sensor data: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            self.error_count += 1
            
        except Exception as e:
            logger.error(f"💥 Error processing sensor data: {e}")
            # Requeue only if it's not a redelivery (avoid infinite loops)
            requeue = not getattr(method, 'redelivered', False)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=requeue)
            self.error_count += 1
    
    def process_device_command(self, ch, method, properties, body):
        """Process device commands for monitoring and logging"""
        try:
            command = json.loads(body.decode('utf-8'))
            node_id = self.extract_node_id(method.routing_key, properties, command)
            
            logger.info(f"📤 Command processed for {node_id}: {command.get('action', 'unknown')}")
            
            # Just acknowledge - commands are handled by the ESP32 directly
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"❌ Error processing device command: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def process_status_update(self, ch, method, properties, body):
        """Process device status updates"""
        try:
            status_data = json.loads(body.decode('utf-8'))
            node_id = status_data.get('node_id') or self.extract_node_id(method.routing_key, properties, status_data)
            
            if node_id:
                logger.info(f"📡 Status update from {node_id}: {status_data.get('status', 'unknown')}")
                self.update_node_status_from_status_message(node_id, status_data)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"❌ Error processing status update: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def extract_node_id(self, routing_key: str, properties, data: Dict[str, Any]) -> str:
        """Extract node_id using multiple methods"""
        # Method 1: From routing key (devices.{node_id}.data)
        if routing_key:
            parts = routing_key.split('.')
            if len(parts) >= 3 and parts[0] == 'devices':
                return parts[1]
        
        # Method 2: From message headers
        if properties and properties.headers:
            node_id = properties.headers.get('node_id')
            if node_id:
                return str(node_id)
        
        # Method 3: From message body
        if isinstance(data, dict):
            node_id = data.get('node_id')
            if node_id:
                return str(node_id)
        
        return None
    
    def store_sensor_data_enhanced(self, node_id: str, data: Dict[str, Any], properties) -> bool:
        """Enhanced sensor data storage with better error handling"""
        db = None
        try:
            db = self.SessionLocal()
            
            # Enhanced data with metadata
            enhanced_data = {
                **data,
                'worker_processed_at': datetime.utcnow().isoformat(),
                'message_id': properties.message_id if properties else None,
                'processing_latency_ms': self.calculate_processing_latency(properties)
            }
            
            # Use parameterized query for better performance and security
            query = text("""
                INSERT INTO sensor_data (node_id, data, received_at)
                VALUES (:node_id, :data, :received_at)
            """)
            
            db.execute(query, {
                'node_id': node_id,
                'data': json.dumps(enhanced_data),
                'received_at': datetime.utcnow()
            })
            db.commit()
            
            logger.debug(f"💾 Enhanced sensor data stored for {node_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing enhanced sensor data for {node_id}: {e}")
            if db:
                db.rollback()
            return False
        finally:
            if db:
                db.close()
    
    def calculate_processing_latency(self, properties) -> float:
        """Calculate message processing latency"""
        if properties and properties.timestamp:
            try:
                message_time = datetime.fromtimestamp(properties.timestamp)
                current_time = datetime.utcnow()
                latency = (current_time - message_time).total_seconds() * 1000
                return round(latency, 2)
            except:
                pass
        return 0.0
    
    def update_node_status_enhanced(self, node_id: str, data: Dict[str, Any]):
        """Enhanced node status update with better tracking"""
        db = None
        try:
            db = self.SessionLocal()
            
            now = datetime.utcnow()
            
            # Update node status tracking
            previous_status = self.node_status.get(node_id, {}).get('status', 'offline')
            self.node_status[node_id] = {
                'status': 'online',
                'last_seen': now,
                'data_points': self.node_status.get(node_id, {}).get('data_points', 0) + 1
            }
            
            # Enhanced database update
            query = text("""
                INSERT INTO nodes (node_id, name, mac_address, status, is_active, last_seen, created_at)
                VALUES (:node_id, :name, :mac_address, 'online', 'true', :last_seen, :created_at)
                ON CONFLICT (node_id)
                DO UPDATE SET 
                    status = 'online',
                    is_active = 'true',
                    last_seen = EXCLUDED.last_seen,
                    updated_at = :last_seen
            """)
            
            # Generate device name from node_id
            device_name = f"ESP32-{node_id[-6:]}" if len(node_id) >= 6 else f"ESP32-{node_id}"
            
            db.execute(query, {
                'node_id': node_id,
                'name': device_name,
                'mac_address': node_id,
                'last_seen': now,
                'created_at': now
            })
            db.commit()
            
            # Broadcast status change if node came online
            if previous_status == 'offline':
                logger.info(f"🟢 Node {node_id} came online")
                self.broadcast_status_change_enhanced(node_id, 'online', {
                    'transition': 'offline_to_online',
                    'last_offline_duration': 'unknown'
                })
            
        except Exception as e:
            logger.error(f"❌ Error updating enhanced node status for {node_id}: {e}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
    
    def update_node_status_from_status_message(self, node_id: str, status_data: Dict[str, Any]):
        """Update node status from explicit status messages"""
        db = None
        try:
            db = self.SessionLocal()
            
            status = status_data.get('status', 'unknown')
            now = datetime.utcnow()
            
            # Update in-memory tracking
            self.node_status[node_id] = {
                'status': status,
                'last_seen': now,
                'explicit_status': True
            }
            
            # Update database
            query = text("""
                UPDATE nodes 
                SET status = :status, last_seen = :last_seen, updated_at = :updated_at
                WHERE node_id = :node_id
            """)
            
            db.execute(query, {
                'node_id': node_id,
                'status': status,
                'last_seen': now,
                'updated_at': now
            })
            db.commit()
            
            logger.info(f"📊 Explicit status update: {node_id} -> {status}")
            
        except Exception as e:
            logger.error(f"❌ Error updating node status from status message: {e}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
    def broadcast_sensor_data_enhanced(self, node_id: str, data: Dict[str, Any], properties):
        """Enhanced sensor data broadcasting with better error handling"""
        try:
            # Create enhanced message for WebSocket broadcasting
            message = {
                "type": "sensor_data_enhanced",
                "node_id": node_id,
                "data": data,
                "timestamp": data.get("timestamp", datetime.utcnow().isoformat()),
                "message_id": properties.message_id if properties else None,
                "processing_latency_ms": self.calculate_processing_latency(properties),
                "worker_id": os.getpid()
            }
            
            logger.debug(f"📡 Broadcasting enhanced sensor data for {node_id}")
            
            # Send to API WebSocket service
            try:
                response = requests.post(
                    f"{self.api_url}/api/internal/broadcast",
                    json=message,
                    timeout=3,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    logger.debug(f"✅ Successfully broadcasted enhanced sensor data for {node_id}")
                else:
                    logger.warning(f"⚠️ Failed to broadcast sensor data: HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"⏱️ Timeout broadcasting sensor data for {node_id}")
            except requests.exceptions.ConnectionError:
                logger.warning(f"🔌 Connection error broadcasting sensor data for {node_id}")
            except Exception as e:
                logger.warning(f"❌ Broadcast error for {node_id}: {e}")
                
        except Exception as e:
            logger.error(f"💥 Error in enhanced sensor data broadcasting: {e}")
    
    def broadcast_status_change_enhanced(self, node_id: str, status: str, metadata: Dict[str, Any] = None):
        """Enhanced status change broadcasting"""
        try:
            message = {
                "type": "node_status_enhanced",
                "node_id": node_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
                "data_points_received": self.node_status.get(node_id, {}).get('data_points', 0),
                "worker_id": os.getpid()
            }
            
            logger.info(f"📡 Broadcasting enhanced status change: {node_id} -> {status}")
            
            try:
                response = requests.post(
                    f"{self.api_url}/api/internal/broadcast",
                    json=message,
                    timeout=3,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    logger.debug(f"✅ Successfully broadcasted status change for {node_id}")
                else:
                    logger.warning(f"⚠️ Failed to broadcast status change: HTTP {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"❌ Status broadcast error for {node_id}: {e}")
                
        except Exception as e:
            logger.error(f"💥 Error in enhanced status broadcasting: {e}")
    
    def update_node_status_offline_enhanced(self, node_id: str, reason: str = "timeout"):
        """Enhanced offline status update"""
        db = None
        try:
            db = self.SessionLocal()
            
            # Update database
            query = text("""
                UPDATE nodes 
                SET status = 'offline', updated_at = :updated_at
                WHERE node_id = :node_id
            """)
            
            now = datetime.utcnow()
            db.execute(query, {
                'node_id': node_id,
                'updated_at': now
            })
            db.commit()
            
            logger.info(f"🔴 Node {node_id} marked offline (reason: {reason})")
            
        except Exception as e:
            logger.error(f"❌ Error updating node to offline: {e}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()

    def check_offline_nodes_enhanced(self):
        """Enhanced offline node detection with better metrics"""
        try:
            now = datetime.utcnow()
            nodes_to_mark_offline = []
            
            for node_id, status_info in self.node_status.items():
                if status_info['status'] == 'online':
                    time_since_last_seen = now - status_info['last_seen']
                    if time_since_last_seen > self.offline_threshold:
                        nodes_to_mark_offline.append({
                            'node_id': node_id,
                            'offline_duration': time_since_last_seen,
                            'last_data_points': status_info.get('data_points', 0)
                        })
            
            for node_info in nodes_to_mark_offline:
                node_id = node_info['node_id']
                offline_duration = node_info['offline_duration']
                
                logger.info(f"🔴 Node {node_id} went offline (no data for {offline_duration.total_seconds():.1f}s)")
                
                # Update in-memory status
                self.node_status[node_id]['status'] = 'offline'
                
                # Update database
                self.update_node_status_offline_enhanced(node_id, "data_timeout")
                
                # Broadcast status change with metadata
                self.broadcast_status_change_enhanced(node_id, 'offline', {
                    'transition': 'online_to_offline',
                    'offline_duration_seconds': offline_duration.total_seconds(),
                    'reason': 'data_timeout'
                })
                
        except Exception as e:
            logger.error(f"💥 Error in enhanced offline node checking: {e}")
    
    def start_enhanced_status_monitor(self):
        """Start enhanced status monitoring with performance metrics"""
        def enhanced_status_monitor():
            monitor_start_time = datetime.utcnow()
            check_count = 0
            
            while True:
                try:
                    check_count += 1
                    self.check_offline_nodes_enhanced()
                    
                    # Log performance metrics every 100 checks
                    if check_count % 100 == 0:
                        uptime = datetime.utcnow() - monitor_start_time
                        logger.info(f"📊 Status monitor metrics:")
                        logger.info(f"   - Uptime: {uptime}")
                        logger.info(f"   - Checks performed: {check_count}")
                        logger.info(f"   - Active nodes: {len([n for n in self.node_status.values() if n['status'] == 'online'])}")
                        logger.info(f"   - Messages processed: {self.message_count}")
                        logger.info(f"   - Error count: {self.error_count}")
                    
                    threading.Event().wait(5)  # Check every 5 seconds
                    
                except Exception as e:
                    logger.error(f"💥 Error in enhanced status monitor: {e}")
                    threading.Event().wait(5)
        
        monitor_thread = threading.Thread(target=enhanced_status_monitor, daemon=True)
        monitor_thread.start()
        logger.info("🔄 Enhanced status monitor started - checking every 5 seconds")
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """Get comprehensive worker statistics"""
        uptime = datetime.utcnow() - self.start_time
        
        online_nodes = len([n for n in self.node_status.values() if n['status'] == 'online'])
        offline_nodes = len([n for n in self.node_status.values() if n['status'] == 'offline'])
        
        return {
            'uptime_seconds': uptime.total_seconds(),
            'messages_processed': self.message_count,
            'error_count': self.error_count,
            'success_rate': (self.message_count / max(self.message_count + self.error_count, 1)) * 100,
            'connected_to_rabbitmq': self.is_connected,
            'node_counts': {
                'online': online_nodes,
                'offline': offline_nodes,
                'total': len(self.node_status)
            },
            'offline_threshold_seconds': self.offline_threshold.total_seconds(),
            'worker_pid': os.getpid()
        }
    
    def start_consuming_enhanced(self):
        """Start enhanced message consumption with better error handling"""
        try:
            # Connect to RabbitMQ
            queue_name = self.connect_rabbitmq()
            
            # Start enhanced status monitoring
            self.start_enhanced_status_monitor()
            
            logger.info("🚀 Enhanced Worker Service started successfully!")
            logger.info(f"📊 Configuration:")
            logger.info(f"   - Offline threshold: {self.offline_threshold.total_seconds()}s")
            logger.info(f"   - Database pool size: 10")
            logger.info(f"   - RabbitMQ prefetch: 10")
            logger.info(f"   - Worker PID: {os.getpid()}")
            
            # Log initial stats
            stats = self.get_worker_stats()
            logger.info(f"📈 Initial stats: {json.dumps(stats, indent=2)}")
            
            # Start consuming with enhanced error handling
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    logger.info("🎯 Starting message consumption...")
                    self.channel.start_consuming()
                    break  # If we get here, consumption ended normally
                    
                except KeyboardInterrupt:
                    logger.info("🛑 Stopping enhanced worker service...")
                    self.channel.stop_consuming()
                    break
                    
                except Exception as e:
                    retry_count += 1
                    logger.error(f"💥 Consumption error (attempt {retry_count}/{max_retries}): {e}")
                    
                    if retry_count < max_retries:
                        logger.info(f"⏳ Retrying in 10 seconds...")
                        time.sleep(10)
                        
                        # Try to reconnect
                        try:
                            self.connect_rabbitmq()
                        except Exception as reconnect_error:
                            logger.error(f"❌ Reconnection failed: {reconnect_error}")
                    else:
                        logger.error("💥 Max retries reached, worker service stopping")
                        raise
            
        except Exception as e:
            logger.error(f"💥 Fatal error in enhanced worker service: {e}")
            raise
        finally:
            # Cleanup
            try:
                if self.connection and not self.connection.is_closed:
                    self.connection.close()
                    logger.info("🔌 RabbitMQ connection closed")
            except:
                pass

# Legacy class name for backwards compatibility
WorkerService = EnhancedWorkerService

def main():
    """Main entry point for the enhanced worker service"""
    logger.info("🚀 Starting RNR IoT Platform - Enhanced Worker Service")
    
    try:
        worker = EnhancedWorkerService()
        worker.start_consuming_enhanced()
    except KeyboardInterrupt:
        logger.info("🛑 Worker service stopped by user")
    except Exception as e:
        logger.error(f"💥 Worker service failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()

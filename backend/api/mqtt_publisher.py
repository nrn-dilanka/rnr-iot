import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
import paho.mqtt.client as mqtt
import threading
import uuid

logger = logging.getLogger(__name__)

class EnhancedMQTTCommandPublisher:
    """Enhanced MQTT command publisher with improved reliability and performance"""
    
    def __init__(self):
        # Configuration from environment variables
        self.mqtt_host = os.getenv("MQTT_BROKER_HOST", "localhost")
        self.mqtt_port = int(os.getenv("MQTT_BROKER_PORT", "1883"))
        self.mqtt_user = os.getenv("MQTT_USERNAME", "rnr_iot_user")
        self.mqtt_password = os.getenv("MQTT_PASSWORD", "rnr_iot_2025!")
        
        # Connection settings
        self.client = None
        self.is_connected = False
        self.connection_lock = threading.Lock()
        
        # Performance tracking
        self.commands_sent = 0
        self.commands_failed = 0
        self.connection_attempts = 0
        self.last_connection_time = None
        
        # Enhanced configuration for persistent sessions
        self.keepalive = 60
        self.qos_level = 1
        self.retain_last_command = True
        self.command_timeout = 30
        self.clean_session = False  # Enable persistent sessions for reliable delivery
        
        # Message tracking
        self.pending_publishes = {}  # Track QoS 1 message confirmations
        self.failed_commands = []
        
        logger.info(f"🚀 Enhanced MQTT Publisher initialized with persistent sessions")
        logger.info(f"   - Broker: {self.mqtt_host}:{self.mqtt_port}")
        logger.info(f"   - User: {self.mqtt_user}")
        logger.info(f"   - QoS Level: {self.qos_level}")
        logger.info(f"   - Persistent Sessions: {not self.clean_session}")
    
    def connect(self) -> bool:
        """Enhanced connection with better error handling and retry logic"""
        with self.connection_lock:
            if self.is_connected and self.client and self.client.is_connected():
                return True
            
            try:
                self.connection_attempts += 1
                logger.info(f"🔗 Connecting to MQTT broker (attempt {self.connection_attempts})")
                
                # Create client with enhanced configuration for persistent sessions
                client_id = f"rnr_backend_publisher_{uuid.uuid4().hex[:8]}"
                self.client = mqtt.Client(
                    client_id=client_id,
                    clean_session=self.clean_session,  # Use configured persistent session setting
                    protocol=mqtt.MQTTv311
                )
                
                # Set authentication
                self.client.username_pw_set(self.mqtt_user, self.mqtt_password)
                
                # Enhanced callbacks
                self.client.on_connect = self._on_connect
                self.client.on_disconnect = self._on_disconnect
                self.client.on_publish = self._on_publish
                self.client.on_log = self._on_log
                
                # Connection options for reliability
                self.client.max_inflight_messages_set(20)
                self.client.max_queued_messages_set(100)
                self.client.message_retry_set(10)
                
                # Connect with timeout
                result = self.client.connect(self.mqtt_host, self.mqtt_port, self.keepalive)
                
                if result == mqtt.MQTT_ERR_SUCCESS:
                    # Start network loop for background processing
                    self.client.loop_start()
                    
                    # Wait for connection confirmation
                    start_time = time.time()
                    while not self.is_connected and (time.time() - start_time) < 10:
                        time.sleep(0.1)
                    
                    if self.is_connected:
                        self.last_connection_time = datetime.utcnow()
                        logger.info(f"✅ Connected to MQTT broker with persistent session!")
                        logger.info(f"   - Client ID: {client_id}")
                        logger.info(f"   - Clean session: {self.clean_session}")
                        logger.info(f"   - Keepalive: {self.keepalive}s")
                        logger.info(f"   - QoS Level: {self.qos_level}")
                        logger.info(f"   - Message queuing: Enabled for offline devices")
                        return True
                    else:
                        logger.error("❌ Connection timeout waiting for CONNACK")
                        return False
                else:
                    error_messages = {
                        1: "Connection refused - incorrect protocol version",
                        2: "Connection refused - invalid client identifier",
                        3: "Connection refused - server unavailable",
                        4: "Connection refused - bad username or password",
                        5: "Connection refused - not authorized"
                    }
                    error_msg = error_messages.get(result, f"Unknown error code {result}")
                    logger.error(f"❌ MQTT connection failed: {error_msg}")
                    return False
                    
            except Exception as e:
                logger.error(f"💥 Exception during MQTT connection: {e}")
                return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Enhanced connection callback"""
        if rc == 0:
            self.is_connected = True
            logger.info(f"✅ MQTT connected with flags: {flags}")
        else:
            self.is_connected = False
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier", 
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorized"
            }
            error_msg = error_messages.get(rc, f"Unknown error code {rc}")
            logger.error(f"❌ MQTT connection failed: {error_msg}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Enhanced disconnection callback"""
        self.is_connected = False
        if rc != 0:
            logger.warning(f"🔌 Unexpected MQTT disconnection (code: {rc})")
        else:
            logger.info("🔌 MQTT disconnected gracefully")
    
    def _on_publish(self, client, userdata, mid):
        """Enhanced publish callback for QoS confirmation"""
        if mid in self.pending_publishes:
            command_info = self.pending_publishes.pop(mid)
            logger.debug(f"✅ Command confirmed published: {command_info.get('node_id', 'unknown')} (mid: {mid})")
        else:
            logger.debug(f"✅ Message published successfully (mid: {mid})")
    
    def _on_log(self, client, userdata, level, buf):
        """Enhanced logging callback"""
        if level == mqtt.MQTT_LOG_ERR:
            logger.error(f"MQTT Error: {buf}")
        elif level == mqtt.MQTT_LOG_WARNING:
            logger.warning(f"MQTT Warning: {buf}")
        # Suppress debug and info logs to avoid spam
    
    def publish_command(self, node_id: str, command: Dict[str, Any], priority: int = 5) -> bool:
        """Enhanced command publishing with comprehensive error handling"""
        if not self.client or not self.is_connected:
            if not self.connect():
                self.commands_failed += 1
                logger.error(f"❌ Cannot publish command - not connected to MQTT broker")
                return False
        
        try:
            # Enhanced command with metadata
            enhanced_command = {
                **command,
                'message_id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat(),
                'cmd_timestamp': int(time.time()),  # For staleness detection
                'node_id': node_id,
                'priority': priority,
                'source': 'rnr_backend_api',
                'retry_count': 0
            }
            
            command_json = json.dumps(enhanced_command)
            topic = f"devices/{node_id}/commands"
            
            # Validate command size
            if len(command_json.encode('utf-8')) > 10240:  # 10KB limit
                logger.error(f"❌ Command too large for {node_id}: {len(command_json)} bytes")
                self.commands_failed += 1
                return False
            
            logger.info(f"📤 Publishing command to {node_id}")
            logger.info(f"   - Action: {command.get('action', 'unknown')}")
            logger.info(f"   - Priority: {priority}")
            logger.info(f"   - Message ID: {enhanced_command['message_id'][:8]}...")
            
            # Publish with QoS=1 for reliable delivery
            message_info = self.client.publish(
                topic=topic,
                payload=command_json,
                qos=self.qos_level,
                retain=False
            )
            
            if message_info.rc == mqtt.MQTT_ERR_SUCCESS:
                # Track pending publish for confirmation
                self.pending_publishes[message_info.mid] = {
                    'node_id': node_id,
                    'action': command.get('action', 'unknown'),
                    'message_id': enhanced_command['message_id'],
                    'timestamp': datetime.utcnow()
                }
                
                # Publish retained "last command" for devices that reconnect
                if self.retain_last_command:
                    try:
                        retained_topic = f"{topic}/last"
                        self.client.publish(
                            topic=retained_topic,
                            payload=command_json,
                            qos=self.qos_level,
                            retain=True
                        )
                        logger.debug(f"📌 Published retained last-command to {retained_topic}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to publish retained command: {e}")
                
                self.commands_sent += 1
                logger.info(f"✅ Command queued for delivery to {node_id}")
                logger.info(f"📦 Message will be delivered when device comes online (persistent session)")
                return True
            else:
                error_messages = {
                    mqtt.MQTT_ERR_NO_CONN: "Not connected to broker",
                    mqtt.MQTT_ERR_QUEUE_SIZE: "Message queue full",
                    mqtt.MQTT_ERR_PAYLOAD_SIZE: "Payload too large",
                    mqtt.MQTT_ERR_PROTOCOL: "Protocol error"
                }
                error_msg = error_messages.get(message_info.rc, f"Error code {message_info.rc}")
                logger.error(f"❌ Failed to queue command for {node_id}: {error_msg}")
                
                self.commands_failed += 1
                self.failed_commands.append({
                    'node_id': node_id,
                    'command': command,
                    'error': error_msg,
                    'timestamp': datetime.utcnow().isoformat()
                })
                return False
                
        except Exception as e:
            logger.error(f"💥 Exception publishing command to {node_id}: {e}")
            self.commands_failed += 1
            self.failed_commands.append({
                'node_id': node_id,
                'command': command,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            return False
    
    def broadcast_command(self, command: Dict[str, Any], exclude_nodes: list = None) -> Dict[str, bool]:
        """Broadcast a command to all devices (use with caution)"""
        exclude_nodes = exclude_nodes or []
        
        # This is a simple implementation - in production you'd want to
        # get the list of active nodes from the database
        logger.warning(f"🔊 Broadcasting command to all devices: {command.get('action', 'unknown')}")
        
        broadcast_topic = "devices/+/commands"  # Wildcard topic
        enhanced_command = {
            **command,
            'message_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'broadcast': True,
            'source': 'rnr_backend_api'
        }
        
        try:
            message_info = self.client.publish(
                topic=broadcast_topic,
                payload=json.dumps(enhanced_command),
                qos=self.qos_level,
                retain=False
            )
            
            if message_info.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✅ Broadcast command queued successfully")
                return {'broadcast': True}
            else:
                logger.error(f"❌ Failed to broadcast command")
                return {'broadcast': False}
                
        except Exception as e:
            logger.error(f"💥 Exception broadcasting command: {e}")
            return {'broadcast': False}
    
    def get_publisher_stats(self) -> Dict[str, Any]:
        """Get comprehensive publisher statistics"""
        uptime = None
        if self.last_connection_time:
            uptime = (datetime.utcnow() - self.last_connection_time).total_seconds()
        
        success_rate = 0
        total_commands = self.commands_sent + self.commands_failed
        if total_commands > 0:
            success_rate = (self.commands_sent / total_commands) * 100
        
        return {
            'is_connected': self.is_connected,
            'connection_attempts': self.connection_attempts,
            'uptime_seconds': uptime,
            'commands_sent': self.commands_sent,
            'commands_failed': self.commands_failed,
            'success_rate_percent': round(success_rate, 2),
            'pending_publishes': len(self.pending_publishes),
            'failed_commands_count': len(self.failed_commands),
            'broker': f"{self.mqtt_host}:{self.mqtt_port}",
            'qos_level': self.qos_level,
            'last_connection': self.last_connection_time.isoformat() if self.last_connection_time else None
        }
    
    def get_failed_commands(self) -> list:
        """Get list of failed commands for debugging"""
        return self.failed_commands.copy()
    
    def clear_failed_commands(self):
        """Clear the failed commands list"""
        self.failed_commands.clear()
        logger.info("🧹 Cleared failed commands list")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_status = {
            'status': 'unknown',
            'timestamp': datetime.utcnow().isoformat(),
            'connection': {
                'connected': self.is_connected,
                'broker': f"{self.mqtt_host}:{self.mqtt_port}"
            },
            'performance': self.get_publisher_stats()
        }
        
        try:
            # Test connection
            if not self.is_connected:
                if self.connect():
                    health_status['status'] = 'healthy'
                else:
                    health_status['status'] = 'unhealthy'
                    health_status['error'] = 'Cannot connect to MQTT broker'
            else:
                # Test publishing capability (dry run)
                test_command = {
                    'action': 'HEALTH_CHECK',
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # Don't actually publish, just validate we can prepare the message
                json.dumps(test_command)
                health_status['status'] = 'healthy'
            
            logger.info(f"✅ MQTT Publisher health check: {health_status['status']}")
            
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
            logger.error(f"❌ MQTT Publisher health check failed: {e}")
        
        return health_status
    
    def disconnect(self):
        """Gracefully disconnect from MQTT broker"""
        with self.connection_lock:
            self.is_connected = False
            
            if self.client:
                try:
                    self.client.loop_stop()
                    self.client.disconnect()
                    logger.info("🔌 Disconnected from MQTT broker")
                except Exception as e:
                    logger.warning(f"⚠️ Error during MQTT disconnect: {e}")
                
                self.client = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

# Global enhanced MQTT command publisher instance
mqtt_command_publisher = EnhancedMQTTCommandPublisher()

# Backwards compatibility alias
MQTTCommandPublisher = EnhancedMQTTCommandPublisher

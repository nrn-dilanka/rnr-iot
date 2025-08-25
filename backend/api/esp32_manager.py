"""
Enhanced MQTT service for automatic ESP32 device discovery and management
"""
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Set
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session

from api.database import get_db, Node, SensorData
from api.websocket import websocket_manager

logger = logging.getLogger(__name__)

class ESP32DeviceManager:
    """Manages automatic ESP32 device discovery and registration"""
    
    def __init__(self):
        self.mqtt_client = None
        self.connected_devices: Set[str] = set()
        self.device_configs: Dict[str, dict] = {}
        self.db_session = None
        
        # MQTT Configuration with persistent session support
        import os
        self.mqtt_host = os.getenv("MQTT_BROKER_HOST", "localhost")
        self.mqtt_port = int(os.getenv("MQTT_BROKER_PORT", "1883"))
        self.mqtt_user = os.getenv("MQTT_USERNAME", "rnr_iot_user")
        self.mqtt_password = os.getenv("MQTT_PASSWORD", "rnr_iot_2025!")
        
        # Enhanced connection settings for persistent sessions
        self.max_retries = int(os.getenv("MQTT_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("MQTT_RETRY_DELAY", "5"))
        self.connection_timeout = int(os.getenv("MQTT_CONNECTION_TIMEOUT", "10"))
        self.keepalive = 60  # Longer keepalive for persistent sessions
        self.qos_level = 1   # QoS=1 for reliable command delivery
        
        # Device discovery topics
        self.data_topic_pattern = "devices/+/data"
        self.command_topic_pattern = "devices/{}/commands"
        
        logger.info("🚀 ESP32 Device Manager with persistent MQTT sessions")
        logger.info(f"   - MQTT Broker: {self.mqtt_host}:{self.mqtt_port}")
        logger.info(f"   - QoS Level: {self.qos_level}")
        logger.info(f"   - Persistent Sessions: Enabled")
        
    async def initialize(self):
        """Initialize the MQTT client and start device discovery"""
        logger.info("Initializing ESP32 Device Manager...")
        
        # Setup MQTT client with persistent session
        client_id = "esp32_device_manager_backend"
        self.mqtt_client = mqtt.Client(
            client_id=client_id,
            clean_session=False,  # Enable persistent sessions
            protocol=mqtt.MQTTv311
        )
        self.mqtt_client.username_pw_set(self.mqtt_user, self.mqtt_password)
        
        # Set callbacks
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message
        self.mqtt_client.on_disconnect = self._on_disconnect
        
        # Connect to MQTT broker with retry logic
        await self._connect_with_retry()
            
    async def _connect_with_retry(self):
        """Connect to MQTT broker with retry logic"""
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Connecting to MQTT broker at {self.mqtt_host}:{self.mqtt_port} (attempt {attempt}/{self.max_retries})")
                
                # Set connection timeout
                self.mqtt_client.socket_timeout = self.connection_timeout
                
                result = self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
                if result == 0:
                    self.mqtt_client.loop_start()
                    logger.info("ESP32 Device Manager started successfully")
                    return
                else:
                    logger.warning(f"MQTT connection failed with code {result}")
                    
            except Exception as e:
                logger.error(f"Failed to connect to MQTT broker (attempt {attempt}): {e}")
                
            if attempt < self.max_retries:
                logger.info(f"Retrying in {self.retry_delay} seconds...")
                await asyncio.sleep(self.retry_delay)
        
        logger.error("All MQTT connection attempts failed - continuing without MQTT")
            
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            logger.info("✅ ESP32 Device Manager connected to MQTT broker")
            # Subscribe to device data topics for auto-discovery
            client.subscribe(self.data_topic_pattern)
            logger.info(f"📡 Subscribed to device discovery topic: {self.data_topic_pattern}")
        else:
            error_codes = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable", 
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorized"
            }
            error_msg = error_codes.get(rc, f"Unknown error code {rc}")
            logger.error(f"❌ Failed to connect to MQTT broker: {error_msg}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        if rc != 0:
            logger.warning(f"🔌 ESP32 Device Manager unexpected disconnection from MQTT (code: {rc})")
        else:
            logger.info("🔌 ESP32 Device Manager disconnected from MQTT gracefully")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming device messages for auto-discovery and data processing"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            # Extract device ID from topic (devices/{device_id}/data)
            topic_parts = topic.split('/')
            if len(topic_parts) >= 3 and topic_parts[0] == "devices" and topic_parts[2] == "data":
                device_id = topic_parts[1]
                
                # Process the message synchronously to avoid event loop issues
                self._process_device_message_sync(device_id, payload)
            
        except Exception as e:
            logger.error(f"Error processing device message: {e}")
    
    def _process_device_message_sync(self, device_id: str, payload: dict):
        """Process incoming device data synchronously (called from MQTT callback)"""
        try:
            # Auto-register new device if not seen before
            if device_id not in self.connected_devices:
                self._auto_register_device_sync(device_id, payload)
            
            # Store sensor data
            self._store_sensor_data_sync(device_id, payload)
            
            # Update device last seen
            self._update_device_status_sync(device_id, payload)
            
            # For WebSocket broadcasting, we'll need to handle this differently
            # since it requires async context
            logger.info(f"📊 Processed data from device {device_id}: {payload}")
            
        except Exception as e:
            logger.error(f"Error processing message from device {device_id}: {e}")
    
    async def _process_device_message(self, device_id: str, payload: dict):
        """Process incoming device data and auto-register new devices"""
        try:
            # Auto-register new device if not seen before
            if device_id not in self.connected_devices:
                await self._auto_register_device(device_id, payload)
            
            # Store sensor data
            await self._store_sensor_data(device_id, payload)
            
            # Update device last seen
            await self._update_device_status(device_id, payload)
            
            # Broadcast to WebSocket clients
            await websocket_manager.broadcast({
                "type": "device_data",
                "device_id": device_id,
                "data": payload
            })
            
        except Exception as e:
            logger.error(f"Error processing message from device {device_id}: {e}")
    
    def _auto_register_device_sync(self, device_id: str, payload: dict):
        """Synchronously register a new ESP32 device"""
        try:
            logger.info(f"🔍 New ESP32 device discovered: {device_id}")
            
            # Get database session
            db = next(get_db())
            
            try:
                # Check if device already exists in database
                existing_device = db.query(Node).filter(Node.node_id == device_id).first()
                
                if not existing_device:
                    # Extract device information from payload
                    device_name = f"ESP32-{device_id[-6:]}"  # Use last 6 chars of device ID
                    
                    # Create new device record
                    new_device = Node(
                        node_id=device_id,
                        name=device_name,
                        mac_address=device_id,  # Using device_id as MAC for now
                        is_active="true",
                        last_seen=datetime.utcnow()
                    )
                    
                    db.add(new_device)
                    db.commit()
                    
                    logger.info(f"✅ Auto-registered new ESP32 device: {device_name} ({device_id})")
                    
                    # Send welcome message to device
                    self._send_welcome_message_sync(device_id)
                    
                else:
                    # Device exists, just mark as active
                    existing_device.is_active = "true"
                    existing_device.last_seen = datetime.utcnow()
                    db.commit()
                    logger.info(f"🔄 ESP32 device reconnected: {existing_device.name} ({device_id})")
                
                # Add to connected devices set
                self.connected_devices.add(device_id)
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error auto-registering device {device_id}: {e}")
    
    def _send_welcome_message_sync(self, device_id: str):
        """Send a welcome message to newly discovered device (synchronous)"""
        try:
            welcome_command = {
                "action": "STATUS_REQUEST",
                "message": "Welcome to RNR Solutions IoT Platform! Device auto-registered successfully.",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            command_topic = self.command_topic_pattern.format(device_id)
            self.mqtt_client.publish(command_topic, json.dumps(welcome_command))
            
            logger.info(f"📨 Sent welcome message to device: {device_id}")
            
        except Exception as e:
            logger.error(f"Error sending welcome message to {device_id}: {e}")
    
    def _store_sensor_data_sync(self, device_id: str, payload: dict):
        """Store sensor data in database (synchronous)"""
        try:
            db = next(get_db())
            
            try:
                # Create sensor data record
                sensor_data = SensorData(
                    node_id=device_id,
                    data=payload  # Store full payload as JSON
                )
                
                db.add(sensor_data)
                db.commit()
                
                logger.debug(f"💾 Stored sensor data for device {device_id}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error storing sensor data for {device_id}: {e}")
    
    def _update_device_status_sync(self, device_id: str, payload: dict):
        """Update device status and last seen timestamp (synchronous)"""
        try:
            db = next(get_db())
            
            try:
                device = db.query(Node).filter(Node.node_id == device_id).first()
                if device:
                    device.last_seen = datetime.utcnow()
                    device.is_active = "true"
                    
                    # Update status based on payload
                    if payload.get("type") == "heartbeat" or payload.get("status"):
                        device.status = payload.get("status", "online")
                    else:
                        device.status = "online"  # Default to online if receiving data
                    
                    db.commit()
                    logger.debug(f"📊 Updated device {device_id} status to {device.status}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error updating device status for {device_id}: {e}")

    async def _auto_register_device(self, device_id: str, payload: dict):
        """Automatically register a new ESP32 device when it first connects"""
        try:
            logger.info(f"🔍 New ESP32 device discovered: {device_id}")
            
            # Get database session
            db = next(get_db())
            
            try:
                # Check if device already exists in database
                existing_device = db.query(Node).filter(Node.node_id == device_id).first()
                
                if not existing_device:
                    # Extract device information from payload
                    device_name = f"ESP32-{device_id[-6:]}"  # Use last 6 chars of MAC
                    
                    # Create new device record
                    new_device = Node(
                        node_id=device_id,
                        name=device_name,
                        mac_address=device_id,  # Using device_id as MAC for now
                        last_seen=datetime.utcnow()
                    )
                    
                    db.add(new_device)
                    db.commit()
                    
                    logger.info(f"✅ Auto-registered new ESP32 device: {device_name} ({device_id})")
                    
                    # Send welcome/configuration message to device
                    await self._send_welcome_message(device_id)
                    
                    # Broadcast device registration to WebSocket clients
                    await websocket_manager.broadcast({
                        "type": "device_registered",
                        "device": {
                            "device_id": device_id,
                            "name": device_name,
                            "is_active": True
                        }
                    })
                else:
                    # Device exists, just mark as active
                    existing_device.is_active = "true"
                    existing_device.last_seen = datetime.utcnow()
                    db.commit()
                    logger.info(f"🔄 ESP32 device reconnected: {existing_device.name} ({device_id})")
                
                # Add to connected devices set
                self.connected_devices.add(device_id)
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error auto-registering device {device_id}: {e}")
    
    async def _send_welcome_message(self, device_id: str):
        """Send a welcome/configuration message to newly discovered device"""
        try:
            welcome_command = {
                "action": "STATUS_REQUEST",
                "message": "Welcome to RNR Solutions IoT Platform! Device auto-registered successfully.",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            command_topic = self.command_topic_pattern.format(device_id)
            self.mqtt_client.publish(command_topic, json.dumps(welcome_command))
            
            logger.info(f"📨 Sent welcome message to device: {device_id}")
            
        except Exception as e:
            logger.error(f"Error sending welcome message to {device_id}: {e}")
    
    async def _store_sensor_data(self, device_id: str, payload: dict):
        """Store sensor data in database"""
        try:
            db = next(get_db())
            
            try:
                # Create sensor data record
                sensor_data = SensorData(
                    node_id=device_id,
                    data=payload  # Store full payload as JSON
                )
                
                db.add(sensor_data)
                db.commit()
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error storing sensor data for {device_id}: {e}")
    
    async def _update_device_status(self, device_id: str, payload: dict):
        """Update device status and last seen timestamp"""
        try:
            db = next(get_db())
            
            try:
                device = db.query(Node).filter(Node.node_id == device_id).first()
                if device:
                    device.last_seen = datetime.utcnow()
                    
                    db.commit()
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error updating device status for {device_id}: {e}")
    
    async def send_command_to_device(self, device_id: str, command: dict):
        """Send a command to a specific ESP32 device with persistent session support"""
        try:
            command_topic = self.command_topic_pattern.format(device_id)
            
            # Add enhanced command metadata
            enhanced_command = {
                **command,
                "timestamp": datetime.utcnow().isoformat(),
                "cmd_timestamp": int(datetime.utcnow().timestamp()),  # For staleness detection
                "message_id": f"cmd_{int(datetime.utcnow().timestamp() * 1000)}",
                "source": "backend_api"
            }
            
            # Publish with QoS=1 for reliable delivery with persistent sessions
            message_info = self.mqtt_client.publish(
                command_topic,
                json.dumps(enhanced_command),
                qos=self.qos_level,  # QoS=1 for reliable delivery
                retain=False
            )
            
            logger.info(f"📤 Command queued for device {device_id}: {command.get('action', 'unknown')}")
            logger.info(f"📦 Using persistent session - command will be delivered when device comes online")
            logger.info(f"🔖 Message ID: {enhanced_command['message_id']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error queuing command for device {device_id}: {e}")
            return False
    
    async def broadcast_command_to_all(self, command: dict):
        """Broadcast a command to all connected ESP32 devices"""
        try:
            success_count = 0
            for device_id in self.connected_devices:
                if await self.send_command_to_device(device_id, command):
                    success_count += 1
            
            logger.info(f"📡 Broadcast command to {success_count}/{len(self.connected_devices)} devices")
            return success_count
            
        except Exception as e:
            logger.error(f"Error broadcasting command: {e}")
            return 0
    
    def get_connected_devices(self) -> Set[str]:
        """Get list of currently connected device IDs"""
        return self.connected_devices.copy()
    
    def is_device_connected(self, device_id: str) -> bool:
        """Check if a specific device is currently connected"""
        return device_id in self.connected_devices

# Global device manager instance
esp32_device_manager = ESP32DeviceManager()

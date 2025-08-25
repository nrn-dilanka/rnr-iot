import os
import json
import logging
import paho.mqtt.client as mqtt
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MQTTCommandPublisher:
    def __init__(self):
        self.mqtt_host = os.getenv("MQTT_HOST", "rabbitmq")
        self.mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
        self.mqtt_user = os.getenv("MQTT_USER", "iotuser")
        self.mqtt_password = os.getenv("MQTT_PASSWORD", "iotpassword")
        self.client = None
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            # Create a named client and use a persistent session so broker can queue
            # messages for subscriptions that belong to this client if needed.
            self.client = mqtt.Client(client_id="rnr_backend_publisher", clean_session=False, protocol=mqtt.MQTTv311)
            self.client.username_pw_set(self.mqtt_user, self.mqtt_password)
            self.client.connect(self.mqtt_host, self.mqtt_port, 60)
            # Start network loop in background to ensure in-flight messages and QoS1/2 delivery are handled
            self.client.loop_start()
            logger.info(f"Connected to MQTT broker at {self.mqtt_host}:{self.mqtt_port} (client_id=rnr_backend_publisher)")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def publish_command(self, node_id: str, command: Dict[str, Any]) -> bool:
        """Publish a command to a specific node via MQTT"""
        if not self.client:
            if not self.connect():
                return False
        
        topic = f"devices/{node_id}/commands"
        message = json.dumps(command)
        
        try:
            result = self.client.publish(topic, message, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published MQTT command to {topic}: {message}")
                # Also publish a retained "last command" message so devices that
                # reconnect without persistent subscriptions can still retrieve
                # the most recent command. This acts as a reliable fallback.
                try:
                    retained_topic = f"{topic}/last"
                    self.client.publish(retained_topic, message, qos=1, retain=True)
                    logger.info(f"Published retained last-command to {retained_topic}")
                except Exception as re:
                    logger.warning(f"Failed to publish retained last-command: {re}")
                return True
            else:
                logger.error(f"Failed to publish MQTT command: {result.rc}")
                return False
        except Exception as e:
            logger.error(f"Error publishing MQTT command: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")

# Global MQTT command publisher instance
mqtt_command_publisher = MQTTCommandPublisher()

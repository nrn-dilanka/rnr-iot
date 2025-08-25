"""
Queue Message Processors for ESP32 Communication
Handles processing of different types of messages from ESP32 devices
"""
import json
from datetime import datetime
import logging

# Import queue manager
try:
    from queue_manager import queue_manager
except ImportError:
    print("⚠️ queue_manager not available - queue responses will not work")
    queue_manager = None

class QueueProcessor:
    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
        
    def log_processing(self, message_type, node_id, success=True):
        """Log message processing statistics"""
        if success:
            self.processed_count += 1
            print(f"✅ Processed {message_type} from {node_id} (total: {self.processed_count})")
        else:
            self.error_count += 1
            print(f"❌ Failed to process {message_type} from {node_id} (errors: {self.error_count})")

# Global processor instance
processor = QueueProcessor()

def process_sensor_data(message):
    """Process sensor data from ESP32"""
    try:
        data = message.get('data', {})
        node_id = data.get('node_id', 'unknown')
        message_id = message.get('message_id', 'unknown')
        
        print(f"🌡️ Processing sensor data from {node_id}:")
        print(f"   Message ID: {message_id}")
        print(f"   Temperature: {data.get('temperature', 'N/A')}°C")
        print(f"   Humidity: {data.get('humidity', 'N/A')}%")
        print(f"   Gas Sensor: {data.get('gas_sensor', 'N/A')}")
        print(f"   WiFi RSSI: {data.get('wifi_rssi', 'N/A')} dBm")
        print(f"   Uptime: {data.get('uptime', 'N/A')} ms")
        
        # Store in database (implement your database logic here)
        save_result = save_sensor_data_to_db(data)
        
        # Check for alert conditions
        check_alert_conditions(data)
        
        # Send acknowledgment back to ESP32
        if queue_manager:
            response_data = {
                'status': 'received',
                'message_id': message_id,
                'processed_at': datetime.now().isoformat(),
                'database_saved': save_result,
                'data_points': len(data)
            }
            
            queue_manager.send_response_to_esp32(node_id, 'data_ack', response_data)
        
        processor.log_processing('sensor_data', node_id, True)
        return True
        
    except Exception as e:
        print(f"❌ Error processing sensor data: {e}")
        processor.log_processing('sensor_data', message.get('data', {}).get('node_id', 'unknown'), False)
        return False

def process_alert(message):
    """Process alert from ESP32"""
    try:
        data = message.get('data', {})
        node_id = data.get('node_id', 'unknown')
        alert_type = data.get('alert_type', 'unknown')
        alert_message = data.get('message', 'No message')
        severity = data.get('severity', 'medium')
        
        print(f"🚨 ALERT from {node_id}:")
        print(f"   Type: {alert_type}")
        print(f"   Severity: {severity}")
        print(f"   Message: {alert_message}")
        print(f"   Timestamp: {message.get('timestamp', 'unknown')}")
        
        # Handle different alert types
        action_taken = "logged"
        
        if alert_type == 'temperature':
            action_taken = handle_temperature_alert(data)
        elif alert_type == 'gas':
            action_taken = handle_gas_alert(data)
        elif alert_type == 'humidity':
            action_taken = handle_humidity_alert(data)
        elif alert_type == 'connectivity':
            action_taken = handle_connectivity_alert(data)
        else:
            action_taken = handle_generic_alert(data)
        
        # Log alert to database
        log_alert_to_db(data, action_taken)
        
        # Send alert response
        if queue_manager:
            response_data = {
                'alert_received': True,
                'action_taken': action_taken,
                'timestamp': datetime.now().isoformat(),
                'alert_id': f"alert_{int(datetime.now().timestamp())}"
            }
            
            queue_manager.send_response_to_esp32(node_id, 'alert_ack', response_data)
        
        processor.log_processing('alert', node_id, True)
        return True
        
    except Exception as e:
        print(f"❌ Error processing alert: {e}")
        processor.log_processing('alert', message.get('data', {}).get('node_id', 'unknown'), False)
        return False

def process_data_request(message):
    """Process data request from ESP32"""
    try:
        data = message.get('data', {})
        node_id = data.get('node_id', 'unknown')
        request_type = data.get('request_type', 'unknown')
        
        print(f"📝 Data request from {node_id}: {request_type}")
        
        response_sent = False
        
        # Handle different request types
        if request_type == 'config':
            config_data = get_esp32_config(node_id)
            if queue_manager:
                queue_manager.send_response_to_esp32(node_id, 'config_update', config_data)
                response_sent = True
            
        elif request_type == 'commands':
            pending_commands = get_pending_commands(node_id)
            if queue_manager:
                queue_manager.send_response_to_esp32(node_id, 'command_batch', pending_commands)
                response_sent = True
            
        elif request_type == 'status':
            status_data = {'requested_status': 'send_full_status'}
            if queue_manager:
                queue_manager.send_response_to_esp32(node_id, 'status_request', status_data)
                response_sent = True
                
        elif request_type == 'time_sync':
            time_data = {
                'current_time': datetime.now().isoformat(),
                'timezone': 'UTC',
                'ntp_server': 'pool.ntp.org'
            }
            if queue_manager:
                queue_manager.send_response_to_esp32(node_id, 'time_sync', time_data)
                response_sent = True
        
        print(f"📤 Response sent to {node_id}: {response_sent}")
        processor.log_processing('data_request', node_id, response_sent)
        return response_sent
        
    except Exception as e:
        print(f"❌ Error processing data request: {e}")
        processor.log_processing('data_request', message.get('data', {}).get('node_id', 'unknown'), False)
        return False

def process_status_update(message):
    """Process status update from ESP32"""
    try:
        data = message.get('data', {})
        node_id = data.get('node_id', 'unknown')
        status = data.get('status', 'unknown')
        
        print(f"📊 Status update from {node_id}: {status}")
        
        # Update device status in database
        update_device_status(node_id, data)
        
        # Check if any action needed based on status
        if status == 'low_memory':
            send_memory_optimization_config(node_id)
        elif status == 'high_temperature':
            send_cooling_commands(node_id)
        elif status == 'connectivity_issues':
            send_connectivity_troubleshooting(node_id)
        
        processor.log_processing('status_update', node_id, True)
        return True
        
    except Exception as e:
        print(f"❌ Error processing status update: {e}")
        processor.log_processing('status_update', message.get('data', {}).get('node_id', 'unknown'), False)
        return False

# Alert Handlers
def handle_temperature_alert(data):
    """Handle temperature alerts"""
    try:
        temp = data.get('temperature', 0)
        node_id = data.get('node_id', 'unknown')
        
        if temp > 35:
            print("🔥 Critical temperature detected - emergency cooling")
            # Send emergency cooling command
            if queue_manager:
                cooling_command = {
                    'action': 'FAN_CONTROL',
                    'state': True,
                    'speed': 100,
                    'reason': 'critical_temperature_alert',
                    'duration': 300000  # 5 minutes
                }
                queue_manager.send_command_to_esp32(node_id, 'FAN_CONTROL', cooling_command, priority=10)
            return "emergency_cooling_activated"
            
        elif temp > 30:
            print("🌡️ High temperature detected - activating cooling")
            # Send normal cooling command
            if queue_manager:
                cooling_command = {
                    'action': 'FAN_CONTROL',
                    'state': True,
                    'speed': 70,
                    'reason': 'temperature_alert'
                }
                queue_manager.send_command_to_esp32(node_id, 'FAN_CONTROL', cooling_command, priority=7)
            return "cooling_activated"
        
        return "temperature_logged"
        
    except Exception as e:
        print(f"❌ Error handling temperature alert: {e}")
        return "error_handling_temperature"

def handle_gas_alert(data):
    """Handle gas sensor alerts"""
    try:
        gas_level = data.get('gas_sensor', 0)
        node_id = data.get('node_id', 'unknown')
        
        if gas_level > 3000:
            print("💨 Critical gas levels detected - emergency ventilation")
            # Send emergency ventilation command
            if queue_manager:
                ventilation_command = {
                    'action': 'FAN_CONTROL',
                    'state': True,
                    'speed': 100,
                    'reason': 'critical_gas_alert',
                    'duration': 600000  # 10 minutes
                }
                queue_manager.send_command_to_esp32(node_id, 'FAN_CONTROL', ventilation_command, priority=10)
                
                # Also turn on lights for visibility
                light_command = {
                    'action': 'LIGHT_CONTROL',
                    'state': True,
                    'reason': 'gas_emergency'
                }
                queue_manager.send_command_to_esp32(node_id, 'LIGHT_CONTROL', light_command, priority=9)
            
            return "emergency_ventilation_activated"
            
        elif gas_level > 2000:
            print("🌬️ High gas levels detected - activating ventilation")
            # Send normal ventilation command
            if queue_manager:
                ventilation_command = {
                    'action': 'FAN_CONTROL',
                    'state': True,
                    'speed': 80,
                    'reason': 'gas_alert'
                }
                queue_manager.send_command_to_esp32(node_id, 'FAN_CONTROL', ventilation_command, priority=8)
            
            return "ventilation_activated"
        
        return "gas_levels_normal"
        
    except Exception as e:
        print(f"❌ Error handling gas alert: {e}")
        return "error_handling_gas"

def handle_humidity_alert(data):
    """Handle humidity alerts"""
    try:
        humidity = data.get('humidity', 0)
        node_id = data.get('node_id', 'unknown')
        
        if humidity > 85:
            print("💧 High humidity detected - activating dehumidification")
            # Send dehumidification command
            if queue_manager:
                dehumidify_command = {
                    'action': 'FAN_CONTROL',
                    'state': True,
                    'speed': 60,
                    'reason': 'high_humidity'
                }
                queue_manager.send_command_to_esp32(node_id, 'FAN_CONTROL', dehumidify_command, priority=6)
            
            return "dehumidification_activated"
        
        return "humidity_normal"
        
    except Exception as e:
        print(f"❌ Error handling humidity alert: {e}")
        return "error_handling_humidity"

def handle_connectivity_alert(data):
    """Handle connectivity alerts"""
    try:
        rssi = data.get('wifi_rssi', 0)
        node_id = data.get('node_id', 'unknown')
        
        if rssi < -80:
            print("📶 Poor WiFi signal detected - sending optimization config")
            # Send WiFi optimization config
            if queue_manager:
                wifi_config = {
                    'reduce_transmission_rate': True,
                    'increase_retry_attempts': True,
                    'enable_power_save': False
                }
                queue_manager.send_response_to_esp32(node_id, 'wifi_optimization', wifi_config)
            
            return "wifi_optimization_sent"
        
        return "connectivity_normal"
        
    except Exception as e:
        print(f"❌ Error handling connectivity alert: {e}")
        return "error_handling_connectivity"

def handle_generic_alert(data):
    """Handle generic alerts"""
    alert_type = data.get('alert_type', 'unknown')
    print(f"ℹ️ Generic alert handled: {alert_type}")
    return f"generic_alert_{alert_type}_logged"

# Data Helper Functions
def save_sensor_data_to_db(data):
    """Save sensor data to database (implement your database logic here)"""
    try:
        # Placeholder for database saving logic
        print(f"💾 Saving sensor data to database for node: {data.get('node_id', 'unknown')}")
        return True
    except Exception as e:
        print(f"❌ Database save error: {e}")
        return False

def log_alert_to_db(data, action_taken):
    """Log alert to database"""
    try:
        # Placeholder for alert logging logic
        print(f"📝 Logging alert to database: {data.get('alert_type', 'unknown')} - {action_taken}")
        return True
    except Exception as e:
        print(f"❌ Alert logging error: {e}")
        return False

def update_device_status(node_id, status_data):
    """Update device status in database"""
    try:
        # Placeholder for status update logic
        print(f"🔄 Updating device status for {node_id}")
        return True
    except Exception as e:
        print(f"❌ Status update error: {e}")
        return False

def check_alert_conditions(data):
    """Check sensor data for alert conditions"""
    try:
        node_id = data.get('node_id', 'unknown')
        
        # Temperature check
        temp = data.get('temperature', 0)
        if temp > 30:
            print(f"⚠️ Temperature alert condition detected: {temp}°C")
        
        # Gas sensor check
        gas = data.get('gas_sensor', 0)
        if gas > 2000:
            print(f"⚠️ Gas alert condition detected: {gas}")
        
        # Humidity check
        humidity = data.get('humidity', 0)
        if humidity > 80:
            print(f"⚠️ Humidity alert condition detected: {humidity}%")
        
        # WiFi signal check
        rssi = data.get('wifi_rssi', 0)
        if rssi < -70:
            print(f"⚠️ WiFi signal weak: {rssi} dBm")
            
    except Exception as e:
        print(f"❌ Error checking alert conditions: {e}")

def get_esp32_config(node_id):
    """Get configuration for specific ESP32"""
    try:
        # Placeholder for configuration retrieval
        config = {
            'sensor_interval': 1000,
            'heartbeat_interval': 30000,
            'alert_thresholds': {
                'temperature_max': 30,
                'temperature_critical': 35,
                'gas_max': 2000,
                'gas_critical': 3000,
                'humidity_max': 80,
                'wifi_rssi_min': -70
            },
            'device_settings': {
                'enable_auto_cooling': True,
                'enable_auto_ventilation': True,
                'power_save_mode': False
            }
        }
        print(f"📋 Retrieved config for {node_id}")
        return config
    except Exception as e:
        print(f"❌ Error getting config for {node_id}: {e}")
        return {}

def get_pending_commands(node_id):
    """Get pending commands for ESP32"""
    try:
        # Placeholder for pending commands retrieval
        commands = [
            {'action': 'LIGHT_CONTROL', 'state': True, 'reason': 'scheduled'},
            {'action': 'SERVO_CONTROL', 'angle': 45, 'reason': 'calibration'}
        ]
        print(f"📋 Retrieved {len(commands)} pending commands for {node_id}")
        return commands
    except Exception as e:
        print(f"❌ Error getting pending commands for {node_id}: {e}")
        return []

# Convenience functions for specific device actions
def send_memory_optimization_config(node_id):
    """Send memory optimization configuration"""
    if queue_manager:
        config = {
            'reduce_buffer_size': True,
            'enable_garbage_collection': True,
            'optimize_json_processing': True
        }
        queue_manager.send_response_to_esp32(node_id, 'memory_optimization', config)

def send_cooling_commands(node_id):
    """Send cooling commands to device"""
    if queue_manager:
        command = {
            'action': 'FAN_CONTROL',
            'state': True,
            'speed': 80,
            'reason': 'auto_cooling'
        }
        queue_manager.send_command_to_esp32(node_id, 'FAN_CONTROL', command, priority=7)

def send_connectivity_troubleshooting(node_id):
    """Send connectivity troubleshooting commands"""
    if queue_manager:
        commands = {
            'wifi_scan': True,
            'signal_strength_report': True,
            'connection_diagnostics': True
        }
        queue_manager.send_response_to_esp32(node_id, 'connectivity_troubleshooting', commands)

# Export main functions
__all__ = [
    'process_sensor_data', 'process_alert', 'process_data_request', 'process_status_update',
    'processor', 'QueueProcessor'
]

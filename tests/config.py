# Test Configuration File for MQTT Persistent Sessions

# API Configuration
API_BASE_URL = "http://localhost:3005/api"
API_TIMEOUT = 5  # seconds

# MQTT Configuration
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_USERNAME = "rnr_iot_user"
MQTT_PASSWORD = "rnr_iot_2025!"
MQTT_TIMEOUT = 60  # seconds

# Test Configuration
TEST_NODE_ID = "AABBCCDDEEFF"
TEST_TIMEOUT = 30  # seconds for individual tests
LOAD_TEST_COMMANDS = 20  # number of commands for load testing

# ESP32 Serial Configuration
# Update these values for your system
ESP32_SERIAL_PORT = "COM3"  # Windows
# ESP32_SERIAL_PORT = "/dev/ttyUSB0"  # Linux
# ESP32_SERIAL_PORT = "/dev/cu.usbserial-*"  # macOS
ESP32_BAUDRATE = 115200
ESP32_SERIAL_TIMEOUT = 1

# Test Thresholds
MIN_SUCCESS_RATE = 80  # Minimum success rate for tests to pass
DATA_TRANSMISSION_TOLERANCE = 20  # Percentage tolerance for timing tests
QOS_RELIABILITY_THRESHOLD = 95  # Minimum QoS reliability percentage

# Logging Configuration
LOG_LEVEL = "INFO"
ENABLE_VERBOSE_LOGGING = True

# Performance Test Configuration
PERFORMANCE_TEST_DURATION = 15  # seconds
PERFORMANCE_COMMAND_COUNT = 20
PERFORMANCE_API_THRESHOLD = 95  # percentage
PERFORMANCE_MQTT_THRESHOLD = 95  # percentage

# Integration Test Configuration
INTEGRATION_TEST_DEVICES = ["DEVICE_001", "DEVICE_002", "DEVICE_003"]
PERSISTENT_SESSION_TEST_COMMANDS = 3
MULTI_DEVICE_TIMEOUT = 10  # seconds

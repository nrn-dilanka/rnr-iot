# MQTT Persistent Session Test Cases

## 🧪 Test Suite Overview

This document provides comprehensive test cases for the enhanced MQTT persistent session system, covering both ESP32 firmware and backend services.

## 📋 Test Categories

1. **ESP32 Firmware Tests**
2. **Backend API Tests**
3. **MQTT Broker Tests**
4. **Integration Tests**
5. **Performance Tests**
6. **Error Handling Tests**

---

## 1. 🔧 ESP32 Firmware Tests

### Test Case 1.1: Persistent Session Connection

**Objective**: Verify ESP32 connects with persistent session enabled

**Prerequisites**:

- ESP32 flashed with updated firmware
- RabbitMQ MQTT broker running
- WiFi network available

**Test Steps**:

1. Power on ESP32
2. Monitor serial output
3. Verify connection to MQTT broker

**Expected Results**:

```
Connected to RabbitMQ MQTT broker with persistent session!
📦 Persistent session enabled - queued messages will be received on reconnect
Subscribed to: devices/AABBCCDDEEFF/commands (qos=1, persistent)
🔄 Persistent session active - checking for queued messages...
💭 Any commands sent while offline will be delivered now
```

**Pass Criteria**: ✅ Connection established with cleanSession=false

---

### Test Case 1.2: Command Reception While Online

**Objective**: Verify ESP32 receives and executes commands when online

**Test Steps**:

1. ESP32 connected and online
2. Send command via web dashboard: `{"action": "LIGHT_CONTROL", "state": true}`
3. Monitor serial output

**Expected Results**:

```
📨 Message received on topic: devices/AABBCCDDEEFF/commands
📏 Message length: 45 bytes
📋 Message content: {"action":"LIGHT_CONTROL","state":true}
💡 Received light control command via MQTT
💡 Light turned ON
```

**Pass Criteria**: ✅ Command executed immediately

---

### Test Case 1.3: Queued Command Reception After Reconnection

**Objective**: Verify ESP32 receives queued commands after reconnection

**Test Steps**:

1. ESP32 connected and online
2. Disconnect ESP32 power
3. Send commands via dashboard:
   - `{"action": "LIGHT_CONTROL", "state": true}`
   - `{"action": "SERVO_CONTROL", "angle": 45}`
   - `{"action": "FAN_CONTROL", "state": true}`
4. Reconnect ESP32 power
5. Monitor serial output

**Expected Results**:

```
Connected to RabbitMQ MQTT broker with persistent session!
🔄 Persistent session active - checking for queued messages...
📨 Message received on topic: devices/AABBCCDDEEFF/commands
💡 Light turned ON
📨 Message received on topic: devices/AABBCCDDEEFF/commands
🔧 Servo moved to 45°
📨 Message received on topic: devices/AABBCCDDEEFF/commands
🌀 Fan turned ON
```

**Pass Criteria**: ✅ All queued commands executed in order

---

### Test Case 1.4: Data Transmission Every 1 Second

**Objective**: Verify ESP32 sends sensor data every 1 second

**Test Steps**:

1. ESP32 connected and online
2. Monitor serial output for 10 seconds
3. Count data transmission messages

**Expected Results**:

- 10 sensor data messages in 10 seconds
- Messages contain: temperature, humidity, gas_sensor, etc.

**Pass Criteria**: ✅ Consistent 1-second interval data transmission

---

## 2. 🖥️ Backend API Tests

### Test Case 2.1: MQTT Status Endpoint

**Objective**: Verify MQTT status endpoint returns correct information

**Test Steps**:

1. Backend services running
2. Send GET request to `/api/mqtt/status`

**Expected Response**:

```json
{
  "timestamp": "2025-08-25T10:30:00Z",
  "persistent_sessions": {
    "enabled": true,
    "description": "Commands are queued for offline devices"
  },
  "device_manager": {
    "connected_devices": 1,
    "device_list": ["AABBCCDDEEFF"]
  },
  "mqtt_publisher": {
    "commands_sent": 0,
    "commands_failed": 0,
    "connection_status": true,
    "qos_level": 1,
    "clean_session": false
  }
}
```

**Pass Criteria**: ✅ Response shows persistent_sessions.enabled = true

---

### Test Case 2.2: Command Queuing Response

**Objective**: Verify enhanced command response messages

**Test Steps**:

1. Send POST to `/api/nodes/AABBCCDDEEFF/actions`
2. Body: `{"action": "LIGHT_CONTROL", "value": true}`

**Expected Response**:

```json
{
  "message": "Command 'LIGHT_CONTROL' queued successfully for delivery via MQTT"
}
```

**Pass Criteria**: ✅ Response indicates command was queued

---

### Test Case 2.3: Enhanced Command Metadata

**Objective**: Verify commands include enhanced metadata

**Test Steps**:

1. Monitor MQTT traffic using MQTT client
2. Send command via API
3. Capture published message

**Expected Message**:

```json
{
  "action": "LIGHT_CONTROL",
  "value": true,
  "timestamp": "2025-08-25T10:30:00Z",
  "cmd_timestamp": 1724584200,
  "message_id": "cmd_1724584200123",
  "source": "backend_api"
}
```

**Pass Criteria**: ✅ Message includes metadata fields

---

## 3. 📡 MQTT Broker Tests

### Test Case 3.1: Persistent Session Storage

**Objective**: Verify broker stores messages for offline clients

**Test Steps**:

1. Connect ESP32 with client ID `ESP32-AABBCCDDEEFF`
2. Disconnect ESP32
3. Publish command to `devices/AABBCCDDEEFF/commands`
4. Reconnect ESP32 with same client ID
5. Verify message delivery

**Pass Criteria**: ✅ Message delivered after reconnection

---

### Test Case 3.2: QoS=1 Message Delivery

**Objective**: Verify QoS=1 delivery confirmation

**Test Steps**:

1. Subscribe to topic with QoS=1
2. Publish message with QoS=1
3. Monitor PUBACK acknowledgment

**Pass Criteria**: ✅ PUBACK received for published message

---

## 4. 🔄 Integration Tests

### Test Case 4.1: End-to-End Command Flow

**Objective**: Test complete command flow from web UI to ESP32

**Test Steps**:

1. Open web dashboard
2. ESP32 online and connected
3. Click "Turn On Light" button
4. Monitor ESP32 serial output

**Expected Flow**:

```
Web UI → Backend API → MQTT Broker → ESP32 → Light ON
```

**Pass Criteria**: ✅ Light turns on within 2 seconds

---

### Test Case 4.2: Offline Device Command Queuing

**Objective**: Test command queuing for offline device

**Test Steps**:

1. ESP32 offline (powered off)
2. Send 3 different commands via web UI
3. Power on ESP32
4. Verify all commands execute

**Expected Behavior**:

- Commands accepted by API while device offline
- All 3 commands execute when device comes online
- Commands execute in correct order

**Pass Criteria**: ✅ All queued commands executed successfully

---

### Test Case 4.3: Multiple Device Management

**Objective**: Test persistent sessions with multiple ESP32 devices

**Test Steps**:

1. Connect 3 ESP32 devices
2. Disconnect device 2
3. Send commands to all devices
4. Reconnect device 2
5. Verify selective command delivery

**Pass Criteria**: ✅ Each device receives only its commands

---

## 5. ⚡ Performance Tests

### Test Case 5.1: High-Frequency Data Transmission

**Objective**: Test 1-second data transmission under load

**Test Steps**:

1. Run ESP32 for 1 hour
2. Monitor data transmission consistency
3. Check for missed intervals

**Expected Results**:

- 3600 data messages in 1 hour
- <1% missed transmissions
- Consistent timing intervals

**Pass Criteria**: ✅ >99% transmission success rate

---

### Test Case 5.2: Command Queue Performance

**Objective**: Test handling of multiple queued commands

**Test Steps**:

1. ESP32 offline
2. Send 50 commands rapidly
3. Bring ESP32 online
4. Monitor command execution

**Expected Results**:

- All 50 commands queued successfully
- Commands execute in order
- No command loss

**Pass Criteria**: ✅ 100% command delivery

---

### Test Case 5.3: Connection Recovery Performance

**Objective**: Test reconnection speed and reliability

**Test Steps**:

1. ESP32 connected
2. Simulate WiFi interruption (10 times)
3. Measure reconnection time
4. Verify session persistence

**Expected Results**:

- Reconnection within 30 seconds
- Session maintained across reconnections
- No message loss

**Pass Criteria**: ✅ <30s average reconnection time

---

## 6. 🚨 Error Handling Tests

### Test Case 6.1: WiFi Connection Failure Recovery

**Objective**: Test recovery from WiFi failures

**Test Steps**:

1. ESP32 connected
2. Disable WiFi router
3. Wait 2 minutes
4. Re-enable WiFi router
5. Monitor recovery

**Expected Behavior**:

```
WiFi disconnected.
Attempting to reconnect to WiFi...
WiFi Connected successfully!
Connected to RabbitMQ MQTT broker with persistent session!
🔄 Persistent session active - checking for queued messages...
```

**Pass Criteria**: ✅ Automatic recovery within 60 seconds

---

### Test Case 6.2: MQTT Broker Disconnection

**Objective**: Test recovery from broker disconnections

**Test Steps**:

1. ESP32 connected to broker
2. Stop RabbitMQ service
3. Send commands (should queue)
4. Start RabbitMQ service
5. Verify command delivery

**Pass Criteria**: ✅ Commands delivered after broker recovery

---

### Test Case 6.3: Invalid Command Handling

**Objective**: Test handling of malformed commands

**Test Steps**:

1. Send invalid JSON: `{"action": "INVALID_ACTION"}`
2. Send malformed JSON: `{"action":}`
3. Monitor ESP32 response

**Expected Behavior**:

```
JSON parsing failed: InvalidInput
Unknown action: INVALID_ACTION
```

**Pass Criteria**: ✅ Graceful error handling, no crashes

---

## 7. 🧪 Automated Test Scripts

### Test Script 7.1: Python Test Suite

```python
#!/usr/bin/env python3
"""
Automated test suite for MQTT persistent sessions
"""
import requests
import json
import time
import paho.mqtt.client as mqtt
from datetime import datetime

class PersistentSessionTester:
    def __init__(self):
        self.api_base = "http://localhost:3005/api"
        self.mqtt_host = "localhost"
        self.mqtt_port = 1883
        self.mqtt_user = "rnr_iot_user"
        self.mqtt_password = "rnr_iot_2025!"
        self.test_node_id = "AABBCCDDEEFF"

    def test_mqtt_status(self):
        """Test MQTT status endpoint"""
        response = requests.get(f"{self.api_base}/mqtt/status")
        data = response.json()

        assert response.status_code == 200
        assert data["persistent_sessions"]["enabled"] == True
        assert data["mqtt_publisher"]["qos_level"] == 1
        assert data["mqtt_publisher"]["clean_session"] == False

        print("✅ MQTT Status Test: PASSED")

    def test_command_queuing(self):
        """Test command queuing response"""
        command = {"action": "LIGHT_CONTROL", "value": True}
        response = requests.post(
            f"{self.api_base}/nodes/{self.test_node_id}/actions",
            json=command
        )

        assert response.status_code == 200
        data = response.json()
        assert "queued successfully" in data["message"]

        print("✅ Command Queuing Test: PASSED")

    def test_mqtt_message_format(self):
        """Test MQTT message format"""
        received_messages = []

        def on_message(client, userdata, msg):
            message = json.loads(msg.payload.decode())
            received_messages.append(message)

        # Subscribe to command topic
        client = mqtt.Client("test_client")
        client.username_pw_set(self.mqtt_user, self.mqtt_password)
        client.on_message = on_message
        client.connect(self.mqtt_host, self.mqtt_port, 60)
        client.subscribe(f"devices/{self.test_node_id}/commands")
        client.loop_start()

        # Send command via API
        command = {"action": "TEST_COMMAND"}
        requests.post(
            f"{self.api_base}/nodes/{self.test_node_id}/actions",
            json=command
        )

        # Wait for message
        time.sleep(2)
        client.loop_stop()
        client.disconnect()

        assert len(received_messages) > 0
        msg = received_messages[0]
        assert "message_id" in msg
        assert "cmd_timestamp" in msg
        assert "source" in msg
        assert msg["source"] == "backend_api"

        print("✅ MQTT Message Format Test: PASSED")

    def run_all_tests(self):
        """Run all automated tests"""
        print("🧪 Starting Persistent Session Test Suite...")
        print("=" * 50)

        try:
            self.test_mqtt_status()
            self.test_command_queuing()
            self.test_mqtt_message_format()

            print("=" * 50)
            print("🎉 ALL TESTS PASSED!")

        except Exception as e:
            print(f"❌ TEST FAILED: {e}")
            return False

        return True

if __name__ == "__main__":
    tester = PersistentSessionTester()
    tester.run_all_tests()
```

### Test Script 7.2: ESP32 Serial Monitor Test

```python
#!/usr/bin/env python3
"""
ESP32 Serial Monitor Test for Persistent Sessions
"""
import serial
import time
import re
from datetime import datetime

class ESP32SerialTester:
    def __init__(self, port="COM3", baudrate=115200):
        self.serial = serial.Serial(port, baudrate, timeout=1)
        self.test_results = []

    def wait_for_pattern(self, pattern, timeout=30):
        """Wait for specific pattern in serial output"""
        start_time = time.time()
        buffer = ""

        while time.time() - start_time < timeout:
            if self.serial.in_waiting:
                data = self.serial.read(self.serial.in_waiting).decode('utf-8', errors='ignore')
                buffer += data
                print(data, end='')  # Echo to console

                if re.search(pattern, buffer):
                    return True

        return False

    def test_persistent_connection(self):
        """Test persistent session connection"""
        print("🔗 Testing persistent session connection...")

        patterns = [
            r"persistent session",
            r"qos=1, persistent",
            r"checking for queued messages"
        ]

        for pattern in patterns:
            if self.wait_for_pattern(pattern, 30):
                print(f"✅ Found: {pattern}")
            else:
                print(f"❌ Missing: {pattern}")
                return False

        return True

    def test_data_transmission_rate(self):
        """Test 1-second data transmission"""
        print("📊 Testing 1-second data transmission...")

        message_count = 0
        start_time = time.time()

        while time.time() - start_time < 10:  # Test for 10 seconds
            if self.wait_for_pattern(r"Data sent to RabbitMQ", 2):
                message_count += 1

        expected_messages = 10  # 10 seconds at 1-second intervals
        success_rate = (message_count / expected_messages) * 100

        print(f"📈 Messages sent: {message_count}/{expected_messages}")
        print(f"📈 Success rate: {success_rate:.1f}%")

        return success_rate >= 90  # 90% success rate threshold

    def run_tests(self):
        """Run all ESP32 serial tests"""
        print("🧪 Starting ESP32 Serial Test Suite...")
        print("=" * 50)

        tests = [
            ("Persistent Connection", self.test_persistent_connection),
            ("Data Transmission Rate", self.test_data_transmission_rate)
        ]

        passed = 0
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")

        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{len(tests)} passed")

        if passed == len(tests):
            print("🎉 ALL ESP32 TESTS PASSED!")
        else:
            print("⚠️ Some ESP32 tests failed!")

        self.serial.close()

if __name__ == "__main__":
    # Update COM port for your system
    tester = ESP32SerialTester(port="COM3")
    tester.run_tests()
```

## 8. 📋 Manual Test Checklist

### Pre-Test Setup

- [ ] RabbitMQ running with MQTT plugin
- [ ] Backend services started
- [ ] ESP32 flashed with updated firmware
- [ ] Web dashboard accessible
- [ ] Serial monitor connected to ESP32

### Basic Functionality Tests

- [ ] ESP32 connects with persistent session
- [ ] Commands work when device online
- [ ] Data transmitted every 1 second
- [ ] Web dashboard shows device status

### Persistent Session Tests

- [ ] Commands queued when device offline
- [ ] Queued commands delivered on reconnection
- [ ] Multiple commands execute in order
- [ ] Session survives power cycles

### Error Recovery Tests

- [ ] Recovers from WiFi disconnection
- [ ] Recovers from MQTT broker restart
- [ ] Handles invalid commands gracefully
- [ ] Reconnects after network issues

### Performance Tests

- [ ] Consistent 1-second data intervals
- [ ] Commands execute within 2 seconds
- [ ] No memory leaks over 1 hour
- [ ] Handles 50+ queued commands

## 9. 📊 Test Results Template

### Test Execution Report

**Date**: ******\_******
**Tester**: ******\_******
**Environment**: ******\_******

#### Test Results Summary

| Test Category  | Total Tests | Passed   | Failed   | Success Rate |
| -------------- | ----------- | -------- | -------- | ------------ |
| ESP32 Firmware | 4           | \_\_     | \_\_     | \_\_%        |
| Backend API    | 3           | \_\_     | \_\_     | \_\_%        |
| MQTT Broker    | 2           | \_\_     | \_\_     | \_\_%        |
| Integration    | 3           | \_\_     | \_\_     | \_\_%        |
| Performance    | 3           | \_\_     | \_\_     | \_\_%        |
| Error Handling | 3           | \_\_     | \_\_     | \_\_%        |
| **TOTAL**      | **18**      | **\_\_** | **\_\_** | **\_\_%**    |

#### Critical Issues Found

- [ ] None
- [ ] Minor issues (list below)
- [ ] Major issues (list below)

#### Issues Detail

1. ***
2. ***
3. ***

#### Recommendations

1. ***
2. ***
3. ***

**Overall Assessment**: ✅ PASS / ❌ FAIL

---

## 🚀 Continuous Testing

### GitHub Actions Workflow (Optional)

```yaml
name: MQTT Persistent Session Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start RabbitMQ
        run: docker run -d --name rabbitmq -p 1883:1883 -p 15672:15672 rabbitmq:3-management-alpine
      - name: Run Backend Tests
        run: python tests/test_persistent_sessions.py
      - name: Run Integration Tests
        run: python tests/test_integration.py
```

This comprehensive test suite ensures your **MQTT persistent session** implementation works reliably across all components! 🧪✅

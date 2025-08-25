# MQTT Persistent Session Test Suite

## 📋 Overview

This comprehensive test suite validates the **MQTT persistent session** functionality across all components of your IoT system:

- **ESP32 Firmware** (1-second data transmission + persistent sessions)
- **Backend API** (Enhanced MQTT publisher with QoS=1)
- **MQTT Broker** (RabbitMQ with persistent message queuing)
- **Integration Testing** (End-to-end system validation)

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
# Navigate to tests directory
cd tests

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Start Required Services

```powershell
# Start RabbitMQ (if not running)
docker-compose up -d

# Start backend API
cd backend
npm start
```

### 3. Run All Tests

```powershell
# Run complete test suite
python tests/run_all_tests.py
```

## 🧪 Individual Test Suites

### Backend API Tests

```powershell
python tests/test_persistent_sessions.py
```

Tests:

- ✅ MQTT status endpoint
- ✅ Command queuing responses
- ✅ Message format validation
- ✅ QoS=1 delivery confirmation

### Integration Tests

```powershell
python tests/test_integration.py
```

Tests:

- ✅ End-to-end command flow
- ✅ Persistent session simulation
- ✅ Multiple device management
- ✅ Performance under load

### ESP32 Serial Tests

```powershell
python tests/test_esp32_serial.py
```

Tests:

- ✅ Boot sequence validation
- ✅ Persistent session connection
- ✅ 1-second data transmission
- ✅ Command reception capability

## ⚙️ Configuration

Edit `tests/config.py` to customize:

```python
# API Configuration
API_BASE_URL = "http://localhost:3005/api"

# MQTT Configuration
MQTT_HOST = "localhost"
MQTT_PORT = 1883

# ESP32 Serial Port (update for your system)
ESP32_SERIAL_PORT = "COM3"  # Windows
# ESP32_SERIAL_PORT = "/dev/ttyUSB0"  # Linux
```

## 📊 Test Results

Tests generate detailed reports:

- `test_report_persistent_sessions.json` - Backend API results
- `integration_test_report.json` - Integration test results
- `esp32_serial_test_report.json` - ESP32 firmware results

## 🔍 Manual Testing Checklist

### Pre-Test Setup

- [ ] RabbitMQ running with MQTT plugin
- [ ] Backend services started (`npm start`)
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

## 🧪 Test Scenarios

### Scenario 1: Basic Persistent Session

1. ESP32 online and connected
2. Send command → should execute immediately
3. Disconnect ESP32 power
4. Send 3 commands via web dashboard
5. Reconnect ESP32 power
6. **Expected**: All 3 commands execute in order

### Scenario 2: High-Frequency Data

1. Monitor ESP32 serial output for 60 seconds
2. Count data transmission messages
3. **Expected**: ~60 messages (1 per second)

### Scenario 3: QoS=1 Reliability

1. Subscribe to command topic with QoS=1
2. Send command via API
3. Monitor PUBACK acknowledgments
4. **Expected**: PUBACK received for each message

### Scenario 4: Multiple Device Commands

1. Send commands to 3 different device IDs
2. Monitor MQTT traffic
3. **Expected**: Each device receives only its commands

## 🔧 Troubleshooting

### Common Issues

**"Backend API not accessible"**

```powershell
# Check if backend is running
curl http://localhost:3005/api/nodes

# Start backend if needed
cd backend
npm start
```

**"MQTT Broker connection failed"**

```powershell
# Check RabbitMQ status
docker ps | grep rabbitmq

# Start RabbitMQ if needed
docker-compose up -d
```

**"ESP32 serial connection failed"**

```powershell
# List available serial ports
python -c "import serial.tools.list_ports; print([p.device for p in serial.tools.list_ports.comports()])"

# Update port in tests/config.py
ESP32_SERIAL_PORT = "COM4"  # Use correct port
```

**"Missing dependencies"**

```powershell
pip install requests paho-mqtt pyserial
```

### Debug Mode

Enable verbose logging in `tests/config.py`:

```python
ENABLE_VERBOSE_LOGGING = True
LOG_LEVEL = "DEBUG"
```

## 📈 Success Criteria

**✅ System Ready for Production**

- Backend API Tests: 100% pass rate
- Integration Tests: ≥80% pass rate
- ESP32 Serial Tests: ≥80% pass rate
- Data transmission: ≥90% success rate
- Command delivery: 100% reliability

**⚠️ Needs Attention**

- 60-79% overall pass rate
- Some functionality works but issues exist
- Review failed tests before deployment

**❌ Significant Issues**

- <60% pass rate
- Core functionality broken
- System needs major fixes

## 🚀 Advanced Testing

### Load Testing

```python
# Send 100 commands rapidly
for i in range(100):
    send_command(f"LOAD_TEST_{i}")
```

### Stress Testing

```python
# Multiple devices with high command frequency
devices = ["DEV_001", "DEV_002", "DEV_003"]
for device in devices:
    for i in range(50):
        send_command_to_device(device, f"STRESS_{i}")
```

### Long-Duration Testing

```python
# Run for 24 hours monitoring stability
start_time = time.time()
while time.time() - start_time < 86400:  # 24 hours
    monitor_system_health()
    time.sleep(60)
```

## 📋 Continuous Integration

### GitHub Actions (Optional)

```yaml
name: MQTT Persistent Session Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start RabbitMQ
        run: docker run -d --name rabbitmq -p 1883:1883 rabbitmq:3-management-alpine
      - name: Install dependencies
        run: pip install -r tests/requirements.txt
      - name: Run tests
        run: python tests/run_all_tests.py
```

## 📞 Support

For issues with the test suite:

1. Check **troubleshooting section** above
2. Review **test configuration** in `tests/config.py`
3. Examine **detailed test reports** in JSON files
4. Verify **system prerequisites** are met

---

**Happy Testing!** 🧪✅

This test suite ensures your MQTT persistent session system works reliably across all components!

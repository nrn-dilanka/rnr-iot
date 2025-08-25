#!/usr/bin/env python3
"""
Test Queue Communication
Test script to verify queue functionality between ESP32 and backend
"""
import json
import time
from datetime import datetime

# Import queue components
try:
    from queue_manager import queue_manager
except ImportError:
    print("❌ Cannot import queue_manager. Install pika: pip install pika")
    exit(1)

def test_send_sensor_data():
    """Test sending sensor data to queue"""
    print("🧪 Testing sensor data queue...")
    
    # Simulate ESP32 sensor data
    sensor_data = {
        'node_id': 'TEST_ESP32_001',
        'temperature': 25.6,
        'humidity': 65.2,
        'gas_sensor': 1234,
        'wifi_rssi': -45,
        'uptime': 123456789,
        'status': 'online'
    }
    
    success = queue_manager.send_to_queue('sensor_data', sensor_data, priority=1)
    
    if success:
        print("✅ Sensor data sent to queue successfully")
    else:
        print("❌ Failed to send sensor data to queue")
    
    return success

def test_send_alert():
    """Test sending alert to queue"""
    print("\n🚨 Testing alert queue...")
    
    # Simulate high-priority alert
    alert_data = {
        'node_id': 'TEST_ESP32_001',
        'alert_type': 'temperature',
        'message': 'Temperature critical: 35.5°C',
        'severity': 'high',
        'temperature': 35.5
    }
    
    success = queue_manager.send_to_queue('alerts', alert_data, priority=10)
    
    if success:
        print("✅ Alert sent to queue successfully")
    else:
        print("❌ Failed to send alert to queue")
    
    return success

def test_send_data_request():
    """Test sending data request to queue"""
    print("\n📝 Testing data request queue...")
    
    # Simulate ESP32 requesting configuration
    request_data = {
        'node_id': 'TEST_ESP32_001',
        'request_type': 'config',
        'response_queue': 'esp32_responses_TEST_ESP32_001'
    }
    
    success = queue_manager.send_to_queue('data_requests', request_data, priority=5)
    
    if success:
        print("✅ Data request sent to queue successfully")
    else:
        print("❌ Failed to send data request to queue")
    
    return success

def test_send_response_to_esp32():
    """Test sending response back to ESP32"""
    print("\n📤 Testing ESP32 response queue...")
    
    # Simulate backend sending response to ESP32
    response_data = {
        'sensor_interval': 2000,
        'alert_thresholds': {
            'temperature_max': 30,
            'gas_max': 2000
        },
        'device_settings': {
            'enable_auto_cooling': True
        }
    }
    
    success = queue_manager.send_response_to_esp32('TEST_ESP32_001', 'config_update', response_data)
    
    if success:
        print("✅ Response sent to ESP32 successfully")
    else:
        print("❌ Failed to send response to ESP32")
    
    return success

def test_broadcast_message():
    """Test broadcasting message to all ESP32 devices"""
    print("\n📢 Testing broadcast queue...")
    
    # Simulate broadcasting firmware update notification
    broadcast_data = {
        'firmware_version': '2.1.0',
        'update_url': 'http://example.com/firmware.bin',
        'mandatory': False,
        'release_notes': 'Bug fixes and performance improvements'
    }
    
    success = queue_manager.broadcast_to_all_esp32('firmware_update', broadcast_data)
    
    if success:
        print("✅ Broadcast message sent successfully")
    else:
        print("❌ Failed to send broadcast message")
    
    return success

def test_queue_info():
    """Test getting queue information"""
    print("\n📊 Testing queue information...")
    
    queues_to_check = ['sensor_data', 'alerts', 'data_requests', 'esp32_responses', 'broadcast']
    
    for queue_name in queues_to_check:
        info = queue_manager.get_queue_info(queue_name)
        if info:
            print(f"   📦 {queue_name}: {info['message_count']} messages, {info['consumer_count']} consumers")
        else:
            print(f"   ❌ {queue_name}: Failed to get queue info")

def simulate_esp32_communication():
    """Simulate a complete ESP32 communication cycle"""
    print("\n🔄 Simulating complete ESP32 communication cycle...")
    
    # 1. ESP32 sends sensor data
    print("1. ESP32 sending sensor data...")
    test_send_sensor_data()
    time.sleep(1)
    
    # 2. ESP32 sends alert
    print("\n2. ESP32 sending temperature alert...")
    test_send_alert()
    time.sleep(1)
    
    # 3. ESP32 requests configuration
    print("\n3. ESP32 requesting configuration...")
    test_send_data_request()
    time.sleep(1)
    
    # 4. Backend sends response
    print("\n4. Backend sending configuration response...")
    test_send_response_to_esp32()
    time.sleep(1)
    
    # 5. Backend broadcasts update
    print("\n5. Backend broadcasting firmware update...")
    test_broadcast_message()
    
    print("\n✅ Complete communication cycle simulated!")

def main():
    """Main test function"""
    print("🧪 QUEUE COMMUNICATION TEST SUITE")
    print("=" * 60)
    print(f"🕒 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Connect to RabbitMQ
    print("🔌 Connecting to RabbitMQ...")
    if not queue_manager.connect():
        print("❌ Failed to connect to RabbitMQ")
        print("💡 Make sure RabbitMQ is running: docker-compose up -d")
        return False
    
    print("✅ Connected to RabbitMQ successfully")
    print()
    
    # Run tests
    tests = [
        ("Sensor Data Queue", test_send_sensor_data),
        ("Alert Queue", test_send_alert),
        ("Data Request Queue", test_send_data_request),
        ("ESP32 Response Queue", test_send_response_to_esp32),
        ("Broadcast Queue", test_broadcast_message)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🔍 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
        print()
    
    # Show queue status
    test_queue_info()
    
    # Run complete simulation
    simulate_esp32_communication()
    
    # Final results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"📈 Tests passed: {passed}/{total}")
    print(f"📊 Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Queue system is working correctly!")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    print(f"🕒 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Cleanup
    queue_manager.close()
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

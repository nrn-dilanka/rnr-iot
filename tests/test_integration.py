#!/usr/bin/env python3
"""
Integration test suite for MQTT persistent sessions
Tests end-to-end functionality across all system components
"""
import requests
import json
import time
import paho.mqtt.client as mqtt
from datetime import datetime
import sys
import threading
import queue
import subprocess

class IntegrationTester:
    def __init__(self):
        self.api_base = "http://localhost:3005/api"
        self.mqtt_host = "localhost"
        self.mqtt_port = 1883
        self.mqtt_user = "rnr_iot_user"
        self.mqtt_password = "rnr_iot_2025!"
        self.test_node_id = "AABBCCDDEEFF"
        self.test_results = []
        self.mqtt_messages = queue.Queue()
        
    def log_result(self, test_name, status, message=""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        icon = "✅" if status == "PASS" else "❌"
        print(f"{icon} {test_name}: {status}")
        if message:
            print(f"   📝 {message}")
            
    def setup_mqtt_monitor(self):
        """Setup MQTT message monitoring"""
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                # Subscribe to all device topics
                client.subscribe("devices/+/commands", qos=1)
                client.subscribe("devices/+/data", qos=1)
                print("📡 MQTT monitor connected and subscribed")
            else:
                print(f"❌ MQTT monitor connection failed: {rc}")
        
        def on_message(client, userdata, msg):
            try:
                message_data = {
                    "topic": msg.topic,
                    "payload": json.loads(msg.payload.decode()),
                    "qos": msg.qos,
                    "timestamp": datetime.now().isoformat()
                }
                self.mqtt_messages.put(message_data)
            except json.JSONDecodeError:
                message_data = {
                    "topic": msg.topic,
                    "payload": msg.payload.decode(),
                    "qos": msg.qos,
                    "timestamp": datetime.now().isoformat(),
                    "error": "Invalid JSON"
                }
                self.mqtt_messages.put(message_data)
        
        self.mqtt_client = mqtt.Client("integration_test_monitor", clean_session=False)
        self.mqtt_client.username_pw_set(self.mqtt_user, self.mqtt_password)
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_message = on_message
        
        try:
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            time.sleep(2)  # Wait for connection
            return True
        except Exception as e:
            print(f"❌ Failed to setup MQTT monitor: {e}")
            return False
            
    def cleanup_mqtt_monitor(self):
        """Cleanup MQTT monitoring"""
        if hasattr(self, 'mqtt_client'):
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            
    def wait_for_mqtt_message(self, topic_pattern=None, timeout=10):
        """Wait for MQTT message matching pattern"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                message = self.mqtt_messages.get(timeout=1)
                if topic_pattern is None or topic_pattern in message["topic"]:
                    return message
                else:
                    # Put message back if it doesn't match
                    self.mqtt_messages.put(message)
            except queue.Empty:
                continue
                
        return None
        
    def test_system_health_check(self):
        """Test overall system health"""
        print("🏥 Testing system health...")
        
        health_checks = []
        
        # Check backend API
        try:
            response = requests.get(f"{self.api_base}/nodes", timeout=5)
            if response.status_code == 200:
                health_checks.append(("Backend API", True, "Responding"))
            else:
                health_checks.append(("Backend API", False, f"HTTP {response.status_code}"))
        except Exception as e:
            health_checks.append(("Backend API", False, str(e)))
        
        # Check MQTT status endpoint
        try:
            response = requests.get(f"{self.api_base}/mqtt/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                persistent_enabled = data.get("persistent_sessions", {}).get("enabled", False)
                health_checks.append(("MQTT Status", persistent_enabled, 
                                    "Persistent sessions enabled" if persistent_enabled else "Persistent sessions disabled"))
            else:
                health_checks.append(("MQTT Status", False, f"HTTP {response.status_code}"))
        except Exception as e:
            health_checks.append(("MQTT Status", False, str(e)))
        
        # Check MQTT broker connectivity
        mqtt_connected = hasattr(self, 'mqtt_client') and self.mqtt_client.is_connected()
        health_checks.append(("MQTT Broker", mqtt_connected, 
                            "Connected" if mqtt_connected else "Not connected"))
        
        # Evaluate results
        passed_checks = sum(1 for _, status, _ in health_checks if status)
        total_checks = len(health_checks)
        
        for check_name, status, message in health_checks:
            icon = "✅" if status else "❌"
            print(f"   {icon} {check_name}: {message}")
        
        if passed_checks == total_checks:
            self.log_result("System Health Check", "PASS", 
                           f"All {total_checks} health checks passed")
            return True
        else:
            self.log_result("System Health Check", "FAIL", 
                           f"Only {passed_checks}/{total_checks} health checks passed")
            return False
            
    def test_end_to_end_command_flow(self):
        """Test complete command flow from API to MQTT"""
        print("\n🔄 Testing end-to-end command flow...")
        
        # Clear message queue
        while not self.mqtt_messages.empty():
            try:
                self.mqtt_messages.get_nowait()
            except queue.Empty:
                break
        
        # Send command via API
        command = {
            "action": "INTEGRATION_TEST",
            "value": "test_data",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/nodes/{self.test_node_id}/actions",
                json=command,
                timeout=5
            )
            
            if response.status_code != 200:
                self.log_result("End-to-End Command Flow", "FAIL", 
                               f"API request failed: HTTP {response.status_code}")
                return False
            
        except Exception as e:
            self.log_result("End-to-End Command Flow", "FAIL", 
                           f"API request error: {e}")
            return False
        
        # Wait for MQTT message
        mqtt_message = self.wait_for_mqtt_message("commands", timeout=10)
        
        if not mqtt_message:
            self.log_result("End-to-End Command Flow", "FAIL", 
                           "No MQTT message received")
            return False
        
        # Validate message content
        payload = mqtt_message["payload"]
        
        if isinstance(payload, dict):
            if payload.get("action") == "INTEGRATION_TEST":
                # Check for enhanced metadata
                metadata_fields = ["message_id", "cmd_timestamp", "source"]
                missing_fields = [field for field in metadata_fields if field not in payload]
                
                if not missing_fields:
                    self.log_result("End-to-End Command Flow", "PASS", 
                                   "Command flow successful with metadata")
                    return True
                else:
                    self.log_result("End-to-End Command Flow", "FAIL", 
                                   f"Missing metadata: {missing_fields}")
                    return False
            else:
                self.log_result("End-to-End Command Flow", "FAIL", 
                               f"Wrong action received: {payload.get('action')}")
                return False
        else:
            self.log_result("End-to-End Command Flow", "FAIL", 
                           "Invalid message payload format")
            return False
            
    def test_persistent_session_simulation(self):
        """Test persistent session by simulating device offline/online"""
        print("\n💾 Testing persistent session simulation...")
        
        # Create a test client that simulates ESP32
        test_device_id = "TEST_DEVICE_123"
        
        def simulate_device_connection():
            """Simulate device connecting with persistent session"""
            device_client = mqtt.Client(f"ESP32-{test_device_id}", clean_session=False)
            device_client.username_pw_set(self.mqtt_user, self.mqtt_password)
            
            received_commands = []
            
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    client.subscribe(f"devices/{test_device_id}/commands", qos=1)
                    
            def on_message(client, userdata, msg):
                try:
                    command = json.loads(msg.payload.decode())
                    received_commands.append(command)
                except json.JSONDecodeError:
                    received_commands.append({"error": "Invalid JSON"})
            
            device_client.on_connect = on_connect
            device_client.on_message = on_message
            
            try:
                # First connection
                device_client.connect(self.mqtt_host, self.mqtt_port, 60)
                device_client.loop_start()
                time.sleep(2)
                
                # Disconnect (simulate offline)
                device_client.disconnect()
                device_client.loop_stop()
                time.sleep(1)
                
                # Send commands while offline
                commands_sent = []
                for i in range(3):
                    command = {
                        "action": f"OFFLINE_TEST_{i}",
                        "value": f"data_{i}"
                    }
                    commands_sent.append(command)
                    
                    response = requests.post(
                        f"{self.api_base}/nodes/{test_device_id}/actions",
                        json=command,
                        timeout=5
                    )
                    
                    if response.status_code != 200:
                        return False, f"Failed to send command {i}"
                
                time.sleep(2)  # Wait for commands to be queued
                
                # Reconnect (simulate online)
                device_client.connect(self.mqtt_host, self.mqtt_port, 60)
                device_client.loop_start()
                time.sleep(5)  # Wait for queued messages
                
                device_client.loop_stop()
                device_client.disconnect()
                
                # Check if all commands were received
                if len(received_commands) == len(commands_sent):
                    return True, f"All {len(commands_sent)} queued commands delivered"
                else:
                    return False, f"Only {len(received_commands)}/{len(commands_sent)} commands delivered"
                    
            except Exception as e:
                return False, f"Simulation error: {e}"
        
        try:
            success, message = simulate_device_connection()
            
            if success:
                self.log_result("Persistent Session Simulation", "PASS", message)
                return True
            else:
                self.log_result("Persistent Session Simulation", "FAIL", message)
                return False
                
        except Exception as e:
            self.log_result("Persistent Session Simulation", "FAIL", 
                           f"Test error: {e}")
            return False
            
    def test_multiple_device_management(self):
        """Test managing multiple devices simultaneously"""
        print("\n👥 Testing multiple device management...")
        
        device_ids = ["DEVICE_001", "DEVICE_002", "DEVICE_003"]
        
        # Send commands to all devices
        sent_commands = {}
        
        for device_id in device_ids:
            command = {
                "action": "MULTI_DEVICE_TEST",
                "device_id": device_id,
                "timestamp": datetime.now().isoformat()
            }
            
            try:
                response = requests.post(
                    f"{self.api_base}/nodes/{device_id}/actions",
                    json=command,
                    timeout=5
                )
                
                if response.status_code == 200:
                    sent_commands[device_id] = command
                else:
                    self.log_result("Multiple Device Management", "FAIL", 
                                   f"Failed to send command to {device_id}")
                    return False
                    
            except Exception as e:
                self.log_result("Multiple Device Management", "FAIL", 
                               f"Error sending command to {device_id}: {e}")
                return False
        
        # Wait for and collect MQTT messages
        received_messages = []
        timeout = 10
        start_time = time.time()
        
        while len(received_messages) < len(device_ids) and time.time() - start_time < timeout:
            message = self.wait_for_mqtt_message("commands", timeout=2)
            if message:
                received_messages.append(message)
        
        # Validate messages
        received_device_ids = set()
        for message in received_messages:
            topic_parts = message["topic"].split("/")
            if len(topic_parts) >= 2:
                device_id = topic_parts[1]
                received_device_ids.add(device_id)
        
        if len(received_device_ids) == len(device_ids):
            self.log_result("Multiple Device Management", "PASS", 
                           f"Commands sent to all {len(device_ids)} devices")
            return True
        else:
            self.log_result("Multiple Device Management", "FAIL", 
                           f"Only {len(received_device_ids)}/{len(device_ids)} devices received commands")
            return False
            
    def test_qos_reliability(self):
        """Test QoS=1 message reliability"""
        print("\n🔒 Testing QoS=1 reliability...")
        
        # Create client to test QoS delivery
        qos_test_client = mqtt.Client("qos_test_client", clean_session=False)
        qos_test_client.username_pw_set(self.mqtt_user, self.mqtt_password)
        
        messages_received = []
        puback_count = 0
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                client.subscribe("test/qos/reliability", qos=1)
                
        def on_message(client, userdata, msg):
            messages_received.append({
                "qos": msg.qos,
                "payload": msg.payload.decode(),
                "mid": getattr(msg, 'mid', None)
            })
            
        def on_publish(client, userdata, mid):
            nonlocal puback_count
            puback_count += 1
        
        qos_test_client.on_connect = on_connect
        qos_test_client.on_message = on_message
        qos_test_client.on_publish = on_publish
        
        try:
            qos_test_client.connect(self.mqtt_host, self.mqtt_port, 60)
            qos_test_client.loop_start()
            time.sleep(2)
            
            # Publish test messages with QoS=1
            test_messages = ["message_1", "message_2", "message_3"]
            published_count = 0
            
            for i, message in enumerate(test_messages):
                result = qos_test_client.publish("test/qos/reliability", message, qos=1)
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    published_count += 1
                    
            time.sleep(3)  # Wait for delivery
            
            qos_test_client.loop_stop()
            qos_test_client.disconnect()
            
            # Validate results
            qos1_messages = [msg for msg in messages_received if msg["qos"] == 1]
            
            if len(qos1_messages) == published_count and puback_count == published_count:
                self.log_result("QoS=1 Reliability", "PASS", 
                               f"All {published_count} messages delivered with QoS=1")
                return True
            else:
                self.log_result("QoS=1 Reliability", "FAIL", 
                               f"Expected {published_count} QoS=1 messages, got {len(qos1_messages)}")
                return False
                
        except Exception as e:
            self.log_result("QoS=1 Reliability", "FAIL", 
                           f"QoS test error: {e}")
            return False
            
    def test_performance_under_load(self):
        """Test system performance under load"""
        print("\n⚡ Testing performance under load...")
        
        # Send multiple commands rapidly
        num_commands = 20
        start_time = time.time()
        successful_commands = 0
        
        for i in range(num_commands):
            command = {
                "action": "LOAD_TEST",
                "sequence": i,
                "timestamp": datetime.now().isoformat()
            }
            
            try:
                response = requests.post(
                    f"{self.api_base}/nodes/{self.test_node_id}/actions",
                    json=command,
                    timeout=2
                )
                
                if response.status_code == 200:
                    successful_commands += 1
                    
            except Exception:
                pass  # Count failures
                
        api_duration = time.time() - start_time
        
        # Wait for MQTT messages
        mqtt_start_time = time.time()
        received_commands = 0
        
        while received_commands < successful_commands and time.time() - mqtt_start_time < 15:
            message = self.wait_for_mqtt_message("commands", timeout=1)
            if message and isinstance(message["payload"], dict):
                if message["payload"].get("action") == "LOAD_TEST":
                    received_commands += 1
        
        mqtt_duration = time.time() - mqtt_start_time
        
        # Calculate performance metrics
        api_success_rate = (successful_commands / num_commands) * 100
        mqtt_success_rate = (received_commands / successful_commands) * 100 if successful_commands > 0 else 0
        avg_api_time = (api_duration / num_commands) * 1000  # ms per command
        
        print(f"   📊 API Performance: {successful_commands}/{num_commands} commands ({api_success_rate:.1f}%)")
        print(f"   📊 MQTT Delivery: {received_commands}/{successful_commands} messages ({mqtt_success_rate:.1f}%)")
        print(f"   ⏱️ Average API time: {avg_api_time:.1f}ms per command")
        print(f"   ⏱️ Total MQTT time: {mqtt_duration:.1f}s")
        
        if api_success_rate >= 95 and mqtt_success_rate >= 95:
            self.log_result("Performance Under Load", "PASS", 
                           f"API: {api_success_rate:.1f}%, MQTT: {mqtt_success_rate:.1f}%")
            return True
        else:
            self.log_result("Performance Under Load", "FAIL", 
                           f"Performance below threshold - API: {api_success_rate:.1f}%, MQTT: {mqtt_success_rate:.1f}%")
            return False
            
    def generate_report(self):
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "="*60)
        print("📊 INTEGRATION TEST REPORT")
        print("="*60)
        print(f"🕒 Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        print()
        
        # Detailed results
        print("📋 DETAILED RESULTS:")
        print("-" * 60)
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_icon} {result['test']}")
            if result["message"]:
                print(f"   📝 {result['message']}")
        
        print("\n" + "="*60)
        
        if success_rate == 100:
            print("🎉 ALL INTEGRATION TESTS PASSED!")
            print("🚀 System is ready for production deployment!")
        elif success_rate >= 80:
            print("⚠️ Most integration tests passed. Review failures before deployment.")
        else:
            print("🚨 Multiple integration test failures. System needs significant work.")
        
        # Save detailed report
        report_file = "integration_test_report.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": success_rate,
                    "timestamp": datetime.now().isoformat()
                },
                "results": self.test_results,
                "test_environment": {
                    "api_base": self.api_base,
                    "mqtt_host": self.mqtt_host,
                    "mqtt_port": self.mqtt_port
                }
            }, f, indent=2)
        
        print(f"📄 Detailed report saved to: {report_file}")
        return success_rate >= 80
        
    def run_all_tests(self):
        """Run complete integration test suite"""
        print("🧪 INTEGRATION TEST SUITE")
        print("="*60)
        print("🔍 Testing end-to-end MQTT persistent session functionality...")
        print()
        
        # Setup MQTT monitoring
        if not self.setup_mqtt_monitor():
            print("❌ Cannot continue without MQTT monitoring")
            return False
        
        try:
            # Define test sequence
            tests = [
                ("System Health Check", self.test_system_health_check),
                ("End-to-End Command Flow", self.test_end_to_end_command_flow),
                ("Persistent Session Simulation", self.test_persistent_session_simulation),
                ("Multiple Device Management", self.test_multiple_device_management),
                ("QoS=1 Reliability", self.test_qos_reliability),
                ("Performance Under Load", self.test_performance_under_load)
            ]
            
            # Run tests sequentially
            for test_name, test_func in tests:
                print(f"\n🔍 Running: {test_name}")
                try:
                    test_func()
                except Exception as e:
                    self.log_result(test_name, "FAIL", f"Unexpected error: {e}")
                
                time.sleep(2)  # Delay between tests
            
        finally:
            # Cleanup
            self.cleanup_mqtt_monitor()
        
        # Generate final report
        return self.generate_report()

def main():
    """Main test execution"""
    print("🚀 Starting Integration Test Suite...")
    print()
    
    tester = IntegrationTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test execution interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n\n🚨 Integration test suite failed: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()

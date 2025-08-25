#!/usr/bin/env python3
"""
Automated test suite for MQTT persistent sessions
Tests the backend API and MQTT functionality
"""
import requests
import json
import time
import paho.mqtt.client as mqtt
from datetime import datetime
import sys
import os

class PersistentSessionTester:
    def __init__(self):
        self.api_base = "http://localhost:3005/api"
        self.mqtt_host = "localhost"
        self.mqtt_port = 1883
        self.mqtt_user = "rnr_iot_user"
        self.mqtt_password = "rnr_iot_2025!"
        self.test_node_id = "AABBCCDDEEFF"
        self.test_results = []
        
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
        
    def test_backend_health(self):
        """Test if backend services are running"""
        try:
            response = requests.get(f"{self.api_base}/nodes", timeout=5)
            if response.status_code == 200:
                self.log_result("Backend Health Check", "PASS", 
                               f"Backend responding on port 3005")
                return True
            else:
                self.log_result("Backend Health Check", "FAIL", 
                               f"Backend returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_result("Backend Health Check", "FAIL", 
                           f"Cannot connect to backend: {e}")
            return False
        
    def test_mqtt_status_endpoint(self):
        """Test MQTT status endpoint"""
        try:
            response = requests.get(f"{self.api_base}/mqtt/status", timeout=5)
            
            if response.status_code != 200:
                self.log_result("MQTT Status Endpoint", "FAIL", 
                               f"HTTP {response.status_code}")
                return False
                
            data = response.json()
            
            # Check required fields
            required_fields = [
                ("persistent_sessions", "enabled"),
                ("mqtt_publisher", "qos_level"),
                ("mqtt_publisher", "clean_session")
            ]
            
            for field_path in required_fields:
                current = data
                for key in field_path:
                    if key not in current:
                        self.log_result("MQTT Status Endpoint", "FAIL", 
                                       f"Missing field: {'.'.join(field_path)}")
                        return False
                    current = current[key]
            
            # Verify persistent session configuration
            if not data["persistent_sessions"]["enabled"]:
                self.log_result("MQTT Status Endpoint", "FAIL", 
                               "Persistent sessions not enabled")
                return False
                
            if data["mqtt_publisher"]["qos_level"] != 1:
                self.log_result("MQTT Status Endpoint", "FAIL", 
                               f"QoS level is {data['mqtt_publisher']['qos_level']}, expected 1")
                return False
                
            if data["mqtt_publisher"]["clean_session"] != False:
                self.log_result("MQTT Status Endpoint", "FAIL", 
                               "Clean session should be False for persistent sessions")
                return False
            
            self.log_result("MQTT Status Endpoint", "PASS", 
                           "All persistent session settings correct")
            return True
            
        except Exception as e:
            self.log_result("MQTT Status Endpoint", "FAIL", str(e))
            return False
        
    def test_command_queuing_response(self):
        """Test command queuing API response"""
        try:
            command = {"action": "LIGHT_CONTROL", "value": True}
            response = requests.post(
                f"{self.api_base}/nodes/{self.test_node_id}/actions",
                json=command,
                timeout=5
            )
            
            if response.status_code != 200:
                self.log_result("Command Queuing Response", "FAIL", 
                               f"HTTP {response.status_code}")
                return False
                
            data = response.json()
            
            if "message" not in data:
                self.log_result("Command Queuing Response", "FAIL", 
                               "Response missing 'message' field")
                return False
                
            if "queued successfully" not in data["message"].lower():
                self.log_result("Command Queuing Response", "FAIL", 
                               f"Unexpected response: {data['message']}")
                return False
            
            self.log_result("Command Queuing Response", "PASS", 
                           "Command queuing response correct")
            return True
            
        except Exception as e:
            self.log_result("Command Queuing Response", "FAIL", str(e))
            return False
        
    def test_mqtt_message_format(self):
        """Test MQTT message format and metadata"""
        try:
            received_messages = []
            
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    client.subscribe(f"devices/{self.test_node_id}/commands", qos=1)
                else:
                    raise Exception(f"MQTT connection failed with code {rc}")
            
            def on_message(client, userdata, msg):
                try:
                    message = json.loads(msg.payload.decode())
                    received_messages.append(message)
                except json.JSONDecodeError:
                    received_messages.append({"error": "Invalid JSON"})
            
            # Connect to MQTT broker
            client = mqtt.Client("test_client_persistent", clean_session=False)
            client.username_pw_set(self.mqtt_user, self.mqtt_password)
            client.on_connect = on_connect
            client.on_message = on_message
            
            try:
                client.connect(self.mqtt_host, self.mqtt_port, 60)
            except Exception as e:
                self.log_result("MQTT Message Format", "FAIL", 
                               f"Cannot connect to MQTT broker: {e}")
                return False
                
            client.loop_start()
            time.sleep(2)  # Wait for connection
            
            # Send command via API
            command = {"action": "TEST_COMMAND", "value": "test_data"}
            response = requests.post(
                f"{self.api_base}/nodes/{self.test_node_id}/actions",
                json=command,
                timeout=5
            )
            
            if response.status_code != 200:
                client.loop_stop()
                client.disconnect()
                self.log_result("MQTT Message Format", "FAIL", 
                               f"API request failed: HTTP {response.status_code}")
                return False
            
            # Wait for MQTT message
            timeout = 10
            start_time = time.time()
            while len(received_messages) == 0 and time.time() - start_time < timeout:
                time.sleep(0.5)
            
            client.loop_stop()
            client.disconnect()
            
            if len(received_messages) == 0:
                self.log_result("MQTT Message Format", "FAIL", 
                               "No MQTT message received within timeout")
                return False
            
            msg = received_messages[0]
            
            if "error" in msg:
                self.log_result("MQTT Message Format", "FAIL", 
                               "Received invalid JSON message")
                return False
            
            # Check required metadata fields
            required_fields = ["message_id", "cmd_timestamp", "source", "action"]
            missing_fields = [field for field in required_fields if field not in msg]
            
            if missing_fields:
                self.log_result("MQTT Message Format", "FAIL", 
                               f"Missing fields: {missing_fields}")
                return False
            
            if msg["source"] != "backend_api":
                self.log_result("MQTT Message Format", "FAIL", 
                               f"Expected source 'backend_api', got '{msg['source']}'")
                return False
                
            if msg["action"] != "TEST_COMMAND":
                self.log_result("MQTT Message Format", "FAIL", 
                               f"Expected action 'TEST_COMMAND', got '{msg['action']}'")
                return False
            
            self.log_result("MQTT Message Format", "PASS", 
                           f"Message format correct with all metadata")
            return True
            
        except Exception as e:
            self.log_result("MQTT Message Format", "FAIL", str(e))
            return False
        
    def test_mqtt_broker_connection(self):
        """Test direct MQTT broker connection"""
        try:
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    userdata["connected"] = True
                else:
                    userdata["connected"] = False
                    userdata["error"] = f"Connection failed with code {rc}"
            
            userdata = {"connected": False}
            client = mqtt.Client("test_broker_connection")
            client.username_pw_set(self.mqtt_user, self.mqtt_password)
            client.user_data_set(userdata)
            client.on_connect = on_connect
            
            try:
                client.connect(self.mqtt_host, self.mqtt_port, 60)
                client.loop_start()
                
                # Wait for connection
                timeout = 10
                start_time = time.time()
                while not userdata["connected"] and time.time() - start_time < timeout:
                    time.sleep(0.5)
                
                client.loop_stop()
                client.disconnect()
                
                if userdata["connected"]:
                    self.log_result("MQTT Broker Connection", "PASS", 
                                   "Successfully connected to MQTT broker")
                    return True
                else:
                    error_msg = userdata.get("error", "Connection timeout")
                    self.log_result("MQTT Broker Connection", "FAIL", error_msg)
                    return False
                    
            except Exception as e:
                self.log_result("MQTT Broker Connection", "FAIL", 
                               f"Connection error: {e}")
                return False
                
        except Exception as e:
            self.log_result("MQTT Broker Connection", "FAIL", str(e))
            return False
        
    def test_persistent_session_qos(self):
        """Test QoS=1 message delivery"""
        try:
            message_received = {"status": False, "qos": None}
            
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    # Subscribe with QoS=1
                    client.subscribe("test/qos/topic", qos=1)
                else:
                    raise Exception(f"Connection failed with code {rc}")
            
            def on_message(client, userdata, msg):
                message_received["status"] = True
                message_received["qos"] = msg.qos
            
            # Test client with persistent session
            client = mqtt.Client("test_qos_client", clean_session=False)
            client.username_pw_set(self.mqtt_user, self.mqtt_password)
            client.on_connect = on_connect
            client.on_message = on_message
            
            try:
                client.connect(self.mqtt_host, self.mqtt_port, 60)
                client.loop_start()
                time.sleep(2)  # Wait for connection and subscription
                
                # Publish message with QoS=1
                client.publish("test/qos/topic", "test_qos_message", qos=1)
                
                # Wait for message
                timeout = 5
                start_time = time.time()
                while not message_received["status"] and time.time() - start_time < timeout:
                    time.sleep(0.1)
                
                client.loop_stop()
                client.disconnect()
                
                if message_received["status"]:
                    if message_received["qos"] == 1:
                        self.log_result("QoS=1 Message Delivery", "PASS", 
                                       "Message delivered with QoS=1")
                        return True
                    else:
                        self.log_result("QoS=1 Message Delivery", "FAIL", 
                                       f"Expected QoS=1, got QoS={message_received['qos']}")
                        return False
                else:
                    self.log_result("QoS=1 Message Delivery", "FAIL", 
                                   "No message received")
                    return False
                    
            except Exception as e:
                self.log_result("QoS=1 Message Delivery", "FAIL", 
                               f"Test error: {e}")
                return False
                
        except Exception as e:
            self.log_result("QoS=1 Message Delivery", "FAIL", str(e))
            return False
        
    def generate_report(self):
        """Generate test execution report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "="*60)
        print("📊 TEST EXECUTION REPORT")
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
            print("🎉 ALL TESTS PASSED! Persistent Session system is ready!")
        elif success_rate >= 80:
            print("⚠️ Most tests passed. Review failed tests before deployment.")
        else:
            print("🚨 Multiple test failures. System needs attention.")
        
        # Save report to file
        report_file = "test_report_persistent_sessions.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": success_rate,
                    "timestamp": datetime.now().isoformat()
                },
                "results": self.test_results
            }, f, indent=2)
        
        print(f"📄 Report saved to: {report_file}")
        return success_rate == 100
        
    def run_all_tests(self):
        """Run all automated tests"""
        print("🧪 MQTT PERSISTENT SESSION TEST SUITE")
        print("="*60)
        print("🔍 Testing enhanced MQTT persistent session functionality...")
        print()
        
        # Define test sequence
        tests = [
            ("Backend Health Check", self.test_backend_health),
            ("MQTT Broker Connection", self.test_mqtt_broker_connection),
            ("MQTT Status Endpoint", self.test_mqtt_status_endpoint),
            ("Command Queuing Response", self.test_command_queuing_response),
            ("MQTT Message Format", self.test_mqtt_message_format),
            ("QoS=1 Message Delivery", self.test_persistent_session_qos)
        ]
        
        # Run tests sequentially
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                test_func()
            except Exception as e:
                self.log_result(test_name, "FAIL", f"Unexpected error: {e}")
            
            time.sleep(1)  # Small delay between tests
        
        # Generate final report
        return self.generate_report()

def main():
    """Main test execution"""
    print("🚀 Starting MQTT Persistent Session Test Suite...")
    print()
    
    # Check if running in correct directory
    if not os.path.exists("package.json"):
        print("⚠️ Warning: package.json not found. Are you in the correct directory?")
        print("   Expected: IoT project root directory")
        print()
    
    tester = PersistentSessionTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test execution interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n\n🚨 Test suite failed with error: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
ESP32 Serial Monitor Test for Persistent Sessions
Tests ESP32 firmware functionality via serial communication
"""
import serial
import time
import re
import json
import sys
from datetime import datetime

class ESP32SerialTester:
    def __init__(self, port="COM3", baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.test_results = []
        self.serial_buffer = ""
        
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
            
    def connect_serial(self):
        """Connect to ESP32 via serial"""
        try:
            print(f"🔌 Connecting to ESP32 on {self.port} at {self.baudrate} baud...")
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Wait for connection to stabilize
            
            # Clear initial buffer
            self.serial.flushInput()
            
            print(f"✅ Serial connection established")
            return True
            
        except serial.SerialException as e:
            print(f"❌ Serial connection failed: {e}")
            print(f"💡 Available ports: {[p.device for p in serial.tools.list_ports.comports()]}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error connecting to serial: {e}")
            return False
            
    def read_serial_data(self, timeout=1):
        """Read data from serial port"""
        if not self.serial or not self.serial.is_open:
            return ""
            
        end_time = time.time() + timeout
        data = ""
        
        while time.time() < end_time:
            if self.serial.in_waiting:
                try:
                    chunk = self.serial.read(self.serial.in_waiting).decode('utf-8', errors='ignore')
                    data += chunk
                    self.serial_buffer += chunk
                except Exception as e:
                    print(f"⚠️ Serial read error: {e}")
                    break
            else:
                time.sleep(0.1)
                
        return data
        
    def wait_for_pattern(self, pattern, timeout=30, case_sensitive=False):
        """Wait for specific pattern in serial output"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            data = self.read_serial_data(1)
            if data:
                print(data, end='')  # Echo to console
                
                # Check pattern
                search_text = self.serial_buffer if case_sensitive else self.serial_buffer.lower()
                search_pattern = pattern if case_sensitive else pattern.lower()
                
                if re.search(search_pattern, search_text):
                    return True
                    
        return False
        
    def wait_for_multiple_patterns(self, patterns, timeout=30):
        """Wait for multiple patterns to appear"""
        found_patterns = set()
        start_time = time.time()
        
        while time.time() - start_time < timeout and len(found_patterns) < len(patterns):
            data = self.read_serial_data(1)
            if data:
                print(data, end='')
                
                # Check each pattern
                for i, pattern in enumerate(patterns):
                    if i not in found_patterns:
                        if re.search(pattern.lower(), self.serial_buffer.lower()):
                            found_patterns.add(i)
                            print(f"\n✅ Found pattern: {pattern}")
                            
        return len(found_patterns) == len(patterns)
        
    def clear_buffer(self):
        """Clear the serial buffer"""
        self.serial_buffer = ""
        if self.serial:
            self.serial.flushInput()
            
    def test_esp32_boot_sequence(self):
        """Test ESP32 boot and initialization"""
        print("🔄 Testing ESP32 boot sequence...")
        self.clear_buffer()
        
        # Wait for boot patterns
        boot_patterns = [
            r"Starting ESP32 IoT Platform Node",
            r"wifi.*connected",
            r"connected to.*mqtt.*broker"
        ]
        
        found_all = self.wait_for_multiple_patterns(boot_patterns, 60)
        
        if found_all:
            self.log_result("ESP32 Boot Sequence", "PASS", 
                           "All boot patterns detected")
            return True
        else:
            self.log_result("ESP32 Boot Sequence", "FAIL", 
                           "Missing boot patterns")
            return False
            
    def test_persistent_session_connection(self):
        """Test persistent session connection"""
        print("\n🔗 Testing persistent session connection...")
        self.clear_buffer()
        
        # Look for persistent session indicators
        persistent_patterns = [
            r"persistent session",
            r"clean.*session.*false",
            r"qos.*1.*persistent",
            r"checking for queued messages"
        ]
        
        found_count = 0
        for pattern in persistent_patterns:
            if self.wait_for_pattern(pattern, 30):
                print(f"✅ Found: {pattern}")
                found_count += 1
            else:
                print(f"❌ Missing: {pattern}")
                
        success_rate = (found_count / len(persistent_patterns)) * 100
        
        if success_rate >= 75:  # Allow for some variation in messages
            self.log_result("Persistent Session Connection", "PASS", 
                           f"Found {found_count}/{len(persistent_patterns)} indicators")
            return True
        else:
            self.log_result("Persistent Session Connection", "FAIL", 
                           f"Only found {found_count}/{len(persistent_patterns)} indicators")
            return False
            
    def test_data_transmission_rate(self):
        """Test 1-second data transmission rate"""
        print("\n📊 Testing 1-second data transmission rate...")
        self.clear_buffer()
        
        # Count data transmission messages
        message_count = 0
        test_duration = 15  # Test for 15 seconds
        start_time = time.time()
        
        print(f"⏱️ Monitoring for {test_duration} seconds...")
        
        while time.time() - start_time < test_duration:
            data = self.read_serial_data(2)
            if data:
                # Look for data transmission indicators
                if re.search(r"data sent|publishing.*data|sensor.*data", data.lower()):
                    message_count += 1
                    print(f"📡 Data transmission #{message_count}")
                    
        elapsed_time = time.time() - start_time
        expected_messages = int(elapsed_time)  # ~1 message per second
        success_rate = (message_count / expected_messages) * 100 if expected_messages > 0 else 0
        
        print(f"\n📈 Results:")
        print(f"   ⏱️ Test duration: {elapsed_time:.1f} seconds")
        print(f"   📊 Messages sent: {message_count}")
        print(f"   🎯 Expected: ~{expected_messages}")
        print(f"   📈 Success rate: {success_rate:.1f}%")
        
        if success_rate >= 80:  # Allow 20% tolerance
            self.log_result("Data Transmission Rate", "PASS", 
                           f"{success_rate:.1f}% transmission rate")
            return True
        else:
            self.log_result("Data Transmission Rate", "FAIL", 
                           f"Only {success_rate:.1f}% transmission rate")
            return False
            
    def test_command_reception(self):
        """Test command reception and processing"""
        print("\n📨 Testing command reception capability...")
        self.clear_buffer()
        
        # Look for command-related messages
        command_patterns = [
            r"subscribed.*commands",
            r"message received.*topic",
            r"command.*received",
            r"mqtt.*callback"
        ]
        
        print("⏳ Waiting for command reception indicators...")
        
        found_count = 0
        for pattern in command_patterns:
            if self.wait_for_pattern(pattern, 20):
                found_count += 1
                
        if found_count >= 2:  # At least 2 indicators
            self.log_result("Command Reception", "PASS", 
                           f"Found {found_count} command indicators")
            return True
        else:
            self.log_result("Command Reception", "FAIL", 
                           f"Only found {found_count} command indicators")
            return False
            
    def test_error_handling(self):
        """Test error handling and recovery"""
        print("\n🚨 Testing error handling...")
        self.clear_buffer()
        
        # Look for error handling patterns
        error_patterns = [
            r"reconnect",
            r"retry",
            r"connection.*lost",
            r"wifi.*disconnected"
        ]
        
        recovery_patterns = [
            r"connected.*successfully",
            r"reconnected",
            r"connection.*restored"
        ]
        
        print("⏳ Monitoring for error handling patterns...")
        
        # Monitor for 30 seconds
        error_found = False
        recovery_found = False
        
        for pattern in error_patterns:
            if self.wait_for_pattern(pattern, 10):
                error_found = True
                print(f"✅ Found error pattern: {pattern}")
                break
                
        if error_found:
            for pattern in recovery_patterns:
                if self.wait_for_pattern(pattern, 20):
                    recovery_found = True
                    print(f"✅ Found recovery pattern: {pattern}")
                    break
                    
        if error_found and recovery_found:
            self.log_result("Error Handling", "PASS", 
                           "Error detected and recovery successful")
            return True
        elif not error_found:
            self.log_result("Error Handling", "SKIP", 
                           "No errors occurred during test period")
            return True  # Not a failure if no errors occur
        else:
            self.log_result("Error Handling", "FAIL", 
                           "Error detected but no recovery")
            return False
            
    def test_memory_stability(self):
        """Test memory stability over time"""
        print("\n🧠 Testing memory stability...")
        self.clear_buffer()
        
        # Look for memory-related issues
        memory_issues = [
            r"out of memory",
            r"heap.*low",
            r"stack.*overflow",
            r"memory.*error",
            r"guru meditation"
        ]
        
        print("⏳ Monitoring for memory issues (30 seconds)...")
        
        issue_found = False
        start_time = time.time()
        
        while time.time() - start_time < 30:
            data = self.read_serial_data(2)
            if data:
                for pattern in memory_issues:
                    if re.search(pattern.lower(), data.lower()):
                        issue_found = True
                        print(f"⚠️ Memory issue detected: {pattern}")
                        break
                        
                if issue_found:
                    break
                    
        if not issue_found:
            self.log_result("Memory Stability", "PASS", 
                           "No memory issues detected")
            return True
        else:
            self.log_result("Memory Stability", "FAIL", 
                           "Memory issues detected")
            return False
            
    def generate_report(self):
        """Generate test execution report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        skipped_tests = len([r for r in self.test_results if r["status"] == "SKIP"])
        failed_tests = total_tests - passed_tests - skipped_tests
        success_rate = (passed_tests / (total_tests - skipped_tests) * 100) if (total_tests - skipped_tests) > 0 else 0
        
        print("\n" + "="*60)
        print("📊 ESP32 SERIAL TEST REPORT")
        print("="*60)
        print(f"🕒 Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔌 Serial Port: {self.port}")
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏭️ Skipped: {skipped_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        print()
        
        # Detailed results
        print("📋 DETAILED RESULTS:")
        print("-" * 60)
        for result in self.test_results:
            if result["status"] == "PASS":
                status_icon = "✅"
            elif result["status"] == "SKIP":
                status_icon = "⏭️"
            else:
                status_icon = "❌"
                
            print(f"{status_icon} {result['test']}")
            if result["message"]:
                print(f"   📝 {result['message']}")
        
        print("\n" + "="*60)
        
        if success_rate == 100:
            print("🎉 ALL ESP32 TESTS PASSED! Firmware is working correctly!")
        elif success_rate >= 80:
            print("⚠️ Most ESP32 tests passed. Review failed tests.")
        else:
            print("🚨 Multiple ESP32 test failures. Firmware needs attention.")
        
        # Save report to file
        report_file = "esp32_serial_test_report.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "skipped": skipped_tests,
                    "success_rate": success_rate,
                    "serial_port": self.port,
                    "timestamp": datetime.now().isoformat()
                },
                "results": self.test_results
            }, f, indent=2)
        
        print(f"📄 Report saved to: {report_file}")
        return success_rate >= 80  # 80% success threshold
        
    def run_tests(self):
        """Run all ESP32 serial tests"""
        print("🧪 ESP32 SERIAL TEST SUITE")
        print("="*60)
        print("🔍 Testing ESP32 firmware via serial communication...")
        print()
        
        # Connect to serial port
        if not self.connect_serial():
            print("❌ Cannot continue without serial connection")
            return False
        
        try:
            # Define test sequence
            tests = [
                ("ESP32 Boot Sequence", self.test_esp32_boot_sequence),
                ("Persistent Session Connection", self.test_persistent_session_connection),
                ("Data Transmission Rate", self.test_data_transmission_rate),
                ("Command Reception", self.test_command_reception),
                ("Error Handling", self.test_error_handling),
                ("Memory Stability", self.test_memory_stability)
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
            # Clean up
            if self.serial and self.serial.is_open:
                self.serial.close()
                print(f"\n🔌 Serial connection closed")
        
        # Generate final report
        return self.generate_report()

def main():
    """Main test execution"""
    print("🚀 Starting ESP32 Serial Test Suite...")
    print()
    
    # Check for available serial ports
    import serial.tools.list_ports
    ports = [p.device for p in serial.tools.list_ports.comports()]
    
    if not ports:
        print("❌ No serial ports found!")
        print("💡 Make sure ESP32 is connected via USB")
        sys.exit(1)
    
    print(f"📡 Available serial ports: {ports}")
    
    # Try to determine the correct port
    esp32_port = None
    for port in ports:
        if "CH340" in str(port) or "CP210" in str(port) or "UART" in str(port):
            esp32_port = port
            break
    
    if not esp32_port:
        esp32_port = ports[0]  # Use first available port
    
    print(f"🎯 Using port: {esp32_port}")
    print("💡 If this is wrong, edit the script and change the port")
    print()
    
    tester = ESP32SerialTester(port=esp32_port)
    
    try:
        success = tester.run_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test execution interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n\n🚨 Test suite failed with error: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()

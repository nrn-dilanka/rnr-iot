#!/usr/bin/env python3
"""
Test runner for all MQTT persistent session tests
Runs backend, ESP32, and integration tests in sequence
"""
import subprocess
import sys
import os
import time
from datetime import datetime

def run_command(command, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking test dependencies...")
    
    dependencies = [
        ("requests", "pip install requests"),
        ("paho-mqtt", "pip install paho-mqtt"),
        ("pyserial", "pip install pyserial")
    ]
    
    missing_deps = []
    
    for dep, install_cmd in dependencies:
        try:
            __import__(dep.replace('-', '_'))
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep} - missing")
            missing_deps.append((dep, install_cmd))
    
    if missing_deps:
        print("\n📦 Missing dependencies found. Install them with:")
        for dep, cmd in missing_deps:
            print(f"   {cmd}")
        return False
    
    print("✅ All dependencies available")
    return True

def check_system_services():
    """Check if required system services are running"""
    print("\n🔍 Checking system services...")
    
    # Check if backend is running
    try:
        import requests
        response = requests.get("http://localhost:3005/api/nodes", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend API (localhost:3005)")
        else:
            print(f"   ❌ Backend API responding with status {response.status_code}")
            return False
    except Exception:
        print("   ❌ Backend API not accessible")
        return False
    
    # Check if MQTT broker is accessible
    try:
        import paho.mqtt.client as mqtt
        client = mqtt.Client("service_check")
        client.username_pw_set("rnr_iot_user", "rnr_iot_2025!")
        result = client.connect("localhost", 1883, 60)
        if result == 0:
            print("   ✅ MQTT Broker (localhost:1883)")
            client.disconnect()
        else:
            print(f"   ❌ MQTT Broker connection failed: {result}")
            return False
    except Exception as e:
        print(f"   ❌ MQTT Broker error: {e}")
        return False
    
    print("✅ All required services are running")
    return True

def run_test_suite(test_file, test_name):
    """Run a specific test suite"""
    print(f"\n🧪 Running {test_name}...")
    print("=" * 60)
    
    success, stdout, stderr = run_command(f"python {test_file}")
    
    if success:
        print(f"✅ {test_name} completed successfully")
        return True
    else:
        print(f"❌ {test_name} failed")
        if stdout:
            print("📄 Output:")
            print(stdout)
        if stderr:
            print("🚨 Errors:")
            print(stderr)
        return False

def main():
    """Main test runner"""
    print("🚀 MQTT PERSISTENT SESSION TEST RUNNER")
    print("=" * 60)
    print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("tests"):
        print("❌ Error: 'tests' directory not found")
        print("   Make sure you're running this from the project root directory")
        return False
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Cannot continue without required dependencies")
        return False
    
    # Check system services
    if not check_system_services():
        print("\n❌ Cannot continue without required services")
        print("\n💡 Make sure to:")
        print("   1. Start the backend API server")
        print("   2. Start RabbitMQ with MQTT plugin")
        print("   3. Ensure services are accessible")
        return False
    
    # Run test suites
    test_suites = [
        ("tests/test_persistent_sessions.py", "Backend API Tests"),
        ("tests/test_integration.py", "Integration Tests")
    ]
    
    results = []
    
    for test_file, test_name in test_suites:
        if os.path.exists(test_file):
            success = run_test_suite(test_file, test_name)
            results.append((test_name, success))
        else:
            print(f"⚠️ Test file not found: {test_file}")
            results.append((test_name, False))
    
    # ESP32 Serial Test (optional)
    print(f"\n🔍 ESP32 Serial Test (Optional)")
    print("=" * 60)
    print("💡 ESP32 serial test requires ESP32 connected via USB")
    user_input = input("📋 Run ESP32 serial test? (y/N): ").strip().lower()
    
    if user_input in ['y', 'yes']:
        if os.path.exists("tests/test_esp32_serial.py"):
            success = run_test_suite("tests/test_esp32_serial.py", "ESP32 Serial Tests")
            results.append(("ESP32 Serial Tests", success))
        else:
            print("⚠️ ESP32 test file not found")
            results.append(("ESP32 Serial Tests", False))
    else:
        print("⏭️ Skipping ESP32 serial tests")
        results.append(("ESP32 Serial Tests", "SKIPPED"))
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, result in results:
        if result == "SKIPPED":
            print(f"⏭️ {test_name}: SKIPPED")
            skipped += 1
        elif result:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        else:
            print(f"❌ {test_name}: FAILED")
            failed += 1
    
    total = passed + failed
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n📈 Results: {passed} passed, {failed} failed, {skipped} skipped")
    print(f"📊 Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 Your MQTT persistent session system is ready for production!")
    elif success_rate >= 80:
        print("\n⚠️ Most tests passed, but some issues need attention")
        print("📋 Review failed tests before deploying to production")
    else:
        print("\n🚨 Multiple test failures detected")
        print("🔧 System needs significant work before deployment")
    
    print(f"\n🕒 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return success_rate >= 80

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test execution interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n\n🚨 Test runner failed: {e}")
        sys.exit(3)

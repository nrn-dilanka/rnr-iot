#!/usr/bin/env python3
"""
RNR Solutions IoT Platform - Comprehensive Node Monitoring Dashboard Test
Tests real-time monitoring, WebSocket connections, and dashboard functionality.
"""

import asyncio
import json
import requests
import websockets
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

API_BASE = "http://localhost:8000/api"
WS_URL = "ws://localhost:8000/ws"

class MonitoringDashboardTest:
    def __init__(self):
        self.test_results = []
        self.ws_messages = []
        self.monitoring_active = True
        
    def log_test(self, name, status, message, duration=None):
        """Log test result"""
        result = {
            'test': name,
            'status': status,
            'message': message,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        duration_str = f" ({duration:.2f}s)" if duration else ""
        print(f"{status_icon} {name}: {message}{duration_str}")

    def create_test_nodes(self):
        """Create test nodes for monitoring"""
        print("\n🔧 Setting up Test Environment...")
        
        test_nodes = [
            {
                "node_id": "MONITOR_001",
                "name": "Production Node 1",
                "device_type": "ESP32",
                "location": "Factory Floor A",
                "capabilities": ["temperature", "humidity", "pressure"],
                "status": "online"
            },
            {
                "node_id": "MONITOR_002", 
                "name": "Production Node 2",
                "device_type": "ESP32",
                "location": "Factory Floor B",
                "capabilities": ["temperature", "humidity"],
                "status": "online"
            },
            {
                "node_id": "MONITOR_003",
                "name": "Quality Control Node",
                "device_type": "ESP32", 
                "location": "QC Lab",
                "capabilities": ["temperature", "humidity", "light"],
                "status": "offline"
            }
        ]
        
        created_nodes = []
        for node_data in test_nodes:
            try:
                start_time = time.time()
                response = requests.post(f"{API_BASE}/nodes", json=node_data, timeout=10)
                duration = time.time() - start_time
                
                if response.status_code == 201:
                    created_nodes.append(node_data["node_id"])
                    self.log_test(f"Create Node: {node_data['name']}", "PASS", 
                                f"Node created successfully", duration)
                else:
                    self.log_test(f"Create Node: {node_data['name']}", "FAIL",
                                f"HTTP {response.status_code}: {response.text[:100]}", duration)
                    
            except Exception as e:
                self.log_test(f"Create Node: {node_data['name']}", "FAIL", 
                            f"Error: {str(e)}")
        
        return created_nodes

    def test_monitoring_apis(self):
        """Test all monitoring-related APIs"""
        print("\n📊 Testing Monitoring APIs...")
        
        api_tests = [
            {
                'name': 'Node List API',
                'endpoint': f"{API_BASE}/nodes",
                'method': 'GET',
                'validate': lambda data: len(data) if isinstance(data, list) else len(data.get('data', []))
            },
            {
                'name': 'Platform Status API', 
                'endpoint': "http://localhost:8000/",
                'method': 'GET',
                'validate': lambda data: data.get('status') == 'running'
            },
            {
                'name': 'Sensor Data API',
                'endpoint': f"{API_BASE}/sensor-data?limit=5",
                'method': 'GET', 
                'validate': lambda data: True  # Any response is valid
            }
        ]
        
        for test in api_tests:
            try:
                start_time = time.time()
                response = requests.get(test['endpoint'], timeout=10)
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    validation_result = test['validate'](data)
                    
                    if validation_result:
                        self.log_test(test['name'], "PASS", 
                                    f"API working correctly", duration)
                    else:
                        self.log_test(test['name'], "WARNING",
                                    f"API returned unexpected data", duration)
                else:
                    self.log_test(test['name'], "FAIL",
                                f"HTTP {response.status_code}", duration)
                    
            except Exception as e:
                self.log_test(test['name'], "FAIL", f"Error: {str(e)}")

    async def test_realtime_monitoring(self):
        """Test real-time WebSocket monitoring"""
        print("\n📡 Testing Real-time Monitoring...")
        
        try:
            start_time = time.time()
            
            # Test WebSocket connection
            async with websockets.connect(WS_URL) as websocket:
                connect_duration = time.time() - start_time
                self.log_test("WebSocket Connection", "PASS", 
                            "Connected successfully", connect_duration)
                
                # Listen for messages for a short time
                message_start = time.time()
                message_count = 0
                
                try:
                    # Listen for 10 seconds
                    while time.time() - message_start < 10:
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=1)
                            data = json.loads(message)
                            self.ws_messages.append(data)
                            message_count += 1
                            
                        except asyncio.TimeoutError:
                            continue
                        except json.JSONDecodeError:
                            continue
                            
                except Exception:
                    pass
                
                listen_duration = time.time() - message_start
                
                if message_count > 0:
                    self.log_test("Real-time Data Stream", "PASS",
                                f"Received {message_count} real-time messages", listen_duration)
                else:
                    self.log_test("Real-time Data Stream", "WARNING",
                                "No real-time messages (may be expected if no active devices)", listen_duration)
                
        except Exception as e:
            self.log_test("WebSocket Connection", "FAIL", f"Connection failed: {str(e)}")

    def test_node_health_monitoring(self):
        """Test comprehensive node health monitoring"""
        print("\n🏥 Testing Node Health Monitoring...")
        
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE}/nodes", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code != 200:
                self.log_test("Node Health Check", "FAIL", 
                            f"Failed to get nodes: HTTP {response.status_code}", duration)
                return
                
            nodes = response.json()
            if isinstance(nodes, list):
                node_list = nodes
            else:
                node_list = nodes.get('data', nodes.get('nodes', []))
            
            if not node_list:
                self.log_test("Node Health Check", "WARNING",
                            "No nodes found for health monitoring", duration)
                return
            
            # Analyze node health
            total_nodes = len(node_list)
            online_nodes = 0
            offline_nodes = 0
            unknown_nodes = 0
            
            for node in node_list:
                node_id = node.get('node_id', 'Unknown')
                name = node.get('name', 'Unnamed')
                status = node.get('status', 'unknown')
                last_seen = node.get('last_seen')
                location = node.get('location', 'Unknown')
                
                if status == 'online':
                    online_nodes += 1
                    self.log_test(f"Node Status: {name}", "PASS",
                                f"Online at {location}")
                elif status == 'offline':
                    offline_nodes += 1
                    self.log_test(f"Node Status: {name}", "WARNING", 
                                f"Offline at {location}")
                else:
                    unknown_nodes += 1
                    self.log_test(f"Node Status: {name}", "WARNING",
                                f"Status unknown at {location}")
            
            # Overall health assessment
            health_percentage = (online_nodes / total_nodes * 100) if total_nodes > 0 else 0
            
            health_message = f"{online_nodes}/{total_nodes} nodes online ({health_percentage:.1f}%)"
            
            if health_percentage >= 80:
                self.log_test("Overall Node Health", "PASS", health_message)
            elif health_percentage >= 50:
                self.log_test("Overall Node Health", "WARNING", health_message)
            else:
                self.log_test("Overall Node Health", "FAIL", health_message)
                
        except Exception as e:
            self.log_test("Node Health Check", "FAIL", f"Health check failed: {str(e)}")

    def test_monitoring_performance(self):
        """Test monitoring system performance"""
        print("\n⚡ Testing Monitoring Performance...")
        
        # Test API response times
        endpoints = [
            f"{API_BASE}/nodes",
            "http://localhost:8000/",
            f"{API_BASE}/sensor-data?limit=1"
        ]
        
        total_time = 0
        successful_requests = 0
        
        for endpoint in endpoints:
            try:
                start = time.time()
                response = requests.get(endpoint, timeout=5)
                duration = time.time() - start
                
                if response.status_code == 200:
                    total_time += duration
                    successful_requests += 1
                    
                    if duration < 1.0:
                        self.log_test(f"API Performance: {endpoint.split('/')[-1]}", "PASS",
                                    f"Fast response", duration)
                    elif duration < 2.0:
                        self.log_test(f"API Performance: {endpoint.split('/')[-1]}", "WARNING",
                                    f"Acceptable response", duration)
                    else:
                        self.log_test(f"API Performance: {endpoint.split('/')[-1]}", "FAIL",
                                    f"Slow response", duration)
                        
            except Exception as e:
                self.log_test(f"API Performance: {endpoint.split('/')[-1]}", "FAIL",
                            f"Request failed: {str(e)}")
        
        if successful_requests > 0:
            avg_response_time = total_time / successful_requests
            if avg_response_time < 0.5:
                self.log_test("Average API Performance", "PASS",
                            f"Excellent average response time", avg_response_time)
            elif avg_response_time < 1.0:
                self.log_test("Average API Performance", "WARNING", 
                            f"Good average response time", avg_response_time)
            else:
                self.log_test("Average API Performance", "FAIL",
                            f"Poor average response time", avg_response_time)

    def simulate_device_activity(self):
        """Simulate device activity for monitoring"""
        print("\n🤖 Testing Device Activity Simulation...")
        
        # This would normally involve sending MQTT messages or updating nodes
        # For now, we'll just test if the system can handle node updates
        
        try:
            # Get a test node to update
            response = requests.get(f"{API_BASE}/nodes", timeout=10)
            if response.status_code == 200:
                nodes = response.json()
                if isinstance(nodes, list):
                    node_list = nodes
                else:
                    node_list = nodes.get('data', nodes.get('nodes', []))
                
                if node_list:
                    test_node = node_list[0]
                    node_id = test_node.get('node_id')
                    
                    # Try to update the node (simulate activity)
                    update_data = {
                        "name": test_node.get('name', 'Test Node'),
                        "status": "online" if test_node.get('status') != 'online' else 'offline'
                    }
                    
                    start_time = time.time()
                    update_response = requests.put(f"{API_BASE}/nodes/{node_id}", 
                                                 json=update_data, timeout=10)
                    duration = time.time() - start_time
                    
                    if update_response.status_code == 200:
                        self.log_test("Device Activity Simulation", "PASS",
                                    f"Successfully updated node status", duration)
                    else:
                        self.log_test("Device Activity Simulation", "WARNING",
                                    f"Update failed: HTTP {update_response.status_code}", duration)
                else:
                    self.log_test("Device Activity Simulation", "WARNING",
                                "No nodes available for simulation")
            else:
                self.log_test("Device Activity Simulation", "FAIL",
                            f"Cannot get nodes: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Device Activity Simulation", "FAIL", f"Simulation error: {str(e)}")

    def cleanup_test_nodes(self, node_ids):
        """Clean up test nodes"""
        print("\n🧹 Cleaning up test environment...")
        
        cleanup_count = 0
        for node_id in node_ids:
            try:
                response = requests.delete(f"{API_BASE}/nodes/{node_id}", timeout=10)
                if response.status_code in [200, 204]:
                    cleanup_count += 1
                    self.log_test(f"Cleanup: {node_id}", "PASS", "Node deleted")
                else:
                    self.log_test(f"Cleanup: {node_id}", "WARNING", 
                                f"Delete failed: HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"Cleanup: {node_id}", "WARNING", f"Delete error: {str(e)}")
        
        print(f"🧹 Cleaned up {cleanup_count}/{len(node_ids)} test nodes")

    def generate_monitoring_report(self):
        """Generate comprehensive monitoring report"""
        print("\n" + "="*70)
        print("🏥 NODE MONITORING DASHBOARD TEST REPORT")
        print("="*70)
        
        # Categorize results
        categories = {
            'Setup': [r for r in self.test_results if 'Create Node' in r['test']],
            'API Tests': [r for r in self.test_results if 'API' in r['test']],
            'Real-time': [r for r in self.test_results if 'WebSocket' in r['test'] or 'Real-time' in r['test']],
            'Health Monitoring': [r for r in self.test_results if 'Health' in r['test'] or 'Node Status' in r['test']],
            'Performance': [r for r in self.test_results if 'Performance' in r['test']],
            'Simulation': [r for r in self.test_results if 'Simulation' in r['test']],
            'Cleanup': [r for r in self.test_results if 'Cleanup' in r['test']]
        }
        
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_warnings = 0
        
        for category, tests in categories.items():
            if not tests:
                continue
                
            passed = len([t for t in tests if t['status'] == 'PASS'])
            failed = len([t for t in tests if t['status'] == 'FAIL']) 
            warnings = len([t for t in tests if t['status'] == 'WARNING'])
            
            total_tests += len(tests)
            total_passed += passed
            total_failed += failed
            total_warnings += warnings
            
            print(f"\n📊 {category}:")
            print(f"   ✅ Passed: {passed}")
            print(f"   ❌ Failed: {failed}")
            print(f"   ⚠️ Warnings: {warnings}")
        
        print(f"\n🎯 OVERALL MONITORING SYSTEM ASSESSMENT:")
        print("-" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {total_passed} ({total_passed/total_tests*100:.1f}%)")
        print(f"❌ Failed: {total_failed} ({total_failed/total_tests*100:.1f}%)")
        print(f"⚠️ Warnings: {total_warnings} ({total_warnings/total_tests*100:.1f}%)")
        
        success_rate = total_passed / total_tests * 100 if total_tests > 0 else 0
        
        print(f"\n📈 MONITORING SYSTEM RATING:")
        if success_rate >= 90:
            print("🏆 EXCELLENT: Monitoring system is production-ready!")
        elif success_rate >= 75:
            print("✅ GOOD: Monitoring system is working well!")
        elif success_rate >= 60:
            print("⚠️ FAIR: Monitoring system needs some improvements.")
        else:
            print("🚨 POOR: Monitoring system requires immediate attention!")
        
        # Key findings
        print(f"\n🔍 KEY FINDINGS:")
        failed_tests = [t for t in self.test_results if t['status'] == 'FAIL']
        if failed_tests:
            print("❌ Failed Tests:")
            for test in failed_tests[:3]:  # Show top 3 failed tests
                print(f"   • {test['test']}: {test['message']}")
        
        warning_tests = [t for t in self.test_results if t['status'] == 'WARNING']
        if warning_tests:
            print("⚠️ Warning Tests:")
            for test in warning_tests[:3]:  # Show top 3 warnings
                print(f"   • {test['test']}: {test['message']}")
        
        print("="*70)

    async def run_comprehensive_test(self):
        """Run complete monitoring dashboard test suite"""
        print("🏥 RNR Solutions IoT Platform - Comprehensive Monitoring Test")
        print("="*70)
        print("Testing enterprise-grade node monitoring and dashboard capabilities...")
        
        # Setup test environment
        created_nodes = self.create_test_nodes()
        
        # Run all tests
        self.test_monitoring_apis()
        await self.test_realtime_monitoring()
        self.test_node_health_monitoring()
        self.test_monitoring_performance()
        self.simulate_device_activity()
        
        # Cleanup
        self.cleanup_test_nodes(created_nodes)
        
        # Generate report
        self.generate_monitoring_report()

def main():
    """Main test execution"""
    test = MonitoringDashboardTest()
    asyncio.run(test.run_comprehensive_test())

if __name__ == "__main__":
    main()

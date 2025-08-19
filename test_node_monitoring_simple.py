#!/usr/bin/env python3
"""
RNR Solutions IoT Platform - Simple Node Monitoring Test
Creates test nodes and monitors their status.
"""

import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:8000/api"

def create_test_node(node_id, name):
    """Create a test node"""
    node_data = {
        "node_id": node_id,
        "name": name,
        "device_type": "ESP32",
        "location": "Test Lab",
        "capabilities": ["temperature", "humidity"],
        "status": "online"
    }
    
    try:
        response = requests.post(f"{API_BASE}/nodes", json=node_data, timeout=10)
        if response.status_code == 201:
            print(f"✅ Created test node: {name} ({node_id})")
            return True
        else:
            print(f"❌ Failed to create node {name}: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error creating node {name}: {e}")
        return False

def test_node_monitoring():
    """Test node monitoring capabilities"""
    print("🏥 RNR Solutions IoT Platform - Node Monitoring Test")
    print("="*60)
    
    # Create test nodes
    print("\n🔧 Creating Test Nodes...")
    test_nodes = [
        ("TEST001", "Test Node 1"),
        ("TEST002", "Test Node 2"),
        ("TEST003", "Test Node 3")
    ]
    
    created_nodes = []
    for node_id, name in test_nodes:
        if create_test_node(node_id, name):
            created_nodes.append((node_id, name))
    
    print(f"\n📊 Created {len(created_nodes)} test nodes")
    
    # Test API endpoints
    print("\n🔌 Testing Node Monitoring APIs...")
    
    endpoints = [
        {
            'name': 'Get All Nodes',
            'url': f"{API_BASE}/nodes",
            'expected_min': len(created_nodes)
        },
        {
            'name': 'Get Platform Status',
            'url': f"http://localhost:8000/",
            'expected_min': 0
        },
        {
            'name': 'Get Sensor Data',
            'url': f"{API_BASE}/sensor-data?limit=10",
            'expected_min': 0
        }
    ]
    
    results = []
    
    for endpoint in endpoints:
        try:
            start_time = time.time()
            response = requests.get(endpoint['url'], timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if endpoint['name'] == 'Get All Nodes':
                    if isinstance(data, list):
                        count = len(data)
                    else:
                        count = len(data.get('data', data.get('nodes', [])))
                    
                    if count >= endpoint['expected_min']:
                        print(f"✅ {endpoint['name']}: Found {count} nodes ({duration:.2f}s)")
                        results.append(True)
                    else:
                        print(f"⚠️ {endpoint['name']}: Expected {endpoint['expected_min']}, found {count} ({duration:.2f}s)")
                        results.append(False)
                        
                elif endpoint['name'] == 'Get Platform Status':
                    platform = data.get('message', 'Unknown')
                    version = data.get('version', 'Unknown')
                    status = data.get('status', 'unknown')
                    print(f"✅ {endpoint['name']}: {platform} v{version} - {status} ({duration:.2f}s)")
                    results.append(True)
                    
                elif endpoint['name'] == 'Get Sensor Data':
                    if isinstance(data, list):
                        count = len(data)
                    else:
                        count = len(data.get('data', []))
                    print(f"✅ {endpoint['name']}: Retrieved {count} sensor records ({duration:.2f}s)")
                    results.append(True)
                    
            else:
                print(f"❌ {endpoint['name']}: HTTP {response.status_code} ({duration:.2f}s)")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {endpoint['name']}: Error - {e}")
            results.append(False)
    
    # Test individual node monitoring
    print("\n🏥 Testing Individual Node Health...")
    
    try:
        response = requests.get(f"{API_BASE}/nodes", timeout=10)
        if response.status_code == 200:
            nodes = response.json()
            if isinstance(nodes, list):
                node_list = nodes
            else:
                node_list = nodes.get('data', nodes.get('nodes', []))
            
            healthy_nodes = 0
            for node in node_list:
                node_id = node.get('node_id')
                name = node.get('name', 'Unnamed')
                status = node.get('status', 'unknown')
                last_seen = node.get('last_seen')
                
                if status == 'online':
                    print(f"✅ Node Health: {name} ({node_id}) - {status}")
                    healthy_nodes += 1
                else:
                    print(f"⚠️ Node Health: {name} ({node_id}) - {status}")
            
            if len(node_list) > 0:
                health_rate = (healthy_nodes / len(node_list)) * 100
                print(f"\n📊 Node Health Summary: {healthy_nodes}/{len(node_list)} nodes healthy ({health_rate:.1f}%)")
                results.append(health_rate >= 80)
            else:
                print("\n⚠️ No nodes found for health monitoring")
                results.append(False)
        else:
            print(f"❌ Failed to get nodes for health check: HTTP {response.status_code}")
            results.append(False)
            
    except Exception as e:
        print(f"❌ Node health check failed: {e}")
        results.append(False)
    
    # Cleanup - delete test nodes
    print("\n🧹 Cleaning up test nodes...")
    cleanup_count = 0
    for node_id, name in created_nodes:
        try:
            response = requests.delete(f"{API_BASE}/nodes/{node_id}", timeout=10)
            if response.status_code in [200, 204]:
                print(f"✅ Deleted test node: {name}")
                cleanup_count += 1
            else:
                print(f"⚠️ Failed to delete {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"⚠️ Error deleting {name}: {e}")
    
    print(f"\n🧹 Cleaned up {cleanup_count}/{len(created_nodes)} test nodes")
    
    # Final results
    print("\n" + "="*60)
    print("🎯 MONITORING TEST RESULTS")
    print("="*60)
    
    passed_tests = sum(results)
    total_tests = len(results)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests} ({success_rate:.1f}%)")
    print(f"❌ Failed: {total_tests - passed_tests} ({100 - success_rate:.1f}%)")
    
    if success_rate >= 90:
        print("\n🎉 EXCELLENT: Node monitoring system is working perfectly!")
    elif success_rate >= 75:
        print("\n👍 GOOD: Node monitoring system is working well!")
    elif success_rate >= 50:
        print("\n⚠️ FAIR: Node monitoring system has some issues.")
    else:
        print("\n🚨 POOR: Node monitoring system needs attention!")
    
    print("="*60)

if __name__ == "__main__":
    test_node_monitoring()

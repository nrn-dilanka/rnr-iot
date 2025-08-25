#!/usr/bin/env python3
"""
Simple RabbitMQ Connection Test
Tests if we can connect to RabbitMQ management interface
"""

import urllib.request
import urllib.error
import base64
import json
import sys

def test_rabbitmq_connection():
    """Test RabbitMQ management interface connectivity"""
    print("🐰 Simple RabbitMQ Connection Test")
    print("=" * 50)
    
    # Configuration
    host = "localhost"
    port = 15672
    username = "rnr_iot_user" 
    password = "rnr_iot_2025!"
    
    # Create basic auth header
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    # Test URLs
    test_urls = [
        f"http://{host}:{port}/api/overview",
        f"http://{host}:{port}/api/queues",
        f"http://{host}:{port}/api/exchanges",
        f"http://{host}:{port}/api/connections"
    ]
    
    print(f"🔗 Testing connection to {host}:{port}")
    print(f"👤 Username: {username}")
    print()
    
    for url in test_urls:
        endpoint = url.split("/")[-1]
        print(f"📊 Testing {endpoint}...")
        
        try:
            # Create request with authentication
            req = urllib.request.Request(url)
            req.add_header('Authorization', f'Basic {encoded_credentials}')
            
            # Make request with timeout
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    print(f"   ✅ {endpoint}: OK")
                    
                    # Show specific information based on endpoint
                    if endpoint == "overview":
                        version = data.get('rabbitmq_version', 'unknown')
                        print(f"   📦 RabbitMQ Version: {version}")
                    elif endpoint == "queues":
                        queue_count = len(data)
                        print(f"   📋 Queues found: {queue_count}")
                        if queue_count > 0:
                            for queue in data[:3]:  # Show first 3 queues
                                name = queue.get('name', 'unknown')
                                messages = queue.get('messages', 0)
                                print(f"      📦 {name}: {messages} messages")
                    elif endpoint == "exchanges":
                        exchange_count = len(data)
                        print(f"   🔄 Exchanges found: {exchange_count}")
                    elif endpoint == "connections":
                        conn_count = len(data)
                        print(f"   🔌 Active connections: {conn_count}")
                else:
                    print(f"   ❌ {endpoint}: HTTP {response.status}")
                    
        except urllib.error.HTTPError as e:
            print(f"   ❌ {endpoint}: HTTP {e.code} - {e.reason}")
            if e.code == 401:
                print("   🔐 Authentication failed - check credentials")
            elif e.code == 404:
                print("   🔍 Endpoint not found - RabbitMQ may not be running")
        except urllib.error.URLError as e:
            print(f"   ❌ {endpoint}: Connection failed - {e.reason}")
            print("   🚫 RabbitMQ service may not be running")
        except Exception as e:
            print(f"   ❌ {endpoint}: Unexpected error - {e}")
        
        print()
    
    # Summary
    print("🎯 Quick Troubleshooting Tips:")
    print("1. Ensure Docker containers are running: docker ps")
    print("2. Check RabbitMQ logs: docker logs rnr_iot_rabbitmq")
    print("3. Try accessing management UI: http://localhost:15672")
    print("4. Verify container health: docker exec rnr_iot_rabbitmq rabbitmq-diagnostics ping")
    print()
    
    return True

if __name__ == "__main__":
    try:
        test_rabbitmq_connection()
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

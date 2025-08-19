#!/usr/bin/env python3
"""
Quick WebSocket client test to verify real-time ESP32 data is being received
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket():
    uri = "ws://192.168.8.105:8000/ws"
    
    try:
        print("🔌 Connecting to WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket!")
            print("🎧 Listening for ESP32 real-time data...")
            print("=" * 50)
            
            message_count = 0
            
            # Listen for messages for 30 seconds
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_count += 1
                    
                    if data.get('type') == 'sensor_data':
                        node_id = data.get('node_id', 'Unknown')
                        sensor_data = data.get('data', {})
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        print(f"📡 [{timestamp}] ESP32 Data from {node_id[:8]}...")
                        print(f"   🌡️  Temperature: {sensor_data.get('temperature', 'N/A')}°C")
                        print(f"   💧 Humidity: {sensor_data.get('humidity', 'N/A')}%")
                        print(f"   🌬️  Gas Sensor: {sensor_data.get('gas_sensor', 'N/A')}")
                        print(f"   📶 WiFi RSSI: {sensor_data.get('wifi_rssi', 'N/A')} dBm")
                        print(f"   🔧 Servo Angle: {sensor_data.get('servo_angle', 'N/A')}°")
                        print("   " + "-" * 40)
                    
                    elif data.get('type') == 'node_status':
                        node_id = data.get('node_id', 'Unknown')
                        status = data.get('status', 'Unknown')
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        status_emoji = "🟢" if status == 'online' else "🔴"
                        print(f"{status_emoji} [{timestamp}] Node Status: {node_id[:8]}... is {status}")
                        print("   " + "-" * 40)
                    
                    else:
                        print(f"📨 [{datetime.now().strftime('%H:%M:%S')}] Other message: {data.get('type', 'unknown')}")
                        print("   " + "-" * 40)
                    
                    # Stop after 20 messages for this test
                    if message_count >= 20:
                        print(f"\n✅ Test complete! Received {message_count} real-time messages")
                        break
                        
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON received: {message}")
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
    
    except ConnectionRefusedError:
        print("❌ Could not connect to WebSocket server")
        print("   Make sure the API server is running on http://192.168.8.105:8000")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

async def main():
    print("🧪 ESP32 Real-time WebSocket Test")
    print("=" * 40)
    print("Testing WebSocket connection to receive ESP32 data...")
    print()
    
    await test_websocket()
    
    print()
    print("🎯 If you saw ESP32 data above, real-time updates are working!")
    print("🌐 Check your dashboard at: http://192.168.8.105:3000")

if __name__ == "__main__":
    asyncio.run(main())

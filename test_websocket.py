#!/usr/bin/env python3
"""
Simple WebSocket test client to verify the connection
"""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Successfully connected to WebSocket!")
            
            # Listen for a few messages
            for i in range(3):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"📨 Received message {i+1}: {data}")
                except asyncio.TimeoutError:
                    print(f"⏰ No message received within 5 seconds (attempt {i+1})")
                    
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())

#!/usr/bin/env python3
"""
ESP32 Real-time Data Simulator
Simulates multiple ESP32 devices sending sensor data in real-time to test the WebSocket updates.
"""

import json
import time
import random
import asyncio
from datetime import datetime
import paho.mqtt.client as mqtt
import threading

class ESP32Simulator:
    def __init__(self, device_id):
        self.device_id = device_id
        self.mqtt_client = None
        self.running = False
        
        # Simulated sensor baselines
        self.temperature_base = random.uniform(20.0, 30.0)
        self.humidity_base = random.uniform(40.0, 70.0)
        self.gas_sensor_base = random.randint(50, 200)
        self.servo_angle = 90
        
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, f"esp32_sim_{self.device_id}")
        self.mqtt_client.username_pw_set("rnr_iot_user", "rnr_iot_2025!")
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print(f"🔗 [{self.device_id}] Connected to MQTT")
                # Subscribe to commands
                client.subscribe(f"devices/{self.device_id}/commands")
            else:
                print(f"❌ [{self.device_id}] Failed to connect to MQTT: {rc}")
        
        def on_message(client, userdata, msg):
            try:
                command = json.loads(msg.payload.decode())
                print(f"📨 [{self.device_id}] Received command: {command}")
                
                if command.get('action') == 'SERVO_CONTROL':
                    self.servo_angle = command.get('angle', 90)
                    print(f"🔧 [{self.device_id}] Servo set to {self.servo_angle}°")
                    
                elif command.get('action') == 'FIRMWARE_UPDATE':
                    firmware_url = command.get('url', '')
                    print(f"🔄 [{self.device_id}] Starting OTA firmware update from: {firmware_url}")
                    
                    # Simulate firmware update process
                    self.simulate_firmware_update(firmware_url)
                    
                elif command.get('action') == 'REBOOT':
                    print(f"🔃 [{self.device_id}] Rebooting device...")
                    # Simulate reboot by resetting some values
                    self.servo_angle = 90
                    
                else:
                    print(f"❓ [{self.device_id}] Unknown command: {command.get('action')}")
                    
            except Exception as e:
                print(f"❌ [{self.device_id}] Error processing command: {e}")
        
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_message = on_message
        
        try:
            self.mqtt_client.connect("16.171.30.3", 1883, 60)
            self.mqtt_client.loop_start()
            return True
        except Exception as e:
            print(f"❌ [{self.device_id}] MQTT connection error: {e}")
            return False
    
    def simulate_firmware_update(self, firmware_url):
        """Simulate an OTA firmware update process"""
        def ota_process():
            try:
                print(f"🔄 [{self.device_id}] Connecting to firmware server...")
                time.sleep(1)
                
                print(f"📥 [{self.device_id}] Downloading firmware from {firmware_url}")
                time.sleep(2)
                
                print(f"✅ [{self.device_id}] Firmware downloaded successfully")
                print(f"🔍 [{self.device_id}] Verifying firmware integrity...")
                time.sleep(1)
                
                print(f"✅ [{self.device_id}] Firmware verification passed")
                print(f"💾 [{self.device_id}] Installing firmware...")
                time.sleep(2)
                
                print(f"🎉 [{self.device_id}] Firmware update completed successfully!")
                print(f"🔃 [{self.device_id}] Device will reboot in 3 seconds...")
                time.sleep(3)
                
                print(f"🟢 [{self.device_id}] Device rebooted with new firmware")
                
                # Send confirmation back to server
                if self.mqtt_client:
                    update_status = {
                        "device_id": self.device_id,
                        "status": "success",
                        "message": "Firmware update completed successfully",
                        "timestamp": datetime.now().isoformat(),
                        "firmware_url": firmware_url
                    }
                    self.mqtt_client.publish(f"devices/{self.device_id}/ota_status", json.dumps(update_status))
                    
            except Exception as e:
                print(f"❌ [{self.device_id}] OTA update failed: {e}")
                if self.mqtt_client:
                    error_status = {
                        "device_id": self.device_id,
                        "status": "error",
                        "message": f"Firmware update failed: {str(e)}",
                        "timestamp": datetime.now().isoformat(),
                        "firmware_url": firmware_url
                    }
                    self.mqtt_client.publish(f"devices/{self.device_id}/ota_status", json.dumps(error_status))
        
        # Run OTA process in background thread
        threading.Thread(target=ota_process, daemon=True).start()
    
    def generate_sensor_data(self):
        """Generate realistic sensor data"""
        # Add some random variation
        temperature = self.temperature_base + random.uniform(-2.0, 2.0)
        humidity = self.humidity_base + random.uniform(-5.0, 5.0)
        gas_sensor = self.gas_sensor_base + random.randint(-20, 20)
        
        # Clamp values to realistic ranges
        temperature = max(15.0, min(35.0, temperature))
        humidity = max(30.0, min(80.0, humidity))
        gas_sensor = max(0, min(4095, gas_sensor))
        
        return {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1),
            "gas_sensor": gas_sensor,
            "status": "online",
            "node_id": self.device_id,
            "servo_angle": self.servo_angle,
            "uptime": int(time.time() * 1000),  # Simulated uptime
            "wifi_rssi": random.randint(-80, -30),
            "free_heap": random.randint(100000, 200000)
        }
    
    def publish_data(self):
        """Publish sensor data to MQTT"""
        if not self.mqtt_client or not self.running:
            return
        
        data = self.generate_sensor_data()
        topic = f"devices/{self.device_id}/data"
        
        try:
            result = self.mqtt_client.publish(topic, json.dumps(data))
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📡 [{self.device_id}] Published: T={data['temperature']}°C, H={data['humidity']}%, Gas={data['gas_sensor']}")
            else:
                print(f"❌ [{self.device_id}] Publish failed: {result.rc}")
        except Exception as e:
            print(f"❌ [{self.device_id}] Publish error: {e}")
    
    def start_simulation(self, interval=3):
        """Start sending data at regular intervals"""
        if not self.connect_mqtt():
            return
        
        self.running = True
        print(f"🚀 [{self.device_id}] Starting simulation (interval: {interval}s)")
        
        def data_loop():
            while self.running:
                self.publish_data()
                time.sleep(interval)
        
        self.data_thread = threading.Thread(target=data_loop, daemon=True)
        self.data_thread.start()
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.running = False
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        print(f"⏹️ [{self.device_id}] Simulation stopped")

class ESP32FleetSimulator:
    def __init__(self):
        self.devices = []
        self.running = False
    
    def add_device(self, device_id):
        """Add a new ESP32 device to simulate"""
        device = ESP32Simulator(device_id)
        self.devices.append(device)
        return device
    
    def start_fleet(self, interval=3):
        """Start all devices"""
        print(f"🚀 Starting ESP32 fleet simulation with {len(self.devices)} devices")
        print("=" * 60)
        
        for device in self.devices:
            device.start_simulation(interval)
            time.sleep(0.5)  # Stagger startup
        
        self.running = True
        print(f"\n✅ All {len(self.devices)} ESP32 devices are now sending data!")
        print("🌐 Open your dashboard at: http://localhost:3000")
        print("📊 Navigate to 'ESP32 Manager' to see real-time updates")
        print("🔄 Press Ctrl+C to stop simulation")
    
    def stop_fleet(self):
        """Stop all devices"""
        print(f"\n⏹️ Stopping {len(self.devices)} ESP32 devices...")
        for device in self.devices:
            device.stop_simulation()
        self.running = False
        print("✅ Fleet simulation stopped")

def main():
    # Create fleet simulator
    fleet = ESP32FleetSimulator()
    
    # Add multiple ESP32 devices with realistic MAC-style IDs
    device_ids = [
        "441793F9456C",  # Existing test device
        "A0B1C2D3E4F5",  # New test device 1
        "1A2B3C4D5E6F",  # New test device 2
        "F0E1D2C3B4A5",  # New test device 3
    ]
    
    for device_id in device_ids:
        fleet.add_device(device_id)
    
    try:
        # Start the simulation
        fleet.start_fleet(interval=2)  # Send data every 2 seconds
        
        # Keep running until interrupted
        while fleet.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Simulation interrupted by user")
    except Exception as e:
        print(f"❌ Simulation error: {e}")
    finally:
        fleet.stop_fleet()

if __name__ == "__main__":
    print("🔬 ESP32 Real-time Data Simulator")
    print("=" * 40)
    print("This simulator creates multiple virtual ESP32 devices")
    print("that send real-time sensor data to test your IoT platform.")
    print()
    main()

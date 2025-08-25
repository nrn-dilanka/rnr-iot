#!/usr/bin/env python3
"""
Start all queue consumers for processing ESP32 messages
This script starts the queue consumer services to handle ESP32 communication
"""
import sys
import time
import signal
from datetime import datetime

# Import queue components
try:
    from queue_manager import queue_manager
    from queue_processors import (
        process_sensor_data, 
        process_alert, 
        process_data_request, 
        process_status_update,
        processor
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you have installed: pip install pika")
    sys.exit(1)

class QueueConsumerService:
    def __init__(self):
        self.running = False
        self.start_time = None
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n⚠️ Received signal {signum}. Shutting down queue consumers...")
        self.running = False
        
    def start_consumers(self):
        """Start all queue consumers"""
        print("🚀 Starting Queue Consumer Service...")
        print("=" * 60)
        
        # Connect to RabbitMQ
        if not queue_manager.connect():
            print("❌ Failed to connect to RabbitMQ")
            return False
        
        # Define consumers with their processors
        consumers = [
            ('sensor_data', process_sensor_data, "Sensor data from ESP32 devices"),
            ('alerts', process_alert, "Alerts and critical notifications"),
            ('data_requests', process_data_request, "Data requests from ESP32"),
            ('status_updates', process_status_update, "Status updates from devices")
        ]
        
        # Start each consumer
        started_consumers = 0
        for queue_name, processor_func, description in consumers:
            print(f"\n🔧 Starting consumer for '{queue_name}'...")
            print(f"   📋 Purpose: {description}")
            
            if queue_manager.consume_queue(queue_name, processor_func):
                print(f"   ✅ Consumer started successfully")
                started_consumers += 1
            else:
                print(f"   ❌ Failed to start consumer")
        
        if started_consumers == len(consumers):
            print(f"\n🎉 All {started_consumers} queue consumers started successfully!")
            return True
        else:
            print(f"\n⚠️ Only {started_consumers}/{len(consumers)} consumers started")
            return False
    
    def show_status(self):
        """Show service status"""
        print(f"\n📊 Queue Consumer Service Status:")
        print(f"   🕒 Started: {self.start_time}")
        print(f"   ⏱️ Running: {time.time() - self.start_time.timestamp():.0f} seconds")
        print(f"   📈 Messages processed: {processor.processed_count}")
        print(f"   ❌ Processing errors: {processor.error_count}")
        
        # Show queue information
        queues_to_check = ['sensor_data', 'alerts', 'data_requests', 'status_updates']
        print(f"\n📋 Queue Status:")
        
        for queue_name in queues_to_check:
            queue_info = queue_manager.get_queue_info(queue_name)
            if queue_info:
                print(f"   📦 {queue_name}: {queue_info['message_count']} messages, {queue_info['consumer_count']} consumers")
            else:
                print(f"   ❌ {queue_name}: Unable to get queue info")
    
    def run(self):
        """Main service loop"""
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.start_time = datetime.now()
        
        # Start consumers
        if not self.start_consumers():
            print("❌ Failed to start all consumers. Exiting.")
            return False
        
        self.running = True
        
        print(f"\n📡 Queue consumers are now active!")
        print(f"🔍 Monitoring queues: sensor_data, alerts, data_requests, status_updates")
        print(f"💡 Send messages from ESP32 devices to see them processed here")
        print(f"⚠️ Press Ctrl+C to stop gracefully")
        print("=" * 60)
        
        # Main service loop
        status_interval = 30  # Show status every 30 seconds
        last_status_time = 0
        
        try:
            while self.running:
                current_time = time.time()
                
                # Show periodic status
                if current_time - last_status_time >= status_interval:
                    self.show_status()
                    last_status_time = current_time
                
                # Small sleep to prevent busy waiting
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n⚠️ Keyboard interrupt received")
            self.running = False
        
        # Cleanup
        print("\n🔄 Shutting down queue consumers...")
        queue_manager.close()
        
        runtime = time.time() - self.start_time.timestamp()
        print(f"✅ Queue consumer service stopped after {runtime:.0f} seconds")
        print(f"📊 Final stats: {processor.processed_count} processed, {processor.error_count} errors")
        
        return True

def main():
    """Main entry point"""
    print("🧪 MQTT Queue Consumer Service")
    print("=" * 60)
    print(f"🕒 Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if RabbitMQ is accessible
    print("🔍 Checking RabbitMQ connection...")
    if not queue_manager.connect():
        print("❌ Cannot connect to RabbitMQ. Make sure it's running:")
        print("   💡 Start with: docker-compose up -d")
        print("   💡 Check status: docker ps | grep rabbitmq")
        print("   💡 Check logs: docker logs <rabbitmq-container>")
        return False
    
    print("✅ RabbitMQ connection successful")
    
    # Start the service
    service = QueueConsumerService()
    success = service.run()
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n🚨 Unexpected error: {e}")
        sys.exit(2)

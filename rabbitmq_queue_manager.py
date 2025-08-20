#!/usr/bin/env python3
"""
RabbitMQ Queue and Stream Management Script
Manages queues, exchanges, and streams for the RNR IoT Platform
"""

import pika
import json
import requests
from datetime import datetime
import argparse

class RabbitMQManager:
    def __init__(self, host="16.171.30.3", port=5672, username="rnr_iot_user", password="rnr_iot_2025!", vhost="rnr_iot_vhost"):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.vhost = vhost
        self.management_port = 15672
        self.connection = None
        self.channel = None
        
    def connect(self):
        """Connect to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                virtual_host=self.vhost,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            print(f"✅ Connected to RabbitMQ at {self.host}:{self.port}")
            return True
        except pika.exceptions.ProbableAuthenticationError as e:
            print(f"❌ Authentication failed: {e}")
            return False
        except pika.exceptions.ProbableAccessDeniedError as e:
            print(f"❌ Access denied: {e}")
            return False
        except Exception as e:
            print(f"❌ Failed to connect to RabbitMQ: {e}")
            print(f"   Host: {self.host}:{self.port}")
            print(f"   VHost: {self.vhost}")
            print(f"   User: {self.username}")
            return False
    
    def disconnect(self):
        """Disconnect from RabbitMQ"""
        if self.connection:
            self.connection.close()
            print("🔌 Disconnected from RabbitMQ")
    
    def create_queue(self, queue_name, durable=True, auto_delete=False):
        """Create a queue"""
        try:
            self.channel.queue_declare(
                queue=queue_name,
                durable=durable,
                auto_delete=auto_delete
            )
            print(f"✅ Queue '{queue_name}' created successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to create queue '{queue_name}': {e}")
            return False
    
    def delete_queue(self, queue_name):
        """Delete a queue"""
        try:
            self.channel.queue_delete(queue=queue_name)
            print(f"🗑️ Queue '{queue_name}' deleted successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to delete queue '{queue_name}': {e}")
            return False
    
    def purge_queue(self, queue_name):
        """Purge all messages from a queue"""
        try:
            self.channel.queue_purge(queue=queue_name)
            print(f"🧹 Queue '{queue_name}' purged successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to purge queue '{queue_name}': {e}")
            return False
    
    def create_exchange(self, exchange_name, exchange_type="direct", durable=True):
        """Create an exchange"""
        try:
            self.channel.exchange_declare(
                exchange=exchange_name,
                exchange_type=exchange_type,
                durable=durable
            )
            print(f"✅ Exchange '{exchange_name}' ({exchange_type}) created successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to create exchange '{exchange_name}': {e}")
            return False
    
    def bind_queue(self, queue_name, exchange_name, routing_key=""):
        """Bind a queue to an exchange"""
        try:
            self.channel.queue_bind(
                queue=queue_name,
                exchange=exchange_name,
                routing_key=routing_key
            )
            print(f"🔗 Queue '{queue_name}' bound to exchange '{exchange_name}' with routing key '{routing_key}'")
            return True
        except Exception as e:
            print(f"❌ Failed to bind queue '{queue_name}' to exchange '{exchange_name}': {e}")
            return False
    
    def publish_message(self, exchange_name, routing_key, message, properties=None):
        """Publish a message to an exchange"""
        try:
            if isinstance(message, dict):
                message = json.dumps(message)
            
            self.channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=message,
                properties=properties
            )
            print(f"📤 Message published to exchange '{exchange_name}' with routing key '{routing_key}'")
            return True
        except Exception as e:
            print(f"❌ Failed to publish message: {e}")
            return False
    
    def get_queue_info_via_api(self, queue_name):
        """Get queue information via Management API"""
        try:
            vhost_encoded = self.vhost.replace("/", "%2F")
            url = f"http://{self.host}:{self.management_port}/api/queues/{vhost_encoded}/{queue_name}"
            response = requests.get(url, auth=(self.username, self.password))
            
            if response.status_code == 200:
                queue_info = response.json()
                print(f"📊 Queue '{queue_name}' Info:")
                print(f"   Messages: {queue_info.get('messages', 0)}")
                print(f"   Consumers: {queue_info.get('consumers', 0)}")
                print(f"   Memory: {queue_info.get('memory', 0)} bytes")
                print(f"   State: {queue_info.get('state', 'unknown')}")
                return queue_info
            else:
                print(f"❌ Failed to get queue info: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error getting queue info: {e}")
            return None
    
    def list_queues(self):
        """List all queues via Management API"""
        try:
            vhost_encoded = self.vhost.replace("/", "%2F")
            url = f"http://{self.host}:{self.management_port}/api/queues/{vhost_encoded}"
            response = requests.get(url, auth=(self.username, self.password))
            
            if response.status_code == 200:
                queues = response.json()
                print(f"📋 Found {len(queues)} queues:")
                print("-" * 80)
                for queue in queues:
                    print(f"Queue: {queue['name']}")
                    print(f"   Messages: {queue.get('messages', 0)}")
                    print(f"   Consumers: {queue.get('consumers', 0)}")
                    print(f"   Durable: {queue.get('durable', False)}")
                    print(f"   Auto Delete: {queue.get('auto_delete', False)}")
                    print("-" * 40)
                return queues
            else:
                print(f"❌ Failed to list queues: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error listing queues: {e}")
            return []
    
    def list_exchanges(self):
        """List all exchanges via Management API"""
        try:
            vhost_encoded = self.vhost.replace("/", "%2F")
            url = f"http://{self.host}:{self.management_port}/api/exchanges/{vhost_encoded}"
            response = requests.get(url, auth=(self.username, self.password))
            
            if response.status_code == 200:
                exchanges = response.json()
                print(f"🔄 Found {len(exchanges)} exchanges:")
                print("-" * 80)
                for exchange in exchanges:
                    print(f"Exchange: {exchange['name'] or '(default)'}")
                    print(f"   Type: {exchange.get('type', 'unknown')}")
                    print(f"   Durable: {exchange.get('durable', False)}")
                    print(f"   Auto Delete: {exchange.get('auto_delete', False)}")
                    print("-" * 40)
                return exchanges
            else:
                print(f"❌ Failed to list exchanges: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error listing exchanges: {e}")
            return []
    
    def setup_iot_queues(self):
        """Set up standard IoT platform queues"""
        print("🚀 Setting up IoT Platform queues...")
        
        # Create exchanges
        exchanges = [
            ("iot.sensor.data", "topic"),
            ("iot.device.commands", "direct"),
            ("iot.alerts", "fanout"),
            ("iot.firmware", "direct")
        ]
        
        for exchange_name, exchange_type in exchanges:
            self.create_exchange(exchange_name, exchange_type)
        
        # Create queues
        queues = [
            "sensor_data_processing",
            "device_commands",
            "alert_notifications", 
            "firmware_deployments",
            "esp32_heartbeats",
            "esp32_sensor_data",
            "esp32_commands",
            "mqtt_messages"
        ]
        
        for queue_name in queues:
            self.create_queue(queue_name)
        
        # Set up bindings
        bindings = [
            ("sensor_data_processing", "iot.sensor.data", "sensor.*"),
            ("esp32_sensor_data", "iot.sensor.data", "esp32.*"),
            ("device_commands", "iot.device.commands", ""),
            ("esp32_commands", "iot.device.commands", "esp32"),
            ("alert_notifications", "iot.alerts", ""),
            ("firmware_deployments", "iot.firmware", "")
        ]
        
        for queue, exchange, routing_key in bindings:
            self.bind_queue(queue, exchange, routing_key)
        
        print("✅ IoT Platform queues setup completed!")

def main():
    parser = argparse.ArgumentParser(description='RabbitMQ Queue Manager for RNR IoT Platform')
    parser.add_argument('--action', choices=[
        'list-queues', 'list-exchanges', 'create-queue', 'delete-queue', 
        'purge-queue', 'queue-info', 'setup-iot', 'create-exchange'
    ], required=True, help='Action to perform')
    
    parser.add_argument('--name', help='Queue or exchange name')
    parser.add_argument('--type', default='direct', help='Exchange type (direct, topic, fanout, headers)')
    parser.add_argument('--routing-key', default='', help='Routing key for bindings')
    parser.add_argument('--api-only', action='store_true', help='Use only Management API (no AMQP connection)')
    
    args = parser.parse_args()
    
    # Create manager and connect
    manager = RabbitMQManager()
    
    # For read-only operations, try API-only mode if AMQP fails
    read_only_actions = ['list-queues', 'list-exchanges', 'queue-info']
    
    if args.api_only or args.action in read_only_actions:
        print("🌐 Using Management API mode")
        amqp_connected = False
    else:
        amqp_connected = manager.connect()
        if not amqp_connected and args.action in read_only_actions:
            print("⚠️ AMQP connection failed, falling back to API-only mode")
    
    try:
        if args.action == 'list-queues':
            manager.list_queues()
        
        elif args.action == 'list-exchanges':
            manager.list_exchanges()
        
        elif args.action == 'queue-info':
            if not args.name:
                print("❌ Queue name required for queue-info action")
                return
            manager.get_queue_info_via_api(args.name)
        
        elif not amqp_connected:
            print("❌ AMQP connection required for this action but connection failed")
            return
        
        elif args.action == 'create-queue':
            if not args.name:
                print("❌ Queue name required for create-queue action")
                return
            manager.create_queue(args.name)
        
        elif args.action == 'delete-queue':
            if not args.name:
                print("❌ Queue name required for delete-queue action")
                return
            manager.delete_queue(args.name)
        
        elif args.action == 'purge-queue':
            if not args.name:
                print("❌ Queue name required for purge-queue action")
                return
            manager.purge_queue(args.name)
        
        elif args.action == 'create-exchange':
            if not args.name:
                print("❌ Exchange name required for create-exchange action")
                return
            manager.create_exchange(args.name, args.type)
        
        elif args.action == 'setup-iot':
            manager.setup_iot_queues()
        
    finally:
        if amqp_connected:
            manager.disconnect()

if __name__ == "__main__":
    print("🐰 RabbitMQ Queue Manager for RNR IoT Platform")
    print("=" * 60)
    main()

#!/usr/bin/env python3
"""
RabbitMQ Real-time Monitoring Dashboard
Live monitoring of queues, connections, and MQTT activity
"""

import requests
import json
import time
import os
from datetime import datetime
import argparse

class RabbitMQMonitor:
    def __init__(self, host="16.171.30.3", username="rnr_iot_user", password="rnr_iot_2025!", vhost="rnr_iot_vhost"):
        self.host = host
        self.username = username
        self.password = password
        self.vhost = vhost
        self.management_port = 15672
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def get_api_data(self, endpoint):
        """Get data from RabbitMQ Management API"""
        try:
            vhost_encoded = self.vhost.replace("/", "%2F")
            if "vhost" in endpoint and "{vhost}" in endpoint:
                endpoint = endpoint.replace("{vhost}", vhost_encoded)
            
            url = f"http://{self.host}:{self.management_port}/api/{endpoint}"
            response = requests.get(url, auth=(self.username, self.password))
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"❌ API Error: {e}")
            return None
    
    def get_overview(self):
        """Get RabbitMQ overview"""
        return self.get_api_data("overview")
    
    def get_queues(self):
        """Get all queues"""
        return self.get_api_data(f"queues/{self.vhost}")
    
    def get_connections(self):
        """Get all connections"""
        return self.get_api_data("connections")
    
    def get_channels(self):
        """Get all channels"""
        return self.get_api_data("channels")
    
    def get_exchanges(self):
        """Get all exchanges"""
        return self.get_api_data(f"exchanges/{self.vhost}")
    
    def format_bytes(self, bytes_value):
        """Format bytes to human readable"""
        if bytes_value < 1024:
            return f"{bytes_value} B"
        elif bytes_value < 1024**2:
            return f"{bytes_value/1024:.1f} KB"
        elif bytes_value < 1024**3:
            return f"{bytes_value/(1024**2):.1f} MB"
        else:
            return f"{bytes_value/(1024**3):.1f} GB"
    
    def print_header(self, title):
        """Print section header"""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
    
    def display_overview(self, overview):
        """Display system overview"""
        if not overview:
            return
            
        self.print_header("RABBITMQ OVERVIEW")
        print(f"🐰 RabbitMQ Version: {overview.get('rabbitmq_version', 'unknown')}")
        print(f"🔄 Management Version: {overview.get('management_version', 'unknown')}")
        print(f"📊 Uptime: {overview.get('uptime', 0) / 1000:.0f} seconds")
        
        stats = overview.get('message_stats', {})
        print(f"📤 Total Published: {stats.get('publish', 0)}")
        print(f"📥 Total Delivered: {stats.get('deliver_get', 0)}")
        print(f"✅ Total Acknowledged: {stats.get('ack', 0)}")
        
        listeners = overview.get('listeners', [])
        print(f"🌐 Active Listeners:")
        for listener in listeners:
            protocol = listener.get('protocol', 'unknown')
            port = listener.get('port', 'unknown')
            print(f"   {protocol}: {port}")
    
    def display_queues(self, queues):
        """Display queue information"""
        if not queues:
            return
            
        self.print_header(f"QUEUES ({len(queues)} total)")
        
        # Sort by message count (descending)
        queues_sorted = sorted(queues, key=lambda x: x.get('messages', 0), reverse=True)
        
        for queue in queues_sorted:
            name = queue['name']
            messages = queue.get('messages', 0)
            consumers = queue.get('consumers', 0)
            memory = self.format_bytes(queue.get('memory', 0))
            state = queue.get('state', 'unknown')
            
            # Color coding based on message count
            if messages > 100:
                status = "🔴"
            elif messages > 10:
                status = "🟡"
            elif messages > 0:
                status = "🟢"
            else:
                status = "⚪"
            
            print(f"{status} {name}")
            print(f"   📨 Messages: {messages}")
            print(f"   👥 Consumers: {consumers}")
            print(f"   💾 Memory: {memory}")
            print(f"   ⚡ State: {state}")
            
            # Show message rates if available
            msg_stats = queue.get('message_stats', {})
            if msg_stats:
                publish_rate = msg_stats.get('publish_details', {}).get('rate', 0)
                deliver_rate = msg_stats.get('deliver_details', {}).get('rate', 0)
                if publish_rate > 0 or deliver_rate > 0:
                    print(f"   📈 Rates: {publish_rate:.1f}/s in, {deliver_rate:.1f}/s out")
            
            print("-" * 40)
    
    def display_connections(self, connections):
        """Display connection information"""
        if not connections:
            return
            
        self.print_header(f"CONNECTIONS ({len(connections)} total)")
        
        mqtt_connections = []
        amqp_connections = []
        
        for conn in connections:
            protocol = conn.get('protocol', 'unknown')
            if protocol == 'MQTT':
                mqtt_connections.append(conn)
            else:
                amqp_connections.append(conn)
        
        if mqtt_connections:
            print(f"📡 MQTT Connections ({len(mqtt_connections)}):")
            for conn in mqtt_connections:
                client_id = conn.get('client_properties', {}).get('client_id', 'unknown')
                peer_host = conn.get('peer_host', 'unknown')
                peer_port = conn.get('peer_port', 'unknown')
                state = conn.get('state', 'unknown')
                channels = conn.get('channels', 0)
                
                print(f"   🔌 {client_id}")
                print(f"      From: {peer_host}:{peer_port}")
                print(f"      State: {state}")
                print(f"      Channels: {channels}")
                print("-" * 30)
        
        if amqp_connections:
            print(f"\n🔗 AMQP Connections ({len(amqp_connections)}):")
            for conn in amqp_connections:
                name = conn.get('name', 'unknown')
                user = conn.get('user', 'unknown')
                vhost = conn.get('vhost', 'unknown')
                state = conn.get('state', 'unknown')
                channels = conn.get('channels', 0)
                
                print(f"   🔌 {name}")
                print(f"      User: {user}")
                print(f"      VHost: {vhost}")
                print(f"      State: {state}")
                print(f"      Channels: {channels}")
                print("-" * 30)
    
    def display_exchanges(self, exchanges):
        """Display exchange information"""
        if not exchanges:
            return
            
        self.print_header(f"EXCHANGES ({len(exchanges)} total)")
        
        for exchange in exchanges:
            name = exchange['name'] or '(default)'
            ex_type = exchange.get('type', 'unknown')
            durable = exchange.get('durable', False)
            
            # Skip default AMQP exchanges unless they have activity
            if name.startswith('amq.') and name != 'amq.topic':
                continue
            
            print(f"🔄 {name}")
            print(f"   Type: {ex_type}")
            print(f"   Durable: {durable}")
            
            # Show message rates if available
            msg_stats = exchange.get('message_stats', {})
            if msg_stats:
                publish_in = msg_stats.get('publish_in', 0)
                publish_out = msg_stats.get('publish_out', 0)
                if publish_in > 0 or publish_out > 0:
                    print(f"   📈 Messages: {publish_in} in, {publish_out} out")
            
            print("-" * 30)
    
    def run_monitor(self, interval=5):
        """Run continuous monitoring"""
        print("🚀 Starting RabbitMQ Monitor...")
        print(f"📊 Refresh interval: {interval} seconds")
        print("🔄 Press Ctrl+C to stop")
        
        try:
            while True:
                self.clear_screen()
                
                print(f"🐰 RabbitMQ Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"🌐 Host: {self.host}:{self.management_port}")
                print(f"🏠 VHost: {self.vhost}")
                
                # Get all data
                overview = self.get_overview()
                queues = self.get_queues()
                connections = self.get_connections()
                exchanges = self.get_exchanges()
                
                # Display sections
                self.display_overview(overview)
                self.display_queues(queues)
                self.display_connections(connections)
                self.display_exchanges(exchanges)
                
                print(f"\n🔄 Refreshing in {interval} seconds... (Ctrl+C to stop)")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n👋 Monitor stopped by user")
        except Exception as e:
            print(f"\n❌ Monitor error: {e}")
    
    def run_single_report(self):
        """Run single monitoring report"""
        print(f"🐰 RabbitMQ Status Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Host: {self.host}:{self.management_port}")
        print(f"🏠 VHost: {self.vhost}")
        
        # Get all data
        overview = self.get_overview()
        queues = self.get_queues()
        connections = self.get_connections()
        exchanges = self.get_exchanges()
        
        # Display sections
        self.display_overview(overview)
        self.display_queues(queues)
        self.display_connections(connections)
        self.display_exchanges(exchanges)

def main():
    parser = argparse.ArgumentParser(description='RabbitMQ Real-time Monitor')
    parser.add_argument('--monitor', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--interval', type=int, default=5, help='Refresh interval in seconds (default: 5)')
    parser.add_argument('--report', action='store_true', help='Run single status report')
    
    args = parser.parse_args()
    
    monitor = RabbitMQMonitor()
    
    if args.monitor:
        monitor.run_monitor(args.interval)
    elif args.report:
        monitor.run_single_report()
    else:
        # Default to single report
        monitor.run_single_report()

if __name__ == "__main__":
    main()

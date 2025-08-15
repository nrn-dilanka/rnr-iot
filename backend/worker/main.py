import os
import json
import logging
import asyncio
import threading
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any

import pika
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkerService:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql://iotuser:iotpassword@localhost:5432/iot_platform")
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://iotuser:iotpassword@localhost:5672/iot_vhost")
        self.api_url = os.getenv("API_URL", "http://localhost:8000")
        
        # Database connection
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # RabbitMQ connection
        self.connection = None
        self.channel = None
        
        # Track node status
        self.node_status = {}  # {node_id: {'status': 'online/offline', 'last_seen': datetime}}
        self.offline_threshold = timedelta(seconds=10)  # Node offline after 10 seconds for faster detection
    
    def connect_rabbitmq(self):
        """Connect to RabbitMQ with retry logic"""
        max_retries = 10
        retry_delay = 1  # Initial delay in seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to RabbitMQ (attempt {attempt + 1}/{max_retries})")
                self.connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
                self.channel = self.connection.channel()
                
                # Declare exchange
                self.channel.exchange_declare(
                    exchange='amq.topic',
                    exchange_type='topic',
                    durable=True
                )
                
                # Declare queue for device data
                result = self.channel.queue_declare(queue='device_data', durable=True)
                queue_name = result.method.queue
                
                # Bind queue to exchange with routing key pattern
                self.channel.queue_bind(
                    exchange='amq.topic',
                    queue=queue_name,
                    routing_key='devices.*.data'
                )
                
                logger.info("Connected to RabbitMQ and set up queues")
                return queue_name
                
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:  # Don't wait after the last attempt
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 30)  # Exponential backoff, max 30 seconds
                else:
                    logger.error("Failed to connect to RabbitMQ after all retries")
                    raise
    
    def process_sensor_data(self, ch, method, properties, body):
        """Process incoming sensor data from devices"""
        try:
            # Parse the message
            data = json.loads(body.decode('utf-8'))
            
            # Extract node_id from routing key (devices.{node_id}.data)
            routing_key_parts = method.routing_key.split('.')
            if len(routing_key_parts) >= 3:
                node_id = routing_key_parts[1]
            else:
                logger.error(f"Invalid routing key format: {method.routing_key}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            logger.info(f"Processing sensor data from node {node_id}: {data}")
            
            # Store data in database
            self.store_sensor_data(node_id, data)
            
            # Update node's last_seen timestamp
            logger.info(f"⏰ Updating last_seen and status for node {node_id}")
            self.update_node_last_seen(node_id)
            
            # Update node status tracking
            now = datetime.utcnow()
            previous_status = self.node_status.get(node_id, {}).get('status', 'offline')
            self.node_status[node_id] = {
                'status': 'online',
                'last_seen': now
            }
            
            # If node was offline and now online, broadcast status change
            if previous_status == 'offline':
                logger.info(f"Node {node_id} came online")
                self.broadcast_status_change(node_id, 'online')
            
            # Send data to WebSocket clients (in a real implementation, use Redis pub/sub)
            self.broadcast_sensor_data(node_id, data)
            
            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"Error processing sensor data: {e}")
            # Reject the message and don't requeue (to avoid infinite loops)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def store_sensor_data(self, node_id: str, data: Dict[str, Any]):
        """Store sensor data in the database"""
        db = self.SessionLocal()
        try:
            # Insert sensor data using raw SQL with SQLAlchemy session
            query = text("""
                INSERT INTO sensor_data (node_id, data, received_at)
                VALUES (:node_id, :data, :received_at)
            """)
            
            db.execute(query, {
                'node_id': node_id,
                'data': json.dumps(data),
                'received_at': datetime.utcnow()
            })
            db.commit()
                    
            logger.info(f"Stored sensor data for node {node_id}")
            
        except Exception as e:
            logger.error(f"Error storing sensor data: {e}")
            db.rollback()
        finally:
            db.close()
    
    def update_node_last_seen(self, node_id: str):
        """Update the last_seen timestamp and status for a node"""
        db = self.SessionLocal()
        try:
            query = text("""
                INSERT INTO nodes (node_id, status, last_seen, created_at)
                VALUES (:node_id, 'online', :last_seen, :created_at)
                ON CONFLICT (node_id)
                DO UPDATE SET 
                    status = 'online',
                    last_seen = EXCLUDED.last_seen
            """)
            
            now = datetime.utcnow()
            db.execute(query, {
                'node_id': node_id,
                'last_seen': now,
                'created_at': now
            })
            db.commit()
                    
            logger.info(f"Updated last_seen and status=online for node {node_id}")
            
        except Exception as e:
            logger.error(f"Error updating node last_seen: {e}")
            db.rollback()
        finally:
            db.close()
    
    def broadcast_sensor_data(self, node_id: str, data: Dict[str, Any]):
        """Broadcast sensor data to WebSocket clients via API"""
        try:
            # Create a message for WebSocket broadcasting
            message = {
                "type": "sensor_data",
                "node_id": node_id,
                "data": data,
                "timestamp": data.get("timestamp", datetime.utcnow().isoformat())
            }
            
            logger.info(f"Broadcasting sensor data: {message}")
            
            # Send to API WebSocket service via HTTP endpoint (for simplicity)
            # In production, you'd use Redis pub/sub or similar
            try:
                response = requests.post(
                    f"{self.api_url}/api/internal/broadcast",
                    json=message,
                    timeout=2
                )
                if response.status_code == 200:
                    logger.info(f"Successfully broadcasted sensor data for node {node_id}")
                else:
                    logger.warning(f"Failed to broadcast sensor data: {response.status_code}")
            except Exception as e:
                logger.warning(f"Could not reach API for broadcasting: {e}")
                
        except Exception as e:
            logger.error(f"Error broadcasting sensor data: {e}")
    
    def broadcast_status_change(self, node_id: str, status: str):
        """Broadcast node status change to WebSocket clients"""
        try:
            message = {
                "type": "node_status",
                "node_id": node_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Broadcasting status change: Node {node_id} is {status}")
            
            try:
                response = requests.post(
                    f"{self.api_url}/api/internal/broadcast",
                    json=message,
                    timeout=2
                )
                if response.status_code == 200:
                    logger.info(f"Successfully broadcasted status change for node {node_id}")
                else:
                    logger.warning(f"Failed to broadcast status change: {response.status_code}")
            except Exception as e:
                logger.warning(f"Could not reach API for status broadcasting: {e}")
                
        except Exception as e:
            logger.error(f"Error broadcasting status change: {e}")
    
    def update_node_status_offline(self, node_id: str):
        """Update node status to offline in the database"""
        db = self.SessionLocal()
        try:
            query = text("""
                UPDATE nodes 
                SET status = 'offline' 
                WHERE node_id = :node_id
            """)
            
            db.execute(query, {'node_id': node_id})
            db.commit()
                    
            logger.info(f"Updated status=offline for node {node_id}")
            
        except Exception as e:
            logger.error(f"Error updating node to offline: {e}")
            db.rollback()
        finally:
            db.close()

    def check_offline_nodes(self):
        """Check for nodes that should be marked as offline"""
        try:
            now = datetime.utcnow()
            nodes_to_mark_offline = []
            
            for node_id, status_info in self.node_status.items():
                if status_info['status'] == 'online':
                    time_since_last_seen = now - status_info['last_seen']
                    if time_since_last_seen > self.offline_threshold:
                        nodes_to_mark_offline.append(node_id)
            
            for node_id in nodes_to_mark_offline:
                logger.info(f"Node {node_id} went offline (no data for {self.offline_threshold.total_seconds()} seconds)")
                self.node_status[node_id]['status'] = 'offline'
                self.update_node_status_offline(node_id)  # Update database
                self.broadcast_status_change(node_id, 'offline')
                
        except Exception as e:
            logger.error(f"Error checking offline nodes: {e}")
    
    def start_status_monitor(self):
        """Start a background thread to monitor node status"""
        def status_monitor():
            while True:
                try:
                    self.check_offline_nodes()
                    threading.Event().wait(3)  # Check every 3 seconds for ultra-fast detection
                except Exception as e:
                    logger.error(f"Error in status monitor: {e}")
                    threading.Event().wait(3)
        
        monitor_thread = threading.Thread(target=status_monitor, daemon=True)
        monitor_thread.start()
        logger.info("Status monitor thread started - checking every 3 seconds for ultra-fast disconnect detection")
    
    def start_consuming(self):
        """Start consuming messages from RabbitMQ"""
        try:
            queue_name = self.connect_rabbitmq()
            
            # Start status monitoring thread
            self.start_status_monitor()
            
            # Set up consumer
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=self.process_sensor_data
            )
            
            logger.info("Worker service started. Waiting for messages...")
            logger.info("Status monitor thread started")
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("Stopping worker service...")
            self.channel.stop_consuming()
            self.connection.close()
        except Exception as e:
            logger.error(f"Error in worker service: {e}")
            raise

def main():
    """Main entry point for the worker service"""
    worker = WorkerService()
    worker.start_consuming()

if __name__ == "__main__":
    main()

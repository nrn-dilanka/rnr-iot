#!/usr/bin/env python3
"""
Emergency AWS Database Connection Fix
Creates sample nodes if database is empty and fixes connection issues
"""
import os
import logging
import psycopg2
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_url():
    """Get database URL from environment or default"""
    return os.getenv("DATABASE_URL", "postgresql://iotuser:iotpassword@localhost:15432/iot_platform")

def test_connection():
    """Test basic database connection"""
    try:
        db_url = get_db_url()
        logger.info(f"Testing connection to: {db_url.replace(':iotpassword@', ':***@')}")
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"Database version: {version[0][:50]}...")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False

def check_tables():
    """Check if required tables exist"""
    try:
        db_url = get_db_url()
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Check if nodes table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'nodes'
            );
        """)
        nodes_exists = cursor.fetchone()[0]
        
        if nodes_exists:
            cursor.execute("SELECT COUNT(*) FROM nodes;")
            node_count = cursor.fetchone()[0]
            logger.info(f"Nodes table exists with {node_count} records")
        else:
            logger.warning("Nodes table does not exist")
        
        cursor.close()
        conn.close()
        return nodes_exists, node_count if nodes_exists else 0
        
    except Exception as e:
        logger.error(f"Table check failed: {e}")
        return False, 0

def create_sample_nodes():
    """Create sample nodes if table is empty"""
    try:
        db_url = get_db_url()
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Create sample nodes
        sample_nodes = [
            ("441793F9456C", "ESP32-F9456C", "24:6F:28:F9:45:6C", "true", "online"),
            ("A0B1C2D3E4F5", "ESP32-D3E4F5", "A0:B1:C2:D3:E4:F5", "true", "offline"),
            ("123456789ABC", "ESP32-Testing", "12:34:56:78:9A:BC", "false", "offline"),
            ("FEDCBA987654", "ESP32-Backup", "FE:DC:BA:98:76:54", "true", "offline")
        ]
        
        for node_id, name, mac, is_active, status in sample_nodes:
            cursor.execute("""
                INSERT INTO nodes (node_id, name, mac_address, is_active, status, created_at, last_seen)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (node_id) DO NOTHING;
            """, (node_id, name, mac, is_active, status, datetime.utcnow(), datetime.utcnow()))
        
        conn.commit()
        
        # Check final count
        cursor.execute("SELECT COUNT(*) FROM nodes;")
        final_count = cursor.fetchone()[0]
        logger.info(f"Sample nodes created. Total nodes: {final_count}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Sample node creation failed: {e}")
        return False

def main():
    """Main diagnostic and fix function"""
    print("🔧 Emergency AWS Database Fix")
    print("=" * 30)
    
    # Test connection
    if not test_connection():
        print("❌ Database connection failed")
        return False
    
    # Check tables
    tables_exist, node_count = check_tables()
    if not tables_exist:
        print("❌ Nodes table missing")
        return False
    
    # Create sample data if empty
    if node_count == 0:
        print("📝 Creating sample nodes...")
        if create_sample_nodes():
            print("✅ Sample nodes created")
        else:
            print("❌ Failed to create sample nodes")
            return False
    
    print(f"✅ Database ready with {node_count} nodes")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

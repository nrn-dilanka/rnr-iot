import os
import logging
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.database import get_db, Node, Firmware, NodeFirmware, SensorData
from api.schemas import NodeCreate, NodeUpdate, FirmwareCreate
from datetime import datetime

logger = logging.getLogger(__name__)

class NodeService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_node(self, node_data: NodeCreate) -> Node:
        """Create a new node"""
        # Check if node already exists
        existing_node = self.db.query(Node).filter(Node.node_id == node_data.node_id).first()
        if existing_node:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Node with this ID already exists"
            )
        
        db_node = Node(**node_data.dict())
        self.db.add(db_node)
        self.db.commit()
        self.db.refresh(db_node)
        return db_node
    
    def get_nodes(self) -> List[Node]:
        """Get all nodes with enhanced error handling"""
        try:
            logger.info("Querying database for all nodes...")
            
            # Test database connection first
            self.db.execute("SELECT 1")
            
            # Get all nodes
            nodes = self.db.query(Node).all()
            logger.info(f"Successfully retrieved {len(nodes)} nodes from database")
            return nodes
            
        except Exception as e:
            logger.error(f"Database error in get_nodes: {e}")
            logger.error(f"Database connection state: {self.db}")
            
            # Try to handle specific database errors
            if "connection" in str(e).lower():
                logger.error("Database connection issue detected")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database connection unavailable"
                )
            elif "table" in str(e).lower() or "relation" in str(e).lower():
                logger.error("Database schema issue detected")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database schema not initialized"
                )
            else:
                logger.error(f"Unknown database error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database query failed: {str(e)}"
                )
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a specific node by ID"""
        return self.db.query(Node).filter(Node.node_id == node_id).first()
    
    def update_node(self, node_id: str, node_data: NodeUpdate) -> Node:
        """Update a node"""
        db_node = self.get_node(node_id)
        if not db_node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found"
            )
        
        update_data = node_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_node, field, value)
        
        self.db.commit()
        self.db.refresh(db_node)
        return db_node
    
    def delete_node(self, node_id: str) -> bool:
        """Delete a node"""
        db_node = self.get_node(node_id)
        if not db_node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found"
            )
        
        self.db.delete(db_node)
        self.db.commit()
        return True
    
    def update_last_seen(self, node_id: str) -> None:
        """Update the last seen timestamp for a node"""
        db_node = self.get_node(node_id)
        if db_node:
            db_node.last_seen = datetime.utcnow()
            self.db.commit()

class FirmwareService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_firmware(self, firmware_data: FirmwareCreate) -> Firmware:
        """Create a new firmware version"""
        db_firmware = Firmware(**firmware_data.dict())
        self.db.add(db_firmware)
        self.db.commit()
        self.db.refresh(db_firmware)
        return db_firmware
    
    def get_firmwares(self) -> List[Firmware]:
        """Get all firmware versions"""
        return self.db.query(Firmware).order_by(Firmware.uploaded_at.desc()).all()
    
    def get_firmware(self, firmware_id: int) -> Optional[Firmware]:
        """Get a specific firmware by ID"""
        return self.db.query(Firmware).filter(Firmware.id == firmware_id).first()
    
    def assign_firmware_to_node(self, node_id: str, firmware_id: int) -> bool:
        """Assign firmware to a node"""
        # Check if node exists
        node = self.db.query(Node).filter(Node.node_id == node_id).first()
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found"
            )
        
        # Check if firmware exists
        firmware = self.get_firmware(firmware_id)
        if not firmware:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Firmware not found"
            )
        
        # Remove existing assignment
        existing = self.db.query(NodeFirmware).filter(NodeFirmware.node_id == node_id).first()
        if existing:
            self.db.delete(existing)
        
        # Create new assignment
        assignment = NodeFirmware(node_id=node_id, firmware_id=firmware_id)
        self.db.add(assignment)
        self.db.commit()
        return True

class SensorDataService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_sensor_data(self, node_id: str, data: dict) -> SensorData:
        """Store sensor data from a node"""
        db_sensor_data = SensorData(node_id=node_id, data=data)
        self.db.add(db_sensor_data)
        self.db.commit()
        self.db.refresh(db_sensor_data)
        return db_sensor_data
    
    def get_sensor_data(self, node_id: str = None, limit: int = 100) -> List[SensorData]:
        """Get sensor data, optionally filtered by node"""
        query = self.db.query(SensorData)
        if node_id:
            query = query.filter(SensorData.node_id == node_id)
        
        return query.order_by(SensorData.received_at.desc()).limit(limit).all()

# Dependency functions
def get_node_service(db: Session = Depends(get_db)) -> NodeService:
    return NodeService(db)

def get_firmware_service(db: Session = Depends(get_db)) -> FirmwareService:
    return FirmwareService(db)

def get_sensor_data_service(db: Session = Depends(get_db)) -> SensorDataService:
    return SensorDataService(db)

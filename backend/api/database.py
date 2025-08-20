import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, BigInteger, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from typing import Optional

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://iotuser:iotpassword@localhost:5432/iot_platform")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Node(Base):
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    mac_address = Column(String)
    is_active = Column(String, default="true")  # Store as string for compatibility
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime)
    
    # Relationships
    sensor_data = relationship("SensorData", back_populates="node")
    firmware_assignments = relationship("NodeFirmware", back_populates="node")

class Firmware(Base):
    __tablename__ = "firmware"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, nullable=False)
    file_name = Column(String)
    file_url = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    node_assignments = relationship("NodeFirmware", back_populates="firmware")

class NodeFirmware(Base):
    __tablename__ = "node_firmware"
    
    node_id = Column(String, ForeignKey("nodes.node_id"), primary_key=True)
    firmware_id = Column(Integer, ForeignKey("firmware.id"), primary_key=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    node = relationship("Node", back_populates="firmware_assignments")
    firmware = relationship("Firmware", back_populates="node_assignments")

class SensorData(Base):
    __tablename__ = "sensor_data"
    
    id = Column(BigInteger, primary_key=True, index=True)
    node_id = Column(String, ForeignKey("nodes.node_id"), nullable=False)
    data = Column(JSONB)
    received_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    node = relationship("Node", back_populates="sensor_data")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

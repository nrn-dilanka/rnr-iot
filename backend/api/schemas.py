from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

# Node schemas
class NodeBase(BaseModel):
    node_id: str
    name: Optional[str] = None
    mac_address: Optional[str] = None

class NodeCreate(NodeBase):
    pass

class NodeUpdate(BaseModel):
    name: Optional[str] = None

class NodeResponse(NodeBase):
    id: int
    created_at: datetime
    last_seen: Optional[datetime] = None
    is_active: Optional[str] = None
    status: Optional[str] = None
    
    class Config:
        from_attributes = True

# Firmware schemas
class FirmwareBase(BaseModel):
    version: str
    file_name: Optional[str] = None

class FirmwareCreate(FirmwareBase):
    file_url: str

class FirmwareResponse(FirmwareBase):
    id: int
    file_url: Optional[str] = None
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

# Action schemas
class NodeAction(BaseModel):
    action: str
    url: Optional[str] = None  # For firmware update actions
    angle: Optional[int] = None  # For servo control actions
    value: Optional[Any] = None  # For generic parameter actions

class ActionResponse(BaseModel):
    message: str

# Firmware deployment schema
class FirmwareDeployment(BaseModel):
    node_id: str
    firmware_id: int

# Sensor data schema
class SensorDataResponse(BaseModel):
    id: int
    node_id: str
    data: Dict[str, Any]
    received_at: datetime
    
    class Config:
        from_attributes = True

# WebSocket message schemas
class WebSocketMessage(BaseModel):
    type: str  # "sensor_data", "node_status", etc.
    data: Dict[str, Any]

# Sensor configuration schemas
class SensorBase(BaseModel):
    name: str
    type: str
    pin: str
    pin_type: str
    node_id: str
    enabled: bool = True
    calibration_offset: float = 0.0
    calibration_scale: float = 1.0
    update_interval: int = 1000
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    description: Optional[str] = None

class SensorCreate(SensorBase):
    pass

class SensorUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    pin: Optional[str] = None
    pin_type: Optional[str] = None
    enabled: Optional[bool] = None
    calibration_offset: Optional[float] = None
    calibration_scale: Optional[float] = None
    update_interval: Optional[int] = None
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    description: Optional[str] = None

class SensorResponse(SensorBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SensorCodeGeneration(BaseModel):
    sensor_id: int
    language: str = "arduino"  # arduino, micropython, etc.

class SensorCodeResponse(BaseModel):
    code: str
    language: str
    sensor_name: str

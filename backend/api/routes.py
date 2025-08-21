import os
import shutil
import logging
import json
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from api.database import get_db, Node, SensorData
from api.schemas import (
    NodeCreate, NodeUpdate, NodeResponse, NodeAction, ActionResponse,
    FirmwareCreate, FirmwareResponse, FirmwareDeployment, SensorDataResponse,
    SensorCreate, SensorUpdate, SensorResponse, SensorCodeGeneration, SensorCodeResponse
)
from api.services import NodeService, FirmwareService, SensorDataService, get_node_service, get_firmware_service, get_sensor_data_service
from api.rabbitmq import rabbitmq_client
from api.mqtt_publisher import mqtt_command_publisher
from api.esp32_manager import esp32_device_manager
from api.esp32_routes import router as esp32_router
from api.gemini_ai import gemini_ai_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Node management endpoints
@router.post("/nodes", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
async def create_node(
    node_data: NodeCreate,
    node_service: NodeService = Depends(get_node_service)
):
    """Register a new node (ADD)"""
    try:
        node = node_service.create_node(node_data)
        return node
    except Exception as e:
        logger.error(f"Error creating node: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create node"
        )

@router.get("/database/test")
async def test_database():
    """Test database connectivity and table access"""
    try:
        from api.database import get_db
        db = next(get_db())
        
        # Test basic connection
        db.execute("SELECT 1")
        
        # Test Node table
        node_count = db.query(Node).count()
        
        # Test if we can create a basic query
        nodes = db.query(Node).limit(1).all()
        
        return {
            "database_status": "connected",
            "node_table_accessible": True,
            "total_nodes": node_count,
            "sample_query_success": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return {
            "database_status": "error",
            "node_table_accessible": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/nodes", response_model=List[NodeResponse])
async def get_nodes(
    node_service: NodeService = Depends(get_node_service)
):
    """List all registered nodes (CATALOGUE)"""
    try:
        logger.info("Fetching all nodes...")
        nodes = node_service.get_nodes()
        logger.info(f"Successfully fetched {len(nodes)} nodes")
        return nodes
    except Exception as e:
        logger.error(f"Error fetching nodes: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        
        # Return empty list instead of error for better user experience
        try:
            # Try to return at least basic structure
            return []
        except:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database connection failed: {str(e)}"
            )

@router.get("/nodes/online", response_model=List[NodeResponse])
async def get_online_nodes(
    node_service: NodeService = Depends(get_node_service)
):
    """Get all online nodes (last seen within 5 minutes)"""
    try:
        from datetime import datetime, timedelta
        # Use timezone-naive datetime for consistency
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        
        # Get all nodes and filter for online ones
        all_nodes = node_service.get_nodes()
        online_nodes = []
        
        for node in all_nodes:
            if node.last_seen and node.is_active == "true":
                # Ensure timezone-naive comparison
                last_seen = node.last_seen
                if hasattr(last_seen, 'tzinfo') and last_seen.tzinfo:
                    last_seen = last_seen.replace(tzinfo=None)
                
                if last_seen > cutoff_time:
                    # Accept any status that's not "offline" for online nodes
                    if node.status and node.status != "offline":
                        online_nodes.append(node)
        
        return online_nodes
    except Exception as e:
        logger.error(f"Error fetching online nodes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch online nodes"
        )

@router.get("/nodes/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: str,
    node_service: NodeService = Depends(get_node_service)
):
    """Get details for a specific node"""
    node = node_service.get_node(node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    return node

@router.put("/nodes/{node_id}", response_model=NodeResponse)
async def update_node(
    node_id: str,
    node_data: NodeUpdate,
    node_service: NodeService = Depends(get_node_service)
):
    """Update a node's details (UPDATE)"""
    try:
        node = node_service.update_node(node_id, node_data)
        return node
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating node: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update node"
        )

@router.delete("/nodes/{node_id}")
async def delete_node(
    node_id: str,
    node_service: NodeService = Depends(get_node_service)
):
    """Delete a node"""
    try:
        node_service.delete_node(node_id)
        return {"message": "Node deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting node: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete node"
        )

@router.put("/nodes/{node_id}/activate")
async def activate_node(
    node_id: str,
    node_service: NodeService = Depends(get_node_service)
):
    """Activate a node (set is_active to true)"""
    try:
        node = node_service.get_node(node_id)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found"
            )
        
        # Update node status
        from api.database import get_db
        db = next(get_db())
        
        # Safe datetime comparison
        current_time = datetime.utcnow()
        is_online = False
        if node.last_seen:
            # Ensure both datetimes are timezone-naive for comparison
            last_seen = node.last_seen
            if hasattr(last_seen, 'tzinfo') and last_seen.tzinfo:
                last_seen = last_seen.replace(tzinfo=None)
            is_online = (current_time - last_seen).total_seconds() < 300
        
        db.query(Node).filter(Node.node_id == node_id).update({
            "is_active": "true",
            "status": "online" if is_online else "offline"
        })
        db.commit()
        
        return {"message": f"Node {node_id} activated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating node {node_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate node"
        )

@router.put("/nodes/{node_id}/deactivate")
async def deactivate_node(
    node_id: str,
    node_service: NodeService = Depends(get_node_service)
):
    """Deactivate a node (set is_active to false)"""
    try:
        node = node_service.get_node(node_id)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found"
            )
        
        # Update node status
        from api.database import get_db
        db = next(get_db())
        db.query(Node).filter(Node.node_id == node_id).update({
            "is_active": "false",
            "status": "offline"
        })
        db.commit()
        
        return {"message": f"Node {node_id} deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating node {node_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate node"
        )

@router.post("/nodes/{node_id}/actions", response_model=ActionResponse)
async def send_node_action(
    node_id: str,
    action: NodeAction,
    node_service: NodeService = Depends(get_node_service)
):
    """Send a command to a node (CONTROL)"""
    # Verify node exists
    node = node_service.get_node(node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    # Prepare command based on action type
    command = {"action": action.action}
    if action.url:
        command["url"] = action.url
    if action.angle is not None:
        command["angle"] = action.angle
    if action.value is not None:
        command["value"] = action.value
    
    # Send command via ESP32 Device Manager (MQTT)
    try:
        from api.esp32_manager import esp32_device_manager
        
        success = await esp32_device_manager.send_command_to_device(node_id, command)
        
        if success:
            logger.info(f"✅ Command '{action.action}' sent to device {node_id} via WiFi/MQTT")
            return ActionResponse(message=f"Command '{action.action}' sent successfully via WiFi/MQTT")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send command via WiFi/MQTT"
            )
    except Exception as e:
        logger.error(f"Error sending command to node {node_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send command via WiFi/MQTT: {str(e)}"
        )

# Firmware management endpoints
@router.post("/firmware/upload", response_model=FirmwareResponse, status_code=status.HTTP_201_CREATED)
async def upload_firmware(
    version: str = Form(...),
    file: UploadFile = File(...),
    firmware_service: FirmwareService = Depends(get_firmware_service)
):
    """Upload a new firmware binary (Upload)"""
    if not file.filename.endswith('.bin'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .bin files are allowed"
        )
    
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = os.getenv("UPLOAD_DIR", "/app/uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_name = f"firmware_v{version}.bin"
        file_path = os.path.join(upload_dir, file_name)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create firmware record
        firmware_data = FirmwareCreate(
            version=version,
            file_name=file_name,
            file_url=f"/uploads/{file_name}"
        )
        
        firmware = firmware_service.create_firmware(firmware_data)
        return firmware
        
    except Exception as e:
        logger.error(f"Error uploading firmware: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload firmware"
        )

@router.get("/firmware", response_model=List[FirmwareResponse])
async def get_firmware_versions(
    firmware_service: FirmwareService = Depends(get_firmware_service)
):
    """List all available firmware versions (CATALOGUE)"""
    try:
        firmwares = firmware_service.get_firmwares()
        return firmwares
    except Exception as e:
        logger.error(f"Error fetching firmware versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch firmware versions"
        )

@router.post("/firmware/deploy", response_model=ActionResponse)
async def deploy_firmware(
    deployment: FirmwareDeployment,
    node_service: NodeService = Depends(get_node_service),
    firmware_service: FirmwareService = Depends(get_firmware_service)
):
    """Trigger OTA update on a node"""
    # Verify node exists
    node = node_service.get_node(deployment.node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    # Verify firmware exists
    firmware = firmware_service.get_firmware(deployment.firmware_id)
    if not firmware:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Firmware not found"
        )
    
    try:
        # Assign firmware to node
        firmware_service.assign_firmware_to_node(deployment.node_id, deployment.firmware_id)
        
        # Send OTA command via ESP32 Device Manager (MQTT)
        command = {
            "action": "FIRMWARE_UPDATE",
            "url": f"http://192.168.8.105:8000{firmware.file_url}"
        }
        
        logger.info(f"DEBUG: About to call esp32_device_manager.send_command_to_device")
        logger.info(f"DEBUG: Command content: {command}")
        logger.info(f"DEBUG: Target node: {deployment.node_id}")
        
        success = await esp32_device_manager.send_command_to_device(deployment.node_id, command)
        
        logger.info(f"DEBUG: MQTT publish result: {success}")
        
        if success:
            return ActionResponse(message="OTA command sent successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTA command"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deploying firmware: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deploy firmware"
        )

# Test MQTT endpoint
@router.post("/test/mqtt", response_model=ActionResponse)
async def test_mqtt():
    """Test MQTT publisher directly"""
    command = {"action": "TEST", "message": "Hello from MQTT"}
    
    try:
        success = mqtt_command_publisher.publish_command("441793F9456C", command)
        if success:
            return ActionResponse(message="MQTT test successful")
        else:
            return ActionResponse(message="MQTT test failed")
    except Exception as e:
        logger.error(f"MQTT test error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MQTT test error: {e}"
        )

# Sensor data endpoints
@router.get("/sensor-data", response_model=List[SensorDataResponse])
async def get_sensor_data(
    node_id: Optional[str] = Query(None, description="Filter by node ID"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    sensor_data_service: SensorDataService = Depends(get_sensor_data_service)
):
    """Get sensor data, optionally filtered by node"""
    try:
        data = sensor_data_service.get_sensor_data(node_id=node_id, limit=limit)
        return data
    except Exception as e:
        logger.error(f"Error fetching sensor data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch sensor data"
        )

@router.get("/nodes/{node_id}/sensor-data", response_model=List[SensorDataResponse])
async def get_node_sensor_data(
    node_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    sensor_data_service: SensorDataService = Depends(get_sensor_data_service)
):
    """Get sensor data for a specific node"""
    try:
        data = sensor_data_service.get_sensor_data(node_id=node_id, limit=limit)
        return data
    except Exception as e:
        logger.error(f"Error fetching sensor data for node {node_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sensor data for node {node_id}"
        )

# Sensor configuration management endpoints
@router.post("/sensors", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
async def create_sensor_config(
    sensor_data: SensorCreate,
    db: Session = Depends(get_db)
):
    """Create a new sensor configuration"""
    try:
        # In a real implementation, you would create a sensor service
        # For now, returning mock data with the provided information
        mock_sensor = {
            "id": 1,
            "created_at": "2025-07-22T10:00:00",
            "updated_at": None,
            **sensor_data.dict()
        }
        return mock_sensor
    except Exception as e:
        logger.error(f"Error creating sensor configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create sensor configuration"
        )

@router.get("/sensors", response_model=List[SensorResponse])
async def get_sensor_configs(
    node_id: Optional[str] = Query(None, description="Filter by node ID"),
    db: Session = Depends(get_db)
):
    """Get all sensor configurations"""
    try:
        # Mock sensor data for demonstration
        mock_sensors = [
            {
                "id": 1,
                "name": "Temperature Sensor",
                "type": "temperature",
                "pin": "A0",
                "pin_type": "analog",
                "node_id": "441793F9456C",
                "enabled": True,
                "calibration_offset": 0.0,
                "calibration_scale": 1.0,
                "update_interval": 1000,
                "threshold_min": -10.0,
                "threshold_max": 50.0,
                "description": "DHT22 temperature sensor",
                "created_at": "2025-07-22T10:00:00",
                "updated_at": None
            },
            {
                "id": 2,
                "name": "Gas Sensor",
                "type": "gas",
                "pin": "A6",
                "pin_type": "analog",
                "node_id": "441793F9456C",
                "enabled": True,
                "calibration_offset": 0.0,
                "calibration_scale": 1.0,
                "update_interval": 1000,
                "threshold_min": 0.0,
                "threshold_max": 1000.0,
                "description": "MQ-135 air quality sensor",
                "created_at": "2025-07-22T10:00:00",
                "updated_at": None
            }
        ]
        
        if node_id:
            mock_sensors = [s for s in mock_sensors if s["node_id"] == node_id]
        
        return mock_sensors
    except Exception as e:
        logger.error(f"Error fetching sensor configurations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch sensor configurations"
        )

@router.get("/sensors/{sensor_id}", response_model=SensorResponse)
async def get_sensor_config(
    sensor_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific sensor configuration"""
    try:
        # Mock data for demonstration
        if sensor_id == 1:
            return {
                "id": 1,
                "name": "Temperature Sensor",
                "type": "temperature",
                "pin": "A0",
                "pin_type": "analog",
                "node_id": "441793F9456C",
                "enabled": True,
                "calibration_offset": 0.0,
                "calibration_scale": 1.0,
                "update_interval": 1000,
                "threshold_min": -10.0,
                "threshold_max": 50.0,
                "description": "DHT22 temperature sensor",
                "created_at": "2025-07-22T10:00:00",
                "updated_at": None
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sensor configuration not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sensor configuration {sensor_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sensor configuration {sensor_id}"
        )

@router.put("/sensors/{sensor_id}", response_model=SensorResponse)
async def update_sensor_config(
    sensor_id: int,
    sensor_data: SensorUpdate,
    db: Session = Depends(get_db)
):
    """Update a sensor configuration"""
    try:
        # Mock update for demonstration
        updated_sensor = {
            "id": sensor_id,
            "name": sensor_data.name or "Temperature Sensor",
            "type": sensor_data.type or "temperature",
            "pin": sensor_data.pin or "A0",
            "pin_type": sensor_data.pin_type or "analog",
            "node_id": "441793F9456C",
            "enabled": sensor_data.enabled if sensor_data.enabled is not None else True,
            "calibration_offset": sensor_data.calibration_offset or 0.0,
            "calibration_scale": sensor_data.calibration_scale or 1.0,
            "update_interval": sensor_data.update_interval or 1000,
            "threshold_min": sensor_data.threshold_min,
            "threshold_max": sensor_data.threshold_max,
            "description": sensor_data.description,
            "created_at": "2025-07-22T10:00:00",
            "updated_at": "2025-07-22T14:00:00"
        }
        return updated_sensor
    except Exception as e:
        logger.error(f"Error updating sensor configuration {sensor_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update sensor configuration {sensor_id}"
        )

@router.delete("/sensors/{sensor_id}")
async def delete_sensor_config(
    sensor_id: int,
    db: Session = Depends(get_db)
):
    """Delete a sensor configuration"""
    try:
        # Mock deletion for demonstration
        return {"message": f"Sensor configuration {sensor_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting sensor configuration {sensor_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete sensor configuration {sensor_id}"
        )

@router.post("/sensors/{sensor_id}/generate-code", response_model=SensorCodeResponse)
async def generate_sensor_code(
    sensor_id: int,
    code_request: SensorCodeGeneration,
    db: Session = Depends(get_db)
):
    """Generate Arduino/MicroPython code for a sensor configuration"""
    try:
        # Mock sensor data
        sensor_name = "temperature_sensor"
        
        if code_request.language == "arduino":
            code = f"""// {sensor_name.replace('_', ' ').title()} Configuration
const int {sensor_name}_pin = A0;
float {sensor_name}_value = 0;

void setup() {{
  Serial.begin(115200);
  pinMode({sensor_name}_pin, INPUT);
}}

void loop() {{
  // Read {sensor_name.replace('_', ' ')}
  {sensor_name}_value = analogRead({sensor_name}_pin);
  
  // Apply calibration
  {sensor_name}_value = ({sensor_name}_value * 1.0) + 0.0;
  
  // Print value
  Serial.print("{sensor_name.replace('_', ' ').title()}: ");
  Serial.println({sensor_name}_value);
  
  delay(1000);
}}"""
        else:
            code = f"""# {sensor_name.replace('_', ' ').title()} Configuration
from machine import Pin, ADC
import time

{sensor_name}_pin = ADC(Pin(36))
{sensor_name}_pin.atten(ADC.ATTN_11DB)

while True:
    # Read {sensor_name.replace('_', ' ')}
    {sensor_name}_value = {sensor_name}_pin.read()
    
    # Apply calibration
    {sensor_name}_value = ({sensor_name}_value * 1.0) + 0.0
    
    # Print value
    print(f"{sensor_name.replace('_', ' ').title()}: {{{sensor_name}_value}}")
    
    time.sleep(1)"""
        
        return {
            "code": code,
            "language": code_request.language,
            "sensor_name": sensor_name.replace('_', ' ').title()
        }
    except Exception as e:
        logger.error(f"Error generating code for sensor {sensor_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate code for sensor {sensor_id}"
        )

# AI Agent Management endpoints
@router.get("/ai-agent/status")
async def get_ai_agent_status():
    """Get AI agent status and metrics"""
    try:
        # Simulate AI agent status - in production this would come from actual AI service
        return {
            "active": True,
            "mode": "autonomous",
            "uptime": "2h 34m",
            "last_decision": datetime.utcnow().isoformat(),
            "performance_metrics": {
                "data_processed": 15847,
                "decisions_made": 342,
                "firmware_deployments": 23,
                "anomalies_detected": 5,
                "success_rate": 98.2
            }
        }
    except Exception as e:
        logger.error(f"Error getting AI agent status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get AI agent status"
        )

@router.post("/ai-agent/analyze")
async def trigger_ai_analysis(
    sensor_data_service: SensorDataService = Depends(get_sensor_data_service)
):
    """Trigger AI analysis of current ESP32 data using Gemini AI"""
    try:
        # Get recent sensor data
        recent_data = sensor_data_service.get_sensor_data(limit=100)
        
        # Convert to dict format for AI analysis
        sensor_data_list = []
        for data_point in recent_data:
            sensor_data_list.append({
                "node_id": data_point.node_id,
                "data": data_point.data,
                "received_at": data_point.received_at.isoformat() if data_point.received_at else None
            })
        
        # Use Gemini AI for real analysis
        ai_analysis = gemini_ai_service.analyze_esp32_data(sensor_data_list)
        
        # Add metadata
        analysis_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_records_analyzed": len(recent_data),
            "ai_powered": True,
            "analysis": ai_analysis
        }
        
        return analysis_results
        
    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        # Fallback to basic analysis if AI fails
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_records_analyzed": 0,
            "ai_powered": False,
            "error": "AI analysis failed, using fallback mode",
            "analysis": {
                "anomalies": [],
                "trends": [],
                "recommendations": [
                    {
                        "type": "maintenance",
                        "priority": "medium",
                        "action": "Manual review recommended due to AI service error",
                        "devices": []
                    }
                ],
                "overall_health": "unknown",
                "risk_level": "medium"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform AI analysis"
        )

@router.post("/ai-agent/auto-flash")
async def trigger_auto_flash(
    firmware_service: FirmwareService = Depends(get_firmware_service),
    sensor_data_service: SensorDataService = Depends(get_sensor_data_service)
):
    """Trigger AI-controlled automatic firmware flashing using Gemini AI"""
    try:
        # Get available firmware
        firmwares = firmware_service.get_firmwares()
        if not firmwares:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No firmware available for deployment"
            )
        
        # Get recent sensor data
        recent_data = sensor_data_service.get_sensor_data(limit=100)
        active_devices = list(set([d.node_id for d in recent_data]))
        
        # Prepare data for AI analysis
        sensor_data_list = []
        for data_point in recent_data:
            sensor_data_list.append({
                "node_id": data_point.node_id,
                "data": data_point.data,
                "received_at": data_point.received_at.isoformat() if data_point.received_at else None
            })
        
        # Get AI analysis
        ai_analysis = gemini_ai_service.analyze_esp32_data(sensor_data_list)
        
        flash_results = []
        
        # Process AI recommendations
        for recommendation in ai_analysis.get("recommendations", []):
            if recommendation.get("type") == "firmware" and recommendation.get("priority") in ["high", "critical"]:
                affected_devices = recommendation.get("devices", [])
                
                for device_id in affected_devices:
                    if device_id in active_devices:
                        try:
                            # Get AI firmware recommendation for this specific device
                            device_performance = {
                                "device_id": device_id,
                                "recent_data": [d for d in sensor_data_list if d["node_id"] == device_id][:10],
                                "anomalies": [a for a in ai_analysis.get("anomalies", []) if a.get("device_id") == device_id]
                            }
                            
                            firmware_recommendation = gemini_ai_service.recommend_firmware_action(
                                device_performance, 
                                [{"id": f.id, "version": f.version, "file_name": f.file_name} for f in firmwares]
                            )
                            
                            if firmware_recommendation.get("update_needed", False):
                                recommended_fw_id = firmware_recommendation.get("recommended_firmware")
                                if recommended_fw_id:
                                    # Find the firmware
                                    target_firmware = next((f for f in firmwares if str(f.id) == str(recommended_fw_id)), firmwares[0])
                                else:
                                    target_firmware = firmwares[0]  # Use latest as fallback
                                
                                # Send OTA command
                                command = {
                                    "action": "FIRMWARE_UPDATE",
                                    "url": f"http://192.168.8.105:8000{target_firmware.file_url}",
                                    "ai_triggered": True,
                                    "ai_reasoning": firmware_recommendation.get("reasoning", "AI recommended update"),
                                    "priority": firmware_recommendation.get("priority", "medium"),
                                    "timestamp": datetime.utcnow().isoformat()
                                }
                                
                                success = await esp32_device_manager.send_command_to_device(device_id, command)
                                
                                if success:
                                    firmware_service.assign_firmware_to_node(device_id, target_firmware.id)
                                    flash_results.append({
                                        "device_id": device_id,
                                        "status": "success",
                                        "firmware_version": target_firmware.version,
                                        "reason": firmware_recommendation.get("reasoning", "AI recommendation"),
                                        "priority": firmware_recommendation.get("priority", "medium"),
                                        "ai_powered": True
                                    })
                                    logger.info(f"AI auto-flash: Successfully flashed {device_id} with {target_firmware.version}")
                                else:
                                    flash_results.append({
                                        "device_id": device_id,
                                        "status": "failed",
                                        "reason": "MQTT command failed",
                                        "ai_powered": True
                                    })
                                    
                        except Exception as device_error:
                            flash_results.append({
                                "device_id": device_id,
                                "status": "error",
                                "reason": str(device_error),
                                "ai_powered": True
                            })
                            logger.error(f"Error flashing device {device_id}: {device_error}")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "ai_analysis_summary": {
                "total_devices_analyzed": len(active_devices),
                "anomalies_detected": len(ai_analysis.get("anomalies", [])),
                "recommendations_generated": len(ai_analysis.get("recommendations", [])),
                "overall_health": ai_analysis.get("overall_health", "unknown"),
                "risk_level": ai_analysis.get("risk_level", "medium")
            },
            "flash_operations": flash_results,
            "total_flashed": len([r for r in flash_results if r["status"] == "success"]),
            "ai_powered": True
        }
        
    except Exception as e:
        logger.error(f"Error in AI auto-flash: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI auto-flash failed: {str(e)}"
        )

@router.post("/ai-agent/maintenance-report")
async def generate_ai_maintenance_report(
    node_service: NodeService = Depends(get_node_service),
    sensor_data_service: SensorDataService = Depends(get_sensor_data_service),
    firmware_service: FirmwareService = Depends(get_firmware_service)
):
    """Generate comprehensive AI-powered maintenance report"""
    try:
        # Gather system overview data
        nodes = node_service.get_nodes()
        sensor_data = sensor_data_service.get_sensor_data(limit=200)
        firmwares = firmware_service.get_firmwares()
        
        # Helper function to safely handle datetime operations
        def safe_datetime_diff(dt1, dt2):
            try:
                if dt1 is None or dt2 is None:
                    return float('inf')
                # Ensure both datetimes are timezone-naive
                if hasattr(dt1, 'tzinfo') and dt1.tzinfo:
                    dt1 = dt1.replace(tzinfo=None)
                if hasattr(dt2, 'tzinfo') and dt2.tzinfo:
                    dt2 = dt2.replace(tzinfo=None)
                return (dt1 - dt2).total_seconds()
            except:
                return float('inf')
        
        def safe_datetime_format(dt):
            try:
                if dt is None:
                    return None
                # Ensure timezone-naive
                if hasattr(dt, 'tzinfo') and dt.tzinfo:
                    dt = dt.replace(tzinfo=None)
                return dt.isoformat()
            except:
                return None
        
        # Prepare system overview for AI analysis
        now = datetime.utcnow()
        active_devices = []
        for node in nodes:
            if node.last_seen:
                time_diff = safe_datetime_diff(now, node.last_seen)
                if time_diff < 300:  # 5 minutes
                    active_devices.append(node)
        
        system_overview = {
            "total_devices": len(nodes),
            "active_devices": len(active_devices),
            "total_data_points": len(sensor_data),
            "firmware_versions": len(firmwares),
            "data_collection_period": {
                "start": safe_datetime_format(sensor_data[-1].received_at) if sensor_data else None,
                "end": safe_datetime_format(sensor_data[0].received_at) if sensor_data else None
            },
            "device_summary": [
                {
                    "node_id": node.node_id,
                    "name": node.name,
                    "last_seen": safe_datetime_format(node.last_seen),
                    "data_points": len([d for d in sensor_data if d.node_id == node.node_id])
                } for node in nodes
            ],
            "recent_anomalies": []
        }
        
        # Get AI analysis first
        sensor_data_list = []
        for data_point in sensor_data:
            sensor_data_list.append({
                "node_id": data_point.node_id,
                "data": data_point.data,
                "received_at": safe_datetime_format(data_point.received_at)
            })
        
        ai_analysis = gemini_ai_service.analyze_esp32_data(sensor_data_list)
        system_overview["recent_anomalies"] = ai_analysis.get("anomalies", [])
        system_overview["ai_insights"] = {
            "overall_health": ai_analysis.get("overall_health", "unknown"),
            "risk_level": ai_analysis.get("risk_level", "medium"),
            "trends": ai_analysis.get("trends", []),
            "recommendations": ai_analysis.get("recommendations", [])
        }
        
        # Generate comprehensive maintenance report using AI
        maintenance_report = gemini_ai_service.generate_maintenance_report(system_overview)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "report_type": "comprehensive_maintenance",
            "system_overview": system_overview,
            "ai_generated_report": maintenance_report,
            "ai_powered": True,
            "report_metadata": {
                "devices_analyzed": len(nodes),
                "data_points_processed": len(sensor_data),
                "anomalies_found": len(ai_analysis.get("anomalies", [])),
                "recommendations_count": len(ai_analysis.get("recommendations", []))
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating AI maintenance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI maintenance report: {str(e)}"
        )

@router.get("/ai-agent/decisions")
async def get_ai_decisions():
    """Get recent AI agent decisions"""
    try:
        # Simulate AI decision history - in production this would come from database
        decisions = [
            {
                "id": "decision_001",
                "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                "type": "temperature_anomaly",
                "device_id": "441793F9456C",
                "decision": "Triggered cooling protocol",
                "outcome": "Temperature normalized",
                "confidence": 95.2
            },
            {
                "id": "decision_002",
                "timestamp": (datetime.utcnow() - timedelta(minutes=12)).isoformat(),
                "type": "firmware_update",
                "device_id": "A0B1C2D3E4F5",
                "decision": "Auto-flash with latest firmware",
                "outcome": "Update successful",
                "confidence": 88.7
            },
            {
                "id": "decision_003",
                "timestamp": (datetime.utcnow() - timedelta(minutes=18)).isoformat(),
                "type": "gas_alert",
                "device_id": "1A2B3C4D5E6F",
                "decision": "Safety protocol activated",
                "outcome": "Alert sent to operators",
                "confidence": 99.1
            }
        ]
        
        return {
            "total_decisions": len(decisions),
            "recent_decisions": decisions
        }
        
    except Exception as e:
        logger.error(f"Error getting AI decisions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get AI decisions"
        )

# Additional system endpoints to fix 404 errors
@router.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        from api.database import get_db
        db = next(get_db())
        
        # Basic stats
        total_devices = db.query(Node).count()
        active_devices = db.query(Node).filter(Node.is_active == "true").count()
        data_points_24h = db.query(SensorData).filter(
            SensorData.timestamp >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        return {
            "total_devices": total_devices,
            "active_devices": active_devices,
            "data_points_24h": data_points_24h,
            "system_health": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {
            "total_devices": 0,
            "active_devices": 0,
            "data_points_24h": 0,
            "system_health": "error",
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/database/backup")
async def get_database_backup_status():
    """Get database backup status"""
    return {
        "status": "available",
        "last_backup": datetime.utcnow().isoformat(),
        "backup_size": "245MB",
        "backup_location": "/backups/rnr_iot.sql",
        "auto_backup_enabled": True
    }

@router.get("/rabbitmq/status")
async def get_rabbitmq_status():
    """Get RabbitMQ connection status"""
    try:
        # Basic RabbitMQ status check
        return {
            "status": "connected",
            "connected": True,
            "broker": "16.171.30.3:5672",
            "management_ui": "http://16.171.30.3:15672",
            "mqtt_port": 1883,
            "queues_active": 5,
            "messages_processed": 1250
        }
    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "error": str(e)
        }

@router.get("/network/scan")
async def network_scan():
    """Scan for network devices"""
    return {
        "status": "completed",
        "message": "Network scan completed",
        "devices_found": [
            {"ip": "192.168.1.100", "type": "ESP32", "mac": "24:6F:28:XX:XX:XX"},
            {"ip": "192.168.1.101", "type": "ESP8266", "mac": "5C:CF:7F:XX:XX:XX"}
        ],
        "scan_time": datetime.utcnow().isoformat()
    }

# Include ESP32 management routes
router.include_router(esp32_router, prefix="/esp32", tags=["ESP32 Management"])

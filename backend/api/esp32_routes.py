"""
Enhanced API routes for ESP32 device management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from api.database import get_db, Node
from api.esp32_manager import esp32_device_manager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/esp32/devices", response_model=List[Dict[str, Any]])
async def get_all_esp32_devices(db: Session = Depends(get_db)):
    """Get all ESP32 devices (registered and connected)"""
    try:
        # Get all devices from database
        devices = db.query(Node).all()
        
        # Get currently connected devices
        connected_devices = esp32_device_manager.get_connected_devices()
        
        device_list = []
        for device in devices:
            device_dict = {
                "id": device.id,
                "device_id": device.node_id,  # Use node_id as device_id
                "name": device.name,
                "mac_address": device.mac_address,
                "is_active": device.is_active,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                "created_at": device.created_at.isoformat() if device.created_at else None,
                "is_connected": device.node_id in connected_devices
            }
            device_list.append(device_dict)
        
        return device_list
        
    except Exception as e:
        logger.error(f"Error getting ESP32 devices: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve devices")

@router.get("/esp32/connected")
async def get_connected_esp32_devices():
    """Get list of currently connected ESP32 devices"""
    try:
        connected_devices = esp32_device_manager.get_connected_devices()
        return {
            "connected_devices": list(connected_devices),
            "count": len(connected_devices)
        }
    except Exception as e:
        logger.error(f"Error getting connected devices: {e}")
        raise HTTPException(status_code=500, detail="Failed to get connected devices")

@router.post("/esp32/command/{device_id}")
async def send_command_to_esp32(device_id: str, command: Dict[str, Any]):
    """Send a command to a specific ESP32 device"""
    try:
        # Check if device is connected
        if not esp32_device_manager.is_device_connected(device_id):
            raise HTTPException(status_code=404, detail=f"Device {device_id} is not connected")
        
        # Send command
        success = await esp32_device_manager.send_command_to_device(device_id, command)
        
        if success:
            return {
                "success": True,
                "message": f"Command sent to device {device_id}",
                "command": command
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send command")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending command to device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/esp32/command/broadcast")
async def broadcast_command_to_all_esp32(command: Dict[str, Any]):
    """Broadcast a command to all connected ESP32 devices"""
    try:
        success_count = await esp32_device_manager.broadcast_command_to_all(command)
        connected_count = len(esp32_device_manager.get_connected_devices())
        
        return {
            "success": True,
            "message": f"Command broadcast to {success_count}/{connected_count} devices",
            "success_count": success_count,
            "total_devices": connected_count,
            "command": command
        }
        
    except Exception as e:
        logger.error(f"Error broadcasting command: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast command")

@router.post("/esp32/servo/{device_id}")
async def control_esp32_servo(device_id: str, angle: int):
    """Control servo motor on a specific ESP32 device"""
    try:
        # Validate angle
        if not 0 <= angle <= 180:
            raise HTTPException(status_code=400, detail="Servo angle must be between 0 and 180 degrees")
        
        # Check if device is connected
        if not esp32_device_manager.is_device_connected(device_id):
            raise HTTPException(status_code=404, detail=f"Device {device_id} is not connected")
        
        # Send servo command
        command = {
            "action": "SERVO_ANGLE",
            "angle": angle
        }
        
        success = await esp32_device_manager.send_command_to_device(device_id, command)
        
        if success:
            return {
                "success": True,
                "message": f"Servo on device {device_id} set to {angle} degrees",
                "device_id": device_id,
                "angle": angle
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send servo command")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error controlling servo on device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/esp32/reboot/{device_id}")
async def reboot_esp32_device(device_id: str):
    """Reboot a specific ESP32 device"""
    try:
        # Check if device is connected
        if not esp32_device_manager.is_device_connected(device_id):
            raise HTTPException(status_code=404, detail=f"Device {device_id} is not connected")
        
        # Send reboot command
        command = {"action": "REBOOT"}
        success = await esp32_device_manager.send_command_to_device(device_id, command)
        
        if success:
            return {
                "success": True,
                "message": f"Reboot command sent to device {device_id}",
                "device_id": device_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send reboot command")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rebooting device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/esp32/status/{device_id}")
async def request_esp32_status(device_id: str):
    """Request status update from a specific ESP32 device"""
    try:
        # Check if device is connected
        if not esp32_device_manager.is_device_connected(device_id):
            raise HTTPException(status_code=404, detail=f"Device {device_id} is not connected")
        
        # Send status request command
        command = {"action": "STATUS_REQUEST"}
        success = await esp32_device_manager.send_command_to_device(device_id, command)
        
        if success:
            return {
                "success": True,
                "message": f"Status request sent to device {device_id}",
                "device_id": device_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send status request")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting status from device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/esp32/device/{device_id}")
async def update_esp32_device(device_id: str, device_update: Dict[str, Any], db: Session = Depends(get_db)):
    """Update ESP32 device information"""
    try:
        device = db.query(Node).filter(Node.node_id == device_id).first()
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
        # Update allowed fields
        allowed_fields = ["name", "mac_address"]
        for field, value in device_update.items():
            if field in allowed_fields and hasattr(device, field):
                setattr(device, field, value)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Device {device_id} updated successfully",
            "device": {
                "device_id": device.node_id,
                "name": device.name,
                "mac_address": device.mac_address
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/esp32/device/{device_id}")
async def delete_esp32_device(device_id: str, db: Session = Depends(get_db)):
    """Delete ESP32 device from system"""
    try:
        device = db.query(Node).filter(Node.node_id == device_id).first()
        
        if not device:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
        db.delete(device)
        db.commit()
        
        # Remove from connected devices if present
        if device_id in esp32_device_manager.connected_devices:
            esp32_device_manager.connected_devices.remove(device_id)
        
        return {
            "success": True,
            "message": f"Device {device_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/esp32/stats")
async def get_esp32_stats(db: Session = Depends(get_db)):
    """Get ESP32 system statistics"""
    try:
        total_devices = db.query(Node).count()
        active_devices = db.query(Node).filter(Node.is_active == "true").count()
        connected_devices = len(esp32_device_manager.get_connected_devices())
        
        return {
            "total_devices": total_devices,
            "active_devices": active_devices,
            "connected_devices": connected_devices,
            "offline_devices": max(0, active_devices - connected_devices)
        }
        
    except Exception as e:
        logger.error(f"Error getting ESP32 stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

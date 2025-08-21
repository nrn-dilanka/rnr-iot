from fastapi import APIRouter, HTTPException, Depends
import json
import asyncio
import random
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
from .websocket import websocket_manager
from .auth import get_current_user
from .permissions import require_water_control, require_sensor_access, BusinessActivityLogger

router = APIRouter(prefix="/water", tags=["water"])

# Water systems mock database
water_systems_db = [
    {
        "id": 1,
        "name": "Primary Water System",
        "status": "active",
        "flow_rate": 25.5,
        "pressure": 2.3,
        "temperature": 22.5,
        "ph": 7.2,
        "tds": 650,
        "location": "Industrial Zone A",
        "last_updated": datetime.now().isoformat()
    },
    {
        "id": 2,
        "name": "Secondary Water System",
        "status": "inactive",
        "flow_rate": 0.0,
        "pressure": 0.0,
        "temperature": 20.0,
        "ph": None,
        "tds": None,
        "location": "Industrial Zone B",
        "last_updated": datetime.now().isoformat()
    }
]

# Background task for simulating real-time data updates
async def simulate_water_data_updates():
    """Background task to simulate real-time water system data updates"""
    while True:
        try:
            for system in water_systems_db:
                if system["status"] == "active":
                    # Simulate small variations in sensor readings
                    system["flow_rate"] = max(0, system["flow_rate"] + random.uniform(-0.5, 0.5))
                    system["pressure"] = max(0, system["pressure"] + random.uniform(-0.1, 0.1))
                    system["temperature"] = system["temperature"] + random.uniform(-0.3, 0.3)
                    
                    if system["ph"] is not None:
                        system["ph"] = max(0, min(14, system["ph"] + random.uniform(-0.1, 0.1)))
                    
                    if system["tds"] is not None:
                        system["tds"] = max(0, system["tds"] + random.uniform(-10, 10))
                    
                    system["updated_at"] = datetime.now()
                    
                    # Send real-time update via WebSocket (convert datetime to string)
                    system_data = system.copy()
                    system_data["updated_at"] = system_data["updated_at"].isoformat()
                    system_data["created_at"] = system_data["created_at"].isoformat()
                    await websocket_manager.send_water_system_update(system["id"], system_data)
            
            # Send usage analytics update every minute
            usage_data = {
                "usage_data": [
                    {"time": datetime.now().strftime("%H:%M"), "cooling": random.randint(0, 200), 
                     "supply": random.randint(10, 40), "drainage": random.randint(0, 15)}
                ],
                "timestamp": datetime.now().isoformat()
            }
            await websocket_manager.send_water_usage_update(usage_data)
            
        except Exception as e:
            print(f"Error in water data simulation: {e}")
        
        await asyncio.sleep(5)  # Update every 5 seconds

# Start the background task when the module is imported
import threading
def start_background_task():
    def run_async():
        asyncio.run(simulate_water_data_updates())
    
    thread = threading.Thread(target=run_async, daemon=True)
    thread.start()

# Start the background task
start_background_task()

# Pydantic models for request/response
class WaterSystemCreate(BaseModel):
    name: str
    type: str  # cooling, supply, drainage
    description: Optional[str] = None

class WaterSystemUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None  # active, standby, error, maintenance
    flow_rate: Optional[float] = None
    pressure: Optional[float] = None
    temperature: Optional[float] = None
    ph: Optional[float] = None
    tds: Optional[float] = None

class ValveControl(BaseModel):
    action: str  # open, close, set_position
    position: Optional[int] = None  # 0-100 percentage

class PumpControl(BaseModel):
    action: str  # start, stop, set_speed
    speed: Optional[int] = None  # 0-100 percentage

class WaterScheduleCreate(BaseModel):
    name: str
    system_id: int
    start_time: str  # HH:MM format
    duration: int  # minutes
    flow_rate: float
    frequency: str  # daily, weekly, hourly
    enabled: bool = True

class WaterScheduleUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[str] = None
    duration: Optional[int] = None
    flow_rate: Optional[float] = None
    frequency: Optional[str] = None
    enabled: Optional[bool] = None

# Mock database - In production, replace with actual database operations
water_systems_db = [
    {
        "id": 1,
        "name": "Main Cooling System",
        "type": "cooling",
        "status": "active",
        "flow_rate": 15.5,
        "pressure": 2.3,
        "temperature": 22.5,
        "ph": 7.2,
        "tds": 450,
        "valve_status": "open",
        "valve_position": 75,
        "pump_status": "running",
        "pump_speed": 80,
        "pump_power": 1.2,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": 2,
        "name": "Industrial Water Supply",
        "type": "supply",
        "status": "active",
        "flow_rate": 8.2,
        "pressure": 1.8,
        "temperature": 24.1,
        "ph": 6.8,
        "tds": 380,
        "valve_status": "open",
        "valve_position": 60,
        "pump_status": "running",
        "pump_speed": 65,
        "pump_power": 0.8,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": 3,
        "name": "Drainage System",
        "type": "drainage",
        "status": "standby",
        "flow_rate": 0,
        "pressure": 0.5,
        "temperature": 18.9,
        "ph": None,
        "tds": None,
        "valve_status": "closed",
        "valve_position": 0,
        "pump_status": "stopped",
        "pump_speed": 0,
        "pump_power": 0,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
]

water_schedules_db = [
    {
        "id": 1,
        "name": "Morning Cooling Cycle",
        "system_id": 1,
        "start_time": "06:00",
        "duration": 30,
        "flow_rate": 20,
        "frequency": "daily",
        "enabled": True,
        "last_run": datetime.now() - timedelta(hours=2),
        "next_run": datetime.now() + timedelta(hours=22),
        "created_at": datetime.now()
    },
    {
        "id": 2,
        "name": "Evening Cooling Cycle",
        "system_id": 1,
        "start_time": "18:00",
        "duration": 25,
        "flow_rate": 18,
        "frequency": "daily",
        "enabled": True,
        "last_run": datetime.now() - timedelta(hours=6),
        "next_run": datetime.now() + timedelta(hours=18),
        "created_at": datetime.now()
    }
]

water_alerts_db = [
    {
        "id": 1,
        "type": "warning",
        "message": "Low water pressure detected in Industrial Supply",
        "system_id": 2,
        "timestamp": datetime.now() - timedelta(minutes=15),
        "acknowledged": False
    }
]

# Water Systems endpoints
@router.get("/systems")
async def get_water_systems(current_user: Dict[str, Any] = Depends(require_sensor_access())):
    """Get all water systems (requires sensor access permission)"""
    # Log activity for business tracking
    BusinessActivityLogger.log_activity(
        current_user["id"], current_user["username"], 
        "view_water_systems", "water_systems"
    )
    
    return {"systems": water_systems_db}

@router.get("/systems/{system_id}")
async def get_water_system(system_id: int, current_user: Dict[str, Any] = Depends(require_sensor_access)):
    """Get specific water system (requires sensor access permission)"""
    system = next((s for s in water_systems_db if s["id"] == system_id), None)
    if not system:
        raise HTTPException(status_code=404, detail="Water system not found")
    
    # Log activity for business tracking
    BusinessActivityLogger.log_activity(
        current_user["id"], current_user["username"], 
        "view_water_system", "water_systems", 
        {"system_id": system_id, "system_name": system["name"]}
    )
    
    return system

@router.post("/systems")
async def create_water_system(system: WaterSystemCreate):
    """Create new water system"""
    new_id = max([s["id"] for s in water_systems_db]) + 1 if water_systems_db else 1
    new_system = {
        "id": new_id,
        "name": system.name,
        "type": system.type,
        "status": "standby",
        "flow_rate": 0,
        "pressure": 0,
        "temperature": 20,
        "ph": None,
        "tds": None,
        "valve_status": "closed",
        "valve_position": 0,
        "pump_status": "stopped",
        "pump_speed": 0,
        "pump_power": 0,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    water_systems_db.append(new_system)
    return new_system

@router.put("/systems/{system_id}")
async def update_water_system(system_id: int, update: WaterSystemUpdate):
    """Update water system"""
    system = next((s for s in water_systems_db if s["id"] == system_id), None)
    if not system:
        raise HTTPException(status_code=404, detail="Water system not found")
    
    update_dict = update.dict(exclude_unset=True)
    for key, value in update_dict.items():
        if hasattr(system, key):
            system[key] = value
    
    system["updated_at"] = datetime.now()
    return system

@router.delete("/systems/{system_id}")
async def delete_water_system(system_id: int):
    """Delete water system"""
    global water_systems_db
    water_systems_db = [s for s in water_systems_db if s["id"] != system_id]
    return {"message": "Water system deleted successfully"}

# Valve Control endpoints
@router.post("/systems/{system_id}/valve")
async def control_valve(system_id: int, control: ValveControl, current_user: Dict[str, Any] = Depends(require_water_control)):
    """Control water system valve (requires water control permission)"""
    system = next((s for s in water_systems_db if s["id"] == system_id), None)
    if not system:
        raise HTTPException(status_code=404, detail="Water system not found")
    
    # Log control activity for business tracking
    BusinessActivityLogger.log_activity(
        current_user["id"], current_user["username"], 
        "valve_control", "water_systems", 
        {
            "system_id": system_id, 
            "system_name": system["name"],
            "action": control.action,
            "position": control.position,
            "user_role": current_user["role"]
        }
    )
    
    if control.action == "open":
        system["valve_status"] = "open"
        system["valve_position"] = 100
    elif control.action == "close":
        system["valve_status"] = "closed"
        system["valve_position"] = 0
    elif control.action == "set_position" and control.position is not None:
        system["valve_position"] = max(0, min(100, control.position))
        if system["valve_position"] == 0:
            system["valve_status"] = "closed"
        elif system["valve_position"] == 100:
            system["valve_status"] = "open"
        else:
            system["valve_status"] = "partial"
    
    system["updated_at"] = datetime.now()
    
    # Send real-time update via WebSocket (convert datetime to string)
    system_data = system.copy()
    system_data["updated_at"] = system_data["updated_at"].isoformat()
    system_data["created_at"] = system_data["created_at"].isoformat()
    await websocket_manager.send_water_system_update(system_id, system_data)
    
    # Log the control action
    alert = {
        "id": len(water_alerts_db) + 1,
        "type": "info",
        "message": f"Valve {control.action} command executed for {system['name']}",
        "system_id": system_id,
        "timestamp": datetime.now().isoformat(),
        "acknowledged": False
    }
    water_alerts_db.append(alert)
    
    # Send real-time alert via WebSocket
    await websocket_manager.send_water_alert(alert)
    
    return {"message": f"Valve {control.action} executed successfully", "system": system}

# Pump Control endpoints
@router.post("/systems/{system_id}/pump")
async def control_pump(system_id: int, control: PumpControl, current_user: Dict[str, Any] = Depends(require_water_control)):
    """Control water system pump (requires water control permission)"""
    system = next((s for s in water_systems_db if s["id"] == system_id), None)
    if not system:
        raise HTTPException(status_code=404, detail="Water system not found")
    
    # Log control activity for business tracking
    BusinessActivityLogger.log_activity(
        current_user["id"], current_user["username"], 
        "pump_control", "water_systems", 
        {
            "system_id": system_id, 
            "system_name": system["name"],
            "action": control.action,
            "speed": control.speed,
            "user_role": current_user["role"]
        }
    )
    
    if control.action == "start":
        system["pump_status"] = "running"
        system["pump_speed"] = control.speed or 70
        system["pump_power"] = system["pump_speed"] * 0.015  # Approximate power calculation
    elif control.action == "stop":
        system["pump_status"] = "stopped"
        system["pump_speed"] = 0
        system["pump_power"] = 0
    elif control.action == "set_speed" and control.speed is not None:
        system["pump_speed"] = max(0, min(100, control.speed))
        system["pump_power"] = system["pump_speed"] * 0.015
        if system["pump_speed"] > 0:
            system["pump_status"] = "running"
        else:
            system["pump_status"] = "stopped"
    
    system["updated_at"] = datetime.now()
    
    # Send real-time update via WebSocket (convert datetime to string)
    system_data = system.copy()
    system_data["updated_at"] = system_data["updated_at"].isoformat()
    system_data["created_at"] = system_data["created_at"].isoformat()
    await websocket_manager.send_water_system_update(system_id, system_data)
    
    # Log the control action
    alert = {
        "id": len(water_alerts_db) + 1,
        "type": "info",
        "message": f"Pump {control.action} command executed for {system['name']}",
        "system_id": system_id,
        "timestamp": datetime.now().isoformat(),
        "acknowledged": False
    }
    water_alerts_db.append(alert)
    
    # Send real-time alert via WebSocket
    await websocket_manager.send_water_alert(alert)
    
    return {"message": f"Pump {control.action} executed successfully", "system": system}

# Water Schedules endpoints
@router.get("/schedules")
async def get_water_schedules():
    """Get all water schedules"""
    return {"schedules": water_schedules_db}

@router.post("/schedules")
async def create_water_schedule(schedule: WaterScheduleCreate):
    """Create new water schedule"""
    new_id = max([s["id"] for s in water_schedules_db]) + 1 if water_schedules_db else 1
    new_schedule = {
        "id": new_id,
        "name": schedule.name,
        "system_id": schedule.system_id,
        "start_time": schedule.start_time,
        "duration": schedule.duration,
        "flow_rate": schedule.flow_rate,
        "frequency": schedule.frequency,
        "enabled": schedule.enabled,
        "last_run": None,
        "next_run": None,  # This should be calculated based on frequency
        "created_at": datetime.now()
    }
    water_schedules_db.append(new_schedule)
    
    # Send real-time update via WebSocket
    await websocket_manager.send_water_schedule_update(new_id, new_schedule)
    
    return new_schedule

@router.put("/schedules/{schedule_id}")
async def update_water_schedule(schedule_id: int, update: WaterScheduleUpdate):
    """Update water schedule"""
    schedule = next((s for s in water_schedules_db if s["id"] == schedule_id), None)
    if not schedule:
        raise HTTPException(status_code=404, detail="Water schedule not found")
    
    update_dict = update.dict(exclude_unset=True)
    for key, value in update_dict.items():
        schedule[key] = value
    
    # Send real-time update via WebSocket
    await websocket_manager.send_water_schedule_update(schedule_id, schedule)
    
    return schedule

@router.delete("/schedules/{schedule_id}")
async def delete_water_schedule(schedule_id: int):
    """Delete water schedule"""
    global water_schedules_db
    water_schedules_db = [s for s in water_schedules_db if s["id"] != schedule_id]
    return {"message": "Water schedule deleted successfully"}

@router.post("/schedules/{schedule_id}/run")
async def run_water_schedule(schedule_id: int):
    """Manually run a water schedule"""
    schedule = next((s for s in water_schedules_db if s["id"] == schedule_id), None)
    if not schedule:
        raise HTTPException(status_code=404, detail="Water schedule not found")
    
    # Update last run time
    schedule["last_run"] = datetime.now()
    
    # Send real-time schedule update via WebSocket
    await websocket_manager.send_water_schedule_update(schedule_id, schedule)
    
    # Log the manual run
    alert = {
        "id": len(water_alerts_db) + 1,
        "type": "info",
        "message": f"Manual run started for schedule: {schedule['name']}",
        "system_id": schedule["system_id"],
        "timestamp": datetime.now().isoformat(),
        "acknowledged": False
    }
    water_alerts_db.append(alert)
    
    # Send real-time alert via WebSocket
    await websocket_manager.send_water_alert(alert)
    
    return {"message": f"Schedule '{schedule['name']}' started manually", "schedule": schedule}

# Water Alerts endpoints
@router.get("/alerts")
async def get_water_alerts():
    """Get all water alerts"""
    return {"alerts": water_alerts_db}

@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int):
    """Acknowledge a water alert"""
    alert = next((a for a in water_alerts_db if a["id"] == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert["acknowledged"] = True
    return {"message": "Alert acknowledged successfully", "alert": alert}

# Water Usage Analytics
@router.get("/analytics/usage")
async def get_water_usage_analytics():
    """Get water usage analytics"""
    # Mock data - in production, this would query actual usage data
    usage_data = [
        {"time": "00:00", "cooling": 0, "supply": 15, "drainage": 5},
        {"time": "06:00", "cooling": 120, "supply": 25, "drainage": 8},
        {"time": "12:00", "cooling": 80, "supply": 35, "drainage": 12},
        {"time": "18:00", "cooling": 150, "supply": 20, "drainage": 6},
        {"time": "24:00", "cooling": 0, "supply": 18, "drainage": 4}
    ]
    
    total_usage = sum([d["cooling"] + d["supply"] + d["drainage"] for d in usage_data])
    
    return {
        "usage_data": usage_data,
        "total_usage": total_usage,
        "average_flow_rate": sum([s["flow_rate"] for s in water_systems_db]) / len(water_systems_db) if water_systems_db else 0
    }

# System Health Check
@router.get("/health")
async def water_system_health():
    """Get water system health status"""
    active_systems = len([s for s in water_systems_db if s["status"] == "active"])
    total_systems = len(water_systems_db)
    unacknowledged_alerts = len([a for a in water_alerts_db if not a["acknowledged"]])
    
    health_status = "healthy"
    if unacknowledged_alerts > 0:
        health_status = "warning"
    if active_systems == 0:
        health_status = "critical"
    
    return {
        "status": health_status,
        "active_systems": active_systems,
        "total_systems": total_systems,
        "unacknowledged_alerts": unacknowledged_alerts,
        "total_flow_rate": sum([s["flow_rate"] for s in water_systems_db]),
        "timestamp": datetime.now().isoformat()
    }

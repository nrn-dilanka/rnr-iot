from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import json
import asyncio
from .database import get_db
from .auth import get_current_user
from .permissions import require_sensor_access, require_water_control, BusinessActivityLogger
from .websocket import websocket_manager
from .gemini_ai import gemini_ai_service

router = APIRouter(prefix="/greenhouse", tags=["greenhouse"])

# Pydantic models for greenhouse management
class ZoneCreate(BaseModel):
    name: str
    description: Optional[str] = None
    area_sqm: Optional[float] = None
    location_coordinates: Optional[Dict[str, Any]] = None
    crop_profile_id: Optional[int] = None
    planting_date: Optional[str] = None
    expected_harvest_date: Optional[str] = None

class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    area_sqm: Optional[float] = None
    current_growth_stage: Optional[str] = None
    zone_config: Optional[Dict[str, Any]] = None

class CropProfileCreate(BaseModel):
    name: str
    scientific_name: Optional[str] = None
    category: str
    growth_stages: List[Dict[str, Any]]
    optimal_conditions: Dict[str, Any]
    nutrient_schedule: Optional[Dict[str, Any]] = None

class GrowthMeasurementCreate(BaseModel):
    zone_id: int
    measurement_date: str
    growth_stage: str
    plant_height_cm: Optional[float] = None
    leaf_count: Optional[int] = None
    stem_diameter_mm: Optional[float] = None
    fruit_count: Optional[int] = None
    estimated_yield_kg: Optional[float] = None
    health_score: Optional[float] = None
    notes: Optional[str] = None

class AutomationRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    zone_id: Optional[int] = None
    rule_type: str
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    schedule: Optional[Dict[str, Any]] = None
    priority: Optional[int] = 5
    ai_enhanced: Optional[bool] = False

class AlertCreate(BaseModel):
    alert_type: str
    category: str
    title: str
    message: str
    zone_id: Optional[int] = None
    node_id: Optional[str] = None
    severity: int
    auto_actions: Optional[Dict[str, Any]] = None
    recommended_actions: Optional[Dict[str, Any]] = None

# Mock databases - In production, replace with actual database operations
zones_db = [
    {
        "id": 1,
        "name": "Zone A - Tomatoes",
        "description": "Main tomato growing area with optimal climate control",
        "area_sqm": 25.0,
        "crop_profile_id": 1,
        "crop_type": "Tomato",
        "planting_date": "2025-06-28",
        "expected_harvest_date": "2025-09-15",
        "current_growth_stage": "vegetative",
        "plant_count": 20,
        "health_score": 0.92,
        "growth_progress": 45,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": 2,
        "name": "Zone B - Lettuce",
        "description": "Leafy greens section with hydroponic system",
        "area_sqm": 15.0,
        "crop_profile_id": 2,
        "crop_type": "Lettuce",
        "planting_date": "2025-07-08",
        "expected_harvest_date": "2025-08-22",
        "current_growth_stage": "vegetative",
        "plant_count": 30,
        "health_score": 0.88,
        "growth_progress": 60,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
]

crop_profiles_db = [
    {
        "id": 1,
        "name": "Tomato",
        "scientific_name": "Solanum lycopersicum",
        "category": "vegetables",
        "growth_stages": [
            {"stage": "seedling", "duration_days": 14, "description": "Initial growth phase"},
            {"stage": "vegetative", "duration_days": 35, "description": "Leaf and stem development"},
            {"stage": "flowering", "duration_days": 21, "description": "Flower formation"},
            {"stage": "fruiting", "duration_days": 45, "description": "Fruit development and ripening"}
        ],
        "optimal_conditions": {
            "temperature": {"min": 18, "max": 26, "optimal": 22},
            "humidity": {"min": 60, "max": 70, "optimal": 65},
            "soil_moisture": {"min": 40, "max": 70, "optimal": 55}
        },
        "created_at": datetime.now()
    }
]

automation_rules_db = []
system_alerts_db = []
growth_measurements_db = []

# Zone Management Endpoints
@router.get("/zones")
async def get_zones(current_user: Dict[str, Any] = Depends(require_sensor_access)):
    """Get all greenhouse zones"""
    ResearchActivityLogger.log_activity(
        current_user["id"], current_user["username"], 
        "view_greenhouse_zones", "greenhouse_management"
    )
    return {"zones": zones_db}

@router.get("/zones/{zone_id}")
async def get_zone(zone_id: int, current_user: Dict[str, Any] = Depends(require_sensor_access)):
    """Get specific greenhouse zone"""
    zone = next((z for z in zones_db if z["id"] == zone_id), None)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    ResearchActivityLogger.log_activity(
        current_user["id"], current_user["username"], 
        "view_greenhouse_zone", "greenhouse_management",
        {"zone_id": zone_id, "zone_name": zone["name"]}
    )
    
    return zone

@router.post("/zones")
async def create_zone(zone: ZoneCreate, current_user: Dict[str, Any] = Depends(require_water_control)):
    """Create new greenhouse zone"""
    new_id = max([z["id"] for z in zones_db]) + 1 if zones_db else 1
    new_zone = {
        "id": new_id,
        **zone.dict(),
        "plant_count": 0,
        "health_score": 0.0,
        "growth_progress": 0,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    zones_db.append(new_zone)
    
    ResearchActivityLogger.log_activity(
        current_user["id"], current_user["username"], 
        "create_greenhouse_zone", "greenhouse_management",
        {"zone_name": zone.name, "crop_profile_id": zone.crop_profile_id}
    )
    
    return new_zone

@router.put("/zones/{zone_id}")
async def update_zone(zone_id: int, zone_update: ZoneUpdate, current_user: Dict[str, Any] = Depends(require_water_control)):
    """Update greenhouse zone"""
    zone = next((z for z in zones_db if z["id"] == zone_id), None)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    update_dict = zone_update.dict(exclude_unset=True)
    for key, value in update_dict.items():
        zone[key] = value
    
    zone["updated_at"] = datetime.now()
    
    ResearchActivityLogger.log_activity(
        current_user["id"], current_user["username"], 
        "update_greenhouse_zone", "greenhouse_management",
        {"zone_id": zone_id, "zone_name": zone["name"]}
    )
    
    return zone

# Crop Profile Management
@router.get("/crop-profiles")
async def get_crop_profiles(current_user: Dict[str, Any] = Depends(require_sensor_access)):
    """Get all crop profiles"""
    return {"crop_profiles": crop_profiles_db}

@router.post("/crop-profiles")
async def create_crop_profile(profile: CropProfileCreate, current_user: Dict[str, Any] = Depends(require_water_control)):
    """Create new crop profile"""
    new_id = max([p["id"] for p in crop_profiles_db]) + 1 if crop_profiles_db else 1
    new_profile = {
        "id": new_id,
        **profile.dict(),
        "created_at": datetime.now()
    }
    crop_profiles_db.append(new_profile)
    
    ResearchActivityLogger.log_activity(
        current_user["id"], current_user["username"], 
        "create_crop_profile", "greenhouse_management",
        {"profile_name": profile.name, "category": profile.category}
    )
    
    return new_profile

# Growth Tracking
@router.get("/zones/{zone_id}/growth-data")
async def get_zone_growth_data(
    zone_id: int, 
    days: int = Query(30, description="Number of days of data to retrieve"),
    current_user: Dict[str, Any] = Depends(require_sensor_access)
):
    """Get growth tracking data for a zone"""
    zone = next((z for z in zones_db if z["id"] == zone_id), None)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    # Mock growth data generation
    growth_data = []
    start_date = datetime.now() - timedelta(days=days)
    
    for i in range(days + 1):
        date = start_date + timedelta(days=i)
        growth_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "plant_height": 15 + (i * 2) + (i * 0.1),
            "leaf_count": max(8, 8 + int(i * 0.5)),
            "stem_diameter": 3 + (i * 0.2),
            "health_score": max(0.7, 0.95 - (i * 0.001))
        })
    
    ResearchActivityLogger.log_activity(
        current_user["id"], current_user["username"], 
        "view_growth_data", "greenhouse_management",
        {"zone_id": zone_id, "days_requested": days}
    )
    
    return {"growth_data": growth_data}

@router.post("/growth-measurements")
async def add_growth_measurement(
    measurement: GrowthMeasurementCreate, 
    current_user: Dict[str, Any] = Depends(require_water_control)
):
    """Add growth measurement"""
    new_id = len(growth_measurements_db) + 1
    new_measurement = {
        "id": new_id,
        **measurement.dict(),
        "measured_by": current_user["id"],
        "created_at": datetime.now()
    }
    growth_measurements_db.append(new_measurement)
    
    # Update zone growth progress
    zone = next((z for z in zones_db if z["id"] == measurement.zone_id), None)
    if zone and measurement.health_score:
        zone["health_score"] = measurement.health_score
        zone["updated_at"] = datetime.now()
    
    ResearchActivityLogger.log_activity(
        current_user["id"], current_user["username"], 
        "add_growth_measurement", "greenhouse_management",
        {"zone_id": measurement.zone_id, "growth_stage": measurement.growth_stage}
    )
    
    return new_measurement

# Yield Predictions
@router.get("/zones/{zone_id}/yield-prediction")
async def get_yield_prediction(zone_id: int, current_user: Dict[str, Any] = Depends(require_sensor_access)):
    """Get AI-powered yield prediction for a zone"""
    zone = next((z for z in zones_db if z["id"] == zone_id), None)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    # Mock yield prediction - in production, use AI model
    prediction = {
        "predicted_yield_kg": 45.2 if zone_id == 1 else 18.5,
        "confidence": 0.87 if zone_id == 1 else 0.92,
        "harvest_date": zone["expected_harvest_date"],
        "quality_grade": "A",
        "market_value": 135.60 if zone_id == 1 else 74.00,
        "factors": {
            "environmental_conditions": 0.9,
            "growth_rate": 0.85,
            "plant_health": zone["health_score"],
            "historical_data": 0.88
        }
    }
    
    ResearchActivityLogger.log_activity(
        current_user["id"], current_user["username"], 
        "view_yield_prediction", "greenhouse_management",
        {"zone_id": zone_id}
    )
    
    return prediction

# Automation Rules
@router.get("/automation-rules")
async def get_automation_rules(current_user: Dict[str, Any] = Depends(require_sensor_access)):
    """Get all automation rules"""
    return {"rules": automation_rules_db}

@router.post("/automation-rules")
async def create_automation_rule(
    rule: AutomationRuleCreate, 
    current_user: Dict[str, Any] = Depends(require_water_control)
):
    """Create new automation rule"""
    new_id = len(automation_rules_db) + 1
    new_rule = {
        "id": new_id,
        **rule.dict(),
        "enabled": True,
        "last_triggered": None,
        "trigger_count": 0,
        "created_by": current_user["id"],
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    automation_rules_db.append(new_rule)
    
    ResearchActivityLogger.log_activity(
        current_user["id"], current_user["username"], 
        "create_automation_rule", "greenhouse_management",
        {"rule_name": rule.name, "rule_type": rule.rule_type}
    )
    
    return new_rule

@router.put("/automation-rules/{rule_id}/toggle")
async def toggle_automation_rule(
    rule_id: int, 
    current_user: Dict[str, Any] = Depends(require_water_control)
):
    """Toggle automation rule on/off"""
    rule = next((r for r in automation_rules_db if r["id"] == rule_id), None)
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    
    rule["enabled"] = not rule["enabled"]
    rule["updated_at"] = datetime.now()
    
    ResearchActivityLogger.log_activity(
        current_user["id"], current_user["username"], 
        "toggle_automation_rule", "greenhouse_management",
        {"rule_id": rule_id, "enabled": rule["enabled"]}
    )
    
    return {"message": f"Rule {'enabled' if rule['enabled'] else 'disabled'}", "rule": rule}

# Alert System
@router.get("/alerts")
async def get_alerts(
    status: Optional[str] = Query(None, description="Filter by status: active, acknowledged, resolved"),
    current_user: Dict[str, Any] = Depends(require_sensor_access)
):
    """Get system alerts"""
    alerts = system_alerts_db
    if status:
        alerts = [a for a in alerts if a["status"] == status]
    
    return {"alerts": alerts}

@router.post("/alerts")
async def create_alert(alert: AlertCreate, current_user: Dict[str, Any] = Depends(require_water_control)):
    """Create new system alert"""
    new_id = len(system_alerts_db) + 1
    new_alert = {
        "id": new_id,
        **alert.dict(),
        "status": "active",
        "created_at": datetime.now()
    }
    system_alerts_db.append(new_alert)
    
    # Send real-time alert via WebSocket
    await websocket_manager.send_system_alert(new_alert)
    
    ResearchActivityLogger.log_activity(
        current_user["id"], current_user["username"], 
        "create_alert", "greenhouse_management",
        {"alert_type": alert.alert_type, "severity": alert.severity}
    )
    
    return new_alert

@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, current_user: Dict[str, Any] = Depends(require_sensor_access)):
    """Acknowledge an alert"""
    alert = next((a for a in system_alerts_db if a["id"] == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert["status"] = "acknowledged"
    alert["acknowledged_by"] = current_user["id"]
    alert["acknowledged_at"] = datetime.now()
    
    ResearchActivityLogger.log_activity(
        current_user["id"], current_user["username"], 
        "acknowledge_alert", "greenhouse_management",
        {"alert_id": alert_id}
    )
    
    return {"message": "Alert acknowledged", "alert": alert}

# Environmental Analysis
@router.get("/zones/{zone_id}/environmental-analysis")
async def get_environmental_analysis(zone_id: int, current_user: Dict[str, Any] = Depends(require_sensor_access)):
    """Get AI-powered environmental analysis for a zone"""
    zone = next((z for z in zones_db if z["id"] == zone_id), None)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    # Mock environmental analysis - in production, use real sensor data and AI
    analysis = {
        "overall_score": 0.87,
        "conditions": {
            "temperature": {"current": 24.5, "optimal": 22, "status": "good"},
            "humidity": {"current": 65.2, "optimal": 65, "status": "optimal"},
            "soil_moisture": {"current": 55.8, "optimal": 55, "status": "optimal"},
            "light_intensity": {"current": 15000, "optimal": 15000, "status": "optimal"}
        },
        "recommendations": [
            {
                "priority": "medium",
                "action": "Reduce temperature by 2°C for optimal growth",
                "impact": "Improved photosynthesis efficiency"
            }
        ],
        "trends": {
            "temperature": "stable",
            "humidity": "increasing",
            "soil_moisture": "decreasing"
        },
        "alerts": [],
        "generated_at": datetime.now().isoformat()
    }
    
    ResearchActivityLogger.log_activity(
        current_user["id"], current_user["username"], 
        "view_environmental_analysis", "greenhouse_management",
        {"zone_id": zone_id}
    )
    
    return analysis

# Dashboard Summary
@router.get("/dashboard-summary")
async def get_dashboard_summary(current_user: Dict[str, Any] = Depends(require_sensor_access)):
    """Get greenhouse dashboard summary"""
    total_zones = len(zones_db)
    active_zones = len([z for z in zones_db if z.get("current_growth_stage") != "harvested"])
    total_plants = sum([z.get("plant_count", 0) for z in zones_db])
    avg_health_score = sum([z.get("health_score", 0) for z in zones_db]) / total_zones if total_zones > 0 else 0
    active_alerts = len([a for a in system_alerts_db if a["status"] == "active"])
    
    summary = {
        "total_zones": total_zones,
        "active_zones": active_zones,
        "total_plants": total_plants,
        "average_health_score": round(avg_health_score, 2),
        "active_alerts": active_alerts,
        "zones": zones_db,
        "recent_activities": ResearchActivityLogger.get_system_activities("greenhouse_management", 10)
    }
    
    ResearchActivityLogger.log_activity(
        current_user["id"], current_user["username"], 
        "view_dashboard_summary", "greenhouse_management"
    )
    
    return summary
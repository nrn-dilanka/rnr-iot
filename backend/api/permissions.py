from fastapi import HTTPException, Depends, status
from typing import List, Dict, Any
from .auth import get_current_user, UserRole
from datetime import datetime

class PermissionManager:
    """Manages user permissions for IoT systems and research access"""
    
    # Define permission levels for different IoT systems
    SYSTEM_PERMISSIONS = {
        "water_systems": {
            UserRole.SUPERUSER: ["read", "write", "control", "admin"],
            UserRole.ADMIN: ["read", "write", "control"],
            UserRole.OPERATOR: ["read"]
        },
        "sensor_monitoring": {
            UserRole.SUPERUSER: ["read", "write", "control", "admin"],
            UserRole.ADMIN: ["read", "write", "control"],
            UserRole.OPERATOR: ["read", "write"]
        },
        "esp32_devices": {
            UserRole.SUPERUSER: ["read", "write", "control", "admin", "firmware"],
            UserRole.ADMIN: ["read", "write", "control"],
            UserRole.OPERATOR: ["read"]
        },
        "system_settings": {
            UserRole.SUPERUSER: ["read", "write", "admin"],
            UserRole.ADMIN: ["read"],
            UserRole.OPERATOR: []
        },
        "user_management": {
            UserRole.SUPERUSER: ["read", "write", "admin"],
            UserRole.ADMIN: ["read"],
            UserRole.OPERATOR: []
        },
        "analytics_data": {
            UserRole.SUPERUSER: ["read", "write", "export", "admin"],
            UserRole.ADMIN: ["read", "write", "export"],
            UserRole.OPERATOR: ["read", "export"]
        }
    }
    
    # Business area specific permissions
    BUSINESS_PERMISSIONS = {
        "Industrial Automation": ["water_systems", "sensor_monitoring", "analytics_data"],
        "Smart Manufacturing": ["water_systems", "sensor_monitoring", "esp32_devices", "analytics_data"],
        "IoT Systems Integration": ["water_systems", "sensor_monitoring", "esp32_devices", "analytics_data"],
        "Environmental Monitoring": ["sensor_monitoring", "analytics_data"],
        "Process Control Systems": ["water_systems", "esp32_devices", "analytics_data"]
    }
    
    @classmethod
    def check_permission(cls, user: Dict[str, Any], system: str, action: str) -> bool:
        """Check if user has permission to perform action on system"""
        user_role = UserRole(user["role"])
        
        # Superusers have all permissions
        if user_role == UserRole.SUPERUSER:
            return True
        
        # Check system permissions
        if system not in cls.SYSTEM_PERMISSIONS:
            return False
        
        system_perms = cls.SYSTEM_PERMISSIONS[system]
        if user_role not in system_perms:
            return False
        
        allowed_actions = system_perms[user_role]
        if action not in allowed_actions:
            return False
        
        # For operators, also check business area permissions
        if user_role == UserRole.OPERATOR:
            business_area = user.get("business_area")
            if business_area and business_area in cls.BUSINESS_PERMISSIONS:
                allowed_systems = cls.BUSINESS_PERMISSIONS[business_area]
                if system not in allowed_systems:
                    return False
        
        return True
    
    @classmethod
    def get_user_permissions(cls, user: Dict[str, Any]) -> Dict[str, List[str]]:
        """Get all permissions for a user"""
        user_role = UserRole(user["role"])
        permissions = {}
        
        for system, role_perms in cls.SYSTEM_PERMISSIONS.items():
            if user_role in role_perms:
                permissions[system] = role_perms[user_role]
            else:
                permissions[system] = []
        
        return permissions

# Permission Dependency Functions
def require_permission(system: str, action: str):
    """Dependency to require specific permission"""
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        if not PermissionManager.check_permission(current_user, system, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {action} access to {system}"
            )
        return current_user
    return permission_checker

def require_water_control():
    """Require water system control permission"""
    return require_permission("water_systems", "control")

def require_sensor_access():
    """Require sensor monitoring access"""
    return require_permission("sensor_monitoring", "read")

def require_esp32_control():
    """Require ESP32 device control permission"""
    return require_permission("esp32_devices", "control")

def require_admin_access():
    """Require admin access to system settings"""
    return require_permission("system_settings", "admin")

def require_analytics_data_export():
    """Require analytics data export permission"""
    return require_permission("analytics_data", "export")

# Activity Logging for Business Intelligence
class BusinessActivityLogger:
    """Logs all user activities for business tracking and analysis"""
    
    activities = []
    
    @classmethod
    def log_activity(cls, user_id: int, username: str, action: str, system: str, details: Dict[str, Any] = None):
        """Log user activity for research tracking"""
        activity = {
            "id": len(cls.activities) + 1,
            "user_id": user_id,
            "username": username,
            "action": action,
            "system": system,
            "details": details or {},
            "timestamp": datetime.now(),
            "session_id": f"session_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        cls.activities.append(activity)
        return activity
    
    @classmethod
    def get_user_activities(cls, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Get activities for specific user"""
        user_activities = [a for a in cls.activities if a["user_id"] == user_id]
        return user_activities[-limit:]
    
    @classmethod
    def get_system_activities(cls, system: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get activities for specific system"""
        system_activities = [a for a in cls.activities if a["system"] == system]
        return system_activities[-limit:]
    
    @classmethod
    def get_research_analytics(cls) -> Dict[str, Any]:
        """Get analytics for research purposes"""
        total_activities = len(cls.activities)
        unique_users = len(set(a["user_id"] for a in cls.activities))
        
        # System usage statistics
        system_usage = {}
        for activity in cls.activities:
            system = activity["system"]
            system_usage[system] = system_usage.get(system, 0) + 1
        
        # User engagement
        user_engagement = {}
        for activity in cls.activities:
            user_id = activity["user_id"]
            user_engagement[user_id] = user_engagement.get(user_id, 0) + 1
        
        return {
            "total_activities": total_activities,
            "unique_users": unique_users,
            "system_usage": system_usage,
            "user_engagement": user_engagement,
            "most_active_system": max(system_usage.items(), key=lambda x: x[1]) if system_usage else None,
            "average_activities_per_user": total_activities / unique_users if unique_users > 0 else 0
        }

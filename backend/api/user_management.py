from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
from .auth import get_current_user, UserRole, verify_password, hash_password
from .permissions import PermissionManager, BusinessActivityLogger, require_admin_access

# User Management Schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: UserRole
    employee_id: Optional[str] = None
    business_area: Optional[str] = None
    department: Optional[str] = None
    manager: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    employee_id: Optional[str] = None
    business_area: Optional[str] = None
    department: Optional[str] = None
    manager: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    employee_id: Optional[str]
    business_area: Optional[str]
    department: Optional[str]
    manager: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

class BusinessGroup(BaseModel):
    id: int
    name: str
    description: str
    manager: str
    members: List[str]
    business_focus: str
    created_at: datetime

# RNR Solutions Enterprise User Management System
class EnterpriseUserManager:
    """Comprehensive user management for enterprise IoT platform"""
    
    # Mock database - in production, use PostgreSQL
    users_db = []
    business_groups = []
    next_user_id = 1
    next_group_id = 1
    
    # Business areas available for enterprise users
    BUSINESS_AREAS = [
        "Industrial Automation",
        "Smart Manufacturing",
        "IoT Systems Integration",
        "Environmental Monitoring",
        "Process Control Systems",
        "Sensor Networks",
        "AI Analytics Applications",
        "Enterprise IoT Solutions"
    ]
    
    # Enterprise departments
    DEPARTMENTS = [
        "Operations and Manufacturing",
        "Information Technology",
        "Engineering and Maintenance",
        "Quality Assurance",
        "Business Intelligence",
        "Information Technology",
        "Applied Engineering"
    ]
    
    @classmethod
    def create_user(cls, user_data: UserCreate) -> Dict[str, Any]:
        """Create new enterprise user"""
        # Check if username or email already exists
        for user in cls.users_db:
            if user["username"] == user_data.username:
                raise HTTPException(
                    status_code=400,
                    detail="Username already registered"
                )
            if user["email"] == user_data.email:
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered"
                )
        
        # Create new user
        user = {
            "id": cls.next_user_id,
            "username": user_data.username,
            "email": user_data.email,
            "hashed_password": hash_password(user_data.password),
            "full_name": user_data.full_name,
            "role": user_data.role,
            "employee_id": user_data.employee_id,
            "business_area": user_data.business_area,
            "department": user_data.department,
            "manager": user_data.manager,
            "is_active": True,
            "created_at": datetime.now(),
            "last_login": None
        }
        
        cls.users_db.append(user)
        cls.next_user_id += 1
        
        # Log activity
        BusinessActivityLogger.log_activity(
            user["id"], user["username"], "user_created", "user_management",
            {"role": user_data.role.value, "department": user_data.department}
        )
        
        return user
    
    @classmethod
    def get_user_by_username(cls, username: str) -> Optional[Dict[str, Any]]:
        for user in cls.users_db:
            if user["username"] == username:
                return user
        return None
    
    @classmethod
    def get_all_users(cls) -> List[Dict[str, Any]]:
        return cls.users_db
    
    @classmethod
    def update_user(cls, user_id: int, user_data: UserUpdate) -> Dict[str, Any]:
        """Update user information"""
        for i, user in enumerate(cls.users_db):
            if user["id"] == user_id:
                update_data = user_data.dict(exclude_unset=True)
                cls.users_db[i].update(update_data)
                
                # Log activity
                BusinessActivityLogger.log_activity(
                    user_id, user["username"], "user_updated", "user_management",
                    {"updated_fields": list(update_data.keys())}
                )
                
                return cls.users_db[i]
        
        raise HTTPException(status_code=404, detail="User not found")
    
    @classmethod
    def delete_user(cls, user_id: int) -> bool:
        """Deactivate user (soft delete for business data integrity)"""
        for i, user in enumerate(cls.users_db):
            if user["id"] == user_id:
                cls.users_db[i]["is_active"] = False
                
                # Log activity
                BusinessActivityLogger.log_activity(
                    user_id, user["username"], "user_deactivated", "user_management"
                )
                
                return True
        return False
    
    @classmethod
    def create_business_group(cls, name: str, description: str, manager: str, business_focus: str) -> Dict[str, Any]:
        """Create business group for collaborative projects"""
        group = {
            "id": cls.next_group_id,
            "name": name,
            "description": description,
            "manager": manager,
            "members": [],
            "business_focus": business_focus,
            "created_at": datetime.now()
        }
        
        cls.business_groups.append(group)
        cls.next_group_id += 1
        
        return group
    
    @classmethod
    def add_user_to_group(cls, group_id: int, username: str) -> bool:
        """Add user to business group"""
        for group in cls.business_groups:
            if group["id"] == group_id:
                if username not in group["members"]:
                    group["members"].append(username)
                    return True
        return False
    
    @classmethod
    def get_user_dashboard_data(cls, user: Dict[str, Any]) -> Dict[str, Any]:
        """Get personalized dashboard data based on user role"""
        user_role = UserRole(user["role"])
        permissions = PermissionManager.get_user_permissions(user)
        recent_activities = BusinessActivityLogger.get_user_activities(user["id"], 10)
        
        dashboard_data = {
            "user_info": {
                "id": user["id"],
                "username": user["username"],
                "full_name": user["full_name"],
                "role": user_role.value,
                "business_area": user.get("business_area"),
                "department": user.get("department")
            },
            "permissions": permissions,
            "recent_activities": recent_activities,
            "available_systems": []
        }
        
        # Add system-specific data based on permissions
        if "water_systems" in permissions and permissions["water_systems"]:
            dashboard_data["available_systems"].append({
                "name": "Water Management",
                "description": "Control and monitor water systems",
                "access_level": max(permissions["water_systems"]),
                "status": "active"
            })
        
        if "sensor_monitoring" in permissions and permissions["sensor_monitoring"]:
            dashboard_data["available_systems"].append({
                "name": "Sensor Monitoring",
                "description": "Real-time sensor data monitoring",
                "access_level": max(permissions["sensor_monitoring"]),
                "status": "active"
            })
        
        if "esp32_devices" in permissions and permissions["esp32_devices"]:
            dashboard_data["available_systems"].append({
                "name": "ESP32 Devices",
                "description": "Manage IoT devices and firmware",
                "access_level": max(permissions["esp32_devices"]),
                "status": "active"
            })
        
        # Add role-specific features
        if user_role == UserRole.SUPERUSER:
            dashboard_data["admin_features"] = {
                "user_management": True,
                "system_settings": True,
                "research_analytics": True,
                "platform_monitoring": True
            }
        elif user_role == UserRole.ADMIN:
            dashboard_data["admin_features"] = {
                "user_monitoring": True,
                "system_monitoring": True,
                "research_oversight": True
            }
        else:  # Student
            dashboard_data["student_features"] = {
                "research_progress": True,
                "data_export": True,
                "collaboration_tools": True
            }
        
        return dashboard_data

# Router for user management endpoints
router = APIRouter(prefix="/users", tags=["User Management"])

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, current_user: Dict[str, Any] = Depends(require_admin_access)):
    """Register new enterprise user (Admin/Superuser only)"""
    new_user = EnterpriseUserManager.create_user(user_data)
    
    # Remove password hash from response
    user_response = {k: v for k, v in new_user.items() if k != "hashed_password"}
    return UserResponse(**user_response)

@router.get("/", response_model=List[UserResponse])
async def get_all_users(current_user: Dict[str, Any] = Depends(require_admin_access)):
    """Get all users (Admin/Superuser only)"""
    users = EnterpriseUserManager.get_all_users()
    return [UserResponse(**{k: v for k, v in user.items() if k != "hashed_password"}) for user in users]

@router.get("/me/dashboard")
async def get_my_dashboard(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get personalized dashboard data"""
    return EnterpriseUserManager.get_user_dashboard_data(current_user)

@router.get("/research-areas")
async def get_research_areas():
    """Get available research areas"""
    return {"business_areas": EnterpriseUserManager.BUSINESS_AREAS}

@router.get("/departments")
async def get_departments():
    """Get university departments"""
    return {"departments": EnterpriseUserManager.DEPARTMENTS}

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdate, current_user: Dict[str, Any] = Depends(require_admin_access)):
    """Update user information (Admin/Superuser only)"""
    updated_user = EnterpriseUserManager.update_user(user_id, user_data)
    return UserResponse(**{k: v for k, v in updated_user.items() if k != "hashed_password"})

@router.delete("/{user_id}")
async def delete_user(user_id: int, current_user: Dict[str, Any] = Depends(require_admin_access)):
    """Deactivate user (Admin/Superuser only)"""
    success = EnterpriseUserManager.delete_user(user_id)
    if success:
        return {"message": "User deactivated successfully"}
    raise HTTPException(status_code=404, detail="User not found")

@router.post("/research-groups")
async def create_research_group(
    name: str, 
    description: str, 
    business_focus: str,
    current_user: Dict[str, Any] = Depends(require_admin_access)
):
    """Create business group"""
    group = EnterpriseUserManager.create_business_group(
        name, description, current_user["username"], business_focus
    )
    return group

@router.get("/analytics")
async def get_business_analytics(current_user: Dict[str, Any] = Depends(require_admin_access)):
    """Get business platform analytics"""
    return BusinessActivityLogger.get_business_analytics()

# Initialize some default users for testing
def initialize_default_users():
    """Create default users for testing the system"""
    if not EnterpriseUserManager.users_db:
        # Create superuser
        superuser_data = UserCreate(
            username="admin",
            email="admin@rnrsolutions.com",
            password="admin123",
            full_name="System Administrator",
            role=UserRole.SUPERUSER,
            department="Information Technology"
        )
        EnterpriseUserManager.create_user(superuser_data)
        
        # Create manager
        manager_data = UserCreate(
            username="manager_jones",
            email="manager.jones@rnrsolutions.com",
            password="manager123",
            full_name="John Jones",
            role=UserRole.ADMIN,
            department="Operations and Manufacturing"
        )
        EnterpriseUserManager.create_user(manager_data)
        
        # Create operator
        operator_data = UserCreate(
            username="operator001",
            email="operator001@rnrsolutions.com",
            password="operator123",
            full_name="Jane Doe",
            role=UserRole.OPERATOR,
            employee_id="OPS2025001",
            business_area="Industrial Automation",
            department="Operations and Manufacturing",
            manager="John Jones"
        )
        EnterpriseUserManager.create_user(operator_data)

# Call initialization
initialize_default_users()

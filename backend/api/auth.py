from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
import jwt
import bcrypt
import json
from enum import Enum

router = APIRouter(tags=["authentication"])
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = "rnr_iot_enterprise_platform_secret_key_2025"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours for enterprise sessions

class UserRole(str, Enum):
    SUPERUSER = "superuser"
    ADMIN = "admin"
    OPERATOR = "operator"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    employee_id: Optional[str] = None
    department: str
    role: UserRole = UserRole.OPERATOR
    business_area: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    business_area: Optional[str] = None
    status: Optional[UserStatus] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    student_id: Optional[str]
    department: str
    role: UserRole
    status: UserStatus
    research_area: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    login_count: int

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
    expires_in: int

# Mock Database - In production, replace with actual database
users_db = [
    {
        "id": 1,
        "username": "admin",
        "email": "admin@university.edu",
        "password": bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "full_name": "System Administrator",
        "student_id": None,
        "department": "Computer Science",
        "role": UserRole.SUPERUSER,
        "status": UserStatus.ACTIVE,
        "research_area": "IoT Systems",
        "created_at": datetime.now(),
        "last_login": None,
        "login_count": 0
    },
    {
        "id": 2,
        "username": "prof_smith",
        "email": "smith@university.edu",
        "password": bcrypt.hashpw("prof123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "full_name": "Dr. John Smith",
        "student_id": None,
        "department": "Engineering",
        "role": UserRole.ADMIN,
        "status": UserStatus.ACTIVE,
        "research_area": "Smart Agriculture",
        "created_at": datetime.now(),
        "last_login": None,
        "login_count": 0
    },
    {
        "id": 3,
        "username": "operator_alice",
        "email": "alice@rnrsolutions.com",
        "password": bcrypt.hashpw("operator123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "full_name": "Alice Johnson",
        "employee_id": "EMP2025001",
        "department": "Computer Science",
        "role": UserRole.OPERATOR,
        "status": UserStatus.ACTIVE,
        "business_area": "Water Management Systems",
        "created_at": datetime.now(),
        "last_login": None,
        "login_count": 0
    }
]

activity_logs = []

# Utility Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_username(username: str):
    return next((user for user in users_db if user["username"] == username), None)

def get_user_by_id(user_id: int):
    return next((user for user in users_db if user["id"] == user_id), None)

def log_activity(user_id: int, action: str, details: str):
    activity_logs.append({
        "id": len(activity_logs) + 1,
        "user_id": user_id,
        "action": action,
        "details": details,
        "timestamp": datetime.now(),
        "ip_address": "127.0.0.1"  # In production, get real IP
    })

# Authentication Dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    user = get_user_by_username(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if user["status"] != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    return user

# Role-based Access Control
def require_role(allowed_roles: List[UserRole]):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}"
            )
        return current_user
    return role_checker

# Authentication Routes
@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Login endpoint for university users"""
    user = get_user_by_username(user_credentials.username)
    
    if not user or not verify_password(user_credentials.password, user["password"]):
        log_activity(0, "LOGIN_FAILED", f"Failed login attempt for {user_credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if user["status"] != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active"
        )
    
    # Update login info
    user["last_login"] = datetime.now()
    user["login_count"] += 1
    
    # Create access token
    access_token = create_access_token(data={"sub": user["username"]})
    
    log_activity(user["id"], "LOGIN_SUCCESS", f"Successful login from {user['role']}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**{k: v for k, v in user.items() if k != "password"}),
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, current_user: dict = Depends(require_role([UserRole.SUPERUSER, UserRole.ADMIN]))):
    """Register new user (Admin/Superuser only)"""
    
    # Check if username exists
    if get_user_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user
    new_user = {
        "id": max([u["id"] for u in users_db]) + 1,
        "username": user_data.username,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "full_name": user_data.full_name,
        "student_id": user_data.student_id,
        "department": user_data.department,
        "role": user_data.role,
        "status": UserStatus.ACTIVE,
        "research_area": user_data.research_area,
        "created_at": datetime.now(),
        "last_login": None,
        "login_count": 0
    }
    
    users_db.append(new_user)
    
    log_activity(current_user["id"], "USER_CREATED", f"Created user {user_data.username} with role {user_data.role}")
    
    return UserResponse(**{k: v for k, v in new_user.items() if k != "password"})

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(**{k: v for k, v in current_user.items() if k != "password"})

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(current_user: dict = Depends(require_role([UserRole.SUPERUSER, UserRole.ADMIN]))):
    """Get all users (Admin/Superuser only)"""
    return [UserResponse(**{k: v for k, v in user.items() if k != "password"}) for user in users_db]

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, 
    user_update: UserUpdate, 
    current_user: dict = Depends(require_role([UserRole.SUPERUSER, UserRole.ADMIN]))
):
    """Update user information"""
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user data
    update_data = user_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        user[key] = value
    
    log_activity(current_user["id"], "USER_UPDATED", f"Updated user {user['username']}")
    
    return UserResponse(**{k: v for k, v in user.items() if k != "password"})

@router.get("/activity-logs")
async def get_activity_logs(current_user: dict = Depends(require_role([UserRole.SUPERUSER, UserRole.ADMIN]))):
    """Get system activity logs"""
    return {
        "logs": activity_logs[-100:],  # Last 100 activities
        "total": len(activity_logs)
    }

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout endpoint"""
    log_activity(current_user["id"], "LOGOUT", f"User logged out")
    return {"message": "Successfully logged out"}

# System Statistics
@router.get("/stats")
async def get_system_stats(current_user: dict = Depends(require_role([UserRole.SUPERUSER, UserRole.ADMIN]))):
    """Get system statistics"""
    total_users = len(users_db)
    active_users = len([u for u in users_db if u["status"] == UserStatus.ACTIVE])
    operators = len([u for u in users_db if u["role"] == UserRole.OPERATOR])
    admins = len([u for u in users_db if u["role"] == UserRole.ADMIN])
    superusers = len([u for u in users_db if u["role"] == UserRole.SUPERUSER])
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "operators": operators,
        "admins": admins,
        "superusers": superusers,
        "total_activities": len(activity_logs),
        "system_uptime": datetime.now() - datetime(2025, 7, 28)
    }

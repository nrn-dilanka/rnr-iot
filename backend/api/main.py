import os
import logging
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from api.database import engine, Base, get_db
from api.routes import router
from api.water_routes import router as water_router
from api.greenhouse_routes import router as greenhouse_router
from api.websocket import websocket_manager
from api.services import get_sensor_data_service, SensorDataService
from api.esp32_manager import esp32_device_manager
from api.auth import router as auth_router
from api.user_management import router as user_router
from api.permissions import BusinessActivityLogger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting RNR Solutions IoT Platform API Server...")
    logger.info("Enterprise IoT Platform v2.0.0")
    logger.info("© 2025 RNR Solutions. All rights reserved.")
    
    # Initialize ESP32 Device Manager
    await esp32_device_manager.initialize()
    
    yield
    
    # Shutdown
    logger.info("Shutting down RNR Solutions IoT Platform API Server...")
    logger.info("ESP32 Device Manager stopped")

# Create FastAPI app
app = FastAPI(
    title="RNR Solutions IoT Platform",
    description="Enterprise-grade IoT monitoring and management platform developed by RNR Solutions. Comprehensive device management, real-time monitoring, and advanced analytics for industrial IoT applications.",
    version="2.0.0",
    openapi_version="3.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "RNR Solutions Support",
        "email": "support@rnrsolutions.com",
        "url": "https://www.rnrsolutions.com"
    },
    license_info={
        "name": "Proprietary License",
        "url": "https://www.rnrsolutions.com/license",
    },
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth_router, prefix="/api/auth")
app.include_router(user_router, prefix="/api")
app.include_router(router, prefix="/api")
app.include_router(water_router, prefix="/api")
app.include_router(greenhouse_router, prefix="/api")

# Serve uploaded files
upload_dir = os.getenv("UPLOAD_DIR", "/app/uploads")
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RNR Solutions IoT Platform",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Multi-user authentication",
            "Role-based access control",
            "Real-time IoT monitoring",
            "Advanced industrial automation",
            "Environmental monitoring",
            "AI-powered analytics",
            "Environmental monitoring",
            "Business intelligence",
            "Enterprise collaboration tools"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "platform": "enterprise_iot"}

@app.get("/openapi.json")
async def get_openapi():
    """Custom OpenAPI JSON endpoint"""
    return app.openapi()

@app.get("/api/platform/stats")
async def get_platform_stats():
    """Get platform statistics for business analytics"""
    analytics = BusinessActivityLogger.get_business_analytics()
    return {
        "platform_stats": analytics,
        "active_systems": ["water_management", "sensor_monitoring", "esp32_devices"],
        "business_areas": ["Industrial Automation", "IoT Systems Integration", "Environmental Monitoring"]
    }

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    sensor_data_service: SensorDataService = Depends(get_sensor_data_service)
):
    """WebSocket endpoint for real-time communication"""
    await websocket_manager.connect(websocket)
    
    try:
        # Send initial data to the client
        recent_data = sensor_data_service.get_sensor_data(limit=10)
        for data in recent_data:
            await websocket_manager.send_personal_message({
                "type": "sensor_data",
                "node_id": data.node_id,
                "data": data.data,
                "timestamp": data.received_at.isoformat()
            }, websocket)
        
        # Keep the connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                # Handle client messages if needed
                logger.info(f"Received WebSocket message: {data}")
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        websocket_manager.disconnect(websocket)

# Internal API endpoints for broadcasting
@app.post("/api/internal/broadcast")
async def broadcast_message(message: dict):
    """Internal endpoint for broadcasting messages to WebSocket clients"""
    try:
        await websocket_manager.broadcast(message)
        return {"status": "success", "message": "Message broadcasted"}
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/internal/broadcast/sensor-data")
async def broadcast_sensor_data(data: dict):
    """Internal endpoint specifically for sensor data broadcasting"""
    try:
        node_id = data.get("node_id")
        sensor_data = data.get("data", {})
        
        if node_id:
            await websocket_manager.send_sensor_data_update(node_id, sensor_data)
            return {"status": "success", "message": f"Sensor data broadcasted for node {node_id}"}
        else:
            return {"status": "error", "message": "node_id is required"}
    except Exception as e:
        logger.error(f"Error broadcasting sensor data: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

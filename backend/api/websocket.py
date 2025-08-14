import os
import json
import logging
from typing import List, Dict, Any, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.node_subscribers: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept a WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from node subscriptions
        for node_id, subscribers in self.node_subscribers.items():
            if websocket in subscribers:
                subscribers.remove(websocket)
        
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected WebSockets"""
        if not self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_to_node_subscribers(self, node_id: str, message: Dict[str, Any]):
        """Broadcast a message to subscribers of a specific node"""
        if node_id not in self.node_subscribers:
            return
        
        message_str = json.dumps(message)
        disconnected = []
        
        for connection in self.node_subscribers[node_id]:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Error broadcasting to node subscriber: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            if connection in self.node_subscribers[node_id]:
                self.node_subscribers[node_id].remove(connection)
    
    def subscribe_to_node(self, websocket: WebSocket, node_id: str):
        """Subscribe a WebSocket to updates from a specific node"""
        if node_id not in self.node_subscribers:
            self.node_subscribers[node_id] = set()
        self.node_subscribers[node_id].add(websocket)
    
    def unsubscribe_from_node(self, websocket: WebSocket, node_id: str):
        """Unsubscribe a WebSocket from updates from a specific node"""
        if node_id in self.node_subscribers and websocket in self.node_subscribers[node_id]:
            self.node_subscribers[node_id].remove(websocket)
    
    async def send_sensor_data_update(self, node_id: str, sensor_data: Dict[str, Any]):
        """Send sensor data update to all connected clients"""
        message = {
            "type": "sensor_data",
            "node_id": node_id,
            "data": sensor_data,
            "timestamp": sensor_data.get("timestamp", "")
        }
        await self.broadcast(message)
    
    async def send_node_status_update(self, node_id: str, status: str):
        """Send node status update to all connected clients"""
        message = {
            "type": "node_status",
            "node_id": node_id,
            "status": status
        }
        await self.broadcast(message)
    
    async def send_water_system_update(self, system_id: int, system_data: Dict[str, Any]):
        """Send water system update to all connected clients"""
        message = {
            "type": "water_system_update",
            "system_id": system_id,
            "data": system_data,
            "timestamp": system_data.get("updated_at", "")
        }
        await self.broadcast(message)
    
    async def send_water_schedule_update(self, schedule_id: int, schedule_data: Dict[str, Any]):
        """Send water schedule update to all connected clients"""
        message = {
            "type": "water_schedule_update",
            "schedule_id": schedule_id,
            "data": schedule_data,
            "timestamp": schedule_data.get("updated_at", "")
        }
        await self.broadcast(message)
    
    async def send_water_alert(self, alert_data: Dict[str, Any]):
        """Send water alert to all connected clients"""
        message = {
            "type": "water_alert",
            "data": alert_data,
            "timestamp": alert_data.get("timestamp", "")
        }
        await self.broadcast(message)
    
    async def send_water_usage_update(self, usage_data: Dict[str, Any]):
        """Send water usage analytics update to all connected clients"""
        message = {
            "type": "water_usage_update",
            "data": usage_data,
            "timestamp": usage_data.get("timestamp", "")
        }
        await self.broadcast(message)
    
    # Enhanced WebSocket methods for greenhouse features
    async def send_environmental_update(self, zone_id: int, sensor_type: str, value: float, unit: str, quality_score: float = 1.0):
        """Send environmental sensor update for a specific zone"""
        from datetime import datetime
        message = {
            "type": "environmental_update",
            "zone_id": zone_id,
            "sensor_type": sensor_type,
            "value": value,
            "unit": unit,
            "quality_score": quality_score,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)

    async def send_crop_growth_update(self, zone_id: int, growth_data: Dict[str, Any]):
        """Send crop growth tracking update"""
        from datetime import datetime
        message = {
            "type": "crop_growth_update",
            "zone_id": zone_id,
            "data": growth_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)

    async def send_system_alert(self, alert_data: Dict[str, Any]):
        """Send system alert to all connected clients"""
        from datetime import datetime
        message = {
            "type": "system_alert",
            "data": alert_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)

    async def send_automation_trigger(self, rule_id: int, rule_name: str, actions_taken: List[Dict[str, Any]]):
        """Send automation rule trigger notification"""
        from datetime import datetime
        message = {
            "type": "automation_trigger",
            "rule_id": rule_id,
            "rule_name": rule_name,
            "actions_taken": actions_taken,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)

    async def send_yield_prediction_update(self, zone_id: int, prediction_data: Dict[str, Any]):
        """Send updated yield prediction"""
        from datetime import datetime
        message = {
            "type": "yield_prediction_update",
            "zone_id": zone_id,
            "data": prediction_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)

    async def send_energy_update(self, energy_data: Dict[str, Any]):
        """Send energy monitoring update"""
        from datetime import datetime
        message = {
            "type": "energy_update",
            "data": energy_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)

    async def send_weather_update(self, weather_data: Dict[str, Any]):
        """Send weather data update"""
        from datetime import datetime
        message = {
            "type": "weather_update",
            "data": weather_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)

    async def send_device_discovery_update(self, discovered_devices: List[Dict[str, Any]]):
        """Send IoT device discovery update"""
        from datetime import datetime
        message = {
            "type": "device_discovery_update",
            "devices": discovered_devices,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)

    async def send_analytics_export_complete(self, export_id: int, export_data: Dict[str, Any]):
        """Send analytics data export completion notification"""
        from datetime import datetime
        message = {
            "type": "analytics_export_complete",
            "export_id": export_id,
            "data": export_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

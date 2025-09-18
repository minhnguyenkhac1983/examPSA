"""
Equilibrium WebSocket Service for Real-time Updates
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import random
import time
from typing import List, Dict
import uvicorn

app = FastAPI(title="Equilibrium WebSocket Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.pricing_connections: List[WebSocket] = []
        self.heatmap_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, connection_type: str = "general"):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if connection_type == "pricing":
            self.pricing_connections.append(websocket)
        elif connection_type == "heatmap":
            self.heatmap_connections.append(websocket)
        
        print(f"New {connection_type} connection established. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, connection_type: str = "general"):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if connection_type == "pricing" and websocket in self.pricing_connections:
            self.pricing_connections.remove(websocket)
        elif connection_type == "heatmap" and websocket in self.heatmap_connections:
            self.heatmap_connections.remove(websocket)
        
        print(f"{connection_type} connection closed. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)

    async def broadcast_pricing_update(self, message: dict):
        if self.pricing_connections:
            message_str = json.dumps(message)
            disconnected = []
            for connection in self.pricing_connections:
                try:
                    await connection.send_text(message_str)
                except:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                self.disconnect(conn, "pricing")

    async def broadcast_heatmap_update(self, message: dict):
        if self.heatmap_connections:
            message_str = json.dumps(message)
            disconnected = []
            for connection in self.heatmap_connections:
                try:
                    await connection.send_text(message_str)
                except:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                self.disconnect(conn, "heatmap")

manager = ConnectionManager()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "websocket-service",
        "version": "1.0.0",
        "active_connections": len(manager.active_connections),
        "pricing_connections": len(manager.pricing_connections),
        "heatmap_connections": len(manager.heatmap_connections)
    }

@app.websocket("/ws/pricing")
async def websocket_pricing_endpoint(websocket: WebSocket):
    await manager.connect(websocket, "pricing")
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "pricing")

@app.websocket("/ws/heatmap")
async def websocket_heatmap_endpoint(websocket: WebSocket):
    await manager.connect(websocket, "heatmap")
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "heatmap")

@app.websocket("/ws/general")
async def websocket_general_endpoint(websocket: WebSocket):
    await manager.connect(websocket, "general")
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back the message
            await manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "general")

# Background task for generating real-time updates
async def generate_pricing_updates():
    """Generate real-time pricing updates"""
    while True:
        try:
            # Simulate pricing updates
            pricing_update = {
                "type": "pricing_update",
                "timestamp": time.time(),
                "data": {
                    "zone_id": random.choice(["downtown_financial", "stadium_area", "airport"]),
                    "surge_multiplier": round(random.uniform(1.0, 3.0), 2),
                    "demand_level": random.choice(["low", "medium", "high", "very_high"]),
                    "supply_count": random.randint(5, 30),
                    "demand_count": random.randint(10, 50)
                }
            }
            
            await manager.broadcast_pricing_update(pricing_update)
            await asyncio.sleep(5)  # Update every 5 seconds
            
        except Exception as e:
            print(f"Error in pricing updates: {e}")
            await asyncio.sleep(5)

async def generate_heatmap_updates():
    """Generate real-time heatmap updates"""
    while True:
        try:
            # Simulate heatmap updates
            heatmap_update = {
                "type": "heatmap_update",
                "timestamp": time.time(),
                "data": {
                    "zones": [
                        {
                            "zone_id": "downtown_financial",
                            "zone_name": "Downtown Financial District",
                            "center": {"latitude": 37.7749, "longitude": -122.4194},
                            "surge_multiplier": round(random.uniform(1.0, 2.5), 2),
                            "demand_level": random.choice(["medium", "high", "very_high"]),
                            "supply_count": random.randint(10, 25),
                            "demand_count": random.randint(15, 40),
                            "color": "#ff6b6b"
                        },
                        {
                            "zone_id": "stadium_area",
                            "zone_name": "Stadium Area",
                            "center": {"latitude": 37.7786, "longitude": -122.3893},
                            "surge_multiplier": round(random.uniform(1.5, 3.0), 2),
                            "demand_level": random.choice(["high", "very_high"]),
                            "supply_count": random.randint(3, 15),
                            "demand_count": random.randint(20, 50),
                            "color": "#ff4757"
                        },
                        {
                            "zone_id": "airport",
                            "zone_name": "San Francisco Airport",
                            "center": {"latitude": 37.6213, "longitude": -122.3790},
                            "surge_multiplier": round(random.uniform(1.0, 1.5), 2),
                            "demand_level": random.choice(["low", "medium", "high"]),
                            "supply_count": random.randint(20, 35),
                            "demand_count": random.randint(8, 25),
                            "color": "#2ed573"
                        }
                    ]
                }
            }
            
            await manager.broadcast_heatmap_update(heatmap_update)
            await asyncio.sleep(10)  # Update every 10 seconds
            
        except Exception as e:
            print(f"Error in heatmap updates: {e}")
            await asyncio.sleep(10)

@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    asyncio.create_task(generate_pricing_updates())
    asyncio.create_task(generate_heatmap_updates())
    print("WebSocket service started with background tasks")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)

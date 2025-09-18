"""
Equilibrium Push Notification Service
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional

app = FastAPI(title="Equilibrium Notification Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class NotificationRequest(BaseModel):
    user_id: str
    title: str
    message: str
    notification_type: str = "info"
    data: Optional[Dict] = None
    priority: str = "normal"

class NotificationResponse(BaseModel):
    notification_id: str
    status: str
    sent_at: str
    delivery_status: str

class DeviceToken(BaseModel):
    user_id: str
    device_token: str
    platform: str  # ios, android, web
    is_active: bool = True

# In-memory storage (in production, use database)
notifications_db = []
device_tokens_db = {}

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "notification-service",
        "version": "1.0.0",
        "total_notifications": len(notifications_db),
        "registered_devices": len(device_tokens_db)
    }

@app.post("/api/v1/notifications/register-device")
async def register_device(device: DeviceToken):
    """Register device for push notifications"""
    device_tokens_db[device.user_id] = {
        "device_token": device.device_token,
        "platform": device.platform,
        "is_active": device.is_active,
        "registered_at": datetime.now().isoformat()
    }
    
    return {
        "status": "success",
        "message": f"Device registered for user {device.user_id}",
        "platform": device.platform
    }

@app.post("/api/v1/notifications/send", response_model=NotificationResponse)
async def send_notification(request: NotificationRequest):
    """Send push notification"""
    notification_id = f"notif_{len(notifications_db) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Check if user has registered device
    if request.user_id not in device_tokens_db:
        raise HTTPException(
            status_code=404,
            detail=f"No device registered for user {request.user_id}"
        )
    
    device_info = device_tokens_db[request.user_id]
    
    # Simulate sending notification
    notification = {
        "notification_id": notification_id,
        "user_id": request.user_id,
        "title": request.title,
        "message": request.message,
        "notification_type": request.notification_type,
        "data": request.data or {},
        "priority": request.priority,
        "platform": device_info["platform"],
        "sent_at": datetime.now().isoformat(),
        "delivery_status": "sent"
    }
    
    notifications_db.append(notification)
    
    return NotificationResponse(
        notification_id=notification_id,
        status="sent",
        sent_at=notification["sent_at"],
        delivery_status="sent"
    )

@app.post("/api/v1/notifications/send-bulk")
async def send_bulk_notifications(requests: List[NotificationRequest]):
    """Send bulk notifications"""
    results = []
    
    for request in requests:
        try:
            notification_id = f"notif_{len(notifications_db) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if request.user_id not in device_tokens_db:
                results.append({
                    "user_id": request.user_id,
                    "status": "failed",
                    "error": "Device not registered"
                })
                continue
            
            device_info = device_tokens_db[request.user_id]
            
            notification = {
                "notification_id": notification_id,
                "user_id": request.user_id,
                "title": request.title,
                "message": request.message,
                "notification_type": request.notification_type,
                "data": request.data or {},
                "priority": request.priority,
                "platform": device_info["platform"],
                "sent_at": datetime.now().isoformat(),
                "delivery_status": "sent"
            }
            
            notifications_db.append(notification)
            
            results.append({
                "user_id": request.user_id,
                "notification_id": notification_id,
                "status": "sent",
                "sent_at": notification["sent_at"]
            })
            
        except Exception as e:
            results.append({
                "user_id": request.user_id,
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "results": results,
        "total_sent": len([r for r in results if r["status"] == "sent"]),
        "total_failed": len([r for r in results if r["status"] == "failed"])
    }

@app.get("/api/v1/notifications/history/{user_id}")
async def get_notification_history(user_id: str, limit: int = 50):
    """Get notification history for user"""
    user_notifications = [
        n for n in notifications_db 
        if n["user_id"] == user_id
    ]
    
    # Sort by sent_at descending and limit
    user_notifications.sort(key=lambda x: x["sent_at"], reverse=True)
    user_notifications = user_notifications[:limit]
    
    return {
        "user_id": user_id,
        "notifications": user_notifications,
        "total": len(user_notifications)
    }

@app.get("/api/v1/notifications/stats")
async def get_notification_stats():
    """Get notification statistics"""
    total_notifications = len(notifications_db)
    
    # Count by type
    type_counts = {}
    for notification in notifications_db:
        notif_type = notification["notification_type"]
        type_counts[notif_type] = type_counts.get(notif_type, 0) + 1
    
    # Count by platform
    platform_counts = {}
    for notification in notifications_db:
        platform = notification["platform"]
        platform_counts[platform] = platform_counts.get(platform, 0) + 1
    
    return {
        "total_notifications": total_notifications,
        "by_type": type_counts,
        "by_platform": platform_counts,
        "registered_devices": len(device_tokens_db),
        "active_devices": len([d for d in device_tokens_db.values() if d["is_active"]])
    }

@app.delete("/api/v1/notifications/device/{user_id}")
async def unregister_device(user_id: str):
    """Unregister device for user"""
    if user_id not in device_tokens_db:
        raise HTTPException(
            status_code=404,
            detail=f"No device registered for user {user_id}"
        )
    
    del device_tokens_db[user_id]
    
    return {
        "status": "success",
        "message": f"Device unregistered for user {user_id}"
    }

# Background task for sending scheduled notifications
async def send_scheduled_notifications():
    """Send scheduled notifications (placeholder for future implementation)"""
    while True:
        try:
            # Placeholder for scheduled notification logic
            await asyncio.sleep(60)  # Check every minute
        except Exception as e:
            print(f"Error in scheduled notifications: {e}")
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    asyncio.create_task(send_scheduled_notifications())
    print("Notification service started with background tasks")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008)

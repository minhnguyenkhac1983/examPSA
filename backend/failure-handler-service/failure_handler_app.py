"""
Equilibrium Failure Handler Service
Handles system failures and graceful degradation
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import time
import json
import redis.asyncio as redis
import asyncpg
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Equilibrium Failure Handler Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ComponentStatus(BaseModel):
    component: str
    status: str  # healthy, degraded, failed
    last_check: datetime
    response_time_ms: float
    error_message: Optional[str] = None
    fallback_active: bool = False

class SystemMode(BaseModel):
    mode: str  # normal, degraded, emergency
    timestamp: datetime
    active_failures: List[str]
    performance_impact: Dict[str, float]

class FailureEvent(BaseModel):
    component: str
    failure_type: str
    severity: str  # low, medium, high, critical
    timestamp: datetime
    description: str
    recovery_attempts: int = 0

# Global variables
redis_client: Optional[redis.Redis] = None
postgres_pool: Optional[asyncpg.Pool] = None
system_mode = "normal"
failure_history = []
component_statuses = {}

# System mode configurations
SYSTEM_MODES = {
    "normal": {
        "max_response_time_ms": 100,
        "min_availability": 99.9,
        "features_enabled": ["realtime", "analytics", "ml_pricing", "notifications"]
    },
    "degraded": {
        "max_response_time_ms": 500,
        "min_availability": 99.0,
        "features_enabled": ["basic_pricing", "cached_data", "notifications"]
    },
    "emergency": {
        "max_response_time_ms": 2000,
        "min_availability": 95.0,
        "features_enabled": ["default_pricing", "basic_auth"]
    }
}

class FailureDetector:
    def __init__(self):
        self.redis_client = redis_client
        self.postgres_pool = postgres_pool
        self.failure_thresholds = {
            "redis": {"timeout": 1.0, "max_failures": 3},
            "database": {"timeout": 2.0, "max_failures": 3},
            "kafka": {"timeout": 3.0, "max_failures": 2},
            "api_gateway": {"timeout": 1.0, "max_failures": 3}
        }
        self.failure_counts = {}
        self.last_failure_times = {}
    
    async def check_component_health(self, component: str) -> ComponentStatus:
        """Check health of a specific component"""
        start_time = time.time()
        
        try:
            if component == "redis":
                status = await self._check_redis_health()
            elif component == "database":
                status = await self._check_database_health()
            elif component == "kafka":
                status = await self._check_kafka_health()
            elif component == "api_gateway":
                status = await self._check_api_gateway_health()
            else:
                status = {"healthy": False, "error": "Unknown component"}
            
            response_time = (time.time() - start_time) * 1000
            
            if status["healthy"]:
                self.failure_counts[component] = 0
                return ComponentStatus(
                    component=component,
                    status="healthy",
                    last_check=datetime.now(),
                    response_time_ms=response_time,
                    fallback_active=False
                )
            else:
                self.failure_counts[component] = self.failure_counts.get(component, 0) + 1
                self.last_failure_times[component] = datetime.now()
                
                # Determine if fallback should be active
                fallback_active = self.failure_counts[component] >= self.failure_thresholds[component]["max_failures"]
                
                return ComponentStatus(
                    component=component,
                    status="failed" if fallback_active else "degraded",
                    last_check=datetime.now(),
                    response_time_ms=response_time,
                    error_message=status.get("error"),
                    fallback_active=fallback_active
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentStatus(
                component=component,
                status="failed",
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_message=str(e),
                fallback_active=True
            )
    
    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            await self.redis_client.ping()
            await self.redis_client.set("health_check", "ok", ex=10)
            value = await self.redis_client.get("health_check")
            return {"healthy": value == "ok"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            async with self.postgres_pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                return {"healthy": result == 1}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_kafka_health(self) -> Dict[str, Any]:
        """Check Kafka health (simplified)"""
        try:
            # This would typically check Kafka connectivity
            # For demo purposes, we'll simulate a check
            await asyncio.sleep(0.1)
            return {"healthy": True}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_api_gateway_health(self) -> Dict[str, Any]:
        """Check API Gateway health"""
        try:
            # This would typically make an HTTP request to the gateway
            # For demo purposes, we'll simulate a check
            await asyncio.sleep(0.1)
            return {"healthy": True}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

class SystemModeManager:
    def __init__(self, failure_detector: FailureDetector):
        self.failure_detector = failure_detector
        self.current_mode = "normal"
        self.mode_change_history = []
    
    async def evaluate_system_mode(self) -> SystemMode:
        """Evaluate current system mode based on component health"""
        components = ["redis", "database", "kafka", "api_gateway"]
        failed_components = []
        degraded_components = []
        
        # Check all components
        for component in components:
            status = await self.failure_detector.check_component_health(component)
            component_statuses[component] = status
            
            if status.status == "failed":
                failed_components.append(component)
            elif status.status == "degraded":
                degraded_components.append(component)
        
        # Determine system mode
        if len(failed_components) == 0 and len(degraded_components) == 0:
            new_mode = "normal"
        elif len(failed_components) <= 1:
            new_mode = "degraded"
        else:
            new_mode = "emergency"
        
        # Update mode if changed
        if new_mode != self.current_mode:
            await self._change_system_mode(new_mode, failed_components + degraded_components)
        
        # Calculate performance impact
        performance_impact = self._calculate_performance_impact()
        
        return SystemMode(
            mode=self.current_mode,
            timestamp=datetime.now(),
            active_failures=failed_components + degraded_components,
            performance_impact=performance_impact
        )
    
    async def _change_system_mode(self, new_mode: str, failed_components: List[str]):
        """Change system mode and implement appropriate strategies"""
        old_mode = self.current_mode
        self.current_mode = new_mode
        
        mode_change = {
            "from": old_mode,
            "to": new_mode,
            "timestamp": datetime.now(),
            "triggered_by": failed_components
        }
        
        self.mode_change_history.append(mode_change)
        
        # Implement mode-specific strategies
        await self._implement_mode_strategies(new_mode)
        
        # Log mode change
        logger.critical(f"System mode changed: {old_mode} -> {new_mode}, triggered by: {failed_components}")
        
        # Store in Redis for other services
        try:
            if redis_client:
                await redis_client.setex(
                    "system_mode", 
                    3600,  # 1 hour TTL
                    json.dumps(mode_change, default=str)
                )
        except Exception as e:
            logger.error(f"Failed to store system mode in Redis: {e}")
    
    async def _implement_mode_strategies(self, mode: str):
        """Implement strategies for the new system mode"""
        if mode == "degraded":
            await self._enable_degraded_mode()
        elif mode == "emergency":
            await self._enable_emergency_mode()
        elif mode == "normal":
            await self._enable_normal_mode()
    
    async def _enable_degraded_mode(self):
        """Enable degraded mode strategies"""
        logger.info("Enabling degraded mode strategies")
        
        # Increase cache TTL
        try:
            if redis_client:
                await redis_client.setex("degraded_mode", 3600, "true")
        except Exception as e:
            logger.error(f"Failed to set degraded mode flag: {e}")
    
    async def _enable_emergency_mode(self):
        """Enable emergency mode strategies"""
        logger.critical("Enabling emergency mode strategies")
        
        # Set emergency pricing
        emergency_pricing = {
            "base_fare": 12.50,
            "surge_multiplier": 1.0,
            "confidence": 0.1,
            "mode": "emergency",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if redis_client:
                await redis_client.setex("emergency_pricing", 3600, json.dumps(emergency_pricing))
                await redis_client.setex("emergency_mode", 3600, "true")
        except Exception as e:
            logger.error(f"Failed to set emergency mode: {e}")
    
    async def _enable_normal_mode(self):
        """Enable normal mode strategies"""
        logger.info("Enabling normal mode strategies")
        
        try:
            if redis_client:
                await redis_client.delete("degraded_mode", "emergency_mode", "emergency_pricing")
        except Exception as e:
            logger.error(f"Failed to clear mode flags: {e}")
    
    def _calculate_performance_impact(self) -> Dict[str, float]:
        """Calculate performance impact of current mode"""
        current_config = SYSTEM_MODES[self.current_mode]
        normal_config = SYSTEM_MODES["normal"]
        
        return {
            "response_time_impact": (current_config["max_response_time_ms"] - normal_config["max_response_time_ms"]) / normal_config["max_response_time_ms"] * 100,
            "availability_impact": (normal_config["min_availability"] - current_config["min_availability"]) / normal_config["min_availability"] * 100,
            "feature_reduction": (len(normal_config["features_enabled"]) - len(current_config["features_enabled"])) / len(normal_config["features_enabled"]) * 100
        }

# Initialize failure detector and mode manager
failure_detector = FailureDetector()
mode_manager = SystemModeManager(failure_detector)

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "failure-handler-service",
        "version": "1.0.0",
        "system_mode": system_mode,
        "active_failures": len([c for c in component_statuses.values() if c.status == "failed"])
    }

@app.get("/api/v1/failure-handler/status")
async def get_system_status():
    """Get comprehensive system status"""
    system_mode_status = await mode_manager.evaluate_system_mode()
    
    return {
        "system_mode": system_mode_status,
        "component_statuses": {k: v.dict() for k, v in component_statuses.items()},
        "failure_history": failure_history[-10:],  # Last 10 failures
        "mode_change_history": mode_manager.mode_change_history[-5:]  # Last 5 mode changes
    }

@app.get("/api/v1/failure-handler/components/{component}")
async def get_component_status(component: str):
    """Get status of a specific component"""
    if component not in ["redis", "database", "kafka", "api_gateway"]:
        raise HTTPException(status_code=404, detail="Component not found")
    
    status = await failure_detector.check_component_health(component)
    return status.dict()

@app.post("/api/v1/failure-handler/test-failure")
async def test_failure_scenario(failure_event: FailureEvent):
    """Test failure scenario (for testing purposes)"""
    # Simulate a failure event
    failure_history.append({
        "component": failure_event.component,
        "failure_type": failure_event.failure_type,
        "severity": failure_event.severity,
        "timestamp": failure_event.timestamp,
        "description": failure_event.description,
        "recovery_attempts": failure_event.recovery_attempts
    })
    
    # Trigger system mode evaluation
    system_mode_status = await mode_manager.evaluate_system_mode()
    
    return {
        "message": "Failure scenario recorded",
        "system_mode": system_mode_status,
        "failure_event": failure_event.dict()
    }

@app.get("/api/v1/failure-handler/metrics")
async def get_failure_metrics():
    """Get failure handling metrics"""
    total_failures = len(failure_history)
    critical_failures = len([f for f in failure_history if f.get("severity") == "critical"])
    
    # Calculate failure rates by component
    component_failures = {}
    for failure in failure_history:
        component = failure.get("component", "unknown")
        component_failures[component] = component_failures.get(component, 0) + 1
    
    # Calculate mode distribution
    mode_distribution = {}
    for change in mode_manager.mode_change_history:
        mode = change.get("to", "unknown")
        mode_distribution[mode] = mode_distribution.get(mode, 0) + 1
    
    return {
        "total_failures": total_failures,
        "critical_failures": critical_failures,
        "component_failures": component_failures,
        "mode_distribution": mode_distribution,
        "current_mode": system_mode,
        "uptime_percentage": 99.9 - (critical_failures * 0.1),  # Simplified calculation
        "last_failure": failure_history[-1] if failure_history else None
    }

@app.post("/api/v1/failure-handler/recovery/{component}")
async def attempt_recovery(component: str):
    """Attempt to recover a failed component"""
    if component not in ["redis", "database", "kafka", "api_gateway"]:
        raise HTTPException(status_code=404, detail="Component not found")
    
    # Reset failure count for the component
    failure_detector.failure_counts[component] = 0
    
    # Check component health
    status = await failure_detector.check_component_health(component)
    
    # Re-evaluate system mode
    system_mode_status = await mode_manager.evaluate_system_mode()
    
    return {
        "component": component,
        "recovery_attempted": True,
        "current_status": status.dict(),
        "system_mode": system_mode_status
    }

# Background task for continuous monitoring
async def monitor_system_health():
    """Continuously monitor system health"""
    while True:
        try:
            await mode_manager.evaluate_system_mode()
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Error in health monitoring: {e}")
            await asyncio.sleep(60)  # Longer delay on error

@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    # Initialize Redis connection
    global redis_client
    try:
        redis_client = redis.from_url("redis://:equilibrium_secure_password@redis:6379/0", decode_responses=True)
        logger.info("Connected to Redis")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
    
    # Initialize PostgreSQL connection
    global postgres_pool
    try:
        postgres_pool = await asyncpg.create_pool(
            host="postgres",
            port=5432,
            database="equilibrium",
            user="equilibrium",
            password="equilibrium123",
            min_size=1,
            max_size=10
        )
        logger.info("Connected to PostgreSQL")
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
    
    # Start monitoring task
    asyncio.create_task(monitor_system_health())
    logger.info("Failure handler service started with health monitoring")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if redis_client:
        await redis_client.close()
    if postgres_pool:
        await postgres_pool.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)

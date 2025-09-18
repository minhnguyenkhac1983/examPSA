"""
Equilibrium Pricing Service
Real-time surge pricing calculation service
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import asyncio
import json
import time
import uuid
import hashlib
from datetime import datetime, timedelta
import redis.asyncio as redis
import asyncpg
from geopy.distance import geodesic
import logging
import uvicorn
from dataclasses import dataclass
import numpy as np
from scipy import stats

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pricing_service.log')
    ]
)
logger = logging.getLogger(__name__)

# Enums for better type safety
class VehicleType(str, Enum):
    STANDARD = "standard"
    PREMIUM = "premium"
    LUXURY = "luxury"
    SHARED = "shared"

class PricingAlgorithm(str, Enum):
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    ML_BASED = "ml_based"
    ADAPTIVE = "adaptive"

class SurgeLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"

app = FastAPI(
    title="Equilibrium Pricing Service",
    version="2.0.0",
    description="Advanced real-time surge pricing calculation service with ML integration",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enhanced middleware stack
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Global variables for demo
redis_client = None
db_pool = None

# Enhanced Pydantic models with validation
class Location(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    
    @validator('latitude', 'longitude')
    def validate_coordinates(cls, v):
        if abs(v) > 180:
            raise ValueError('Invalid coordinate value')
        return v

class PriceEstimateRequest(BaseModel):
    rider_id: str = Field(..., min_length=1, description="Unique rider identifier")
    pickup_location: Location = Field(..., description="Pickup location coordinates")
    dropoff_location: Location = Field(..., description="Dropoff location coordinates")
    vehicle_type: VehicleType = Field(default=VehicleType.STANDARD, description="Vehicle type")
    algorithm: PricingAlgorithm = Field(default=PricingAlgorithm.ADAPTIVE, description="Pricing algorithm")
    include_breakdown: bool = Field(default=False, description="Include fare breakdown")
    request_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional request metadata")
    request_timestamp: Optional[datetime] = Field(default=None, description="Request timestamp")
    
    class Config:
        use_enum_values = True

class FareBreakdown(BaseModel):
    base_fare: float = Field(..., description="Base fare amount")
    distance_fare: float = Field(..., description="Distance-based fare")
    time_fare: float = Field(..., description="Time-based fare")
    surge_fare: float = Field(..., description="Surge pricing amount")
    service_fee: float = Field(..., description="Service fee")
    taxes: float = Field(..., description="Taxes and fees")

class PriceEstimateResponse(BaseModel):
    estimate_id: str = Field(..., description="Unique estimate identifier")
    base_fare: float = Field(..., description="Base fare amount")
    surge_multiplier: float = Field(..., ge=1.0, le=5.0, description="Surge multiplier")
    final_fare: float = Field(..., ge=0, description="Final fare amount")
    currency: str = Field(default="USD", description="Currency code")
    expires_at: datetime = Field(..., description="Estimate expiration time")
    zone_id: str = Field(..., description="Zone identifier")
    estimated_duration: int = Field(..., ge=0, description="Estimated trip duration in minutes")
    estimated_distance: float = Field(..., ge=0, description="Estimated distance in kilometers")
    surge_level: SurgeLevel = Field(..., description="Surge level classification")
    confidence_score: float = Field(..., ge=0, le=1, description="Pricing confidence score")
    algorithm_used: PricingAlgorithm = Field(..., description="Algorithm used for pricing")
    breakdown: Optional[FareBreakdown] = Field(default=None, description="Detailed fare breakdown")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional pricing metadata")
    
    class Config:
        use_enum_values = True

class ZoneInfo(BaseModel):
    zone_id: str = Field(..., description="Zone identifier")
    zone_name: str = Field(..., description="Zone name")
    zone_type: str = Field(..., description="Zone type")
    base_fare: float = Field(..., description="Base fare for zone")
    maximum_surge: float = Field(..., description="Maximum surge multiplier")
    is_active: bool = Field(default=True, description="Zone active status")
    current_demand_level: str

class SurgeZone(BaseModel):
    zone_id: str
    zone_name: str
    city_id: str
    center_lat: float
    center_lng: float
    base_fare: float
    max_surge_multiplier: float = 5.0
    min_surge_multiplier: float = 1.0
    is_active: bool = True

# Demo data
DEMO_ZONES = {
    "downtown_financial": SurgeZone(
        zone_id="550e8400-e29b-41d4-a716-446655440001",
        zone_name="Downtown Financial District",
        city_id="550e8400-e29b-41d4-a716-446655440000",
        center_lat=37.7749,
        center_lng=-122.4194,
        base_fare=12.50,
        max_surge_multiplier=3.0
    ),
    "stadium_area": SurgeZone(
        zone_id="550e8400-e29b-41d4-a716-446655440002",
        zone_name="Stadium Area",
        city_id="550e8400-e29b-41d4-a716-446655440000",
        center_lat=37.7786,
        center_lng=-122.3893,
        base_fare=15.00,
        max_surge_multiplier=5.0
    ),
    "airport": SurgeZone(
        zone_id="550e8400-e29b-41d4-a716-446655440003",
        zone_name="San Francisco Airport",
        city_id="550e8400-e29b-41d4-a716-446655440000",
        center_lat=37.6213,
        center_lng=-122.3790,
        base_fare=25.00,
        max_surge_multiplier=2.5
    )
}

# Demo supply/demand data
DEMO_SUPPLY_DEMAND = {
    "downtown_financial": {"supply": 15, "demand": 8, "multiplier": 1.3},
    "stadium_area": {"supply": 5, "demand": 20, "multiplier": 2.8},
    "airport": {"supply": 25, "demand": 12, "multiplier": 1.1}
}

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    global redis_client, db_pool
    
    try:
        # Initialize Redis connection
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        redis_client.ping()
        logger.info("Connected to Redis")
        
        # Initialize database connection pool
        db_pool = await asyncpg.create_pool(
            "postgresql://equilibrium:equilibrium123@localhost:5432/equilibrium"
        )
        logger.info("Connected to PostgreSQL")
        
        # Initialize demo data
        await initialize_demo_data()
        
    except Exception as e:
        logger.error(f"Failed to initialize connections: {e}")

async def initialize_demo_data():
    """Initialize demo zones and supply/demand data"""
    try:
        # Store demo zones in Redis
        for zone_id, zone in DEMO_ZONES.items():
            zone_key = f"zone:{zone_id}"
            redis_client.hset(zone_key, mapping={
                "zone_id": zone.zone_id,
                "zone_name": zone.zone_name,
                "city_id": zone.city_id,
                "center_lat": str(zone.center_lat),
                "center_lng": str(zone.center_lng),
                "base_fare": str(zone.base_fare),
                "max_surge_multiplier": str(zone.max_surge_multiplier),
                "min_surge_multiplier": str(zone.min_surge_multiplier),
                "is_active": str(zone.is_active)
            })
        
        # Store demo supply/demand data
        for zone_id, data in DEMO_SUPPLY_DEMAND.items():
            sd_key = f"supply_demand:{zone_id}"
            redis_client.hset(sd_key, mapping={
                "supply": str(data["supply"]),
                "demand": str(data["demand"]),
                "multiplier": str(data["multiplier"]),
                "timestamp": str(int(time.time()))
            })
        
        logger.info("Demo data initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize demo data: {e}")

def find_zone_for_location(lat: float, lng: float) -> Optional[SurgeZone]:
    """Find the zone for a given location"""
    min_distance = float('inf')
    closest_zone = None
    
    for zone_id, zone in DEMO_ZONES.items():
        distance = geodesic(
            (lat, lng), 
            (zone.center_lat, zone.center_lng)
        ).kilometers
        
        if distance < min_distance and distance < 5.0:  # Within 5km
            min_distance = distance
            closest_zone = zone
    
    return closest_zone

def calculate_surge_multiplier(supply: int, demand: int) -> float:
    """Calculate surge multiplier based on supply and demand"""
    if supply == 0:
        return 5.0  # Maximum surge if no supply
    
    ratio = demand / supply
    
    if ratio <= 0.5:
        return 1.0
    elif ratio <= 1.0:
        return 1.0 + (ratio - 0.5) * 0.4  # 1.0 to 1.2
    elif ratio <= 1.5:
        return 1.2 + (ratio - 1.0) * 0.6  # 1.2 to 1.5
    elif ratio <= 2.0:
        return 1.5 + (ratio - 1.5) * 1.0  # 1.5 to 2.0
    else:
        return min(2.0 + (ratio - 2.0) * 0.5, 5.0)  # 2.0 to 5.0

def calculate_distance(pickup: Location, dropoff: Location) -> float:
    """Calculate distance between two points in kilometers"""
    return geodesic(
        (pickup.latitude, pickup.longitude),
        (dropoff.latitude, dropoff.longitude)
    ).kilometers

def calculate_duration(distance: float) -> int:
    """Calculate estimated duration in minutes"""
    # Assume average speed of 30 km/h in city
    return int((distance / 30) * 60)

@app.post("/api/v1/pricing/estimate", response_model=PriceEstimateResponse)
async def get_price_estimate(request: PriceEstimateRequest):
    """Get price estimate for a ride"""
    try:
        # Find zone for pickup location
        zone = find_zone_for_location(
            request.pickup_location.latitude,
            request.pickup_location.longitude
        )
        
        if not zone:
            raise HTTPException(status_code=404, detail="No zone found for location")
        
        # Get current supply/demand data
        sd_key = f"supply_demand:{zone.zone_id}"
        supply_demand = redis_client.hgetall(sd_key)
        
        if not supply_demand:
            # Use default values if no data available
            supply = 10
            demand = 5
            current_multiplier = 1.0
        else:
            supply = int(supply_demand.get("supply", 10))
            demand = int(supply_demand.get("demand", 5))
            current_multiplier = float(supply_demand.get("multiplier", 1.0))
        
        # Calculate surge multiplier
        surge_multiplier = calculate_surge_multiplier(supply, demand)
        
        # Ensure multiplier is within zone limits
        surge_multiplier = max(zone.min_surge_multiplier, 
                              min(surge_multiplier, zone.max_surge_multiplier))
        
        # Calculate distance and duration
        distance = calculate_distance(request.pickup_location, request.dropoff_location)
        duration = calculate_duration(distance)
        
        # Calculate final fare
        base_fare = zone.base_fare + (distance * 2.5)  # Base fare + distance rate
        final_fare = base_fare * surge_multiplier
        
        # Generate quote ID and validity
        quote_id = str(uuid.uuid4())
        quote_valid_until = datetime.now() + timedelta(seconds=30)
        
        # Determine demand level
        if surge_multiplier >= 2.0:
            demand_level = "extreme"
        elif surge_multiplier >= 1.5:
            demand_level = "high"
        elif surge_multiplier >= 1.2:
            demand_level = "medium"
        else:
            demand_level = "low"
        
        # Calculate confidence score
        confidence_score = min(0.95, 0.7 + (supply / max(demand, 1)) * 0.25)
        
        # Store quote in Redis for validation
        quote_key = f"quote:{quote_id}"
        redis_client.hset(quote_key, mapping={
            "rider_id": request.rider_id,
            "zone_id": zone.zone_id,
            "base_fare": str(base_fare),
            "surge_multiplier": str(surge_multiplier),
            "final_fare": str(final_fare),
            "quote_valid_until": quote_valid_until.isoformat(),
            "created_at": datetime.now().isoformat()
        })
        redis_client.expire(quote_key, 60)  # Expire after 1 minute
        
        # Log pricing event
        await log_pricing_event(quote_id, zone.zone_id, request.rider_id, 
                               base_fare, surge_multiplier, final_fare)
        
        response = PriceEstimateResponse(
            quote_id=quote_id,
            base_fare=round(base_fare, 2),
            surge_multiplier=round(surge_multiplier, 2),
            final_fare=round(final_fare, 2),
            quote_valid_until=quote_valid_until,
            estimated_duration=duration,
            estimated_distance=round(distance, 2),
            zone_info={
                "zone_id": zone.zone_id,
                "zone_name": zone.zone_name,
                "current_demand_level": demand_level
            },
            confidence_score=round(confidence_score, 2)
        )
        
        logger.info(f"Price estimate generated: {quote_id}, multiplier: {surge_multiplier}")
        return response
        
    except Exception as e:
        logger.error(f"Error generating price estimate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/pricing/quote/{quote_id}")
async def get_quote_status(quote_id: str):
    """Get status of a price quote"""
    try:
        quote_key = f"quote:{quote_id}"
        quote_data = redis_client.hgetall(quote_key)
        
        if not quote_data:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        quote_valid_until = datetime.fromisoformat(quote_data["quote_valid_until"])
        current_time = datetime.now()
        
        if current_time > quote_valid_until:
            status = "expired"
        else:
            status = "valid"
        
        return {
            "quote_id": quote_id,
            "status": status,
            "base_fare": float(quote_data["base_fare"]),
            "surge_multiplier": float(quote_data["surge_multiplier"]),
            "final_fare": float(quote_data["final_fare"]),
            "quote_valid_until": quote_valid_until.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting quote status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/pricing/quote/{quote_id}/confirm")
async def confirm_quote(quote_id: str):
    """Confirm a price quote"""
    try:
        quote_key = f"quote:{quote_id}"
        quote_data = redis_client.hgetall(quote_key)
        
        if not quote_data:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        quote_valid_until = datetime.fromisoformat(quote_data["quote_valid_until"])
        current_time = datetime.now()
        
        if current_time > quote_valid_until:
            raise HTTPException(status_code=400, detail="Quote has expired")
        
        # Mark quote as used
        redis_client.hset(quote_key, "status", "used")
        redis_client.hset(quote_key, "confirmed_at", current_time.isoformat())
        
        # Log ride completion
        await log_pricing_event(quote_id, quote_data["zone_id"], quote_data["rider_id"],
                               float(quote_data["base_fare"]), 
                               float(quote_data["surge_multiplier"]),
                               float(quote_data["final_fare"]),
                               event_type="ride_completed")
        
        return {
            "quote_id": quote_id,
            "status": "confirmed",
            "final_fare": float(quote_data["final_fare"]),
            "confirmed_at": current_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error confirming quote: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def log_pricing_event(quote_id: str, zone_id: str, rider_id: str, 
                           base_fare: float, surge_multiplier: float, 
                           final_fare: float, event_type: str = "price_quote"):
    """Log pricing event to database"""
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO pricing_event_logs 
                    (log_id, zone_id, rider_id, event_type, base_fare, 
                     surge_multiplier, final_fare, quote_timestamp)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, quote_id, zone_id, rider_id, event_type, base_fare,
                    surge_multiplier, final_fare, datetime.now())
    except Exception as e:
        logger.error(f"Failed to log pricing event: {e}")

@app.get("/api/v1/pricing/zones")
async def get_zones():
    """Get all active zones"""
    try:
        zones = []
        for zone_id in DEMO_ZONES.keys():
            zone_key = f"zone:{zone_id}"
            zone_data = redis_client.hgetall(zone_key)
            
            if zone_data:
                sd_key = f"supply_demand:{zone_id}"
                sd_data = redis_client.hgetall(sd_key)
                
                zone_info = {
                    "zone_id": zone_data["zone_id"],
                    "zone_name": zone_data["zone_name"],
                    "city_id": zone_data["city_id"],
                    "center_lat": float(zone_data["center_lat"]),
                    "center_lng": float(zone_data["center_lng"]),
                    "base_fare": float(zone_data["base_fare"]),
                    "max_surge_multiplier": float(zone_data["max_surge_multiplier"]),
                    "current_supply": int(sd_data.get("supply", 0)),
                    "current_demand": int(sd_data.get("demand", 0)),
                    "current_multiplier": float(sd_data.get("multiplier", 1.0)),
                    "is_active": zone_data["is_active"] == "True"
                }
                zones.append(zone_info)
        
        return {"zones": zones}
        
    except Exception as e:
        logger.error(f"Error getting zones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/pricing/zones/{zone_id}/supply-demand")
async def update_supply_demand(zone_id: str, supply: int, demand: int):
    """Update supply and demand for a zone (for demo purposes)"""
    try:
        if zone_id not in DEMO_ZONES:
            raise HTTPException(status_code=404, detail="Zone not found")
        
        # Calculate new surge multiplier
        surge_multiplier = calculate_surge_multiplier(supply, demand)
        zone = DEMO_ZONES[zone_id]
        surge_multiplier = max(zone.min_surge_multiplier, 
                              min(surge_multiplier, zone.max_surge_multiplier))
        
        # Update Redis
        sd_key = f"supply_demand:{zone_id}"
        redis_client.hset(sd_key, mapping={
            "supply": str(supply),
            "demand": str(demand),
            "multiplier": str(surge_multiplier),
            "timestamp": str(int(time.time()))
        })
        
        logger.info(f"Updated supply/demand for {zone_id}: supply={supply}, demand={demand}, multiplier={surge_multiplier}")
        
        return {
            "zone_id": zone_id,
            "supply": supply,
            "demand": demand,
            "surge_multiplier": round(surge_multiplier, 2),
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating supply/demand: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis connection
        redis_client.ping()
        
        # Check database connection
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "redis": "connected",
                "postgres": "connected"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

#!/usr/bin/env python3
"""
Equilibrium Platform - Geospatial Service
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from contextlib import asynccontextmanager

import asyncpg
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from geopy.distance import geodesic
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
redis_client: Optional[redis.Redis] = None
db_pool: Optional[asyncpg.Pool] = None

# Pydantic Models
class Location(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class Zone(BaseModel):
    zone_id: str
    zone_name: str
    center_lat: float
    center_lng: float
    radius_km: float
    is_active: bool = True

class ZoneRequest(BaseModel):
    location: Location
    radius_km: float = 5.0

class ZoneResponse(BaseModel):
    zones: List[Zone]
    total_zones: int
    timestamp: datetime

class DistanceRequest(BaseModel):
    from_location: Location
    to_location: Location

class DistanceResponse(BaseModel):
    distance_km: float
    distance_miles: float
    estimated_time_minutes: float
    timestamp: datetime

# Database connection
async def get_db_pool():
    global db_pool
    if db_pool is None:
        database_url = os.getenv(
            "DATABASE_URL", 
            "postgresql://equilibrium_user:equilibrium_secure_password@postgres:5432/equilibrium"
        )
        db_pool = await asyncpg.create_pool(database_url, min_size=5, max_size=20)
    return db_pool

async def get_redis():
    global redis_client
    if redis_client is None:
        redis_url = os.getenv(
            "REDIS_URL", 
            "redis://:equilibrium_secure_password@redis:6379/0"
        )
        redis_client = redis.from_url(redis_url, decode_responses=True)
    return redis_client

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Equilibrium Geospatial Service...")
    
    # Initialize database connection
    await get_db_pool()
    logger.info("✅ Connected to PostgreSQL")
    
    # Initialize Redis connection
    await get_redis()
    logger.info("✅ Connected to Redis")
    
    # Initialize demo zones
    await initialize_demo_zones()
    logger.info("✅ Demo zones initialized")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Geospatial Service...")
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()

# Create FastAPI app
app = FastAPI(
    title="Equilibrium Geospatial Service",
    description="Geospatial analysis and zone management for Equilibrium Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo zones data
DEMO_ZONES = [
    {
        "zone_id": "downtown_financial",
        "zone_name": "Downtown Financial District",
        "center_lat": 37.7749,
        "center_lng": -122.4194,
        "radius_km": 2.0
    },
    {
        "zone_id": "stadium_area",
        "zone_name": "Stadium Area",
        "center_lat": 37.7786,
        "center_lng": -122.3893,
        "radius_km": 1.5
    },
    {
        "zone_id": "airport",
        "zone_name": "San Francisco Airport",
        "center_lat": 37.6213,
        "center_lng": -122.3790,
        "radius_km": 3.0
    }
]

async def initialize_demo_zones():
    """Initialize demo zones in database"""
    try:
        pool = await get_db_pool()
        redis_conn = await get_redis()
        
        async with pool.acquire() as conn:
            # Create zones table if not exists
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS zones (
                    zone_id VARCHAR(50) PRIMARY KEY,
                    zone_name VARCHAR(100) NOT NULL,
                    center_lat DECIMAL(10, 8) NOT NULL,
                    center_lng DECIMAL(11, 8) NOT NULL,
                    radius_km DECIMAL(5, 2) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert demo zones
            for zone in DEMO_ZONES:
                await conn.execute("""
                    INSERT INTO zones (zone_id, zone_name, center_lat, center_lng, radius_km, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (zone_id) DO UPDATE SET
                        zone_name = EXCLUDED.zone_name,
                        center_lat = EXCLUDED.center_lat,
                        center_lng = EXCLUDED.center_lng,
                        radius_km = EXCLUDED.radius_km,
                        is_active = EXCLUDED.is_active,
                        updated_at = CURRENT_TIMESTAMP
                """, zone["zone_id"], zone["zone_name"], zone["center_lat"], 
                    zone["center_lng"], zone["radius_km"], True)
                
                # Cache zone in Redis
                await redis_conn.hset(f"zone:{zone['zone_id']}", mapping={
                    "zone_name": zone["zone_name"],
                    "center_lat": str(zone["center_lat"]),
                    "center_lng": str(zone["center_lng"]),
                    "radius_km": str(zone["radius_km"]),
                    "is_active": "true"
                })
        
        logger.info("Demo zones initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize demo zones: {e}")

def calculate_distance(loc1: Location, loc2: Location) -> float:
    """Calculate distance between two locations in kilometers"""
    return geodesic((loc1.latitude, loc1.longitude), (loc2.latitude, loc2.longitude)).kilometers

def is_location_in_zone(location: Location, zone: Dict) -> bool:
    """Check if location is within zone radius"""
    zone_location = Location(latitude=zone["center_lat"], longitude=zone["center_lng"])
    distance = calculate_distance(location, zone_location)
    return distance <= zone["radius_km"]

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        # Check Redis connection
        redis_conn = await get_redis()
        await redis_conn.ping()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "service": "geospatial"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/zones", response_model=ZoneResponse)
async def get_zones():
    """Get all available zones"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            zones_data = await conn.fetch("""
                SELECT zone_id, zone_name, center_lat, center_lng, radius_km, is_active
                FROM zones 
                WHERE is_active = true
                ORDER BY zone_name
            """)
        
        zones = [
            Zone(
                zone_id=zone["zone_id"],
                zone_name=zone["zone_name"],
                center_lat=float(zone["center_lat"]),
                center_lng=float(zone["center_lng"]),
                radius_km=float(zone["radius_km"]),
                is_active=zone["is_active"]
            )
            for zone in zones_data
        ]
        
        return ZoneResponse(
            zones=zones,
            total_zones=len(zones),
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error fetching zones: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch zones")

@app.post("/zones/find", response_model=ZoneResponse)
async def find_zones(request: ZoneRequest):
    """Find zones containing the specified location"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Find zones within radius
            zones_data = await conn.fetch("""
                SELECT zone_id, zone_name, center_lat, center_lng, radius_km, is_active
                FROM zones 
                WHERE is_active = true
                AND ST_DWithin(
                    ST_Point($2, $1)::geography,
                    ST_Point(center_lng, center_lat)::geography,
                    $3 * 1000
                )
                ORDER BY ST_Distance(
                    ST_Point($2, $1)::geography,
                    ST_Point(center_lng, center_lat)::geography
                )
            """, request.location.latitude, request.location.longitude, request.radius_km)
        
        zones = [
            Zone(
                zone_id=zone["zone_id"],
                zone_name=zone["zone_name"],
                center_lat=float(zone["center_lat"]),
                center_lng=float(zone["center_lng"]),
                radius_km=float(zone["radius_km"]),
                is_active=zone["is_active"]
            )
            for zone in zones_data
        ]
        
        return ZoneResponse(
            zones=zones,
            total_zones=len(zones),
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error finding zones: {e}")
        raise HTTPException(status_code=500, detail="Failed to find zones")

@app.post("/distance", response_model=DistanceResponse)
async def calculate_distance_endpoint(request: DistanceRequest):
    """Calculate distance between two locations"""
    try:
        distance_km = calculate_distance(request.from_location, request.to_location)
        distance_miles = distance_km * 0.621371
        
        # Estimate travel time (assuming average speed of 30 km/h in city)
        estimated_time_minutes = (distance_km / 30) * 60
        
        return DistanceResponse(
            distance_km=round(distance_km, 2),
            distance_miles=round(distance_miles, 2),
            estimated_time_minutes=round(estimated_time_minutes, 1),
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error calculating distance: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate distance")

@app.get("/zones/{zone_id}")
async def get_zone(zone_id: str):
    """Get specific zone by ID"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            zone_data = await conn.fetchrow("""
                SELECT zone_id, zone_name, center_lat, center_lng, radius_km, is_active
                FROM zones 
                WHERE zone_id = $1
            """, zone_id)
        
        if not zone_data:
            raise HTTPException(status_code=404, detail="Zone not found")
        
        return {
            "zone_id": zone_data["zone_id"],
            "zone_name": zone_data["zone_name"],
            "center_lat": float(zone_data["center_lat"]),
            "center_lng": float(zone_data["center_lng"]),
            "radius_km": float(zone_data["radius_km"]),
            "is_active": zone_data["is_active"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching zone: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch zone")

@app.post("/zones")
async def create_zone(zone: Zone):
    """Create a new zone"""
    try:
        pool = await get_db_pool()
        redis_conn = await get_redis()
        
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO zones (zone_id, zone_name, center_lat, center_lng, radius_km, is_active)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, zone.zone_id, zone.zone_name, zone.center_lat, zone.center_lng, 
                zone.radius_km, zone.is_active)
            
            # Cache zone in Redis
            await redis_conn.hset(f"zone:{zone.zone_id}", mapping={
                "zone_name": zone.zone_name,
                "center_lat": str(zone.center_lat),
                "center_lng": str(zone.center_lng),
                "radius_km": str(zone.radius_km),
                "is_active": str(zone.is_active).lower()
            })
        
        return {
            "message": "Zone created successfully",
            "zone_id": zone.zone_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating zone: {e}")
        raise HTTPException(status_code=500, detail="Failed to create zone")

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8003,
        reload=False,
        log_level="info"
    )

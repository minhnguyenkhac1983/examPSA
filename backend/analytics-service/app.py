#!/usr/bin/env python3
"""
Equilibrium Platform - Analytics Service
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

import asyncpg
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
redis_client: Optional[redis.Redis] = None
db_pool: Optional[asyncpg.Pool] = None

# Pydantic Models
class AnalyticsRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    zone_id: Optional[str] = None
    metric_type: str = "all"

class PricingAnalytics(BaseModel):
    total_estimates: int
    average_fare: float
    average_surge: float
    peak_hours: List[Dict[str, Any]]
    zone_breakdown: List[Dict[str, Any]]

class SupplyDemandAnalytics(BaseModel):
    average_supply: float
    average_demand: float
    supply_demand_ratio: float
    peak_demand_hours: List[Dict[str, Any]]
    zone_analysis: List[Dict[str, Any]]

class RevenueAnalytics(BaseModel):
    total_revenue: float
    revenue_by_zone: List[Dict[str, Any]]
    revenue_trend: List[Dict[str, Any]]
    average_revenue_per_ride: float

class PerformanceAnalytics(BaseModel):
    average_response_time: float
    success_rate: float
    error_rate: float
    throughput: float
    latency_percentiles: Dict[str, float]

class AnalyticsResponse(BaseModel):
    pricing: PricingAnalytics
    supply_demand: SupplyDemandAnalytics
    revenue: RevenueAnalytics
    performance: PerformanceAnalytics
    timestamp: datetime
    period: str

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
    logger.info("🚀 Starting Equilibrium Analytics Service...")
    
    # Initialize database connection
    await get_db_pool()
    logger.info("✅ Connected to PostgreSQL")
    
    # Initialize Redis connection
    await get_redis()
    logger.info("✅ Connected to Redis")
    
    # Initialize analytics tables
    await initialize_analytics_tables()
    logger.info("✅ Analytics tables initialized")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Analytics Service...")
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()

# Create FastAPI app
app = FastAPI(
    title="Equilibrium Analytics Service",
    description="Analytics and reporting for Equilibrium Dynamic Pricing Platform",
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

async def initialize_analytics_tables():
    """Initialize analytics tables"""
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Create pricing events table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS pricing_events (
                    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    rider_id VARCHAR(50) NOT NULL,
                    zone_id VARCHAR(50) NOT NULL,
                    base_fare DECIMAL(10, 2) NOT NULL,
                    surge_multiplier DECIMAL(5, 2) NOT NULL,
                    final_fare DECIMAL(10, 2) NOT NULL,
                    distance_km DECIMAL(8, 2),
                    estimated_time_minutes INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create supply demand events table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS supply_demand_events (
                    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    zone_id VARCHAR(50) NOT NULL,
                    supply INTEGER NOT NULL,
                    demand INTEGER NOT NULL,
                    surge_multiplier DECIMAL(5, 2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create performance metrics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    service_name VARCHAR(50) NOT NULL,
                    endpoint VARCHAR(100) NOT NULL,
                    response_time_ms INTEGER NOT NULL,
                    status_code INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_pricing_events_created_at 
                ON pricing_events(created_at)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_pricing_events_zone_id 
                ON pricing_events(zone_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_supply_demand_events_created_at 
                ON supply_demand_events(created_at)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_performance_metrics_created_at 
                ON performance_metrics(created_at)
            """)
        
        logger.info("Analytics tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize analytics tables: {e}")

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
            "service": "analytics"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/analytics/comprehensive", response_model=AnalyticsResponse)
async def get_comprehensive_analytics(request: AnalyticsRequest):
    """Get comprehensive analytics for the specified period"""
    try:
        pool = await get_db_pool()
        
        # Get pricing analytics
        pricing_analytics = await get_pricing_analytics(pool, request)
        
        # Get supply/demand analytics
        supply_demand_analytics = await get_supply_demand_analytics(pool, request)
        
        # Get revenue analytics
        revenue_analytics = await get_revenue_analytics(pool, request)
        
        # Get performance analytics
        performance_analytics = await get_performance_analytics(pool, request)
        
        return AnalyticsResponse(
            pricing=pricing_analytics,
            supply_demand=supply_demand_analytics,
            revenue=revenue_analytics,
            performance=performance_analytics,
            timestamp=datetime.now(),
            period=f"{request.start_date.isoformat()} to {request.end_date.isoformat()}"
        )
    except Exception as e:
        logger.error(f"Error getting comprehensive analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")

async def get_pricing_analytics(pool: asyncpg.Pool, request: AnalyticsRequest) -> PricingAnalytics:
    """Get pricing analytics"""
    async with pool.acquire() as conn:
        # Base query
        base_query = """
            SELECT 
                COUNT(*) as total_estimates,
                AVG(final_fare) as average_fare,
                AVG(surge_multiplier) as average_surge,
                zone_id
            FROM pricing_events 
            WHERE created_at BETWEEN $1 AND $2
        """
        
        params = [request.start_date, request.end_date]
        
        if request.zone_id:
            base_query += " AND zone_id = $3"
            params.append(request.zone_id)
        
        base_query += " GROUP BY zone_id"
        
        # Get zone breakdown
        zone_data = await conn.fetch(base_query, *params)
        
        # Get peak hours
        peak_hours_query = """
            SELECT 
                EXTRACT(HOUR FROM created_at) as hour,
                COUNT(*) as estimate_count,
                AVG(surge_multiplier) as avg_surge
            FROM pricing_events 
            WHERE created_at BETWEEN $1 AND $2
            GROUP BY EXTRACT(HOUR FROM created_at)
            ORDER BY estimate_count DESC
            LIMIT 5
        """
        
        peak_hours_data = await conn.fetch(peak_hours_query, request.start_date, request.end_date)
        
        # Calculate totals
        total_estimates = sum(row['total_estimates'] for row in zone_data)
        total_fare = sum(row['average_fare'] * row['total_estimates'] for row in zone_data)
        total_surge = sum(row['average_surge'] * row['total_estimates'] for row in zone_data)
        
        average_fare = total_fare / total_estimates if total_estimates > 0 else 0
        average_surge = total_surge / total_estimates if total_estimates > 0 else 0
        
        return PricingAnalytics(
            total_estimates=total_estimates,
            average_fare=round(average_fare, 2),
            average_surge=round(average_surge, 2),
            peak_hours=[
                {
                    "hour": int(row['hour']),
                    "estimate_count": row['estimate_count'],
                    "avg_surge": round(float(row['avg_surge']), 2)
                }
                for row in peak_hours_data
            ],
            zone_breakdown=[
                {
                    "zone_id": row['zone_id'],
                    "total_estimates": row['total_estimates'],
                    "average_fare": round(float(row['average_fare']), 2),
                    "average_surge": round(float(row['average_surge']), 2)
                }
                for row in zone_data
            ]
        )

async def get_supply_demand_analytics(pool: asyncpg.Pool, request: AnalyticsRequest) -> SupplyDemandAnalytics:
    """Get supply/demand analytics"""
    async with pool.acquire() as conn:
        # Get supply/demand data
        query = """
            SELECT 
                AVG(supply) as average_supply,
                AVG(demand) as average_demand,
                AVG(surge_multiplier) as average_surge,
                zone_id
            FROM supply_demand_events 
            WHERE created_at BETWEEN $1 AND $2
        """
        
        params = [request.start_date, request.end_date]
        
        if request.zone_id:
            query += " AND zone_id = $3"
            params.append(request.zone_id)
        
        query += " GROUP BY zone_id"
        
        zone_data = await conn.fetch(query, *params)
        
        # Get peak demand hours
        peak_demand_query = """
            SELECT 
                EXTRACT(HOUR FROM created_at) as hour,
                AVG(demand) as avg_demand,
                AVG(supply) as avg_supply
            FROM supply_demand_events 
            WHERE created_at BETWEEN $1 AND $2
            GROUP BY EXTRACT(HOUR FROM created_at)
            ORDER BY avg_demand DESC
            LIMIT 5
        """
        
        peak_demand_data = await conn.fetch(peak_demand_query, request.start_date, request.end_date)
        
        # Calculate totals
        total_supply = sum(row['average_supply'] for row in zone_data)
        total_demand = sum(row['average_demand'] for row in zone_data)
        
        average_supply = total_supply / len(zone_data) if zone_data else 0
        average_demand = total_demand / len(zone_data) if zone_data else 0
        supply_demand_ratio = average_demand / average_supply if average_supply > 0 else 0
        
        return SupplyDemandAnalytics(
            average_supply=round(average_supply, 2),
            average_demand=round(average_demand, 2),
            supply_demand_ratio=round(supply_demand_ratio, 2),
            peak_demand_hours=[
                {
                    "hour": int(row['hour']),
                    "avg_demand": round(float(row['avg_demand']), 2),
                    "avg_supply": round(float(row['avg_supply']), 2)
                }
                for row in peak_demand_data
            ],
            zone_analysis=[
                {
                    "zone_id": row['zone_id'],
                    "average_supply": round(float(row['average_supply']), 2),
                    "average_demand": round(float(row['average_demand']), 2),
                    "average_surge": round(float(row['average_surge']), 2)
                }
                for row in zone_data
            ]
        )

async def get_revenue_analytics(pool: asyncpg.Pool, request: AnalyticsRequest) -> RevenueAnalytics:
    """Get revenue analytics"""
    async with pool.acquire() as conn:
        # Get revenue by zone
        query = """
            SELECT 
                zone_id,
                SUM(final_fare) as total_revenue,
                COUNT(*) as ride_count,
                AVG(final_fare) as avg_revenue_per_ride
            FROM pricing_events 
            WHERE created_at BETWEEN $1 AND $2
        """
        
        params = [request.start_date, request.end_date]
        
        if request.zone_id:
            query += " AND zone_id = $3"
            params.append(request.zone_id)
        
        query += " GROUP BY zone_id ORDER BY total_revenue DESC"
        
        zone_data = await conn.fetch(query, *params)
        
        # Get revenue trend (daily)
        trend_query = """
            SELECT 
                DATE(created_at) as date,
                SUM(final_fare) as daily_revenue,
                COUNT(*) as daily_rides
            FROM pricing_events 
            WHERE created_at BETWEEN $1 AND $2
            GROUP BY DATE(created_at)
            ORDER BY date
        """
        
        trend_data = await conn.fetch(trend_query, request.start_date, request.end_date)
        
        # Calculate totals
        total_revenue = sum(row['total_revenue'] for row in zone_data)
        total_rides = sum(row['ride_count'] for row in zone_data)
        average_revenue_per_ride = total_revenue / total_rides if total_rides > 0 else 0
        
        return RevenueAnalytics(
            total_revenue=round(total_revenue, 2),
            revenue_by_zone=[
                {
                    "zone_id": row['zone_id'],
                    "total_revenue": round(float(row['total_revenue']), 2),
                    "ride_count": row['ride_count'],
                    "avg_revenue_per_ride": round(float(row['avg_revenue_per_ride']), 2)
                }
                for row in zone_data
            ],
            revenue_trend=[
                {
                    "date": row['date'].isoformat(),
                    "daily_revenue": round(float(row['daily_revenue']), 2),
                    "daily_rides": row['daily_rides']
                }
                for row in trend_data
            ],
            average_revenue_per_ride=round(average_revenue_per_ride, 2)
        )

async def get_performance_analytics(pool: asyncpg.Pool, request: AnalyticsRequest) -> PerformanceAnalytics:
    """Get performance analytics"""
    async with pool.acquire() as conn:
        # Get performance metrics
        query = """
            SELECT 
                AVG(response_time_ms) as avg_response_time,
                COUNT(*) as total_requests,
                COUNT(CASE WHEN status_code < 400 THEN 1 END) as successful_requests,
                COUNT(CASE WHEN status_code >= 400 THEN 1 END) as failed_requests
            FROM performance_metrics 
            WHERE created_at BETWEEN $1 AND $2
        """
        
        performance_data = await conn.fetchrow(query, request.start_date, request.end_date)
        
        # Get latency percentiles
        percentile_query = """
            SELECT 
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY response_time_ms) as p50,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time_ms) as p99
            FROM performance_metrics 
            WHERE created_at BETWEEN $1 AND $2
        """
        
        percentile_data = await conn.fetchrow(percentile_query, request.start_date, request.end_date)
        
        total_requests = performance_data['total_requests'] or 0
        successful_requests = performance_data['successful_requests'] or 0
        failed_requests = performance_data['failed_requests'] or 0
        
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate throughput (requests per second)
        time_diff = (request.end_date - request.start_date).total_seconds()
        throughput = total_requests / time_diff if time_diff > 0 else 0
        
        return PerformanceAnalytics(
            average_response_time=round(float(performance_data['avg_response_time'] or 0), 2),
            success_rate=round(success_rate, 2),
            error_rate=round(error_rate, 2),
            throughput=round(throughput, 2),
            latency_percentiles={
                "p50": round(float(percentile_data['p50'] or 0), 2),
                "p95": round(float(percentile_data['p95'] or 0), 2),
                "p99": round(float(percentile_data['p99'] or 0), 2)
            }
        )

@app.get("/analytics/dashboard")
async def get_dashboard_analytics(
    hours: int = Query(24, description="Number of hours to look back")
):
    """Get dashboard analytics for the last N hours"""
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=hours)
    
    request = AnalyticsRequest(
        start_date=start_date,
        end_date=end_date,
        metric_type="all"
    )
    
    return await get_comprehensive_analytics(request)

@app.post("/analytics/events/pricing")
async def log_pricing_event(event_data: Dict[str, Any]):
    """Log a pricing event for analytics"""
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO pricing_events (
                    rider_id, zone_id, base_fare, surge_multiplier, 
                    final_fare, distance_km, estimated_time_minutes
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, 
                event_data.get("rider_id"),
                event_data.get("zone_id"),
                event_data.get("base_fare"),
                event_data.get("surge_multiplier"),
                event_data.get("final_fare"),
                event_data.get("distance_km"),
                event_data.get("estimated_time_minutes")
            )
        
        return {"message": "Pricing event logged successfully"}
    except Exception as e:
        logger.error(f"Error logging pricing event: {e}")
        raise HTTPException(status_code=500, detail="Failed to log pricing event")

@app.post("/analytics/events/supply-demand")
async def log_supply_demand_event(event_data: Dict[str, Any]):
    """Log a supply/demand event for analytics"""
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO supply_demand_events (
                    zone_id, supply, demand, surge_multiplier
                ) VALUES ($1, $2, $3, $4)
            """, 
                event_data.get("zone_id"),
                event_data.get("supply"),
                event_data.get("demand"),
                event_data.get("surge_multiplier")
            )
        
        return {"message": "Supply/demand event logged successfully"}
    except Exception as e:
        logger.error(f"Error logging supply/demand event: {e}")
        raise HTTPException(status_code=500, detail="Failed to log supply/demand event")

@app.post("/analytics/events/performance")
async def log_performance_event(event_data: Dict[str, Any]):
    """Log a performance event for analytics"""
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO performance_metrics (
                    service_name, endpoint, response_time_ms, status_code
                ) VALUES ($1, $2, $3, $4)
            """, 
                event_data.get("service_name"),
                event_data.get("endpoint"),
                event_data.get("response_time_ms"),
                event_data.get("status_code")
            )
        
        return {"message": "Performance event logged successfully"}
    except Exception as e:
        logger.error(f"Error logging performance event: {e}")
        raise HTTPException(status_code=500, detail="Failed to log performance event")

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info"
    )

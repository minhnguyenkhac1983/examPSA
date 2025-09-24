#!/usr/bin/env python3
"""
Equilibrium Platform - NATs Stream Processor
High-performance stream processing using NATs JetStream instead of Apache Flink
"""

import asyncio
import json
import logging
import os
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

import asyncpg
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from nats_manager import (
    NATsStreamManager, 
    LocationEvent, 
    PricingUpdate, 
    AnalyticsEvent, 
    ConfigUpdate
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
redis_client: Optional[redis.Redis] = None
db_pool: Optional[asyncpg.Pool] = None
nats_manager: Optional[NATsStreamManager] = None
stream_processor_running = False
processing_tasks: List[asyncio.Task] = []

# Pydantic Models
class ProcessingStats(BaseModel):
    total_events_processed: int
    events_per_second: float
    last_processed_time: datetime
    error_count: int
    zones_processed: Dict[str, int]
    memory_usage_percent: float
    cpu_usage_percent: float

class ZoneState(BaseModel):
    zone_id: str
    supply: int
    demand: int
    last_updated: datetime
    surge_multiplier: float

class StreamProcessorConfig(BaseModel):
    nats_url: str = "nats://localhost:4222"
    window_size_seconds: int = 30
    processing_interval_seconds: int = 5
    health_check_interval_seconds: int = 30

class NATsStreamProcessor:
    """NATs Stream Processor for Equilibrium pricing system"""
    
    def __init__(self, config: StreamProcessorConfig):
        self.config = config
        self.supply_demand_state: Dict[str, Dict] = {}
        self.processing_stats = {
            'total_events': 0,
            'errors': 0,
            'zones_processed': {},
            'last_processed': None
        }
        self.window_size = config.window_size_seconds
        self.processing_interval = config.processing_interval_seconds
        
    async def start_processing(self):
        """Start stream processing"""
        global stream_processor_running, processing_tasks
        
        logger.info("🚀 Starting NATs Stream Processor...")
        
        if not stream_processor_running:
            stream_processor_running = True
            
            # Start processing tasks
            processing_tasks = [
                asyncio.create_task(self._process_location_events()),
                asyncio.create_task(self._process_pricing_updates()),
                asyncio.create_task(self._windowed_aggregation()),
                asyncio.create_task(self._health_monitor()),
                asyncio.create_task(self._analytics_processor()),
                asyncio.create_task(self._config_processor())
            ]
            
            logger.info("✅ All processing tasks started")
            
            # Wait for all tasks
            await asyncio.gather(*processing_tasks, return_exceptions=True)
    
    async def stop_processing(self):
        """Stop stream processing"""
        global stream_processor_running, processing_tasks
        
        logger.info("🛑 Stopping NATs Stream Processor...")
        stream_processor_running = False
        
        # Cancel all tasks
        for task in processing_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*processing_tasks, return_exceptions=True)
        processing_tasks.clear()
        
        logger.info("✅ NATs Stream Processor stopped")
    
    async def _process_location_events(self):
        """Process location events from NATs"""
        logger.info("📍 Starting location events processing...")
        
        async def handle_location_event(event: LocationEvent):
            try:
                # Update supply/demand state
                zone_id = event.zone_id
                if zone_id not in self.supply_demand_state:
                    self.supply_demand_state[zone_id] = {
                        'supply': 0,
                        'demand': 0,
                        'last_updated': datetime.utcnow(),
                        'surge_multiplier': 1.0
                    }
                
                # Update supply count based on availability
                if event.is_available:
                    self.supply_demand_state[zone_id]['supply'] += 1
                else:
                    self.supply_demand_state[zone_id]['supply'] = max(0, 
                        self.supply_demand_state[zone_id]['supply'] - 1)
                
                # Update timestamp
                self.supply_demand_state[zone_id]['last_updated'] = datetime.utcnow()
                
                # Update processing stats
                self.processing_stats['total_events'] += 1
                self.processing_stats['zones_processed'][zone_id] = \
                    self.processing_stats['zones_processed'].get(zone_id, 0) + 1
                self.processing_stats['last_processed'] = datetime.utcnow()
                
                # Trigger pricing calculation
                await self._trigger_pricing_calculation(zone_id)
                
                logger.debug(f"📍 Processed location event for zone {zone_id}")
                
            except Exception as e:
                logger.error(f"❌ Error processing location event: {e}")
                self.processing_stats['errors'] += 1
        
        # Subscribe to all location events
        await nats_manager.subscribe_all_location_events(handle_location_event)
    
    async def _trigger_pricing_calculation(self, zone_id: str):
        """Trigger pricing calculation for zone"""
        try:
            # Get supply/demand data
            supply_demand = self.supply_demand_state.get(zone_id, {
                'supply': 0, 
                'demand': 0, 
                'surge_multiplier': 1.0
            })
            
            # Calculate surge multiplier using simple algorithm
            surge_multiplier = await self._calculate_surge_multiplier(
                zone_id, supply_demand
            )
            
            # Update state
            self.supply_demand_state[zone_id]['surge_multiplier'] = surge_multiplier
            
            # Create pricing update
            pricing_update = PricingUpdate(
                zone_id=zone_id,
                surge_multiplier=surge_multiplier,
                supply_count=supply_demand['supply'],
                demand_count=supply_demand['demand'],
                algorithm_used="nats_linear",
                timestamp=datetime.utcnow()
            )
            
            # Publish pricing update
            await nats_manager.publish_pricing_update(pricing_update)
            
            # Update cache
            await self._update_pricing_cache(pricing_update)
            
            logger.info(f"💰 Pricing update for zone {zone_id}: {surge_multiplier}x")
            
        except Exception as e:
            logger.error(f"❌ Error calculating pricing for zone {zone_id}: {e}")
            self.processing_stats['errors'] += 1
    
    async def _calculate_surge_multiplier(self, zone_id: str, supply_demand: Dict) -> float:
        """Calculate surge multiplier using simple linear algorithm"""
        try:
            supply = supply_demand['supply']
            demand = supply_demand['demand']
            
            # Avoid division by zero
            if supply == 0:
                return 3.0  # Maximum surge when no supply
            
            # Calculate supply/demand ratio
            ratio = demand / supply
            
            # Linear pricing algorithm
            if ratio <= 0.5:
                return 1.0  # No surge
            elif ratio <= 1.0:
                return 1.0 + (ratio - 0.5) * 2  # Linear increase from 1.0 to 2.0
            elif ratio <= 2.0:
                return 2.0 + (ratio - 1.0) * 1  # Linear increase from 2.0 to 3.0
            else:
                return 3.0  # Maximum surge
            
        except Exception as e:
            logger.error(f"❌ Error in surge calculation: {e}")
            return 1.0
    
    async def _process_pricing_updates(self):
        """Process pricing updates and update cache"""
        logger.info("💰 Starting pricing updates processing...")
        
        async def handle_pricing_update(update: PricingUpdate):
            try:
                # Update Redis cache
                await self._update_pricing_cache(update)
                
                # Send to analytics
                await self._send_to_analytics(update)
                
                # Broadcast to WebSocket clients
                await self._broadcast_pricing_update(update)
                
                logger.debug(f"💰 Processed pricing update for zone {update.zone_id}")
                
            except Exception as e:
                logger.error(f"❌ Error processing pricing update: {e}")
                self.processing_stats['errors'] += 1
        
        # Subscribe to pricing updates
        await nats_manager.subscribe_pricing_updates(handle_pricing_update)
    
    async def _windowed_aggregation(self):
        """Windowed aggregation for supply/demand data"""
        logger.info("⏰ Starting windowed aggregation...")
        
        while stream_processor_running:
            try:
                current_time = datetime.utcnow()
                
                # Process zones with data older than window_size
                for zone_id, state in self.supply_demand_state.items():
                    time_diff = (current_time - state['last_updated']).total_seconds()
                    
                    if time_diff > self.window_size:
                        # Gradually reduce supply/demand for inactive zones
                        state['supply'] = max(0, state['supply'] - 1)
                        state['demand'] = max(0, state['demand'] - 1)
                        state['last_updated'] = current_time
                        
                        # Trigger pricing recalculation
                        await self._trigger_pricing_calculation(zone_id)
                
                # Wait before next check
                await asyncio.sleep(self.processing_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in windowed aggregation: {e}")
                await asyncio.sleep(5)
    
    async def _analytics_processor(self):
        """Process analytics events"""
        logger.info("📊 Starting analytics processor...")
        
        async def handle_analytics_event(event: AnalyticsEvent):
            try:
                # Store analytics data in database
                await self._store_analytics_data(event)
                logger.debug(f"📊 Processed analytics event: {event.event_type}")
                
            except Exception as e:
                logger.error(f"❌ Error processing analytics event: {e}")
                self.processing_stats['errors'] += 1
        
        # Subscribe to analytics events
        await nats_manager.subscribe_analytics_events(handle_analytics_event)
    
    async def _config_processor(self):
        """Process configuration updates"""
        logger.info("⚙️ Starting config processor...")
        
        async def handle_config_update(update: ConfigUpdate):
            try:
                # Update configuration in database and cache
                await self._update_configuration(update)
                logger.debug(f"⚙️ Processed config update: {update.config_type}")
                
            except Exception as e:
                logger.error(f"❌ Error processing config update: {e}")
                self.processing_stats['errors'] += 1
        
        # Subscribe to config updates
        await nats_manager.subscribe_config_updates(handle_config_update)
    
    async def _health_monitor(self):
        """Monitor stream processor health"""
        logger.info("🏥 Starting health monitor...")
        
        while stream_processor_running:
            try:
                # Check number of active zones
                active_zones = len([
                    zone_id for zone_id, state in self.supply_demand_state.items()
                    if (datetime.utcnow() - state['last_updated']).total_seconds() < 60
                ])
                
                # Check system resources
                memory_percent = psutil.virtual_memory().percent
                cpu_percent = psutil.cpu_percent()
                
                logger.info(f"📊 Health Status: {active_zones} zones active, "
                          f"Memory: {memory_percent:.1f}%, CPU: {cpu_percent:.1f}%")
                
                # Warning if resources are high
                if memory_percent > 80:
                    logger.warning(f"⚠️ High memory usage: {memory_percent:.1f}%")
                if cpu_percent > 80:
                    logger.warning(f"⚠️ High CPU usage: {cpu_percent:.1f}%")
                
                await asyncio.sleep(self.config.health_check_interval_seconds)
                
            except Exception as e:
                logger.error(f"❌ Error in health monitor: {e}")
                await asyncio.sleep(10)
    
    async def _update_pricing_cache(self, pricing_data: PricingUpdate):
        """Update Redis cache with pricing data"""
        try:
            cache_key = f"pricing:{pricing_data.zone_id}"
            cache_data = {
                'surge_multiplier': pricing_data.surge_multiplier,
                'supply_count': pricing_data.supply_count,
                'demand_count': pricing_data.demand_count,
                'algorithm_used': pricing_data.algorithm_used,
                'timestamp': pricing_data.timestamp.isoformat(),
                'ttl': 300  # 5 minutes
            }
            
            await redis_client.setex(
                cache_key,
                300,  # 5 minutes TTL
                json.dumps(cache_data)
            )
            
        except Exception as e:
            logger.error(f"❌ Error updating pricing cache: {e}")
    
    async def _send_to_analytics(self, pricing_data: PricingUpdate):
        """Send pricing data to analytics service"""
        try:
            analytics_event = AnalyticsEvent(
                event_type='pricing_update',
                zone_id=pricing_data.zone_id,
                data={
                    'surge_multiplier': pricing_data.surge_multiplier,
                    'supply_count': pricing_data.supply_count,
                    'demand_count': pricing_data.demand_count,
                    'algorithm_used': pricing_data.algorithm_used
                },
                timestamp=datetime.utcnow()
            )
            
            await nats_manager.publish_analytics_event(analytics_event)
            
        except Exception as e:
            logger.error(f"❌ Error sending to analytics: {e}")
    
    async def _broadcast_pricing_update(self, pricing_data: PricingUpdate):
        """Broadcast pricing update to WebSocket clients"""
        try:
            websocket_data = {
                'type': 'pricing_update',
                'zone_id': pricing_data.zone_id,
                'surge_multiplier': pricing_data.surge_multiplier,
                'timestamp': pricing_data.timestamp.isoformat()
            }
            
            await nats_manager.publish_websocket_event('pricing', websocket_data)
            
        except Exception as e:
            logger.error(f"❌ Error broadcasting pricing update: {e}")
    
    async def _store_analytics_data(self, event: AnalyticsEvent):
        """Store analytics data in database"""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO analytics_events (
                        event_type, zone_id, data, timestamp
                    ) VALUES ($1, $2, $3, $4)
                    ON CONFLICT DO NOTHING
                """, 
                    event.event_type,
                    event.zone_id,
                    json.dumps(event.data),
                    event.timestamp
                )
                
        except Exception as e:
            logger.error(f"❌ Error storing analytics data: {e}")
    
    async def _update_configuration(self, update: ConfigUpdate):
        """Update configuration in database and cache"""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO configuration_updates (
                        config_type, zone_id, config_data, timestamp
                    ) VALUES ($1, $2, $3, $4)
                    ON CONFLICT DO NOTHING
                """, 
                    update.config_type,
                    update.zone_id,
                    json.dumps(update.config_data),
                    update.timestamp
                )
            
            # Update cache
            cache_key = f"config:{update.config_type}"
            if update.zone_id:
                cache_key += f":{update.zone_id}"
            
            await redis_client.setex(
                cache_key,
                3600,  # 1 hour TTL
                json.dumps(update.config_data)
            )
            
        except Exception as e:
            logger.error(f"❌ Error updating configuration: {e}")
    
    def get_processing_stats(self) -> ProcessingStats:
        """Get current processing statistics"""
        try:
            memory_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent()
            
            # Calculate events per second
            events_per_second = 0
            if self.processing_stats['last_processed']:
                time_diff = (datetime.utcnow() - self.processing_stats['last_processed']).total_seconds()
                if time_diff > 0:
                    events_per_second = self.processing_stats['total_events'] / time_diff
            
            return ProcessingStats(
                total_events_processed=self.processing_stats['total_events'],
                events_per_second=round(events_per_second, 2),
                last_processed_time=self.processing_stats['last_processed'] or datetime.utcnow(),
                error_count=self.processing_stats['errors'],
                zones_processed=self.processing_stats['zones_processed'].copy(),
                memory_usage_percent=memory_percent,
                cpu_usage_percent=cpu_percent
            )
            
        except Exception as e:
            logger.error(f"❌ Error getting processing stats: {e}")
            return ProcessingStats(
                total_events_processed=0,
                events_per_second=0,
                last_processed_time=datetime.utcnow(),
                error_count=0,
                zones_processed={},
                memory_usage_percent=0,
                cpu_usage_percent=0
            )

# Global processor instance
processor: Optional[NATsStreamProcessor] = None

# Database connection
async def get_db_pool():
    global db_pool
    if db_pool is None:
        database_url = os.getenv(
            "DATABASE_URL", 
            "postgresql://equilibrium:equilibrium123@postgres:5432/equilibrium"
        )
        db_pool = await asyncpg.create_pool(database_url, min_size=5, max_size=20)
    return db_pool

async def get_redis():
    global redis_client
    if redis_client is None:
        redis_url = os.getenv(
            "REDIS_URL", 
            "redis://:equilibrium123@redis:6379/0"
        )
        redis_client = redis.from_url(redis_url, decode_responses=True)
    return redis_client

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    global nats_manager, processor
    
    # Startup
    logger.info("🚀 Starting Equilibrium NATs Stream Processor...")
    
    # Initialize database connection
    await get_db_pool()
    logger.info("✅ Connected to PostgreSQL")
    
    # Initialize Redis connection
    await get_redis()
    logger.info("✅ Connected to Redis")
    
    # Initialize NATs
    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    nats_manager = NATsStreamManager(nats_url)
    await nats_manager.connect()
    logger.info("✅ Connected to NATs")
    
    # Initialize and start processor
    config = StreamProcessorConfig(nats_url=nats_url)
    processor = NATsStreamProcessor(config)
    await processor.start_processing()
    logger.info("✅ NATs Stream Processor started")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down NATs Stream Processor...")
    if processor:
        await processor.stop_processing()
    if nats_manager:
        await nats_manager.close()
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()

# Create FastAPI app
app = FastAPI(
    title="Equilibrium NATs Stream Processor",
    description="High-performance stream processing using NATs JetStream",
    version="2.0.0",
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
        
        # Check NATs connection
        nats_healthy = nats_manager.is_connected() if nats_manager else False
        
        return {
            "status": "healthy" if nats_healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "service": "nats-stream-processor",
            "processor_running": stream_processor_running,
            "nats_connected": nats_healthy,
            "database_connected": True,
            "redis_connected": True
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/stats", response_model=ProcessingStats)
async def get_processing_stats():
    """Get stream processing statistics"""
    try:
        if processor:
            return processor.get_processing_stats()
        else:
            raise HTTPException(status_code=503, detail="Processor not initialized")
    except Exception as e:
        logger.error(f"Error getting processing stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing stats")

@app.get("/streams/info")
async def get_streams_info():
    """Get NATs streams information"""
    try:
        if nats_manager:
            return await nats_manager.get_all_streams_info()
        else:
            raise HTTPException(status_code=503, detail="NATs manager not initialized")
    except Exception as e:
        logger.error(f"Error getting streams info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get streams info")

@app.get("/zones/state")
async def get_zones_state():
    """Get current zones state"""
    try:
        if processor:
            zones_state = []
            for zone_id, state in processor.supply_demand_state.items():
                zones_state.append(ZoneState(
                    zone_id=zone_id,
                    supply=state['supply'],
                    demand=state['demand'],
                    last_updated=state['last_updated'],
                    surge_multiplier=state['surge_multiplier']
                ))
            return {"zones": zones_state, "total_zones": len(zones_state)}
        else:
            raise HTTPException(status_code=503, detail="Processor not initialized")
    except Exception as e:
        logger.error(f"Error getting zones state: {e}")
        raise HTTPException(status_code=500, detail="Failed to get zones state")

@app.post("/stream/start")
async def start_processor():
    """Start the stream processor"""
    global stream_processor_running
    
    if not stream_processor_running and processor:
        await processor.start_processing()
        return {"message": "NATs Stream processor started", "status": "running"}
    else:
        return {"message": "NATs Stream processor is already running", "status": "running"}

@app.post("/stream/stop")
async def stop_processor():
    """Stop the stream processor"""
    global stream_processor_running
    
    if stream_processor_running and processor:
        await processor.stop_processing()
        return {"message": "NATs Stream processor stopped", "status": "stopped"}
    else:
        return {"message": "NATs Stream processor is already stopped", "status": "stopped"}

@app.get("/stream/status")
async def get_processor_status():
    """Get stream processor status"""
    return {
        "running": stream_processor_running,
        "nats_connected": nats_manager.is_connected() if nats_manager else False,
        "nats_url": os.getenv("NATS_URL", "nats://localhost:4222"),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "nats_stream_processor:app",
        host="0.0.0.0",
        port=8004,
        reload=False,
        log_level="info"
    )

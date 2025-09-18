#!/usr/bin/env python3
"""
Equilibrium Platform - Stream Processor Service
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

import asyncpg
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import json
from kafka import KafkaConsumer, KafkaProducer
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
redis_client: Optional[redis.Redis] = None
db_pool: Optional[asyncpg.Pool] = None
kafka_consumer: Optional[KafkaConsumer] = None
kafka_producer: Optional[KafkaProducer] = None
stream_processor_running = False

# Pydantic Models
class StreamEvent(BaseModel):
    event_type: str
    event_id: str
    timestamp: datetime
    data: Dict[str, Any]
    source: str

class ProcessingStats(BaseModel):
    total_events_processed: int
    events_per_second: float
    last_processed_time: datetime
    error_count: int
    topics: Dict[str, int]

class StreamConfig(BaseModel):
    kafka_brokers: str
    topics: List[str]
    consumer_group: str
    batch_size: int = 100
    processing_interval: int = 5

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

# Kafka configuration
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")
TOPICS = [
    "pricing_events",
    "supply_demand_events", 
    "driver_location_events",
    "rider_requests",
    "performance_metrics"
]

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Equilibrium Stream Processor...")
    
    # Initialize database connection
    await get_db_pool()
    logger.info("✅ Connected to PostgreSQL")
    
    # Initialize Redis connection
    await get_redis()
    logger.info("✅ Connected to Redis")
    
    # Initialize Kafka
    await initialize_kafka()
    logger.info("✅ Kafka initialized")
    
    # Start stream processor
    await start_stream_processor()
    logger.info("✅ Stream processor started")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Stream Processor...")
    await stop_stream_processor()
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()

# Create FastAPI app
app = FastAPI(
    title="Equilibrium Stream Processor",
    description="Real-time stream processing for Equilibrium Dynamic Pricing Platform",
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

async def initialize_kafka():
    """Initialize Kafka consumer and producer"""
    global kafka_consumer, kafka_producer
    
    try:
        # Initialize consumer
        kafka_consumer = KafkaConsumer(
            *TOPICS,
            bootstrap_servers=KAFKA_BROKERS,
            group_id='equilibrium-stream-processor',
            auto_offset_reset='latest',
            enable_auto_commit=True,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        
        # Initialize producer
        kafka_producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKERS,
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
        logger.info("Kafka consumer and producer initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Kafka: {e}")
        raise

async def start_stream_processor():
    """Start the stream processor"""
    global stream_processor_running
    
    if not stream_processor_running:
        stream_processor_running = True
        # Start processing in background
        asyncio.create_task(process_streams())
        logger.info("Stream processor started")

async def stop_stream_processor():
    """Stop the stream processor"""
    global stream_processor_running, kafka_consumer, kafka_producer
    
    stream_processor_running = False
    
    if kafka_consumer:
        kafka_consumer.close()
    
    if kafka_producer:
        kafka_producer.close()
    
    logger.info("Stream processor stopped")

async def process_streams():
    """Main stream processing loop"""
    global stream_processor_running, kafka_consumer
    
    logger.info("Starting stream processing loop...")
    
    while stream_processor_running:
        try:
            if kafka_consumer:
                # Poll for messages
                message_batch = kafka_consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        await process_message(topic_partition.topic, message.value)
                        
                        # Update processing stats
                        await update_processing_stats(topic_partition.topic)
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Error in stream processing: {e}")
            await asyncio.sleep(1)  # Wait before retrying

async def process_message(topic: str, message: Dict[str, Any]):
    """Process individual message based on topic"""
    try:
        if topic == "pricing_events":
            await process_pricing_event(message)
        elif topic == "supply_demand_events":
            await process_supply_demand_event(message)
        elif topic == "driver_location_events":
            await process_driver_location_event(message)
        elif topic == "rider_requests":
            await process_rider_request_event(message)
        elif topic == "performance_metrics":
            await process_performance_metric_event(message)
        else:
            logger.warning(f"Unknown topic: {topic}")
            
    except Exception as e:
        logger.error(f"Error processing message from {topic}: {e}")

async def process_pricing_event(message: Dict[str, Any]):
    """Process pricing event"""
    try:
        pool = await get_db_pool()
        redis_conn = await get_redis()
        
        # Store in database
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO pricing_events (
                    rider_id, zone_id, base_fare, surge_multiplier, 
                    final_fare, distance_km, estimated_time_minutes
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT DO NOTHING
            """, 
                message.get("rider_id"),
                message.get("zone_id"),
                message.get("base_fare"),
                message.get("surge_multiplier"),
                message.get("final_fare"),
                message.get("distance_km"),
                message.get("estimated_time_minutes")
            )
        
        # Update real-time metrics in Redis
        zone_id = message.get("zone_id")
        if zone_id:
            await redis_conn.hincrby(f"zone:{zone_id}:metrics", "total_estimates", 1)
            await redis_conn.hset(f"zone:{zone_id}:metrics", "last_pricing_event", datetime.now().isoformat())
        
        logger.debug(f"Processed pricing event for zone {zone_id}")
        
    except Exception as e:
        logger.error(f"Error processing pricing event: {e}")

async def process_supply_demand_event(message: Dict[str, Any]):
    """Process supply/demand event"""
    try:
        pool = await get_db_pool()
        redis_conn = await get_redis()
        
        # Store in database
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO supply_demand_events (
                    zone_id, supply, demand, surge_multiplier
                ) VALUES ($1, $2, $3, $4)
                ON CONFLICT DO NOTHING
            """, 
                message.get("zone_id"),
                message.get("supply"),
                message.get("demand"),
                message.get("surge_multiplier")
            )
        
        # Update real-time supply/demand in Redis
        zone_id = message.get("zone_id")
        if zone_id:
            await redis_conn.hset(f"zone:{zone_id}", mapping={
                "supply": message.get("supply"),
                "demand": message.get("demand"),
                "surge_multiplier": message.get("surge_multiplier"),
                "last_updated": datetime.now().isoformat()
            })
        
        logger.debug(f"Processed supply/demand event for zone {zone_id}")
        
    except Exception as e:
        logger.error(f"Error processing supply/demand event: {e}")

async def process_driver_location_event(message: Dict[str, Any]):
    """Process driver location event"""
    try:
        pool = await get_db_pool()
        redis_conn = await get_redis()
        
        # Store in database
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO driver_location_events (
                    driver_id, latitude, longitude, zone_id, timestamp
                ) VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT DO NOTHING
            """, 
                message.get("driver_id"),
                message.get("latitude"),
                message.get("longitude"),
                message.get("zone_id"),
                message.get("timestamp", datetime.now())
            )
        
        # Update driver location in Redis
        driver_id = message.get("driver_id")
        if driver_id:
            await redis_conn.hset(f"driver:{driver_id}", mapping={
                "latitude": message.get("latitude"),
                "longitude": message.get("longitude"),
                "zone_id": message.get("zone_id"),
                "last_seen": datetime.now().isoformat()
            })
        
        logger.debug(f"Processed driver location event for driver {driver_id}")
        
    except Exception as e:
        logger.error(f"Error processing driver location event: {e}")

async def process_rider_request_event(message: Dict[str, Any]):
    """Process rider request event"""
    try:
        pool = await get_db_pool()
        redis_conn = await get_redis()
        
        # Store in database
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO rider_requests (
                    rider_id, pickup_lat, pickup_lng, dropoff_lat, dropoff_lng,
                    zone_id, vehicle_type, timestamp
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT DO NOTHING
            """, 
                message.get("rider_id"),
                message.get("pickup_lat"),
                message.get("pickup_lng"),
                message.get("dropoff_lat"),
                message.get("dropoff_lng"),
                message.get("zone_id"),
                message.get("vehicle_type"),
                message.get("timestamp", datetime.now())
            )
        
        # Update zone demand in Redis
        zone_id = message.get("zone_id")
        if zone_id:
            await redis_conn.hincrby(f"zone:{zone_id}", "demand", 1)
            await redis_conn.hset(f"zone:{zone_id}", "last_demand_update", datetime.now().isoformat())
        
        logger.debug(f"Processed rider request event for zone {zone_id}")
        
    except Exception as e:
        logger.error(f"Error processing rider request event: {e}")

async def process_performance_metric_event(message: Dict[str, Any]):
    """Process performance metric event"""
    try:
        pool = await get_db_pool()
        
        # Store in database
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO performance_metrics (
                    service_name, endpoint, response_time_ms, status_code
                ) VALUES ($1, $2, $3, $4)
                ON CONFLICT DO NOTHING
            """, 
                message.get("service_name"),
                message.get("endpoint"),
                message.get("response_time_ms"),
                message.get("status_code")
            )
        
        logger.debug(f"Processed performance metric event for {message.get('service_name')}")
        
    except Exception as e:
        logger.error(f"Error processing performance metric event: {e}")

async def update_processing_stats(topic: str):
    """Update processing statistics"""
    try:
        redis_conn = await get_redis()
        
        # Update topic-specific stats
        await redis_conn.hincrby("stream_processor:stats", f"topic:{topic}", 1)
        await redis_conn.hincrby("stream_processor:stats", "total_events", 1)
        await redis_conn.hset("stream_processor:stats", "last_processed", datetime.now().isoformat())
        
    except Exception as e:
        logger.error(f"Error updating processing stats: {e}")

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
            "service": "stream-processor",
            "processor_running": stream_processor_running
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/stats", response_model=ProcessingStats)
async def get_processing_stats():
    """Get stream processing statistics"""
    try:
        redis_conn = await get_redis()
        
        # Get stats from Redis
        stats_data = await redis_conn.hgetall("stream_processor:stats")
        
        total_events = int(stats_data.get("total_events", 0))
        last_processed = stats_data.get("last_processed")
        
        # Calculate events per second (last minute)
        events_per_second = 0
        if last_processed:
            last_processed_time = datetime.fromisoformat(last_processed)
            time_diff = (datetime.now() - last_processed_time).total_seconds()
            if time_diff > 0:
                events_per_second = total_events / time_diff
        
        # Get topic-specific stats
        topics = {}
        for key, value in stats_data.items():
            if key.startswith("topic:"):
                topic_name = key.replace("topic:", "")
                topics[topic_name] = int(value)
        
        return ProcessingStats(
            total_events_processed=total_events,
            events_per_second=round(events_per_second, 2),
            last_processed_time=datetime.fromisoformat(last_processed) if last_processed else datetime.now(),
            error_count=0,  # TODO: Implement error tracking
            topics=topics
        )
    except Exception as e:
        logger.error(f"Error getting processing stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing stats")

@app.post("/stream/start")
async def start_processor():
    """Start the stream processor"""
    global stream_processor_running
    
    if not stream_processor_running:
        await start_stream_processor()
        return {"message": "Stream processor started", "status": "running"}
    else:
        return {"message": "Stream processor is already running", "status": "running"}

@app.post("/stream/stop")
async def stop_processor():
    """Stop the stream processor"""
    global stream_processor_running
    
    if stream_processor_running:
        await stop_stream_processor()
        return {"message": "Stream processor stopped", "status": "stopped"}
    else:
        return {"message": "Stream processor is already stopped", "status": "stopped"}

@app.get("/stream/status")
async def get_processor_status():
    """Get stream processor status"""
    return {
        "running": stream_processor_running,
        "topics": TOPICS,
        "kafka_brokers": KAFKA_BROKERS,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/stream/publish")
async def publish_event(event: StreamEvent):
    """Publish an event to Kafka"""
    try:
        if kafka_producer:
            # Publish to appropriate topic based on event type
            topic = f"{event.event_type}_events"
            
            message_data = {
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data,
                "source": event.source
            }
            
            kafka_producer.send(topic, value=message_data)
            kafka_producer.flush()
            
            return {"message": "Event published successfully", "topic": topic}
        else:
            raise HTTPException(status_code=503, detail="Kafka producer not available")
            
    except Exception as e:
        logger.error(f"Error publishing event: {e}")
        raise HTTPException(status_code=500, detail="Failed to publish event")

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8004,
        reload=False,
        log_level="info"
    )

#!/usr/bin/env python3
"""
Equilibrium Platform - NATs JetStream Manager
High-performance messaging solution replacing Kafka
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict

import nats
from nats.js import JetStreamContext
from nats.js.api import StreamConfig, RetentionPolicy, StorageType, DiscardPolicy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LocationEvent:
    """Location event data structure"""
    event_id: str
    driver_id: str
    latitude: float
    longitude: float
    s2_cell_id: str
    zone_id: str
    is_available: bool
    vehicle_type: str
    timestamp: datetime

@dataclass
class PricingUpdate:
    """Pricing update data structure"""
    zone_id: str
    surge_multiplier: float
    supply_count: int
    demand_count: int
    algorithm_used: str
    timestamp: datetime

@dataclass
class AnalyticsEvent:
    """Analytics event data structure"""
    event_type: str
    zone_id: str
    data: Dict[str, Any]
    timestamp: datetime

@dataclass
class ConfigUpdate:
    """Configuration update data structure"""
    config_type: str
    zone_id: Optional[str]
    config_data: Dict[str, Any]
    timestamp: datetime

class NATsStreamManager:
    """NATs JetStream manager for Equilibrium pricing system"""
    
    def __init__(self, nats_url: str = "nats://localhost:4222"):
        self.nats_url = nats_url
        self.nc: Optional[nats.NATS] = None
        self.js: Optional[JetStreamContext] = None
        self.streams_configured = False
        self.connected = False
        
    async def connect(self):
        """Connect to NATs server"""
        try:
            logger.info(f"🔌 Connecting to NATs at {self.nats_url}")
            self.nc = await nats.connect(self.nats_url)
            self.js = self.nc.jetstream()
            self.connected = True
            logger.info("✅ Connected to NATs successfully")
            
            # Setup streams
            await self._setup_streams()
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to NATs: {e}")
            raise
    
    async def _setup_streams(self):
        """Setup required JetStream streams"""
        try:
            logger.info("🚀 Setting up NATs JetStream streams...")
            
            # 1. Location Events Stream
            await self.js.add_stream(StreamConfig(
                name="LOCATION_EVENTS",
                subjects=["location.*"],
                retention=RetentionPolicy.WORKQUEUE,
                storage=StorageType.FILE,
                max_age=3600,  # 1 hour
                max_msgs=1000000,
                max_bytes=1024 * 1024 * 100,  # 100MB
                replicas=3,
                discard=DiscardPolicy.OLD,
                compression=StorageType.FILE  # Enable compression
            ))
            logger.info("✅ LOCATION_EVENTS stream configured")
            
            # 2. Pricing Updates Stream
            await self.js.add_stream(StreamConfig(
                name="PRICING_UPDATES",
                subjects=["pricing.*"],
                retention=RetentionPolicy.LIMITS,
                storage=StorageType.FILE,
                max_age=86400,  # 24 hours
                max_msgs=100000,
                max_bytes=1024 * 1024 * 50,  # 50MB
                replicas=3,
                discard=DiscardPolicy.OLD,
                compression=StorageType.FILE
            ))
            logger.info("✅ PRICING_UPDATES stream configured")
            
            # 3. Analytics Events Stream
            await self.js.add_stream(StreamConfig(
                name="ANALYTICS_EVENTS",
                subjects=["analytics.*"],
                retention=RetentionPolicy.LIMITS,
                storage=StorageType.FILE,
                max_age=604800,  # 7 days
                max_msgs=1000000,
                max_bytes=1024 * 1024 * 200,  # 200MB
                replicas=3,
                discard=DiscardPolicy.OLD,
                compression=StorageType.FILE
            ))
            logger.info("✅ ANALYTICS_EVENTS stream configured")
            
            # 4. Configuration Updates Stream
            await self.js.add_stream(StreamConfig(
                name="CONFIG_UPDATES",
                subjects=["config.*"],
                retention=RetentionPolicy.LIMITS,
                storage=StorageType.FILE,
                max_age=2592000,  # 30 days
                max_msgs=10000,
                max_bytes=1024 * 1024 * 10,  # 10MB
                replicas=3,
                discard=DiscardPolicy.OLD,
                compression=StorageType.FILE
            ))
            logger.info("✅ CONFIG_UPDATES stream configured")
            
            # 5. WebSocket Events Stream
            await self.js.add_stream(StreamConfig(
                name="WEBSOCKET_EVENTS",
                subjects=["websocket.*"],
                retention=RetentionPolicy.WORKQUEUE,
                storage=StorageType.FILE,
                max_age=3600,  # 1 hour
                max_msgs=100000,
                max_bytes=1024 * 1024 * 50,  # 50MB
                replicas=3,
                discard=DiscardPolicy.OLD,
                compression=StorageType.FILE
            ))
            logger.info("✅ WEBSOCKET_EVENTS stream configured")
            
            self.streams_configured = True
            logger.info("🎉 All NATs JetStream streams configured successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup streams: {e}")
            raise
    
    async def publish_location_event(self, event: LocationEvent):
        """Publish location event"""
        try:
            subject = f"location.{event.zone_id}"
            data = asdict(event)
            data['timestamp'] = event.timestamp.isoformat()
            
            await self.js.publish(subject, json.dumps(data).encode())
            logger.debug(f"📍 Published location event for zone {event.zone_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to publish location event: {e}")
            raise
    
    async def publish_pricing_update(self, update: PricingUpdate):
        """Publish pricing update"""
        try:
            subject = f"pricing.{update.zone_id}"
            data = asdict(update)
            data['timestamp'] = update.timestamp.isoformat()
            
            await self.js.publish(subject, json.dumps(data).encode())
            logger.debug(f"💰 Published pricing update for zone {update.zone_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to publish pricing update: {e}")
            raise
    
    async def publish_analytics_event(self, event: AnalyticsEvent):
        """Publish analytics event"""
        try:
            subject = f"analytics.{event.event_type}.{event.zone_id}"
            data = asdict(event)
            data['timestamp'] = event.timestamp.isoformat()
            
            await self.js.publish(subject, json.dumps(data).encode())
            logger.debug(f"📊 Published analytics event: {event.event_type}")
            
        except Exception as e:
            logger.error(f"❌ Failed to publish analytics event: {e}")
            raise
    
    async def publish_config_update(self, update: ConfigUpdate):
        """Publish configuration update"""
        try:
            subject = f"config.{update.config_type}"
            if update.zone_id:
                subject += f".{update.zone_id}"
            
            data = asdict(update)
            data['timestamp'] = update.timestamp.isoformat()
            
            await self.js.publish(subject, json.dumps(data).encode())
            logger.debug(f"⚙️ Published config update: {update.config_type}")
            
        except Exception as e:
            logger.error(f"❌ Failed to publish config update: {e}")
            raise
    
    async def publish_websocket_event(self, event_type: str, data: Dict[str, Any]):
        """Publish WebSocket event"""
        try:
            subject = f"websocket.{event_type}"
            event_data = {
                'event_type': event_type,
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await self.js.publish(subject, json.dumps(event_data).encode())
            logger.debug(f"🌐 Published WebSocket event: {event_type}")
            
        except Exception as e:
            logger.error(f"❌ Failed to publish WebSocket event: {e}")
            raise
    
    async def subscribe_location_events(self, zone_id: str, callback: Callable[[LocationEvent], None]):
        """Subscribe to location events for specific zone"""
        try:
            subject = f"location.{zone_id}"
            
            async def message_handler(msg):
                try:
                    data = json.loads(msg.data.decode())
                    event = LocationEvent(
                        event_id=data["event_id"],
                        driver_id=data["driver_id"],
                        latitude=data["latitude"],
                        longitude=data["longitude"],
                        s2_cell_id=data["s2_cell_id"],
                        zone_id=data["zone_id"],
                        is_available=data["is_available"],
                        vehicle_type=data["vehicle_type"],
                        timestamp=datetime.fromisoformat(data["timestamp"])
                    )
                    await callback(event)
                    await msg.ack()
                except Exception as e:
                    logger.error(f"❌ Error processing location event: {e}")
                    await msg.nak()
            
            # Durable consumer to ensure no message loss
            await self.js.subscribe(
                subject,
                cb=message_handler,
                durable=f"location-processor-{zone_id}",
                manual_ack=True
            )
            logger.info(f"📍 Subscribed to location events for zone {zone_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to location events: {e}")
            raise
    
    async def subscribe_all_location_events(self, callback: Callable[[LocationEvent], None]):
        """Subscribe to all location events"""
        try:
            subject = "location.*"
            
            async def message_handler(msg):
                try:
                    data = json.loads(msg.data.decode())
                    event = LocationEvent(
                        event_id=data["event_id"],
                        driver_id=data["driver_id"],
                        latitude=data["latitude"],
                        longitude=data["longitude"],
                        s2_cell_id=data["s2_cell_id"],
                        zone_id=data["zone_id"],
                        is_available=data["is_available"],
                        vehicle_type=data["vehicle_type"],
                        timestamp=datetime.fromisoformat(data["timestamp"])
                    )
                    await callback(event)
                    await msg.ack()
                except Exception as e:
                    logger.error(f"❌ Error processing location event: {e}")
                    await msg.nak()
            
            await self.js.subscribe(
                subject,
                cb=message_handler,
                durable="global-location-processor",
                manual_ack=True
            )
            logger.info("📍 Subscribed to all location events")
            
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to all location events: {e}")
            raise
    
    async def subscribe_pricing_updates(self, callback: Callable[[PricingUpdate], None]):
        """Subscribe to pricing updates"""
        try:
            subject = "pricing.*"
            
            async def message_handler(msg):
                try:
                    data = json.loads(msg.data.decode())
                    update = PricingUpdate(
                        zone_id=data["zone_id"],
                        surge_multiplier=data["surge_multiplier"],
                        supply_count=data["supply_count"],
                        demand_count=data["demand_count"],
                        algorithm_used=data["algorithm_used"],
                        timestamp=datetime.fromisoformat(data["timestamp"])
                    )
                    await callback(update)
                    await msg.ack()
                except Exception as e:
                    logger.error(f"❌ Error processing pricing update: {e}")
                    await msg.nak()
            
            await self.js.subscribe(
                subject,
                cb=message_handler,
                durable="pricing-update-processor",
                manual_ack=True
            )
            logger.info("💰 Subscribed to pricing updates")
            
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to pricing updates: {e}")
            raise
    
    async def subscribe_analytics_events(self, callback: Callable[[AnalyticsEvent], None]):
        """Subscribe to analytics events"""
        try:
            subject = "analytics.*"
            
            async def message_handler(msg):
                try:
                    data = json.loads(msg.data.decode())
                    event = AnalyticsEvent(
                        event_type=data["event_type"],
                        zone_id=data["zone_id"],
                        data=data["data"],
                        timestamp=datetime.fromisoformat(data["timestamp"])
                    )
                    await callback(event)
                    await msg.ack()
                except Exception as e:
                    logger.error(f"❌ Error processing analytics event: {e}")
                    await msg.nak()
            
            await self.js.subscribe(
                subject,
                cb=message_handler,
                durable="analytics-processor",
                manual_ack=True
            )
            logger.info("📊 Subscribed to analytics events")
            
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to analytics events: {e}")
            raise
    
    async def subscribe_config_updates(self, callback: Callable[[ConfigUpdate], None]):
        """Subscribe to configuration updates"""
        try:
            subject = "config.*"
            
            async def message_handler(msg):
                try:
                    data = json.loads(msg.data.decode())
                    update = ConfigUpdate(
                        config_type=data["config_type"],
                        zone_id=data.get("zone_id"),
                        config_data=data["config_data"],
                        timestamp=datetime.fromisoformat(data["timestamp"])
                    )
                    await callback(update)
                    await msg.ack()
                except Exception as e:
                    logger.error(f"❌ Error processing config update: {e}")
                    await msg.nak()
            
            await self.js.subscribe(
                subject,
                cb=message_handler,
                durable="config-processor",
                manual_ack=True
            )
            logger.info("⚙️ Subscribed to config updates")
            
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to config updates: {e}")
            raise
    
    async def get_stream_info(self, stream_name: str) -> Dict[str, Any]:
        """Get stream information"""
        try:
            stream_info = await self.js.stream_info(stream_name)
            return {
                'name': stream_info.config.name,
                'subjects': stream_info.config.subjects,
                'retention': stream_info.config.retention.name,
                'storage': stream_info.config.storage.name,
                'max_age': stream_info.config.max_age,
                'max_msgs': stream_info.config.max_msgs,
                'max_bytes': stream_info.config.max_bytes,
                'replicas': stream_info.config.replicas,
                'state': {
                    'messages': stream_info.state.messages,
                    'bytes': stream_info.state.bytes,
                    'first_seq': stream_info.state.first_seq,
                    'last_seq': stream_info.state.last_seq,
                    'consumer_count': stream_info.state.consumer_count
                }
            }
        except Exception as e:
            logger.error(f"❌ Failed to get stream info: {e}")
            raise
    
    async def get_all_streams_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information for all streams"""
        try:
            streams = {}
            stream_names = [
                "LOCATION_EVENTS",
                "PRICING_UPDATES", 
                "ANALYTICS_EVENTS",
                "CONFIG_UPDATES",
                "WEBSOCKET_EVENTS"
            ]
            
            for stream_name in stream_names:
                try:
                    streams[stream_name] = await self.get_stream_info(stream_name)
                except Exception as e:
                    logger.warning(f"⚠️ Could not get info for stream {stream_name}: {e}")
                    streams[stream_name] = {'error': str(e)}
            
            return streams
            
        except Exception as e:
            logger.error(f"❌ Failed to get all streams info: {e}")
            raise
    
    async def close(self):
        """Close NATs connection"""
        try:
            if self.nc:
                await self.nc.close()
                self.connected = False
                logger.info("🔌 NATs connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing NATs connection: {e}")
    
    def is_connected(self) -> bool:
        """Check if NATs is connected"""
        return self.connected and self.nc is not None and not self.nc.is_closed

# Example usage and testing
async def main():
    """Example usage of NATsStreamManager"""
    nats_manager = NATsStreamManager("nats://localhost:4222")
    
    try:
        # Connect to NATs
        await nats_manager.connect()
        
        # Create sample events
        location_event = LocationEvent(
            event_id="loc_001",
            driver_id="driver_123",
            latitude=10.762622,
            longitude=106.660172,
            s2_cell_id="s2_cell_001",
            zone_id="zone_001",
            is_available=True,
            vehicle_type="car",
            timestamp=datetime.utcnow()
        )
        
        pricing_update = PricingUpdate(
            zone_id="zone_001",
            surge_multiplier=1.5,
            supply_count=10,
            demand_count=15,
            algorithm_used="linear",
            timestamp=datetime.utcnow()
        )
        
        # Publish events
        await nats_manager.publish_location_event(location_event)
        await nats_manager.publish_pricing_update(pricing_update)
        
        # Get stream info
        streams_info = await nats_manager.get_all_streams_info()
        print("📊 Streams Info:")
        for stream_name, info in streams_info.items():
            print(f"  {stream_name}: {info}")
        
        # Keep running for a bit to see messages
        await asyncio.sleep(5)
        
    except Exception as e:
        logger.error(f"❌ Error in main: {e}")
    finally:
        await nats_manager.close()

if __name__ == "__main__":
    asyncio.run(main())

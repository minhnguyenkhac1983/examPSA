"""
Equilibrium Pricing Service - gRPC Server
Real-time surge pricing calculation service with gRPC support
"""

import grpc
from concurrent import futures
import asyncio
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, List
import redis
import asyncpg
from geopy.distance import geodesic

# Import generated gRPC code (would be generated from .proto file)
# from equilibrium.pricing.v1 import pricing_pb2
# from equilibrium.pricing.v1 import pricing_pb2_grpc

# For now, we'll create mock protobuf classes
class MockLocation:
    def __init__(self, latitude: float, longitude: float, address: str = "", zone_id: str = ""):
        self.latitude = latitude
        self.longitude = longitude
        self.address = address
        self.zone_id = zone_id

class MockPriceBreakdown:
    def __init__(self, base_fare: float, distance_fare: float, time_fare: float, 
                 surge_amount: float, taxes: float, fees: float, total_fare: float):
        self.base_fare = base_fare
        self.distance_fare = distance_fare
        self.time_fare = time_fare
        self.surge_amount = surge_amount
        self.taxes = taxes
        self.fees = fees
        self.total_fare = total_fare

class MockSurgeInfo:
    def __init__(self, multiplier: float, reason: str, demand_level: str, 
                 supply_level: str, valid_until: datetime):
        self.multiplier = multiplier
        self.reason = reason
        self.demand_level = demand_level
        self.supply_level = supply_level
        self.valid_until = valid_until

class MockZoneInfo:
    def __init__(self, zone_id: str, zone_name: str, city: str, zone_type: str,
                 base_fare: float, minimum_fare: float, maximum_surge_multiplier: float, is_active: bool):
        self.zone_id = zone_id
        self.zone_name = zone_name
        self.city = city
        self.zone_type = zone_type
        self.base_fare = base_fare
        self.minimum_fare = minimum_fare
        self.maximum_surge_multiplier = maximum_surge_multiplier
        self.is_active = is_active

class MockEstimatePriceRequest:
    def __init__(self, rider_id: str, pickup_location: MockLocation, dropoff_location: MockLocation,
                 vehicle_type: str, service_type: str, request_time: datetime, metadata: dict):
        self.rider_id = rider_id
        self.pickup_location = pickup_location
        self.dropoff_location = dropoff_location
        self.vehicle_type = vehicle_type
        self.service_type = service_type
        self.request_time = request_time
        self.metadata = metadata

class MockEstimatePriceResponse:
    def __init__(self, quote_id: str, estimated_fare: float, currency: str, breakdown: MockPriceBreakdown,
                 surge_info: MockSurgeInfo, pickup_zone: MockZoneInfo, dropoff_zone: MockZoneInfo,
                 estimated_duration_minutes: int, estimated_distance_km: float, 
                 quote_expires_at: datetime, created_at: datetime, status: str, error_message: str):
        self.quote_id = quote_id
        self.estimated_fare = estimated_fare
        self.currency = currency
        self.breakdown = breakdown
        self.surge_info = surge_info
        self.pickup_zone = pickup_zone
        self.dropoff_zone = dropoff_zone
        self.estimated_duration_minutes = estimated_duration_minutes
        self.estimated_distance_km = estimated_distance_km
        self.quote_expires_at = quote_expires_at
        self.created_at = created_at
        self.status = status
        self.error_message = error_message

class MockHeatmapCell:
    def __init__(self, location: MockLocation, surge_multiplier: float, demand_level: str,
                 supply_level: str, available_drivers: int, active_requests: int, zone_id: str):
        self.location = location
        self.surge_multiplier = surge_multiplier
        self.demand_level = demand_level
        self.supply_level = supply_level
        self.available_drivers = available_drivers
        self.active_requests = active_requests
        self.zone_id = zone_id

class MockGetHeatmapDataRequest:
    def __init__(self, center_location: MockLocation, radius_km: float, grid_size: int,
                 vehicle_type: str, timestamp: datetime, zone_ids: List[str]):
        self.center_location = center_location
        self.radius_km = radius_km
        self.grid_size = grid_size
        self.vehicle_type = vehicle_type
        self.timestamp = timestamp
        self.zone_ids = zone_ids

class MockGetHeatmapDataResponse:
    def __init__(self, cells: List[MockHeatmapCell], generated_at: datetime, 
                 grid_resolution_km: float, total_cells: int, status: str, error_message: str):
        self.cells = cells
        self.generated_at = generated_at
        self.grid_resolution_km = grid_resolution_km
        self.total_cells = total_cells
        self.status = status
        self.error_message = error_message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
redis_client = None
db_pool = None

# Demo data
DEMO_ZONES = {
    "sf_downtown_001": {
        "zone_id": "sf_downtown_001",
        "zone_name": "San Francisco Downtown",
        "city": "San Francisco",
        "zone_type": "downtown",
        "center_lat": 37.7749,
        "center_lng": -122.4194,
        "base_fare": 8.50,
        "minimum_fare": 5.00,
        "maximum_surge_multiplier": 5.00,
        "is_active": True
    },
    "sf_mission_001": {
        "zone_id": "sf_mission_001",
        "zone_name": "San Francisco Mission",
        "city": "San Francisco",
        "zone_type": "residential",
        "center_lat": 37.7849,
        "center_lng": -122.4094,
        "base_fare": 7.50,
        "minimum_fare": 5.00,
        "maximum_surge_multiplier": 3.00,
        "is_active": True
    },
    "sf_soma_001": {
        "zone_id": "sf_soma_001",
        "zone_name": "San Francisco SOMA",
        "city": "San Francisco",
        "zone_type": "commercial",
        "center_lat": 37.7649,
        "center_lng": -122.4294,
        "base_fare": 9.00,
        "minimum_fare": 5.00,
        "maximum_surge_multiplier": 4.00,
        "is_active": True
    }
}

DEMO_SUPPLY_DEMAND = {
    "sf_downtown_001": {"supply": 32, "demand": 28, "multiplier": 1.3},
    "sf_mission_001": {"supply": 45, "demand": 15, "multiplier": 1.0},
    "sf_soma_001": {"supply": 28, "demand": 22, "multiplier": 1.1}
}

class PricingServiceServicer:
    """gRPC service implementation for Pricing Service"""
    
    def __init__(self):
        self.redis_client = redis_client
        self.db_pool = db_pool
    
    async def EstimatePrice(self, request, context):
        """🚗 Price Estimation: Requesting a price estimate for a ride"""
        try:
            logger.info(f"Processing price estimate request for rider: {request.rider_id}")
            
            # Find zone for pickup location
            pickup_zone = self.find_zone_for_location(
                request.pickup_location.latitude,
                request.pickup_location.longitude
            )
            
            if not pickup_zone:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("No zone found for pickup location")
                return MockEstimatePriceResponse(
                    quote_id="", estimated_fare=0, currency="USD",
                    breakdown=None, surge_info=None, pickup_zone=None, dropoff_zone=None,
                    estimated_duration_minutes=0, estimated_distance_km=0,
                    quote_expires_at=datetime.now(), created_at=datetime.now(),
                    status="error", error_message="No zone found for pickup location"
                )
            
            # Find zone for dropoff location
            dropoff_zone = self.find_zone_for_location(
                request.dropoff_location.latitude,
                request.dropoff_location.longitude
            )
            
            if not dropoff_zone:
                dropoff_zone = pickup_zone  # Use pickup zone as fallback
            
            # Get current supply/demand data
            supply_demand = DEMO_SUPPLY_DEMAND.get(pickup_zone["zone_id"], {"supply": 10, "demand": 5, "multiplier": 1.0})
            
            # Calculate surge multiplier
            surge_multiplier = self.calculate_surge_multiplier(supply_demand["supply"], supply_demand["demand"])
            surge_multiplier = max(1.0, min(surge_multiplier, pickup_zone["maximum_surge_multiplier"]))
            
            # Calculate distance and duration
            distance = self.calculate_distance(request.pickup_location, request.dropoff_location)
            duration = self.calculate_duration(distance)
            
            # Calculate pricing breakdown
            base_fare = pickup_zone["base_fare"]
            distance_fare = distance * 2.5  # $2.5 per km
            time_fare = duration * 0.5  # $0.5 per minute
            surge_amount = (base_fare + distance_fare + time_fare) * (surge_multiplier - 1.0)
            total_fare = (base_fare + distance_fare + time_fare) * surge_multiplier
            
            # Generate quote ID and validity
            quote_id = str(uuid.uuid4())
            quote_expires_at = datetime.now() + timedelta(seconds=30)
            created_at = datetime.now()
            
            # Determine demand and supply levels
            demand_level = self.get_demand_level(surge_multiplier)
            supply_level = self.get_supply_level(supply_demand["supply"], supply_demand["demand"])
            
            # Create response objects
            breakdown = MockPriceBreakdown(
                base_fare=base_fare,
                distance_fare=distance_fare,
                time_fare=time_fare,
                surge_amount=surge_amount,
                taxes=0.0,
                fees=0.0,
                total_fare=total_fare
            )
            
            surge_info = MockSurgeInfo(
                multiplier=surge_multiplier,
                reason="high_demand_rush_hour" if surge_multiplier > 1.2 else "normal_demand",
                demand_level=demand_level,
                supply_level=supply_level,
                valid_until=quote_expires_at
            )
            
            pickup_zone_info = MockZoneInfo(
                zone_id=pickup_zone["zone_id"],
                zone_name=pickup_zone["zone_name"],
                city=pickup_zone["city"],
                zone_type=pickup_zone["zone_type"],
                base_fare=pickup_zone["base_fare"],
                minimum_fare=pickup_zone["minimum_fare"],
                maximum_surge_multiplier=pickup_zone["maximum_surge_multiplier"],
                is_active=pickup_zone["is_active"]
            )
            
            dropoff_zone_info = MockZoneInfo(
                zone_id=dropoff_zone["zone_id"],
                zone_name=dropoff_zone["zone_name"],
                city=dropoff_zone["city"],
                zone_type=dropoff_zone["zone_type"],
                base_fare=dropoff_zone["base_fare"],
                minimum_fare=dropoff_zone["minimum_fare"],
                maximum_surge_multiplier=dropoff_zone["maximum_surge_multiplier"],
                is_active=dropoff_zone["is_active"]
            )
            
            # Store quote in Redis for validation
            if self.redis_client:
                quote_key = f"quote:{quote_id}"
                self.redis_client.hset(quote_key, mapping={
                    "rider_id": request.rider_id,
                    "pickup_zone_id": pickup_zone["zone_id"],
                    "dropoff_zone_id": dropoff_zone["zone_id"],
                    "base_fare": str(base_fare),
                    "surge_multiplier": str(surge_multiplier),
                    "final_fare": str(total_fare),
                    "quote_expires_at": quote_expires_at.isoformat(),
                    "created_at": created_at.isoformat()
                })
                self.redis_client.expire(quote_key, 60)  # Expire after 1 minute
            
            # Log pricing event
            await self.log_pricing_event(quote_id, pickup_zone["zone_id"], request.rider_id,
                                       base_fare, surge_multiplier, total_fare)
            
            response = MockEstimatePriceResponse(
                quote_id=quote_id,
                estimated_fare=round(total_fare, 2),
                currency="USD",
                breakdown=breakdown,
                surge_info=surge_info,
                pickup_zone=pickup_zone_info,
                dropoff_zone=dropoff_zone_info,
                estimated_duration_minutes=duration,
                estimated_distance_km=round(distance, 2),
                quote_expires_at=quote_expires_at,
                created_at=created_at,
                status="success",
                error_message=""
            )
            
            logger.info(f"Price estimate generated: {quote_id}, multiplier: {surge_multiplier}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating price estimate: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return MockEstimatePriceResponse(
                quote_id="", estimated_fare=0, currency="USD",
                breakdown=None, surge_info=None, pickup_zone=None, dropoff_zone=None,
                estimated_duration_minutes=0, estimated_distance_km=0,
                quote_expires_at=datetime.now(), created_at=datetime.now(),
                status="error", error_message=str(e)
            )
    
    async def GetHeatmapData(self, request, context):
        """🗺️ Heatmap Data: Fetching heatmap data for client apps"""
        try:
            logger.info(f"Processing heatmap data request for center: {request.center_location.latitude}, {request.center_location.longitude}")
            
            cells = []
            grid_resolution = request.radius_km / request.grid_size
            
            # Generate heatmap cells around center location
            for i in range(request.grid_size):
                for j in range(request.grid_size):
                    # Calculate cell location
                    lat_offset = (i - request.grid_size // 2) * grid_resolution / 111.0  # Approximate km to degrees
                    lng_offset = (j - request.grid_size // 2) * grid_resolution / (111.0 * abs(request.center_location.latitude))
                    
                    cell_lat = request.center_location.latitude + lat_offset
                    cell_lng = request.center_location.longitude + lng_offset
                    
                    # Find zone for this cell
                    zone = self.find_zone_for_location(cell_lat, cell_lng)
                    
                    if zone:
                        supply_demand = DEMO_SUPPLY_DEMAND.get(zone["zone_id"], {"supply": 10, "demand": 5, "multiplier": 1.0})
                        
                        cell_location = MockLocation(
                            latitude=cell_lat,
                            longitude=cell_lng,
                            address=f"Cell {i},{j}",
                            zone_id=zone["zone_id"]
                        )
                        
                        cell = MockHeatmapCell(
                            location=cell_location,
                            surge_multiplier=supply_demand["multiplier"],
                            demand_level=self.get_demand_level(supply_demand["multiplier"]),
                            supply_level=self.get_supply_level(supply_demand["supply"], supply_demand["demand"]),
                            available_drivers=supply_demand["supply"],
                            active_requests=supply_demand["demand"],
                            zone_id=zone["zone_id"]
                        )
                        cells.append(cell)
            
            response = MockGetHeatmapDataResponse(
                cells=cells,
                generated_at=datetime.now(),
                grid_resolution_km=grid_resolution,
                total_cells=len(cells),
                status="success",
                error_message=""
            )
            
            logger.info(f"Heatmap data generated: {len(cells)} cells")
            return response
            
        except Exception as e:
            logger.error(f"Error generating heatmap data: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return MockGetHeatmapDataResponse(
                cells=[],
                generated_at=datetime.now(),
                grid_resolution_km=0,
                total_cells=0,
                status="error",
                error_message=str(e)
            )
    
    def find_zone_for_location(self, lat: float, lng: float) -> Optional[dict]:
        """Find the zone for a given location"""
        min_distance = float('inf')
        closest_zone = None
        
        for zone_id, zone in DEMO_ZONES.items():
            distance = geodesic(
                (lat, lng),
                (zone["center_lat"], zone["center_lng"])
            ).kilometers
            
            if distance < min_distance and distance < 5.0:  # Within 5km
                min_distance = distance
                closest_zone = zone
        
        return closest_zone
    
    def calculate_surge_multiplier(self, supply: int, demand: int) -> float:
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
    
    def calculate_distance(self, pickup, dropoff) -> float:
        """Calculate distance between two points in kilometers"""
        return geodesic(
            (pickup.latitude, pickup.longitude),
            (dropoff.latitude, dropoff.longitude)
        ).kilometers
    
    def calculate_duration(self, distance: float) -> int:
        """Calculate estimated duration in minutes"""
        # Assume average speed of 30 km/h in city
        return int((distance / 30) * 60)
    
    def get_demand_level(self, surge_multiplier: float) -> str:
        """Get demand level based on surge multiplier"""
        if surge_multiplier >= 2.0:
            return "extreme"
        elif surge_multiplier >= 1.5:
            return "high"
        elif surge_multiplier >= 1.2:
            return "medium"
        else:
            return "low"
    
    def get_supply_level(self, supply: int, demand: int) -> str:
        """Get supply level based on supply and demand"""
        if supply == 0:
            return "none"
        elif supply < demand * 0.5:
            return "low"
        elif supply < demand:
            return "normal"
        else:
            return "high"
    
    async def log_pricing_event(self, quote_id: str, zone_id: str, rider_id: str,
                               base_fare: float, surge_multiplier: float, final_fare: float):
        """Log pricing event to database"""
        try:
            if self.db_pool:
                async with self.db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO pricing_event_logs 
                        (log_id, zone_id, rider_id, event_type, base_fare, 
                         surge_multiplier, final_fare, quote_timestamp)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """, quote_id, zone_id, rider_id, "price_quote", base_fare,
                        surge_multiplier, final_fare, datetime.now())
        except Exception as e:
            logger.error(f"Failed to log pricing event: {e}")

async def serve():
    """Start the gRPC server"""
    global redis_client, db_pool
    
    # Initialize connections
    try:
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        redis_client.ping()
        logger.info("Connected to Redis")
        
        db_pool = await asyncpg.create_pool(
            "postgresql://equilibrium:equilibrium123@localhost:5432/equilibrium"
        )
        logger.info("Connected to PostgreSQL")
        
    except Exception as e:
        logger.error(f"Failed to initialize connections: {e}")
    
    # Create gRPC server
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add service to server
    # pricing_pb2_grpc.add_PricingServiceServicer_to_server(PricingServiceServicer(), server)
    
    # For now, we'll use a mock server setup
    listen_addr = '[::]:8001'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting gRPC server on {listen_addr}")
    await server.start()
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server")
        await server.stop(5)

if __name__ == "__main__":
    asyncio.run(serve())

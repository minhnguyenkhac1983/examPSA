"""
Simple Equilibrium Pricing Service for Demo
"""

from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Equilibrium Pricing Service", version="1.0.0")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "pricing-service",
        "version": "1.0.0"
    }

@app.get("/api/v1/pricing/zones")
async def get_zones():
    """Get all zones"""
    return {
        "zones": [
            {
                "zone_id": "downtown_financial",
                "zone_name": "Downtown Financial District",
                "current_supply": 15,
                "current_demand": 8,
                "current_multiplier": 1.3
            },
            {
                "zone_id": "stadium_area", 
                "zone_name": "Stadium Area",
                "current_supply": 5,
                "current_demand": 20,
                "current_multiplier": 2.8
            },
            {
                "zone_id": "airport",
                "zone_name": "San Francisco Airport", 
                "current_supply": 25,
                "current_demand": 12,
                "current_multiplier": 1.1
            }
        ]
    }

@app.post("/api/v1/pricing/estimate")
async def get_price_estimate(request: dict):
    """Get price estimate with enhanced logic"""
    # Extract request data
    pickup_location = request.get("pickup_location", {})
    dropoff_location = request.get("dropoff_location", {})
    vehicle_type = request.get("vehicle_type", "standard")
    
    # Calculate base fare
    base_fare = 8.50
    
    # Calculate distance (simplified)
    pickup_lat = pickup_location.get("latitude", 37.7749)
    pickup_lng = pickup_location.get("longitude", -122.4194)
    dropoff_lat = dropoff_location.get("latitude", 37.7849)
    dropoff_lng = dropoff_location.get("longitude", -122.4094)
    
    # Simple distance calculation
    import math
    distance = math.sqrt((dropoff_lat - pickup_lat)**2 + (dropoff_lng - pickup_lng)**2) * 111.32  # km
    
    # Dynamic pricing based on location and time
    surge_multiplier = 1.0
    if pickup_lat > 37.78:  # Airport area
        surge_multiplier = 1.1
    elif pickup_lat < 37.77:  # Downtown area
        surge_multiplier = 1.3
    
    # Vehicle type multiplier
    vehicle_multipliers = {
        "standard": 1.0,
        "premium": 1.5,
        "xl": 1.8
    }
    vehicle_multiplier = vehicle_multipliers.get(vehicle_type, 1.0)
    
    # Calculate final fare
    fare_estimate = base_fare + (distance * 2.5) * surge_multiplier * vehicle_multiplier
    
    return {
        "quote_id": f"quote_{hash(str(request)) % 10000}",
        "base_fare": base_fare,
        "surge_multiplier": round(surge_multiplier, 2),
        "vehicle_multiplier": vehicle_multiplier,
        "final_fare": round(fare_estimate, 2),
        "currency": "USD",
        "quote_valid_until": "2025-09-16T01:30:00Z",
        "estimated_duration": max(8, int(distance * 3)),
        "estimated_distance": round(distance, 2),
        "zone_info": {
            "zone_id": "dynamic_zone",
            "zone_name": "Dynamic Pricing Zone",
            "current_demand_level": "medium"
        },
        "confidence_score": 0.92,
        "breakdown": {
            "base_fare": base_fare,
            "distance_fare": round(distance * 2.5, 2),
            "surge_adjustment": round((surge_multiplier - 1) * 100, 1),
            "vehicle_adjustment": round((vehicle_multiplier - 1) * 100, 1)
        }
    }

@app.get("/api/v1/pricing/heatmap")
async def get_heatmap():
    """Get pricing heatmap data"""
    return {
        "zones": [
            {
                "zone_id": "downtown_financial",
                "zone_name": "Downtown Financial District",
                "center": {"latitude": 37.7749, "longitude": -122.4194},
                "surge_multiplier": 1.3,
                "demand_level": "high",
                "supply_count": 15,
                "demand_count": 25,
                "color": "#ff6b6b"
            },
            {
                "zone_id": "stadium_area",
                "zone_name": "Stadium Area",
                "center": {"latitude": 37.7786, "longitude": -122.3893},
                "surge_multiplier": 2.8,
                "demand_level": "very_high",
                "supply_count": 5,
                "demand_count": 35,
                "color": "#ff4757"
            },
            {
                "zone_id": "airport",
                "zone_name": "San Francisco Airport",
                "center": {"latitude": 37.6213, "longitude": -122.3790},
                "surge_multiplier": 1.1,
                "demand_level": "medium",
                "supply_count": 25,
                "demand_count": 12,
                "color": "#2ed573"
            },
            {
                "zone_id": "mission_district",
                "zone_name": "Mission District",
                "center": {"latitude": 37.7599, "longitude": -122.4148},
                "surge_multiplier": 1.5,
                "demand_level": "high",
                "supply_count": 12,
                "demand_count": 18,
                "color": "#ffa502"
            },
            {
                "zone_id": "soma",
                "zone_name": "SoMa District",
                "center": {"latitude": 37.7749, "longitude": -122.4194},
                "surge_multiplier": 1.8,
                "demand_level": "high",
                "supply_count": 8,
                "demand_count": 22,
                "color": "#ff6348"
            }
        ],
        "last_updated": "2025-09-16T01:00:00Z",
        "total_zones": 5
    }

@app.post("/api/v1/pricing/zones/{zone_id}/supply-demand")
async def update_supply_demand(zone_id: str, supply: int, demand: int):
    """Update supply and demand"""
    return {
        "zone_id": zone_id,
        "supply": supply,
        "demand": demand,
        "surge_multiplier": 1.5,
        "updated_at": "2025-09-16T01:00:00Z"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

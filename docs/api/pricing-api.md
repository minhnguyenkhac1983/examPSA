# Pricing API Documentation

## Overview
The Pricing API provides real-time dynamic pricing calculations for the Equilibrium platform. It handles price estimation requests, surge pricing calculations, and heatmap data.

## Base URL
```
https://api.equilibrium.com/api/v1/pricing
```

## Authentication
All API requests require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Endpoints

### 1. Price Estimation

**POST** `/estimate`

Calculate the estimated fare for a ride request.

#### Request Body
```json
{
  "pickup_location": {
    "latitude": 37.7749,
    "longitude": -122.4194
  },
  "dropoff_location": {
    "latitude": 37.7849,
    "longitude": -122.4094
  },
  "vehicle_type": "standard",
  "user_id": "user_123"
}
```

#### Response
```json
{
  "quote_id": "quote_abc123",
  "base_fare": 8.50,
  "surge_multiplier": 1.3,
  "final_fare": 11.05,
  "currency": "USD",
  "quote_valid_until": "2025-01-16T10:30:00Z",
  "estimated_duration": 12,
  "estimated_distance": 2.1,
  "zone_info": {
    "zone_id": "sf_downtown",
    "zone_name": "San Francisco Downtown",
    "current_demand_level": "high"
  }
}
```

#### Error Responses
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Invalid or missing authentication token
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### 2. Heatmap Data

**GET** `/heatmap`

Retrieve heatmap data for visualization.

#### Query Parameters
- `bounds` (required): Bounding box as "lat1,lng1,lat2,lng2"
- `zoom` (optional): Zoom level (default: 12)

#### Example Request
```
GET /heatmap?bounds=37.7,-122.5,37.8,-122.3&zoom=12
```

#### Response
```json
{
  "zones": [
    {
      "zone_id": "sf_financial",
      "zone_name": "Financial District",
      "center": {"latitude": 37.7749, "longitude": -122.4194},
      "surge_multiplier": 1.8,
      "demand_level": "high",
      "supply_count": 15,
      "demand_count": 25,
      "color": "#ff6b6b"
    }
  ],
  "last_updated": "2025-01-16T10:00:00Z",
  "total_zones": 156
}
```

### 3. Driver Heatmap

**GET** `/driver/heatmap`

Get recommended zones for drivers.

#### Query Parameters
- `driver_id` (required): Driver identifier
- `radius` (optional): Search radius in meters (default: 5000)

#### Example Request
```
GET /driver/heatmap?driver_id=driver_123&radius=5000
```

#### Response
```json
{
  "recommended_zones": [
    {
      "zone_id": "sf_mission",
      "zone_name": "Mission District",
      "distance_meters": 1200,
      "surge_multiplier": 2.1,
      "estimated_earnings_per_hour": 45.50,
      "demand_trend": "increasing"
    }
  ],
  "current_location": {
    "latitude": 37.7599,
    "longitude": -122.4148
  }
}
```

## Rate Limits
- **Price Estimation**: 100 requests per minute per user
- **Heatmap Data**: 60 requests per minute per user
- **Driver Heatmap**: 30 requests per minute per driver

## Response Codes
- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

## WebSocket Updates

### Connection
```
wss://api.equilibrium.com/ws/pricing
```

### Subscribe to Zone Updates
```json
{
  "type": "subscribe",
  "zone_id": "sf_downtown"
}
```

### Price Update Message
```json
{
  "type": "price_update",
  "zone_id": "sf_downtown",
  "surge_multiplier": 1.5,
  "timestamp": "2025-01-16T10:00:00Z"
}
```

## SDK Examples

### Python
```python
import requests

# Price estimation
response = requests.post(
    "https://api.equilibrium.com/api/v1/pricing/estimate",
    headers={"Authorization": "Bearer your_jwt_token"},
    json={
        "pickup_location": {"latitude": 37.7749, "longitude": -122.4194},
        "dropoff_location": {"latitude": 37.7849, "longitude": -122.4094},
        "vehicle_type": "standard",
        "user_id": "user_123"
    }
)
```

### JavaScript
```javascript
// Price estimation
const response = await fetch('https://api.equilibrium.com/api/v1/pricing/estimate', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer your_jwt_token',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    pickup_location: {latitude: 37.7749, longitude: -122.4194},
    dropoff_location: {latitude: 37.7849, longitude: -122.4094},
    vehicle_type: 'standard',
    user_id: 'user_123'
  })
});
```

## Changelog

### v1.0.0 (2025-01-16)
- Initial release
- Price estimation endpoint
- Heatmap data endpoint
- Driver heatmap endpoint
- WebSocket support for real-time updates

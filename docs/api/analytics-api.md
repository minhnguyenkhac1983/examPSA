# Analytics API Documentation

## Overview
The Analytics API provides comprehensive analytics and reporting capabilities for the Equilibrium platform, including pricing trends, driver performance, and zone efficiency metrics.

## Base URL
```
https://api.equilibrium.com/api/v1/analytics
```

## Authentication
All API requests require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Endpoints

### 1. Pricing Trends

**GET** `/pricing-trends`

Get pricing trends over time for specific zones or globally.

#### Query Parameters
- `zone_id` (optional): Specific zone ID
- `start_date` (required): Start date (ISO 8601 format)
- `end_date` (required): End date (ISO 8601 format)
- `granularity` (optional): Data granularity (hour, day, week) - default: day

#### Example Request
```
GET /pricing-trends?zone_id=sf_downtown&start_date=2025-01-01T00:00:00Z&end_date=2025-01-31T23:59:59Z&granularity=day
```

#### Response
```json
{
  "zone_id": "sf_downtown",
  "zone_name": "San Francisco Downtown",
  "granularity": "day",
  "data_points": [
    {
      "timestamp": "2025-01-01T00:00:00Z",
      "avg_surge_multiplier": 1.2,
      "max_surge_multiplier": 2.1,
      "min_surge_multiplier": 1.0,
      "total_requests": 1250,
      "avg_wait_time": 3.5
    }
  ],
  "summary": {
    "avg_surge_multiplier": 1.4,
    "peak_surge_multiplier": 3.2,
    "total_requests": 38750,
    "avg_wait_time": 4.2
  }
}
```

### 2. Driver Performance

**GET** `/driver-performance`

Get performance metrics for drivers.

#### Query Parameters
- `driver_id` (optional): Specific driver ID
- `start_date` (required): Start date (ISO 8601 format)
- `end_date` (required): End date (ISO 8601 format)
- `metrics` (optional): Comma-separated list of metrics (earnings, rides, rating, efficiency)

#### Example Request
```
GET /driver-performance?start_date=2025-01-01T00:00:00Z&end_date=2025-01-31T23:59:59Z&metrics=earnings,rides,rating
```

#### Response
```json
{
  "drivers": [
    {
      "driver_id": "driver_001",
      "name": "John Smith",
      "metrics": {
        "total_earnings": 2450.75,
        "total_rides": 156,
        "avg_rating": 4.8,
        "efficiency_score": 0.92,
        "avg_earnings_per_hour": 28.50,
        "completion_rate": 0.96
      },
      "rank": 1
    }
  ],
  "summary": {
    "total_drivers": 1250,
    "avg_earnings": 1890.25,
    "avg_rating": 4.6,
    "avg_efficiency": 0.87
  }
}
```

### 3. Zone Efficiency

**GET** `/zone-efficiency`

Get efficiency metrics for pricing zones.

#### Query Parameters
- `zone_id` (optional): Specific zone ID
- `start_date` (required): Start date (ISO 8601 format)
- `end_date` (required): End date (ISO 8601 format)
- `metric` (optional): Efficiency metric (completion_rate, revenue_per_ride, utilization)

#### Example Request
```
GET /zone-efficiency?start_date=2025-01-01T00:00:00Z&end_date=2025-01-31T23:59:59Z&metric=completion_rate
```

#### Response
```json
{
  "zones": [
    {
      "zone_id": "sf_downtown",
      "zone_name": "San Francisco Downtown",
      "efficiency_metrics": {
        "completion_rate": 0.94,
        "revenue_per_ride": 18.75,
        "utilization_rate": 0.87,
        "avg_surge_multiplier": 1.4,
        "total_rides": 1250,
        "total_revenue": 23437.50
      },
      "efficiency_rank": 1
    }
  ],
  "summary": {
    "total_zones": 156,
    "avg_completion_rate": 0.89,
    "avg_revenue_per_ride": 16.25,
    "avg_utilization": 0.82
  }
}
```

### 4. Real-time Metrics

**GET** `/realtime-metrics`

Get current real-time system metrics.

#### Response
```json
{
  "timestamp": "2025-01-16T10:00:00Z",
  "system_metrics": {
    "active_drivers": 1250,
    "active_riders": 3400,
    "total_rides_in_progress": 89,
    "avg_wait_time": 3.2,
    "system_load": 0.75
  },
  "zone_metrics": [
    {
      "zone_id": "sf_downtown",
      "active_drivers": 45,
      "pending_requests": 12,
      "avg_surge_multiplier": 1.3,
      "demand_level": "high"
    }
  ]
}
```

### 5. Revenue Analytics

**GET** `/revenue-analytics`

Get revenue analytics and financial metrics.

#### Query Parameters
- `start_date` (required): Start date (ISO 8601 format)
- `end_date` (required): End date (ISO 8601 format)
- `breakdown` (optional): Breakdown by (zone, driver, vehicle_type, time_period)

#### Example Request
```
GET /revenue-analytics?start_date=2025-01-01T00:00:00Z&end_date=2025-01-31T23:59:59Z&breakdown=zone
```

#### Response
```json
{
  "total_revenue": 1250000.00,
  "total_rides": 75000,
  "avg_revenue_per_ride": 16.67,
  "breakdown": [
    {
      "zone_id": "sf_downtown",
      "zone_name": "San Francisco Downtown",
      "revenue": 187500.00,
      "ride_count": 11250,
      "avg_revenue_per_ride": 16.67,
      "percentage": 15.0
    }
  ],
  "trends": {
    "revenue_growth": 0.12,
    "ride_growth": 0.08,
    "avg_fare_growth": 0.04
  }
}
```

### 6. User Behavior Analytics

**GET** `/user-behavior`

Get user behavior analytics and patterns.

#### Query Parameters
- `user_type` (optional): User type (rider, driver)
- `start_date` (required): Start date (ISO 8601 format)
- `end_date` (required): End date (ISO 8601 format)
- `metric` (optional): Behavior metric (retention, engagement, conversion)

#### Example Request
```
GET /user-behavior?user_type=rider&start_date=2025-01-01T00:00:00Z&end_date=2025-01-31T23:59:59Z&metric=retention
```

#### Response
```json
{
  "user_type": "rider",
  "retention_metrics": {
    "day_1_retention": 0.85,
    "day_7_retention": 0.72,
    "day_30_retention": 0.58,
    "monthly_active_users": 125000,
    "new_users": 15000
  },
  "engagement_metrics": {
    "avg_sessions_per_user": 12.5,
    "avg_rides_per_user": 8.3,
    "avg_session_duration": 15.2
  },
  "conversion_metrics": {
    "signup_to_first_ride": 0.78,
    "price_estimate_to_ride": 0.45,
    "app_install_to_signup": 0.62
  }
}
```

## Rate Limits
- **Analytics endpoints**: 100 requests per hour per user
- **Real-time metrics**: 60 requests per minute per user
- **Admin users**: 1000 requests per hour

## Data Retention
- **Real-time metrics**: 24 hours
- **Daily metrics**: 1 year
- **Hourly metrics**: 3 months
- **Raw event data**: 30 days

## Export Formats
Analytics data can be exported in the following formats:
- JSON (default)
- CSV
- Excel

Add `?format=csv` or `?format=excel` to any endpoint to export data.

## SDK Examples

### Python
```python
import requests

# Get pricing trends
response = requests.get(
    "https://api.equilibrium.com/api/v1/analytics/pricing-trends",
    headers={"Authorization": "Bearer your_jwt_token"},
    params={
        "zone_id": "sf_downtown",
        "start_date": "2025-01-01T00:00:00Z",
        "end_date": "2025-01-31T23:59:59Z",
        "granularity": "day"
    }
)

# Get driver performance
response = requests.get(
    "https://api.equilibrium.com/api/v1/analytics/driver-performance",
    headers={"Authorization": "Bearer your_jwt_token"},
    params={
        "start_date": "2025-01-01T00:00:00Z",
        "end_date": "2025-01-31T23:59:59Z",
        "metrics": "earnings,rides,rating"
    }
)
```

### JavaScript
```javascript
// Get pricing trends
const response = await fetch('https://api.equilibrium.com/api/v1/analytics/pricing-trends?' + new URLSearchParams({
  zone_id: 'sf_downtown',
  start_date: '2025-01-01T00:00:00Z',
  end_date: '2025-01-31T23:59:59Z',
  granularity: 'day'
}), {
  headers: {'Authorization': 'Bearer your_jwt_token'}
});

// Get real-time metrics
const realtimeResponse = await fetch('https://api.equilibrium.com/api/v1/analytics/realtime-metrics', {
  headers: {'Authorization': 'Bearer your_jwt_token'}
});
```

## Error Codes

| Code | Description |
|------|-------------|
| `ANALYTICS_001` | Invalid date range |
| `ANALYTICS_002` | Zone not found |
| `ANALYTICS_003` | Insufficient data for analysis |
| `ANALYTICS_004` | Export format not supported |
| `ANALYTICS_005` | Rate limit exceeded |
| `ANALYTICS_006` | Insufficient permissions |

## Changelog

### v1.0.0 (2025-01-16)
- Initial release
- Pricing trends analytics
- Driver performance metrics
- Zone efficiency analysis
- Real-time metrics
- Revenue analytics
- User behavior analytics

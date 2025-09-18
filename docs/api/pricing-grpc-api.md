# Pricing Service - gRPC API

## Service Definition

```protobuf
syntax = "proto3";

package equilibrium.pricing.v1;

import "google/protobuf/timestamp.proto";
import "google/protobuf/empty.proto";

option go_package = "github.com/equilibrium/pricing/v1;pricingv1";

// Pricing Service for dynamic surge pricing
service PricingService {
  // 🚗 Price Estimation: Requesting a price estimate for a ride
  rpc EstimatePrice(EstimatePriceRequest) returns (EstimatePriceResponse);
  
  // 🗺️ Heatmap Data: Fetching heatmap data for client apps
  rpc GetHeatmapData(GetHeatmapDataRequest) returns (GetHeatmapDataResponse);
  
  // Get current surge multipliers for zones
  rpc GetSurgeMultipliers(GetSurgeMultipliersRequest) returns (GetSurgeMultipliersResponse);
  
  // Update supply/demand data for a zone
  rpc UpdateSupplyDemand(UpdateSupplyDemandRequest) returns (UpdateSupplyDemandResponse);
  
  // Get pricing zones
  rpc GetPricingZones(GetPricingZonesRequest) returns (GetPricingZonesResponse);
  
  // Health check
  rpc HealthCheck(google.protobuf.Empty) returns (HealthCheckResponse);
}

// Message Definitions

message Location {
  double latitude = 1;
  double longitude = 2;
  string address = 3;
  string zone_id = 4;
}

message PriceBreakdown {
  double base_fare = 1;
  double distance_fare = 2;
  double time_fare = 3;
  double surge_amount = 4;
  double taxes = 5;
  double fees = 6;
  double total_fare = 7;
}

message SurgeInfo {
  double multiplier = 1;
  string reason = 2;
  string demand_level = 3;
  string supply_level = 4;
  google.protobuf.Timestamp valid_until = 5;
}

message ZoneInfo {
  string zone_id = 1;
  string zone_name = 2;
  string city = 3;
  string zone_type = 4;
  double base_fare = 5;
  double minimum_fare = 6;
  double maximum_surge_multiplier = 7;
  bool is_active = 8;
}

// Request/Response Messages

message EstimatePriceRequest {
  string rider_id = 1;
  Location pickup_location = 2;
  Location dropoff_location = 3;
  string vehicle_type = 4;
  string service_type = 5;
  google.protobuf.Timestamp request_time = 6;
  map<string, string> metadata = 7;
}

message EstimatePriceResponse {
  string quote_id = 1;
  double estimated_fare = 2;
  string currency = 3;
  PriceBreakdown breakdown = 4;
  SurgeInfo surge_info = 5;
  ZoneInfo pickup_zone = 6;
  ZoneInfo dropoff_zone = 7;
  int32 estimated_duration_minutes = 8;
  double estimated_distance_km = 9;
  google.protobuf.Timestamp quote_expires_at = 10;
  google.protobuf.Timestamp created_at = 11;
  string status = 12;
  string error_message = 13;
}

message GetHeatmapDataRequest {
  Location center_location = 1;
  double radius_km = 2;
  int32 grid_size = 3;
  string vehicle_type = 4;
  google.protobuf.Timestamp timestamp = 5;
  repeated string zone_ids = 6;
}

message HeatmapCell {
  Location location = 1;
  double surge_multiplier = 2;
  string demand_level = 3;
  string supply_level = 4;
  int32 available_drivers = 5;
  int32 active_requests = 6;
  string zone_id = 7;
}

message GetHeatmapDataResponse {
  repeated HeatmapCell cells = 1;
  google.protobuf.Timestamp generated_at = 2;
  double grid_resolution_km = 3;
  int32 total_cells = 4;
  string status = 5;
  string error_message = 6;
}

message GetSurgeMultipliersRequest {
  repeated string zone_ids = 1;
  string vehicle_type = 2;
  google.protobuf.Timestamp timestamp = 3;
}

message ZoneSurgeInfo {
  string zone_id = 1;
  double surge_multiplier = 2;
  string demand_level = 3;
  string supply_level = 4;
  int32 available_drivers = 5;
  int32 active_requests = 6;
  google.protobuf.Timestamp last_updated = 7;
}

message GetSurgeMultipliersResponse {
  repeated ZoneSurgeInfo zones = 1;
  google.protobuf.Timestamp generated_at = 2;
  string status = 3;
  string error_message = 4;
}

message UpdateSupplyDemandRequest {
  string zone_id = 1;
  int32 supply_count = 2;
  int32 demand_count = 3;
  string vehicle_type = 4;
  google.protobuf.Timestamp timestamp = 5;
  map<string, string> metadata = 6;
}

message UpdateSupplyDemandResponse {
  string zone_id = 1;
  double new_surge_multiplier = 2;
  string demand_level = 3;
  string supply_level = 4;
  google.protobuf.Timestamp updated_at = 5;
  string status = 6;
  string error_message = 7;
}

message GetPricingZonesRequest {
  Location center_location = 1;
  double radius_km = 2;
  string city = 3;
  string zone_type = 4;
  bool active_only = 5;
}

message GetPricingZonesResponse {
  repeated ZoneInfo zones = 1;
  int32 total_zones = 2;
  google.protobuf.Timestamp generated_at = 3;
  string status = 4;
  string error_message = 5;
}

message HealthCheckResponse {
  string status = 1;
  google.protobuf.Timestamp timestamp = 2;
  string version = 3;
  map<string, string> metadata = 4;
}
```

## 🚗 Price Estimation Endpoint

### Method: `EstimatePrice`

**Description**: Requesting a price estimate for a ride with pickup and dropoff locations.

**Request Example**:
```json
{
  "rider_id": "rider_12345",
  "pickup_location": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "address": "123 Market St, San Francisco, CA",
    "zone_id": "sf_downtown_001"
  },
  "dropoff_location": {
    "latitude": 37.7849,
    "longitude": -122.4094,
    "address": "456 Mission St, San Francisco, CA",
    "zone_id": "sf_mission_001"
  },
  "vehicle_type": "standard",
  "service_type": "ride",
  "request_time": "2025-01-16T10:00:00Z",
  "metadata": {
    "app_version": "2.1.0",
    "platform": "ios"
  }
}
```

**Response Example**:
```json
{
  "quote_id": "quote_abc123456",
  "estimated_fare": 11.05,
  "currency": "USD",
  "breakdown": {
    "base_fare": 8.50,
    "distance_fare": 2.30,
    "time_fare": 1.20,
    "surge_amount": 2.55,
    "taxes": 0.00,
    "fees": 0.00,
    "total_fare": 11.05
  },
  "surge_info": {
    "multiplier": 1.3,
    "reason": "high_demand_rush_hour",
    "demand_level": "high",
    "supply_level": "normal",
    "valid_until": "2025-01-16T10:05:00Z"
  },
  "pickup_zone": {
    "zone_id": "sf_downtown_001",
    "zone_name": "San Francisco Downtown",
    "city": "San Francisco",
    "zone_type": "downtown",
    "base_fare": 8.50,
    "minimum_fare": 5.00,
    "maximum_surge_multiplier": 5.00,
    "is_active": true
  },
  "dropoff_zone": {
    "zone_id": "sf_mission_001",
    "zone_name": "San Francisco Mission",
    "city": "San Francisco",
    "zone_type": "residential",
    "base_fare": 7.50,
    "minimum_fare": 5.00,
    "maximum_surge_multiplier": 3.00,
    "is_active": true
  },
  "estimated_duration_minutes": 8,
  "estimated_distance_km": 2.3,
  "quote_expires_at": "2025-01-16T10:00:30Z",
  "created_at": "2025-01-16T10:00:00Z",
  "status": "success",
  "error_message": ""
}
```

## 🗺️ Heatmap Data Endpoint

### Method: `GetHeatmapData`

**Description**: Fetching heatmap data for client apps to display surge pricing visualization.

**Request Example**:
```json
{
  "center_location": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "address": "San Francisco, CA",
    "zone_id": "sf_downtown_001"
  },
  "radius_km": 10.0,
  "grid_size": 20,
  "vehicle_type": "standard",
  "timestamp": "2025-01-16T10:00:00Z",
  "zone_ids": ["sf_downtown_001", "sf_mission_001", "sf_soma_001"]
}
```

**Response Example**:
```json
{
  "cells": [
    {
      "location": {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "address": "Downtown SF",
        "zone_id": "sf_downtown_001"
      },
      "surge_multiplier": 1.3,
      "demand_level": "high",
      "supply_level": "normal",
      "available_drivers": 32,
      "active_requests": 28,
      "zone_id": "sf_downtown_001"
    },
    {
      "location": {
        "latitude": 37.7849,
        "longitude": -122.4094,
        "address": "Mission District",
        "zone_id": "sf_mission_001"
      },
      "surge_multiplier": 1.0,
      "demand_level": "normal",
      "supply_level": "high",
      "available_drivers": 45,
      "active_requests": 15,
      "zone_id": "sf_mission_001"
    },
    {
      "location": {
        "latitude": 37.7649,
        "longitude": -122.4294,
        "address": "SOMA District",
        "zone_id": "sf_soma_001"
      },
      "surge_multiplier": 1.1,
      "demand_level": "medium",
      "supply_level": "normal",
      "available_drivers": 28,
      "active_requests": 22,
      "zone_id": "sf_soma_001"
    }
  ],
  "generated_at": "2025-01-16T10:00:00Z",
  "grid_resolution_km": 0.5,
  "total_cells": 3,
  "status": "success",
  "error_message": ""
}
```

## Additional Endpoints

### Get Surge Multipliers

**Method**: `GetSurgeMultipliers`

**Request Example**:
```json
{
  "zone_ids": ["sf_downtown_001", "sf_mission_001"],
  "vehicle_type": "standard",
  "timestamp": "2025-01-16T10:00:00Z"
}
```

**Response Example**:
```json
{
  "zones": [
    {
      "zone_id": "sf_downtown_001",
      "surge_multiplier": 1.3,
      "demand_level": "high",
      "supply_level": "normal",
      "available_drivers": 32,
      "active_requests": 28,
      "last_updated": "2025-01-16T10:00:00Z"
    },
    {
      "zone_id": "sf_mission_001",
      "surge_multiplier": 1.0,
      "demand_level": "normal",
      "supply_level": "high",
      "available_drivers": 45,
      "active_requests": 15,
      "last_updated": "2025-01-16T10:00:00Z"
    }
  ],
  "generated_at": "2025-01-16T10:00:00Z",
  "status": "success",
  "error_message": ""
}
```

### Update Supply/Demand

**Method**: `UpdateSupplyDemand`

**Request Example**:
```json
{
  "zone_id": "sf_downtown_001",
  "supply_count": 35,
  "demand_count": 42,
  "vehicle_type": "standard",
  "timestamp": "2025-01-16T10:00:00Z",
  "metadata": {
    "source": "driver_app",
    "accuracy": "high"
  }
}
```

**Response Example**:
```json
{
  "zone_id": "sf_downtown_001",
  "new_surge_multiplier": 1.4,
  "demand_level": "high",
  "supply_level": "normal",
  "updated_at": "2025-01-16T10:00:00Z",
  "status": "success",
  "error_message": ""
}
```

## Error Handling

### gRPC Status Codes

- `OK (0)`: Success
- `INVALID_ARGUMENT (3)`: Invalid request parameters
- `NOT_FOUND (5)`: Zone or resource not found
- `PERMISSION_DENIED (7)`: Authentication/authorization failed
- `RESOURCE_EXHAUSTED (8)`: Rate limit exceeded
- `UNAVAILABLE (14)`: Service temporarily unavailable
- `INTERNAL (13)`: Internal server error

### Error Response Example

```json
{
  "error": {
    "code": 3,
    "message": "Invalid pickup location: latitude must be between -90 and 90",
    "details": [
      {
        "@type": "type.googleapis.com/google.rpc.BadRequest",
        "field_violations": [
          {
            "field": "pickup_location.latitude",
            "description": "Latitude value 95.0 is out of valid range"
          }
        ]
      }
    ]
  }
}
```

## Client Examples

### Python gRPC Client

```python
import grpc
from equilibrium.pricing.v1 import pricing_pb2
from equilibrium.pricing.v1 import pricing_pb2_grpc

def estimate_price():
    # Create gRPC channel
    channel = grpc.insecure_channel('localhost:8001')
    stub = pricing_pb2_grpc.PricingServiceStub(channel)
    
    # Create request
    request = pricing_pb2.EstimatePriceRequest(
        rider_id="rider_12345",
        pickup_location=pricing_pb2.Location(
            latitude=37.7749,
            longitude=-122.4194,
            address="123 Market St, San Francisco, CA",
            zone_id="sf_downtown_001"
        ),
        dropoff_location=pricing_pb2.Location(
            latitude=37.7849,
            longitude=-122.4094,
            address="456 Mission St, San Francisco, CA",
            zone_id="sf_mission_001"
        ),
        vehicle_type="standard",
        service_type="ride"
    )
    
    # Make gRPC call
    response = stub.EstimatePrice(request)
    
    print(f"Estimated fare: ${response.estimated_fare}")
    print(f"Surge multiplier: {response.surge_info.multiplier}")
    print(f"Quote ID: {response.quote_id}")

if __name__ == "__main__":
    estimate_price()
```

### JavaScript gRPC Client

```javascript
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');

// Load proto file
const packageDefinition = protoLoader.loadSync('pricing.proto', {
    keepCase: true,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true
});

const pricingProto = grpc.loadPackageDefinition(packageDefinition).equilibrium.pricing.v1;

// Create client
const client = new pricingProto.PricingService('localhost:8001', grpc.credentials.createInsecure());

// Estimate price
function estimatePrice() {
    const request = {
        rider_id: "rider_12345",
        pickup_location: {
            latitude: 37.7749,
            longitude: -122.4194,
            address: "123 Market St, San Francisco, CA",
            zone_id: "sf_downtown_001"
        },
        dropoff_location: {
            latitude: 37.7849,
            longitude: -122.4094,
            address: "456 Mission St, San Francisco, CA",
            zone_id: "sf_mission_001"
        },
        vehicle_type: "standard",
        service_type: "ride"
    };
    
    client.EstimatePrice(request, (error, response) => {
        if (error) {
            console.error('Error:', error);
        } else {
            console.log(`Estimated fare: $${response.estimated_fare}`);
            console.log(`Surge multiplier: ${response.surge_info.multiplier}`);
            console.log(`Quote ID: ${response.quote_id}`);
        }
    });
}

estimatePrice();
```

## Performance Characteristics

- **Latency**: < 100ms for price estimation
- **Throughput**: 1K+ requests/second
- **Availability**: 99.9% uptime
- **Cache Hit Ratio**: 95%+ for surge multipliers

## Rate Limiting

- **Per Client**: 100 requests/minute
- **Per Zone**: 1000 requests/minute
- **Burst Allowance**: 10 requests/second

## Monitoring

- **Metrics**: Request latency, error rates, cache hit ratios
- **Health Check**: `/grpc.health.v1.Health/Check`
- **Logging**: Structured JSON logs with correlation IDs

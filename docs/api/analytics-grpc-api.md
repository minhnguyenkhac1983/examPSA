# Analytics Service - gRPC API

## Service Definition

```protobuf
syntax = "proto3";

package equilibrium.analytics.v1;

import "google/protobuf/timestamp.proto";
import "google/protobuf/empty.proto";

option go_package = "github.com/equilibrium/analytics/v1;analyticsv1";

// Analytics Service for comprehensive data analysis and reporting
service AnalyticsService {
  // Get comprehensive analytics data
  rpc GetComprehensiveAnalytics(GetComprehensiveAnalyticsRequest) returns (GetComprehensiveAnalyticsResponse);
  
  // Get dashboard analytics
  rpc GetDashboardAnalytics(GetDashboardAnalyticsRequest) returns (GetDashboardAnalyticsResponse);
  
  // Get pricing trends
  rpc GetPricingTrends(GetPricingTrendsRequest) returns (GetPricingTrendsResponse);
  
  // Get supply/demand analytics
  rpc GetSupplyDemandAnalytics(GetSupplyDemandAnalyticsRequest) returns (GetSupplyDemandAnalyticsResponse);
  
  // Get zone performance metrics
  rpc GetZonePerformance(GetZonePerformanceRequest) returns (GetZonePerformanceResponse);
  
  // Get revenue analytics
  rpc GetRevenueAnalytics(GetRevenueAnalyticsRequest) returns (GetRevenueAnalyticsResponse);
  
  // Health check
  rpc HealthCheck(google.protobuf.Empty) returns (HealthCheckResponse);
}

// Message Definitions

message TimeRange {
  google.protobuf.Timestamp start_time = 1;
  google.protobuf.Timestamp end_time = 2;
}

message ZoneFilter {
  repeated string zone_ids = 1;
  string city = 2;
  string zone_type = 3;
}

message VehicleTypeFilter {
  repeated string vehicle_types = 1;
}

message MetricValue {
  string metric_name = 1;
  double value = 2;
  string unit = 3;
  google.protobuf.Timestamp timestamp = 4;
}

message TrendData {
  google.protobuf.Timestamp timestamp = 1;
  double value = 2;
  string label = 3;
  map<string, string> metadata = 4;
}

message ZoneMetrics {
  string zone_id = 1;
  string zone_name = 2;
  double total_revenue = 3;
  int32 total_rides = 4;
  double average_fare = 5;
  double average_surge_multiplier = 6;
  int32 peak_demand_hour = 7;
  double utilization_rate = 8;
  google.protobuf.Timestamp last_updated = 9;
}

message SupplyDemandSnapshot {
  string zone_id = 1;
  int32 supply_count = 2;
  int32 demand_count = 3;
  double supply_demand_ratio = 4;
  double surge_multiplier = 5;
  google.protobuf.Timestamp timestamp = 6;
}

message RevenueBreakdown {
  double total_revenue = 1;
  double base_fare_revenue = 2;
  double surge_revenue = 3;
  double distance_revenue = 4;
  double time_revenue = 5;
  double taxes = 6;
  double fees = 7;
  string currency = 8;
}

// Request/Response Messages

message GetComprehensiveAnalyticsRequest {
  TimeRange time_range = 1;
  ZoneFilter zone_filter = 2;
  VehicleTypeFilter vehicle_filter = 3;
  string metric_type = 4;
  int32 granularity_minutes = 5;
  map<string, string> metadata = 6;
}

message GetComprehensiveAnalyticsResponse {
  repeated MetricValue metrics = 1;
  repeated TrendData trends = 2;
  RevenueBreakdown revenue = 3;
  repeated ZoneMetrics zone_metrics = 4;
  google.protobuf.Timestamp generated_at = 5;
  string status = 6;
  string error_message = 7;
}

message GetDashboardAnalyticsRequest {
  int32 hours = 1;
  ZoneFilter zone_filter = 2;
  VehicleTypeFilter vehicle_filter = 3;
  repeated string metric_types = 4;
}

message DashboardMetric {
  string metric_name = 1;
  double current_value = 2;
  double previous_value = 3;
  double change_percentage = 4;
  string trend = 5;
  string unit = 6;
  google.protobuf.Timestamp last_updated = 7;
}

message GetDashboardAnalyticsResponse {
  repeated DashboardMetric metrics = 1;
  repeated TrendData hourly_trends = 2;
  repeated ZoneMetrics top_zones = 3;
  google.protobuf.Timestamp generated_at = 4;
  string status = 5;
  string error_message = 6;
}

message GetPricingTrendsRequest {
  TimeRange time_range = 1;
  ZoneFilter zone_filter = 2;
  VehicleTypeFilter vehicle_filter = 3;
  string trend_type = 4;
  int32 granularity_minutes = 5;
}

message PricingTrend {
  google.protobuf.Timestamp timestamp = 1;
  double average_surge_multiplier = 2;
  double median_surge_multiplier = 3;
  double max_surge_multiplier = 4;
  double min_surge_multiplier = 5;
  int32 total_rides = 6;
  string zone_id = 7;
}

message GetPricingTrendsResponse {
  repeated PricingTrend trends = 1;
  double overall_average_surge = 2;
  double peak_surge_multiplier = 3;
  google.protobuf.Timestamp peak_surge_time = 4;
  google.protobuf.Timestamp generated_at = 5;
  string status = 6;
  string error_message = 7;
}

message GetSupplyDemandAnalyticsRequest {
  TimeRange time_range = 1;
  ZoneFilter zone_filter = 2;
  VehicleTypeFilter vehicle_filter = 3;
  int32 granularity_minutes = 4;
}

message SupplyDemandAnalytics {
  repeated SupplyDemandSnapshot snapshots = 1;
  double average_supply_demand_ratio = 2;
  double peak_demand_time = 3;
  double peak_supply_time = 4;
  int32 total_supply_events = 5;
  int32 total_demand_events = 6;
}

message GetSupplyDemandAnalyticsResponse {
  SupplyDemandAnalytics analytics = 1;
  repeated ZoneMetrics zone_performance = 2;
  google.protobuf.Timestamp generated_at = 3;
  string status = 4;
  string error_message = 5;
}

message GetZonePerformanceRequest {
  TimeRange time_range = 1;
  ZoneFilter zone_filter = 2;
  VehicleTypeFilter vehicle_filter = 3;
  repeated string performance_metrics = 4;
}

message GetZonePerformanceResponse {
  repeated ZoneMetrics zones = 1;
  ZoneMetrics best_performing_zone = 2;
  ZoneMetrics worst_performing_zone = 3;
  double overall_utilization_rate = 4;
  google.protobuf.Timestamp generated_at = 5;
  string status = 6;
  string error_message = 7;
}

message GetRevenueAnalyticsRequest {
  TimeRange time_range = 1;
  ZoneFilter zone_filter = 2;
  VehicleTypeFilter vehicle_filter = 3;
  string revenue_type = 4;
  int32 granularity_minutes = 5;
}

message RevenueTrend {
  google.protobuf.Timestamp timestamp = 1;
  double total_revenue = 2;
  double base_fare_revenue = 3;
  double surge_revenue = 4;
  int32 total_rides = 5;
  double average_fare = 6;
  string zone_id = 7;
}

message GetRevenueAnalyticsResponse {
  RevenueBreakdown total_revenue = 1;
  repeated RevenueTrend trends = 2;
  repeated ZoneMetrics zone_revenue = 3;
  double revenue_growth_rate = 4;
  google.protobuf.Timestamp generated_at = 5;
  string status = 6;
  string error_message = 7;
}

message HealthCheckResponse {
  string status = 1;
  google.protobuf.Timestamp timestamp = 2;
  string version = 3;
  map<string, string> metadata = 4;
}
```

## Analytics Endpoints

### Get Comprehensive Analytics

**Method**: `GetComprehensiveAnalytics`

**Description**: Get comprehensive analytics data for a specific time range and filters.

**Request Example**:
```json
{
  "time_range": {
    "start_time": "2025-01-16T00:00:00Z",
    "end_time": "2025-01-16T23:59:59Z"
  },
  "zone_filter": {
    "zone_ids": ["sf_downtown_001", "sf_mission_001"],
    "city": "San Francisco",
    "zone_type": "downtown"
  },
  "vehicle_filter": {
    "vehicle_types": ["standard", "premium"]
  },
  "metric_type": "all",
  "granularity_minutes": 60,
  "metadata": {
    "report_type": "daily_summary",
    "user_id": "admin_123"
  }
}
```

**Response Example**:
```json
{
  "metrics": [
    {
      "metric_name": "total_rides",
      "value": 1250,
      "unit": "rides",
      "timestamp": "2025-01-16T23:59:59Z"
    },
    {
      "metric_name": "total_revenue",
      "value": 15625.50,
      "unit": "USD",
      "timestamp": "2025-01-16T23:59:59Z"
    },
    {
      "metric_name": "average_surge_multiplier",
      "value": 1.35,
      "unit": "multiplier",
      "timestamp": "2025-01-16T23:59:59Z"
    }
  ],
  "trends": [
    {
      "timestamp": "2025-01-16T00:00:00Z",
      "value": 45,
      "label": "rides_per_hour",
      "metadata": {
        "zone_id": "sf_downtown_001"
      }
    },
    {
      "timestamp": "2025-01-16T01:00:00Z",
      "value": 52,
      "label": "rides_per_hour",
      "metadata": {
        "zone_id": "sf_downtown_001"
      }
    }
  ],
  "revenue": {
    "total_revenue": 15625.50,
    "base_fare_revenue": 10625.00,
    "surge_revenue": 4250.50,
    "distance_revenue": 750.00,
    "time_revenue": 0.00,
    "taxes": 0.00,
    "fees": 0.00,
    "currency": "USD"
  },
  "zone_metrics": [
    {
      "zone_id": "sf_downtown_001",
      "zone_name": "San Francisco Downtown",
      "total_revenue": 8750.25,
      "total_rides": 650,
      "average_fare": 13.46,
      "average_surge_multiplier": 1.42,
      "peak_demand_hour": 18,
      "utilization_rate": 0.85,
      "last_updated": "2025-01-16T23:59:59Z"
    },
    {
      "zone_id": "sf_mission_001",
      "zone_name": "San Francisco Mission",
      "total_revenue": 6875.25,
      "total_rides": 600,
      "average_fare": 11.46,
      "average_surge_multiplier": 1.28,
      "peak_demand_hour": 19,
      "utilization_rate": 0.78,
      "last_updated": "2025-01-16T23:59:59Z"
    }
  ],
  "generated_at": "2025-01-16T23:59:59Z",
  "status": "success",
  "error_message": ""
}
```

### Get Dashboard Analytics

**Method**: `GetDashboardAnalytics`

**Description**: Get real-time dashboard analytics for monitoring and operations.

**Request Example**:
```json
{
  "hours": 24,
  "zone_filter": {
    "zone_ids": ["sf_downtown_001", "sf_mission_001"],
    "city": "San Francisco"
  },
  "vehicle_filter": {
    "vehicle_types": ["standard"]
  },
  "metric_types": ["revenue", "rides", "surge", "utilization"]
}
```

**Response Example**:
```json
{
  "metrics": [
    {
      "metric_name": "total_revenue",
      "current_value": 15625.50,
      "previous_value": 14230.75,
      "change_percentage": 9.8,
      "trend": "increasing",
      "unit": "USD",
      "last_updated": "2025-01-16T23:59:59Z"
    },
    {
      "metric_name": "total_rides",
      "current_value": 1250,
      "previous_value": 1180,
      "change_percentage": 5.9,
      "trend": "increasing",
      "unit": "rides",
      "last_updated": "2025-01-16T23:59:59Z"
    },
    {
      "metric_name": "average_surge_multiplier",
      "current_value": 1.35,
      "previous_value": 1.28,
      "change_percentage": 5.5,
      "trend": "increasing",
      "unit": "multiplier",
      "last_updated": "2025-01-16T23:59:59Z"
    },
    {
      "metric_name": "utilization_rate",
      "current_value": 0.82,
      "previous_value": 0.79,
      "change_percentage": 3.8,
      "trend": "increasing",
      "unit": "percentage",
      "last_updated": "2025-01-16T23:59:59Z"
    }
  ],
  "hourly_trends": [
    {
      "timestamp": "2025-01-16T00:00:00Z",
      "value": 45,
      "label": "rides_per_hour"
    },
    {
      "timestamp": "2025-01-16T01:00:00Z",
      "value": 52,
      "label": "rides_per_hour"
    }
  ],
  "top_zones": [
    {
      "zone_id": "sf_downtown_001",
      "zone_name": "San Francisco Downtown",
      "total_revenue": 8750.25,
      "total_rides": 650,
      "average_fare": 13.46,
      "average_surge_multiplier": 1.42,
      "peak_demand_hour": 18,
      "utilization_rate": 0.85,
      "last_updated": "2025-01-16T23:59:59Z"
    }
  ],
  "generated_at": "2025-01-16T23:59:59Z",
  "status": "success",
  "error_message": ""
}
```

### Get Pricing Trends

**Method**: `GetPricingTrends`

**Description**: Get pricing trends and surge multiplier analysis over time.

**Request Example**:
```json
{
  "time_range": {
    "start_time": "2025-01-16T00:00:00Z",
    "end_time": "2025-01-16T23:59:59Z"
  },
  "zone_filter": {
    "zone_ids": ["sf_downtown_001"]
  },
  "vehicle_filter": {
    "vehicle_types": ["standard"]
  },
  "trend_type": "surge_multiplier",
  "granularity_minutes": 60
}
```

**Response Example**:
```json
{
  "trends": [
    {
      "timestamp": "2025-01-16T00:00:00Z",
      "average_surge_multiplier": 1.0,
      "median_surge_multiplier": 1.0,
      "max_surge_multiplier": 1.2,
      "min_surge_multiplier": 1.0,
      "total_rides": 45,
      "zone_id": "sf_downtown_001"
    },
    {
      "timestamp": "2025-01-16T01:00:00Z",
      "average_surge_multiplier": 1.1,
      "median_surge_multiplier": 1.0,
      "max_surge_multiplier": 1.5,
      "min_surge_multiplier": 1.0,
      "total_rides": 52,
      "zone_id": "sf_downtown_001"
    }
  ],
  "overall_average_surge": 1.35,
  "peak_surge_multiplier": 2.8,
  "peak_surge_time": "2025-01-16T18:30:00Z",
  "generated_at": "2025-01-16T23:59:59Z",
  "status": "success",
  "error_message": ""
}
```

### Get Supply/Demand Analytics

**Method**: `GetSupplyDemandAnalytics`

**Description**: Get supply and demand analytics with ratio calculations.

**Request Example**:
```json
{
  "time_range": {
    "start_time": "2025-01-16T00:00:00Z",
    "end_time": "2025-01-16T23:59:59Z"
  },
  "zone_filter": {
    "zone_ids": ["sf_downtown_001"]
  },
  "vehicle_filter": {
    "vehicle_types": ["standard"]
  },
  "granularity_minutes": 30
}
```

**Response Example**:
```json
{
  "analytics": {
    "snapshots": [
      {
        "zone_id": "sf_downtown_001",
        "supply_count": 32,
        "demand_count": 28,
        "supply_demand_ratio": 1.14,
        "surge_multiplier": 1.3,
        "timestamp": "2025-01-16T10:00:00Z"
      },
      {
        "zone_id": "sf_downtown_001",
        "supply_count": 28,
        "demand_count": 35,
        "supply_demand_ratio": 0.8,
        "surge_multiplier": 1.5,
        "timestamp": "2025-01-16T10:30:00Z"
      }
    ],
    "average_supply_demand_ratio": 1.05,
    "peak_demand_time": 18.5,
    "peak_supply_time": 14.0,
    "total_supply_events": 1250,
    "total_demand_events": 1180
  },
  "zone_performance": [
    {
      "zone_id": "sf_downtown_001",
      "zone_name": "San Francisco Downtown",
      "total_revenue": 8750.25,
      "total_rides": 650,
      "average_fare": 13.46,
      "average_surge_multiplier": 1.42,
      "peak_demand_hour": 18,
      "utilization_rate": 0.85,
      "last_updated": "2025-01-16T23:59:59Z"
    }
  ],
  "generated_at": "2025-01-16T23:59:59Z",
  "status": "success",
  "error_message": ""
}
```

## Client Examples

### Python gRPC Client

```python
import grpc
from equilibrium.analytics.v1 import analytics_pb2
from equilibrium.analytics.v1 import analytics_pb2_grpc

def get_dashboard_analytics():
    # Create gRPC channel
    channel = grpc.insecure_channel('localhost:8002')
    stub = analytics_pb2_grpc.AnalyticsServiceStub(channel)
    
    # Create request
    request = analytics_pb2.GetDashboardAnalyticsRequest(
        hours=24,
        zone_filter=analytics_pb2.ZoneFilter(
            zone_ids=["sf_downtown_001", "sf_mission_001"],
            city="San Francisco"
        ),
        vehicle_filter=analytics_pb2.VehicleTypeFilter(
            vehicle_types=["standard"]
        ),
        metric_types=["revenue", "rides", "surge", "utilization"]
    )
    
    # Make gRPC call
    response = stub.GetDashboardAnalytics(request)
    
    print(f"Total Revenue: ${response.metrics[0].current_value}")
    print(f"Total Rides: {response.metrics[1].current_value}")
    print(f"Average Surge: {response.metrics[2].current_value}")

if __name__ == "__main__":
    get_dashboard_analytics()
```

## Performance Characteristics

- **Latency**: < 200ms for dashboard analytics
- **Throughput**: 500+ requests/second
- **Data Processing**: Real-time aggregation
- **Cache Hit Ratio**: 90%+ for recent data

## Rate Limiting

- **Per Client**: 50 requests/minute
- **Per Query**: 10 requests/minute
- **Burst Allowance**: 5 requests/second

## Monitoring

- **Metrics**: Query latency, data freshness, cache performance
- **Health Check**: `/grpc.health.v1.Health/Check`
- **Logging**: Structured JSON logs with query details

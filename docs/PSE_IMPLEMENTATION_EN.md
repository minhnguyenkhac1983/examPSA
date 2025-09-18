# 🚀 PSE Implementation - Equilibrium Dynamic Pricing Platform

## Part 1: 🤔 Assumptions and Clarifications

### Assumptions Made:

1. **Geographic Scope**: System operates globally with primary focus on major cities
2. **Current Technology**: Momentum Mobility already has basic infrastructure (databases, APIs)
3. **User Scale**: 100M+ MAU with peak traffic during rush hours
4. **Latency Requirements**: P99 < 150ms for pricing API
5. **Data Consistency**: Eventual consistency for market state, strong consistency for quoted prices
6. **Geographic Segmentation**: Using S2 cells or Geohash for geofencing
7. **Pricing Algorithms**: Support for multiple algorithms (linear, exponential, ML-based)

### Clarification Questions (if interactive session):

1. **Business Logic**:
   - Is there a maximum limit for surge multiplier? (e.g., 5x, 10x)
   - How to handle pricing in emergency situations?
   - Do we need support for different vehicle types with different pricing?

2. **Technical Constraints**:
   - Budget for infrastructure and third-party services?
   - Compliance requirements (GDPR, data retention)?
   - Integration with existing systems?

3. **Operational**:
   - Team size and expertise level?
   - Timeline for implementation?
   - Rollout strategy (gradual vs big bang)?

---

## Part 2: 🏗️ High-Level Architecture

### System Diagram:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Mobile Apps   │    │   Driver Apps   │    │  Admin Portal   │
│   (React/Flutter)│    │   (React/Flutter)│    │     (React)     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │      API Gateway          │
                    │   (Load Balancer + Auth)  │
                    └─────────────┬─────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼────────┐    ┌───────────▼──────────┐    ┌────────▼────────┐
│ Pricing Service│    │  Geospatial Service  │    │ Analytics Service│
│  (FastAPI)     │    │     (FastAPI)        │    │   (FastAPI)     │
└───────┬────────┘    └───────────┬──────────┘    └────────┬────────┘
        │                         │                        │
        └─────────────────────────┼────────────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │   Stream Processor        │
                    │    (Apache Flink)         │
                    └─────────────┬─────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼────────┐    ┌───────────▼──────────┐    ┌────────▼────────┐
│   PostgreSQL   │    │      Redis           │    │    MongoDB      │
│  (Spatial DB)  │    │   (Cache + Session)  │    │  (Analytics)    │
└────────────────┘    └──────────────────────┘    └─────────────────┘
```

### Component Description:

#### 1. **API Gateway**
- **Function**: Load balancing, authentication, rate limiting
- **Technology**: Nginx + FastAPI
- **Port**: 8000

#### 2. **Pricing Service**
- **Function**: Dynamic pricing calculation, providing price estimates
- **Technology**: FastAPI + Python
- **Port**: 8001

#### 3. **Geospatial Service**
- **Function**: Location data processing, geofencing, S2 cells
- **Technology**: FastAPI + PostGIS
- **Port**: 8003

#### 4. **Stream Processor**
- **Function**: Real-time location event processing, supply/demand calculation
- **Technology**: Apache Flink
- **Port**: 8004

#### 5. **Analytics Service**
- **Function**: Reporting, metrics, business intelligence
- **Technology**: FastAPI + MongoDB
- **Port**: 8002

### Data Flow:

1. **Location Updates**: Driver apps → API Gateway → Geospatial Service → Stream Processor
2. **Price Requests**: Mobile apps → API Gateway → Pricing Service → Redis Cache
3. **Market State**: Stream Processor → Redis → Pricing Service
4. **Analytics**: All services → MongoDB → Analytics Service

---

## Part 3: 💾 Data Model and Storage

### Core Entity Schema:

#### 1. **SurgeZone**
```sql
CREATE TABLE surge_zones (
    zone_id VARCHAR(50) PRIMARY KEY,
    zone_name VARCHAR(100) NOT NULL,
    s2_cell_id VARCHAR(20) NOT NULL,
    center_lat DECIMAL(10,8) NOT NULL,
    center_lng DECIMAL(11,8) NOT NULL,
    radius_meters INTEGER NOT NULL,
    base_multiplier DECIMAL(3,2) DEFAULT 1.0,
    max_multiplier DECIMAL(4,2) DEFAULT 5.0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 2. **DriverLocationEvent**
```sql
CREATE TABLE driver_location_events (
    event_id UUID PRIMARY KEY,
    driver_id VARCHAR(50) NOT NULL,
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    s2_cell_id VARCHAR(20) NOT NULL,
    zone_id VARCHAR(50) REFERENCES surge_zones(zone_id),
    is_available BOOLEAN NOT NULL,
    vehicle_type VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

#### 3. **SupplyDemandSnapshot**
```sql
CREATE TABLE supply_demand_snapshots (
    snapshot_id UUID PRIMARY KEY,
    zone_id VARCHAR(50) REFERENCES surge_zones(zone_id),
    supply_count INTEGER NOT NULL,
    demand_count INTEGER NOT NULL,
    surge_multiplier DECIMAL(4,2) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

#### 4. **PricingEventLog**
```sql
CREATE TABLE pricing_event_logs (
    log_id UUID PRIMARY KEY,
    zone_id VARCHAR(50) REFERENCES surge_zones(zone_id),
    old_multiplier DECIMAL(4,2),
    new_multiplier DECIMAL(4,2) NOT NULL,
    trigger_reason VARCHAR(100),
    supply_count INTEGER,
    demand_count INTEGER,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

### Technology Justification:

#### **PostgreSQL + PostGIS**
- **Reason**: Spatial queries, ACID compliance, mature ecosystem
- **Usage**: Core business data, geospatial operations
- **Advantages**: Strong consistency, complex queries, spatial indexing

#### **Redis**
- **Reason**: Ultra-fast caching, pub/sub, session storage
- **Usage**: Real-time pricing cache, session management
- **Advantages**: Sub-millisecond latency, high throughput

#### **MongoDB**
- **Reason**: Flexible schema, horizontal scaling, analytics
- **Usage**: Event logs, analytics data, time-series data
- **Advantages**: Schema flexibility, aggregation pipelines

#### **Apache Kafka**
- **Reason**: High-throughput streaming, durability, replay capability
- **Usage**: Location events, pricing updates, audit logs
- **Advantages**: Fault tolerance, horizontal scaling, ordering guarantees

---

## Part 4: 🔌 API Design

### REST API Endpoints:

#### 1. **Price Estimate API**
```http
POST /api/v1/pricing/estimate
Content-Type: application/json

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

Response:
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

#### 2. **Heatmap Data API**
```http
GET /api/v1/pricing/heatmap?bounds=37.7,-122.5,37.8,-122.3&zoom=12

Response:
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

#### 3. **Driver Heatmap API**
```http
GET /api/v1/driver/heatmap?driver_id=driver_123&radius=5000

Response:
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

---

## Part 5: 🔍 Deep Dive into Critical Component

### **Real-Time Geospatial Aggregation**

#### Processing millions of location events:

```python
# Stream Processor with Apache Flink
class LocationEventProcessor:
    def __init__(self):
        self.s2_level = 12  # ~0.1km² cells
        self.window_size = 30  # seconds
        self.supply_demand_state = {}
    
    def process_location_event(self, event):
        # 1. Convert lat/lng to S2 cell
        s2_cell = s2.lat_lng_to_cell_id(
            event.latitude, 
            event.longitude, 
            self.s2_level
        )
        
        # 2. Update supply/demand state
        if event.is_available:
            self.supply_demand_state[s2_cell]['supply'] += 1
        else:
            self.supply_demand_state[s2_cell]['supply'] -= 1
            
        # 3. Calculate surge multiplier
        multiplier = self.calculate_surge_multiplier(s2_cell)
        
        # 4. Emit pricing update
        self.emit_pricing_update(s2_cell, multiplier)
    
    def calculate_surge_multiplier(self, s2_cell):
        state = self.supply_demand_state[s2_cell]
        supply = state.get('supply', 0)
        demand = state.get('demand', 0)
        
        if supply == 0:
            return 5.0  # Max surge
        
        ratio = demand / supply
        if ratio <= 1.0:
            return 1.0
        elif ratio <= 2.0:
            return 1.0 + (ratio - 1.0) * 0.5
        else:
            return 1.5 + min((ratio - 2.0) * 0.3, 3.5)
```

#### Geospatial indexing:

```python
# S2 Cell implementation
import s2sphere

class GeospatialIndexer:
    def __init__(self):
        self.s2_level = 12
        self.cell_cache = {}
    
    def lat_lng_to_s2_cell(self, lat, lng):
        """Convert lat/lng to S2 cell ID"""
        point = s2sphere.LatLng.from_degrees(lat, lng)
        cell_id = s2sphere.CellId.from_lat_lng(point).parent(self.s2_level)
        return str(cell_id.id())
    
    def get_neighboring_cells(self, cell_id, radius_km=1.0):
        """Get neighboring S2 cells within radius"""
        center_cell = s2sphere.CellId(int(cell_id))
        center_point = center_cell.to_lat_lng()
        
        # Calculate cells within radius
        neighboring_cells = []
        for level in range(8, 16):  # Different granularities
            cell = s2sphere.CellId.from_lat_lng(center_point).parent(level)
            if self.distance_to_cell(cell, center_point) <= radius_km:
                neighboring_cells.append(str(cell.id()))
        
        return neighboring_cells
```

#### Stream processing logic:

```python
# Flink Stream Processing
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment

class PricingStreamProcessor:
    def __init__(self):
        self.env = StreamExecutionEnvironment.get_execution_environment()
        self.table_env = StreamTableEnvironment.create(self.env)
        
    def setup_pricing_pipeline(self):
        # 1. Source: Kafka location events
        location_events = self.table_env.from_kafka(
            "location_events",
            kafka_config={
                "bootstrap.servers": "kafka:9092",
                "group.id": "pricing-processor"
            }
        )
        
        # 2. Windowed aggregation by S2 cell
        windowed_supply_demand = location_events \
            .window(Tumble.over("30.seconds").on("timestamp").alias("w")) \
            .group_by("s2_cell_id, w") \
            .select(
                "s2_cell_id",
                "w.start as window_start",
                "sum(case when is_available then 1 else 0 end) as supply",
                "count(*) as total_events"
            )
        
        # 3. Calculate surge multipliers
        pricing_updates = windowed_supply_demand \
            .map(self.calculate_surge_multiplier) \
            .filter("surge_multiplier > 1.0")
        
        # 4. Sink: Update Redis cache
        pricing_updates.sink_to_redis("pricing_cache")
        
        return pricing_updates
```

---

### **Failure Handling & Graceful Degradation**

### Comprehensive Failure Management Strategy

#### 1. **Failure Categories & Response Strategies**

**Category 1: Infrastructure Failures**
```python
class InfrastructureFailureHandler:
    def __init__(self):
        self.circuit_breakers = {}
        self.fallback_strategies = {
            'redis': self.redis_fallback,
            'database': self.database_fallback,
            'stream_processor': self.stream_processor_fallback
        }
    
    def handle_redis_failure(self):
        """Handle Redis cluster failure with graceful degradation"""
        # 1. Activate circuit breaker
        self.circuit_breakers['redis'] = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=RedisConnectionError
        )
        
        # 2. Switch to local cache + database fallback
        return {
            'cache_strategy': 'local_memory',
            'fallback_source': 'postgresql',
            'degraded_mode': True,
            'performance_impact': 'latency_increase_50ms'
        }
    
    def handle_database_failure(self):
        """Handle database failure with read-only mode"""
        # 1. Switch to read replicas
        # 2. Enable cached data only mode
        # 3. Disable write operations
        return {
            'mode': 'read_only',
            'data_source': 'cached_data',
            'write_operations': 'disabled',
            'user_notification': 'service_limited'
        }
```

**Category 2: Service Failures**
```python
class ServiceFailureHandler:
    def __init__(self):
        self.health_checks = HealthCheckManager()
        self.load_balancer = LoadBalancer()
        self.service_mesh = ServiceMesh()
    
    def handle_pricing_service_failure(self, failed_instances):
        """Handle pricing service instance failures"""
        # 1. Remove failed instances from load balancer
        self.load_balancer.remove_instances(failed_instances)
        
        # 2. Scale up remaining healthy instances
        self.service_mesh.scale_service('pricing-service', scale_factor=1.5)
        
        # 3. Activate simplified pricing algorithm
        return {
            'pricing_algorithm': 'simplified_linear',
            'cache_ttl': 300,  # 5 minutes
            'fallback_multiplier': 1.2,
            'degraded_features': ['complex_pricing', 'ml_predictions']
        }
    
    def handle_geospatial_service_failure(self):
        """Handle geospatial service failure"""
        # 1. Use cached zone data
        # 2. Fallback to simple lat/lng calculations
        # 3. Disable real-time zone updates
        return {
            'zone_calculation': 'cached_zones',
            'real_time_updates': False,
            'fallback_radius': 1000,  # meters
            'accuracy_degradation': 'acceptable'
        }
```

#### 2. **Circuit Breaker Pattern Implementation**

```python
import asyncio
from enum import Enum
from typing import Callable, Any
import time

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: Exception = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenException("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Usage in pricing service
class PricingService:
    def __init__(self):
        self.redis_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=RedisConnectionError
        )
        self.database_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=DatabaseConnectionError
        )
    
    async def get_pricing_data(self, zone_id: str):
        """Get pricing data with circuit breaker protection"""
        try:
            # Try Redis first
            return await self.redis_breaker.call(
                self._get_from_redis, zone_id
            )
        except CircuitBreakerOpenException:
            # Fallback to database
            return await self.database_breaker.call(
                self._get_from_database, zone_id
            )
```

#### 3. **Graceful Degradation Strategies**

**Strategy 1: Progressive Feature Disabling**
```python
class GracefulDegradationManager:
    def __init__(self):
        self.degradation_levels = {
            'level_1': {
                'features_disabled': ['ml_predictions', 'advanced_analytics'],
                'performance_impact': 'minimal',
                'user_experience': 'unaffected'
            },
            'level_2': {
                'features_disabled': ['real_time_updates', 'complex_pricing'],
                'performance_impact': 'moderate',
                'user_experience': 'slightly_degraded'
            },
            'level_3': {
                'features_disabled': ['dynamic_pricing', 'heatmap_data'],
                'performance_impact': 'significant',
                'user_experience': 'basic_functionality_only'
            },
            'level_4': {
                'features_disabled': ['all_advanced_features'],
                'performance_impact': 'maximum',
                'user_experience': 'emergency_mode'
            }
        }
    
    def determine_degradation_level(self, system_health: dict) -> str:
        """Determine appropriate degradation level based on system health"""
        if system_health['redis_health'] < 0.3:
            return 'level_4'
        elif system_health['database_health'] < 0.5:
            return 'level_3'
        elif system_health['stream_processor_health'] < 0.7:
            return 'level_2'
        elif system_health['overall_health'] < 0.9:
            return 'level_1'
        else:
            return 'normal'
    
    def apply_degradation_strategy(self, level: str):
        """Apply degradation strategy for given level"""
        strategy = self.degradation_levels.get(level, {})
        
        # Update service configurations
        self._update_pricing_service_config(strategy)
        self._update_cache_strategies(strategy)
        self._notify_users(strategy)
        
        return strategy
```

**Strategy 2: Fallback Data Sources**
```python
class FallbackDataManager:
    def __init__(self):
        self.data_sources = [
            'redis_cluster',      # Primary
            'local_cache',        # Secondary
            'database_replica',   # Tertiary
            'static_data'         # Emergency
        ]
        self.current_source_index = 0
    
    async def get_pricing_data(self, zone_id: str):
        """Get pricing data with automatic fallback"""
        for i, source in enumerate(self.data_sources[self.current_source_index:]):
            try:
                data = await self._fetch_from_source(source, zone_id)
                if data:
                    # Reset to primary source if successful
                    if i > 0:
                        self.current_source_index = 0
                    return data
            except Exception as e:
                logger.warning(f"Failed to fetch from {source}: {e}")
                continue
        
        # All sources failed, return emergency fallback
        return self._get_emergency_fallback(zone_id)
    
    def _get_emergency_fallback(self, zone_id: str):
        """Emergency fallback with static pricing"""
        return {
            'zone_id': zone_id,
            'surge_multiplier': 1.0,  # No surge pricing
            'base_fare': 8.50,
            'final_fare': 8.50,
            'source': 'emergency_fallback',
            'warning': 'Service operating in limited mode'
        }
```

#### 4. **Error Recovery & Self-Healing**

**Automatic Recovery Mechanisms**
```python
class SelfHealingManager:
    def __init__(self):
        self.recovery_strategies = {
            'redis': self._recover_redis,
            'database': self._recover_database,
            'stream_processor': self._recover_stream_processor
        }
        self.health_monitor = HealthMonitor()
    
    async def monitor_and_recover(self):
        """Continuously monitor services and attempt recovery"""
        while True:
            health_status = await self.health_monitor.check_all_services()
            
            for service, status in health_status.items():
                if status['healthy'] == False:
                    await self._attempt_recovery(service, status)
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def _attempt_recovery(self, service: str, status: dict):
        """Attempt to recover a failed service"""
        recovery_strategy = self.recovery_strategies.get(service)
        if not recovery_strategy:
            return
        
        try:
            # Attempt recovery
            success = await recovery_strategy(status)
            
            if success:
                logger.info(f"Successfully recovered {service}")
                # Notify monitoring systems
                await self._notify_recovery(service)
            else:
                logger.error(f"Failed to recover {service}")
                # Escalate to operations team
                await self._escalate_failure(service, status)
                
        except Exception as e:
            logger.error(f"Recovery attempt failed for {service}: {e}")
    
    async def _recover_redis(self, status: dict):
        """Recover Redis cluster"""
        # 1. Check if it's a temporary network issue
        if await self._check_network_connectivity('redis'):
            # 2. Restart Redis service
            await self._restart_service('redis')
            # 3. Wait for health check
            await asyncio.sleep(10)
            # 4. Verify recovery
            return await self.health_monitor.check_service('redis')
        
        return False
    
    async def _recover_database(self, status: dict):
        """Recover database connection"""
        # 1. Check connection pool
        if status.get('error') == 'connection_pool_exhausted':
            # 2. Reset connection pool
            await self._reset_connection_pool()
            # 3. Verify recovery
            return await self.health_monitor.check_service('database')
        
        return False
```

#### 5. **User Communication & Transparency**

**User Notification System**
```python
class UserNotificationManager:
    def __init__(self):
        self.notification_channels = {
            'mobile_app': MobileNotificationService(),
            'web_app': WebNotificationService(),
            'api_response': APIResponseService()
        }
    
    async def notify_service_degradation(self, level: str, affected_features: list):
        """Notify users about service degradation"""
        message = self._generate_degradation_message(level, affected_features)
        
        # Send to all channels
        for channel, service in self.notification_channels.items():
            try:
                await service.send_notification(message)
            except Exception as e:
                logger.error(f"Failed to send notification via {channel}: {e}")
    
    def _generate_degradation_message(self, level: str, features: list):
        """Generate user-friendly degradation message"""
        messages = {
            'level_1': "We're experiencing minor technical issues. Some advanced features may be temporarily unavailable.",
            'level_2': "We're experiencing technical difficulties. Pricing updates may be delayed.",
            'level_3': "We're experiencing significant technical issues. Basic ride booking is available with standard pricing.",
            'level_4': "We're in emergency mode. Only basic functionality is available. We're working to restore full service."
        }
        
        return {
            'message': messages.get(level, "Service temporarily limited"),
            'affected_features': features,
            'estimated_resolution': self._estimate_resolution_time(level),
            'alternative_options': self._suggest_alternatives(level)
        }
```

#### 6. **Monitoring & Alerting**

**Comprehensive Monitoring Setup**
```python
class FailureMonitoringSystem:
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.dashboard = MonitoringDashboard()
    
    async def setup_monitoring(self):
        """Setup comprehensive failure monitoring"""
        
        # 1. Service health monitoring
        await self._setup_health_checks()
        
        # 2. Performance monitoring
        await self._setup_performance_monitoring()
        
        # 3. Error tracking
        await self._setup_error_tracking()
        
        # 4. Alert configuration
        await self._setup_alerts()
    
    async def _setup_health_checks(self):
        """Setup health check monitoring"""
        health_checks = {
            'pricing_service': {
                'endpoint': '/health',
                'interval': 30,
                'timeout': 5,
                'critical': True
            },
            'redis_cluster': {
                'command': 'redis-cli ping',
                'interval': 15,
                'timeout': 3,
                'critical': True
            },
            'database': {
                'query': 'SELECT 1',
                'interval': 60,
                'timeout': 10,
                'critical': True
            }
        }
        
        for service, config in health_checks.items():
            await self.metrics_collector.add_health_check(service, config)
    
    async def _setup_alerts(self):
        """Setup alerting rules"""
        alert_rules = [
            {
                'name': 'service_down',
                'condition': 'health_check_failed > 3',
                'severity': 'critical',
                'notification': ['slack', 'email', 'pagerduty']
            },
            {
                'name': 'high_error_rate',
                'condition': 'error_rate > 5%',
                'severity': 'warning',
                'notification': ['slack', 'email']
            },
            {
                'name': 'circuit_breaker_open',
                'condition': 'circuit_breaker_state == "open"',
                'severity': 'warning',
                'notification': ['slack']
            }
        ]
        
        for rule in alert_rules:
            await self.alert_manager.add_rule(rule)
```

#### 7. **Disaster Recovery Plan**

**Complete System Recovery**
```python
class DisasterRecoveryManager:
    def __init__(self):
        self.backup_manager = BackupManager()
        self.infrastructure_manager = InfrastructureManager()
        self.data_recovery = DataRecoveryManager()
    
    async def execute_disaster_recovery(self, disaster_type: str):
        """Execute disaster recovery based on disaster type"""
        
        recovery_plans = {
            'data_center_failure': self._recover_from_datacenter_failure,
            'database_corruption': self._recover_from_database_corruption,
            'complete_system_failure': self._recover_from_complete_failure
        }
        
        recovery_plan = recovery_plans.get(disaster_type)
        if not recovery_plan:
            raise ValueError(f"Unknown disaster type: {disaster_type}")
        
        # Execute recovery plan
        return await recovery_plan()
    
    async def _recover_from_datacenter_failure(self):
        """Recover from datacenter failure"""
        # 1. Activate backup datacenter
        await self.infrastructure_manager.activate_backup_datacenter()
        
        # 2. Restore services from backup
        await self._restore_services_from_backup()
        
        # 3. Sync data from last known good state
        await self.data_recovery.sync_from_backup()
        
        # 4. Verify system health
        health_status = await self._verify_system_health()
        
        return {
            'recovery_status': 'completed',
            'recovery_time': '15_minutes',
            'data_loss': 'minimal',
            'system_health': health_status
        }
    
    async def _recover_from_complete_failure(self):
        """Recover from complete system failure"""
        # 1. Restore infrastructure
        await self.infrastructure_manager.restore_infrastructure()
        
        # 2. Restore databases
        await self.backup_manager.restore_databases()
        
        # 3. Restore application services
        await self._restore_application_services()
        
        # 4. Verify end-to-end functionality
        await self._verify_end_to_end_functionality()
        
        return {
            'recovery_status': 'completed',
            'recovery_time': '45_minutes',
            'data_loss': 'acceptable',
            'system_health': 'fully_operational'
        }
```

### Key Benefits of This Failure Handling Strategy:

1. **🛡️ Proactive Protection**: Circuit breakers prevent cascade failures
2. **🔄 Automatic Recovery**: Self-healing mechanisms reduce manual intervention
3. **📊 Transparent Communication**: Users are informed about service status
4. **⚡ Graceful Degradation**: System maintains basic functionality during failures
5. **📈 Continuous Monitoring**: Real-time health checks and alerting
6. **🚀 Fast Recovery**: Automated recovery procedures minimize downtime
7. **💾 Data Protection**: Multiple backup strategies ensure data safety

---
---

## Part 6: 📊 Analytical SQL Queries

### Query to find 5 least efficient surge zones:

```sql
WITH zone_performance AS (
    -- Calculate metrics for each zone in the past month
    SELECT 
        sz.zone_id,
        sz.zone_name,
        AVG(sds.surge_multiplier) as avg_multiplier,
        COUNT(DISTINCT CASE WHEN pel.new_multiplier > pel.old_multiplier 
                           THEN pel.log_id END) as surge_events,
        COUNT(DISTINCT CASE WHEN pel.new_multiplier < pel.old_multiplier 
                           THEN pel.log_id END) as decrease_events
    FROM surge_zones sz
    LEFT JOIN supply_demand_snapshots sds 
        ON sz.zone_id = sds.zone_id 
        AND sds.timestamp >= NOW() - INTERVAL '30 days'
    LEFT JOIN pricing_event_logs pel 
        ON sz.zone_id = pel.zone_id 
        AND pel.timestamp >= NOW() - INTERVAL '30 days'
    WHERE sz.is_active = true
    GROUP BY sz.zone_id, sz.zone_name
),

ride_completion AS (
    -- Calculate ride completion rate
    SELECT 
        zone_id,
        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_rides,
        COUNT(*) as total_rides,
        ROUND(
            COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*), 
            2
        ) as completion_rate
    FROM ride_requests 
    WHERE created_at >= NOW() - INTERVAL '30 days'
    GROUP BY zone_id
),

efficiency_ranking AS (
    -- Combine metrics and calculate efficiency score
    SELECT 
        zp.zone_id,
        zp.zone_name,
        zp.avg_multiplier,
        COALESCE(rc.completion_rate, 0) as completion_rate,
        zp.surge_events,
        zp.decrease_events,
        -- Efficiency score: high multiplier + low completion = inefficient
        (zp.avg_multiplier * 0.7) + ((100 - COALESCE(rc.completion_rate, 0)) * 0.3) as inefficiency_score
    FROM zone_performance zp
    LEFT JOIN ride_completion rc ON zp.zone_id = rc.zone_id
    WHERE zp.avg_multiplier > 1.2  -- Only consider zones with surge
),

ranked_zones AS (
    -- Rank by inefficiency
    SELECT 
        zone_id,
        zone_name,
        avg_multiplier,
        completion_rate,
        surge_events,
        decrease_events,
        inefficiency_score,
        RANK() OVER (ORDER BY inefficiency_score DESC) as inefficiency_rank
    FROM efficiency_ranking
)

-- Final result: Top 5 least efficient zones
SELECT 
    zone_name,
    ROUND(avg_multiplier, 2) as average_multiplier,
    completion_rate,
    inefficiency_rank,
    surge_events,
    decrease_events,
    ROUND(inefficiency_score, 2) as inefficiency_score
FROM ranked_zones
WHERE inefficiency_rank <= 5
ORDER BY inefficiency_rank;
```

---

## Part 7: 🚀 Scalability and Reliability

### High Availability & Fault Tolerance:

#### 1. **High Availability Architecture**
```
┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Load Balancer │
│   (Active)      │    │   (Standby)     │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
     ┌────────────────┼────────────────┐
     │                │                │
┌───▼────┐    ┌──────▼──────┐    ┌───▼────┐
│Pricing │    │  Pricing    │    │Pricing │
│Service │    │  Service    │    │Service │
│Node 1  │    │  Node 2     │    │Node 3  │
└───┬────┘    └──────┬──────┘    └───┬────┘
    │                │                │
    └────────────────┼────────────────┘
                     │
            ┌────────▼────────┐
            │   Redis Cluster │
            │  (3 Masters +   │
            │   6 Replicas)   │
            └─────────────────┘
```

#### 2. **Fault Tolerance Scenarios**

**Scenario 1: Stream Processor Failure**
```python
class StreamProcessorFailover:
    def __init__(self):
        self.primary_processor = FlinkProcessor("primary")
        self.backup_processor = FlinkProcessor("backup")
        self.health_check_interval = 30
        
    def handle_processor_failure(self):
        # 1. Detect failure via health check
        if not self.primary_processor.is_healthy():
            # 2. Switch to backup processor
            self.backup_processor.start()
            
            # 3. Replay events from Kafka
            self.backup_processor.replay_from_checkpoint()
            
            # 4. Update service discovery
            self.update_service_registry("backup")
            
            # 5. Alert operations team
            self.send_alert("Stream processor failover activated")
```

**Scenario 2: Redis Cache Failure**
```python
class CacheFailover:
    def __init__(self):
        self.redis_cluster = RedisCluster()
        self.fallback_cache = LocalCache()
        self.database_fallback = PostgreSQL()
        
    def get_pricing_data(self, zone_id):
        try:
            # Try Redis cluster first
            return self.redis_cluster.get(f"pricing:{zone_id}")
        except RedisConnectionError:
            # Fallback to local cache
            data = self.fallback_cache.get(zone_id)
            if data:
                return data
            
            # Final fallback to database
            return self.database_fallback.get_latest_pricing(zone_id)
```

#### 3. **Recovery Procedures**

```bash
#!/bin/bash

# 1. Health check all services
check_service_health() {
    services=("pricing-service" "geospatial-service" "stream-processor")
    for service in "${services[@]}"; do
        if ! curl -f http://$service:8000/health; then
            echo "Service $service is down, initiating recovery..."
            recover_service $service
        fi
    done
}

# 2. Service recovery
recover_service() {
    local service=$1
    docker-compose restart $service
    sleep 30
    
    # Verify recovery
    if curl -f http://$service:8000/health; then
        echo "Service $service recovered successfully"
    else
        echo "Service $service recovery failed, escalating..."
        send_alert "Critical service $service recovery failed"
    fi
}
```

### Performance Bottlenecks:

#### 1. **10x Scale Bottlenecks**

**Bottleneck 1: Redis Cache**
- **Current**: 10K requests/second
- **10x Scale**: 100K requests/second
- **Solution**: Redis Cluster with 10+ nodes, read replicas

**Bottleneck 2: Database Connections**
- **Current**: 100 connections
- **10x Scale**: 1000+ connections
- **Solution**: Connection pooling, read replicas, sharding

**Bottleneck 3: Stream Processing**
- **Current**: 1M events/minute
- **10x Scale**: 10M events/minute
- **Solution**: Horizontal scaling, parallel processing

#### 2. **Scaling Solutions**

```yaml
# Kubernetes scaling configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pricing-service
spec:
  replicas: 10
  template:
    spec:
      containers:
      - name: pricing-service
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: pricing-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: pricing-service
  minReplicas: 5
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```


## 🎯 Implementation Summary

### ✅ Completed:

1. **Assumptions and clarifications** - Defined scope and constraints
2. **High-level architecture** - Microservices architecture with 5 core services
3. **Data model** - PostgreSQL + Redis + MongoDB + Kafka
4. **API design** - RESTful APIs with 3 main endpoints
5. **Component detail** - Real-time geospatial processing with S2 cells
6. **SQL queries** - Complex analytics query with CTEs and window functions
7. **Scalability** - HA architecture with fault tolerance

### 🚀 Key Features:

- **Real-time pricing** with latency < 150ms
- **Geospatial processing** with S2 cell indexing
- **Fault tolerance** with automatic failover
- **Horizontal scaling** with Kubernetes
- **Analytics** with complex SQL queries
- **Multi-language support** with i18n service

### 📊 Performance Targets:

- **Throughput**: 10K+ requests/second
- **Latency**: P99 < 150ms
- **Availability**: 99.9% uptime
- **Scale**: 100M+ MAU support
- **Geographic**: 1000+ surge zones

---

## 📞 Contact Information

**Project Owner & Developer:**
- **Email**: minh.nguyenkhac1983@gmail.com
- **Phone**: +84 837873388
- **Project**: Equilibrium Dynamic Pricing Platform
- **Copyright**: © 2025 Equilibrium Platform. All rights reserved.
- **AI Support**: This project is enhanced with artificial intelligence technologies.

For technical support, implementation questions, or collaboration inquiries, please contact the project owner directly.

---


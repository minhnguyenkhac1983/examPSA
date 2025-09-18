# Diagram 02: System Architecture (Updated)

## Overview
This diagram illustrates the core system architecture of the Equilibrium Dynamic Pricing Platform, focusing on the main components, data flows, and key services including Event Ingestion, Stream Processing, Pricing Engine, Caching Layer, and Notification Service.

## System Architecture with Key Components

```mermaid
graph TB
    subgraph CLIENT["📱 Client Applications"]
        MA["Mobile App<br/>React Native/Flutter<br/>User Interface"]
        DA["Driver App<br/>React Native/Flutter<br/>Driver Interface"]
        AP["Admin Portal<br/>React.js<br/>Management Dashboard"]
    end
    
    subgraph GATEWAY["🚪 API Gateway & Load Balancer"]
        LB["Load Balancer<br/>Nginx<br/>Traffic Distribution"]
        AG["API Gateway<br/>Port 8000<br/>Request Routing"]
    end
    
    subgraph EVENT_INGESTION["📥 Event Ingestion Layer"]
        EI["Event Ingestion<br/>Real-time Data Collection<br/>GPS, Demand, Supply Events"]
        KAFKA["Apache Kafka<br/>Port 9092<br/>Event Streaming Platform"]
        ZK["Zookeeper<br/>Port 2181<br/>Kafka Coordination"]
    end
    
    subgraph STREAM_PROCESSING["⚡ Stream Processing Layer"]
        SP["Stream Processor<br/>Port 8004<br/>Real-time Data Processing"]
        FLINK["Apache Flink<br/>Event Processing Engine<br/>Window Operations"]
    end
    
    subgraph PRICING_ENGINE["💰 Pricing Engine Layer"]
        PS["Pricing Service<br/>Port 8001<br/>Core Pricing Logic"]
        ML["ML Pricing Service<br/>Port 8007<br/>Machine Learning Models"]
        GS["Geospatial Service<br/>Port 8003<br/>Location Processing"]
    end
    
    subgraph CACHING_LAYER["⚡ Caching Layer"]
        REDIS["Redis Cluster<br/>Port 6379<br/>High-speed Cache"]
        CACHE_POLICY["Cache Policies<br/>TTL, Invalidation<br/>Performance Optimization"]
    end
    
    subgraph NOTIFICATION_SERVICE["📢 Notification Service"]
        NS["Notification Service<br/>Port 8008<br/>Push Notifications"]
        WS["WebSocket Service<br/>Port 8005<br/>Real-time Communication"]
        PUSH_GATEWAY["Push Gateway<br/>FCM, APNS<br/>Mobile Notifications"]
    end
    
    subgraph DATA_STORAGE["💾 Data Storage Layer"]
        PG["PostgreSQL<br/>Port 5432<br/>Transactional Data"]
        POSTGIS["PostGIS<br/>Spatial Extensions<br/>Geographic Data"]
        MONGO["MongoDB<br/>Port 27017<br/>Event Storage"]
    end
    
    subgraph MONITORING["📊 Monitoring & Analytics"]
        PROM["Prometheus<br/>Port 9090<br/>Metrics Collection"]
        GRAF["Grafana<br/>Port 3001<br/>Visualization"]
        AS["Analytics Service<br/>Port 8002<br/>Business Intelligence"]
    end
    
    %% Client to Gateway
    MA --> LB
    DA --> LB
    AP --> LB
    LB --> AG
    
    %% Gateway to Services
    AG --> PS
    AG --> NS
    AG --> AS
    
    %% Event Ingestion Flow
    MA --> EI
    DA --> EI
    EI --> KAFKA
    KAFKA --> ZK
    
    %% Stream Processing Flow
    KAFKA --> SP
    SP --> FLINK
    FLINK --> PS
    FLINK --> ML
    
    %% Pricing Engine Flow
    PS --> ML
    PS --> GS
    PS --> REDIS
    ML --> REDIS
    GS --> PG
    PG --> POSTGIS
    
    %% Caching Layer Flow
    PS --> CACHE_POLICY
    CACHE_POLICY --> REDIS
    REDIS --> PS
    REDIS --> ML
    
    %% Notification Service Flow
    PS --> NS
    NS --> WS
    NS --> PUSH_GATEWAY
    WS --> MA
    WS --> DA
    PUSH_GATEWAY --> MA
    PUSH_GATEWAY --> DA
    
    %% Data Storage Flow
    SP --> MONGO
    PS --> PG
    AS --> PG
    AS --> MONGO
    
    %% Monitoring Flow
    PS --> PROM
    SP --> PROM
    NS --> PROM
    PROM --> GRAF
    AS --> GRAF
    
    %% Styling
    classDef clientLayer fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    classDef gatewayLayer fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    classDef eventLayer fill:#e8f5e8,stroke:#388e3c,stroke-width:3px
    classDef streamLayer fill:#fff3e0,stroke:#f57c00,stroke-width:3px
    classDef pricingLayer fill:#fce4ec,stroke:#c2185b,stroke-width:3px
    classDef cacheLayer fill:#f1f8e9,stroke:#689f38,stroke-width:3px
    classDef notificationLayer fill:#e0f2f1,stroke:#00796b,stroke-width:3px
    classDef dataLayer fill:#fff8e1,stroke:#ff8f00,stroke-width:3px
    classDef monitorLayer fill:#f3e5f5,stroke:#9c27b0,stroke-width:3px
    
    class MA,DA,AP clientLayer
    class LB,AG gatewayLayer
    class EI,KAFKA,ZK eventLayer
    class SP,FLINK streamLayer
    class PS,ML,GS pricingLayer
    class REDIS,CACHE_POLICY cacheLayer
    class NS,WS,PUSH_GATEWAY notificationLayer
    class PG,POSTGIS,MONGO dataLayer
    class PROM,GRAF,AS monitorLayer
```

## Component Descriptions

### 📱 Client Applications
- **Mobile App**: User interface for ride requests and price estimation
- **Driver App**: Driver interface for ride acceptance and navigation
- **Admin Portal**: Management dashboard for system monitoring and control

### 🚪 API Gateway & Load Balancer
- **Load Balancer**: Distributes incoming traffic across multiple service instances
- **API Gateway**: Central entry point for all API requests with routing and authentication

### 📥 Event Ingestion Layer
- **Event Ingestion**: Collects real-time events from mobile apps and external sources
- **Apache Kafka**: High-throughput event streaming platform for data ingestion
- **Zookeeper**: Coordinates Kafka cluster and manages configuration

### ⚡ Stream Processing Layer
- **Stream Processor**: Processes real-time data streams for pricing calculations
- **Apache Flink**: Distributed stream processing engine with window operations

### 💰 Pricing Engine Layer
- **Pricing Service**: Core pricing logic and surge calculation algorithms
- **ML Pricing Service**: Machine learning models for predictive pricing
- **Geospatial Service**: Location-based processing and zone management

### ⚡ Caching Layer
- **Redis Cluster**: High-speed in-memory cache for frequently accessed data
- **Cache Policies**: TTL management and cache invalidation strategies

### 📢 Notification Service
- **Notification Service**: Manages push notifications and alerts
- **WebSocket Service**: Real-time bidirectional communication
- **Push Gateway**: Integrates with FCM and APNS for mobile notifications

### 💾 Data Storage Layer
- **PostgreSQL**: Primary transactional database with ACID compliance
- **PostGIS**: Spatial database extensions for geographic data processing
- **MongoDB**: Document database for event storage and analytics

### 📊 Monitoring & Analytics
- **Prometheus**: Metrics collection and monitoring system
- **Grafana**: Data visualization and dashboard platform
- **Analytics Service**: Business intelligence and reporting

## Data Flows Between Services

### 1. **Real-time Event Processing Flow**
```mermaid
graph LR
    A[Client Apps] --> B[Event Ingestion]
    B --> C[Kafka Streams]
    C --> D[Stream Processor]
    D --> E[Pricing Engine]
    E --> F[Cache Layer]
    F --> G[Notification Service]
    G --> H[Client Apps]
```

### 2. **Pricing Calculation Flow**
```mermaid
graph LR
    A[Price Request] --> B[API Gateway]
    B --> C[Pricing Service]
    C --> D[ML Service]
    C --> E[Geospatial Service]
    D --> F[Cache Check]
    E --> F
    F --> G[Price Response]
```

### 3. **Notification Flow**
```mermaid
graph LR
    A[Price Update] --> B[Notification Service]
    B --> C[WebSocket Service]
    B --> D[Push Gateway]
    C --> E[Real-time Updates]
    D --> F[Mobile Notifications]
```

## Key Service Interactions

### Event Ingestion → Stream Processor
- **Data Flow**: Real-time events from mobile apps and external sources
- **Processing**: Event filtering, validation, and enrichment
- **Output**: Structured events for downstream processing

### Stream Processor → Pricing Engine
- **Data Flow**: Processed events with location and demand data
- **Processing**: Real-time pricing calculations and surge detection
- **Output**: Updated pricing information and market conditions

### Pricing Engine → Caching Layer
- **Data Flow**: Calculated prices and market data
- **Processing**: Cache storage with TTL and invalidation policies
- **Output**: Fast access to pricing data for API responses

### Caching Layer → Notification Service
- **Data Flow**: Cache invalidation events and price updates
- **Processing**: Real-time notification triggers
- **Output**: Push notifications and WebSocket updates

## Performance Characteristics

| Component | Latency | Throughput | Availability |
|-----------|---------|------------|--------------|
| Event Ingestion | < 10ms | 100K+ events/s | 99.9% |
| Stream Processor | < 50ms | 50K+ events/s | 99.9% |
| Pricing Engine | < 100ms | 10K+ requests/s | 99.9% |
| Caching Layer | < 5ms | 100K+ ops/s | 99.9% |
| Notification Service | < 200ms | 5K+ notifications/s | 99.9% |

## Scalability Features

### Horizontal Scaling
- **Event Ingestion**: Kafka partitions for parallel processing
- **Stream Processor**: Flink task managers for distributed processing
- **Pricing Engine**: Multiple service instances with load balancing
- **Caching Layer**: Redis cluster with sharding
- **Notification Service**: Multiple notification workers

### Vertical Scaling
- **Resource Allocation**: CPU and memory optimization per service
- **Connection Pooling**: Database and cache connection management
- **Memory Management**: Efficient data structures and garbage collection

## Security Considerations

### Data Protection
- **Encryption**: TLS 1.3 for data in transit
- **Authentication**: JWT tokens and OAuth 2.0
- **Authorization**: Role-based access control (RBAC)
- **Rate Limiting**: API throttling and DDoS protection

### Privacy
- **Data Anonymization**: Personal data protection
- **Audit Logging**: Comprehensive activity tracking
- **Compliance**: GDPR and data protection regulations

---

*This architecture provides a scalable, real-time dynamic pricing platform with high availability and performance for ride-sharing services.*

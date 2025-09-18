# Diagram 03: Service Sequence Diagrams

## Overview
This document contains sequence diagrams showing the interaction patterns between different services in the Equilibrium Dynamic Pricing Platform.

## 1. Price Estimation Sequence

```mermaid
sequenceDiagram
    participant MA as Mobile App
    participant AG as API Gateway
    participant PS as Pricing Service
    participant GS as Geospatial Service
    participant ML as ML Pricing Service
    participant REDIS as Redis Cache
    participant PG as PostgreSQL
    participant KAFKA as Kafka

    MA->>AG: POST /api/v1/pricing/estimate
    Note over MA,AG: Request with pickup/dropoff locations
    
    AG->>PS: Forward pricing request
    Note over AG,PS: Route to pricing service
    
    PS->>REDIS: Check cache for recent pricing
    alt Cache Hit
        REDIS-->>PS: Return cached price
        PS-->>AG: Return cached price estimate
        AG-->>MA: Return price estimate
    else Cache Miss
        PS->>GS: Get zone information
        Note over PS,GS: Determine pricing zone
        
        GS->>PG: Query zone boundaries
        PG-->>GS: Return zone data
        GS-->>PS: Return zone information
        
        PS->>ML: Calculate dynamic price
        Note over PS,ML: ML-based pricing calculation
        
        ML->>PG: Get historical data
        PG-->>ML: Return pricing history
        ML->>REDIS: Get real-time factors
        REDIS-->>ML: Return demand/supply data
        ML-->>PS: Return calculated price
        
        PS->>REDIS: Cache price result
        PS->>KAFKA: Publish pricing event
        Note over PS,KAFKA: Log pricing decision
        
        PS-->>AG: Return price estimate
        AG-->>MA: Return price estimate
    end
```

## 2. User Authentication Sequence

```mermaid
sequenceDiagram
    participant MA as Mobile App
    participant AG as API Gateway
    participant AUTH as Auth Service
    participant PG as PostgreSQL
    participant REDIS as Redis Cache
    participant NS as Notification Service

    MA->>AG: POST /api/v1/auth/login
    Note over MA,AG: Login credentials
    
    AG->>AUTH: Forward authentication request
    Note over AG,AUTH: Route to auth service
    
    AUTH->>PG: Validate user credentials
    PG-->>AUTH: Return user data
    
    alt Valid Credentials
        AUTH->>AUTH: Generate JWT token
        AUTH->>REDIS: Store session data
        AUTH->>NS: Send login notification
        Note over AUTH,NS: Optional push notification
        
        AUTH-->>AG: Return JWT token + user data
        AG-->>MA: Return authentication success
    else Invalid Credentials
        AUTH-->>AG: Return authentication error
        AG-->>MA: Return login failure
    end
```

## 3. Real-time Price Update Sequence

```mermaid
sequenceDiagram
    participant SP as Stream Processor
    participant KAFKA as Kafka
    participant PS as Pricing Service
    participant ML as ML Pricing Service
    participant REDIS as Redis Cache
    participant WS as WebSocket Service
    participant MA as Mobile App

    SP->>KAFKA: Consume demand/supply events
    Note over SP,KAFKA: Real-time data ingestion
    
    SP->>PS: Trigger price recalculation
    Note over SP,PS: Price update trigger
    
    PS->>ML: Recalculate prices for affected zones
    ML->>REDIS: Get current market data
    REDIS-->>ML: Return real-time factors
    ML-->>PS: Return updated prices
    
    PS->>REDIS: Update cached prices
    PS->>KAFKA: Publish price update events
    
    KAFKA->>WS: Stream price updates
    WS->>MA: Send WebSocket price update
    Note over WS,MA: Real-time price notification
```

## 4. Driver Matching Sequence

```mermaid
sequenceDiagram
    participant MA as Mobile App
    participant AG as API Gateway
    participant PS as Pricing Service
    participant GS as Geospatial Service
    participant NS as Notification Service
    participant DA as Driver App
    participant PG as PostgreSQL

    MA->>AG: POST /api/v1/booking/request
    Note over MA,AG: Ride booking request
    
    AG->>PS: Forward booking request
    PS->>GS: Find nearby drivers
    GS->>PG: Query available drivers
    PG-->>GS: Return driver list
    GS-->>PS: Return nearby drivers
    
    PS->>NS: Send driver notifications
    Note over PS,NS: Notify available drivers
    
    loop For each nearby driver
        NS->>DA: Push notification
        Note over NS,DA: Ride request notification
    end
    
    DA->>AG: POST /api/v1/driver/accept
    Note over DA,AG: Driver accepts ride
    
    AG->>PS: Update booking status
    PS->>PG: Update ride status
    PS->>NS: Notify user of driver acceptance
    NS->>MA: Push notification
    Note over NS,MA: Driver assigned notification
```

## 5. Analytics Data Collection Sequence

```mermaid
sequenceDiagram
    participant PS as Pricing Service
    participant KAFKA as Kafka
    participant SP as Stream Processor
    participant AAS as Advanced Analytics
    participant PG as PostgreSQL
    participant MONGO as MongoDB
    participant REDIS as Redis Cache

    PS->>KAFKA: Publish pricing event
    Note over PS,KAFKA: Price calculation event
    
    KAFKA->>SP: Stream pricing data
    SP->>SP: Process and aggregate data
    SP->>AAS: Send processed analytics
    
    AAS->>PG: Store structured analytics
    AAS->>MONGO: Store event data
    AAS->>REDIS: Cache real-time metrics
    
    Note over AAS: Analytics processing complete
    
    AAS->>AAS: Generate insights
    AAS->>REDIS: Update dashboard cache
    Note over AAS,REDIS: Real-time analytics ready
```

## 6. Multi-language Support Sequence

```mermaid
sequenceDiagram
    participant MA as Mobile App
    participant AG as API Gateway
    participant I18N as i18n Service
    participant REDIS as Redis Cache
    participant PS as Pricing Service

    MA->>AG: GET /api/v1/pricing/estimate
    Note over MA,AG: Request with language header
    
    AG->>I18N: Get translations
    Note over AG,I18N: Language preference
    
    I18N->>REDIS: Check translation cache
    alt Translation Cached
        REDIS-->>I18N: Return cached translations
    else Translation Not Cached
        I18N->>I18N: Load translation files
        I18N->>REDIS: Cache translations
    end
    
    I18N-->>AG: Return translated content
    AG->>PS: Get pricing data
    PS-->>AG: Return pricing information
    
    AG->>AG: Apply translations to response
    AG-->>MA: Return localized response
    Note over AG,MA: Localized pricing data
```

## 7. Error Handling Sequence

```mermaid
sequenceDiagram
    participant MA as Mobile App
    participant AG as API Gateway
    participant PS as Pricing Service
    participant GS as Geospatial Service
    participant REDIS as Redis Cache
    participant MONITOR as Monitoring

    MA->>AG: POST /api/v1/pricing/estimate
    AG->>PS: Forward request
    
    PS->>GS: Get zone information
    GS-->>PS: Service unavailable error
    
    PS->>PS: Handle fallback logic
    PS->>REDIS: Get cached zone data
    REDIS-->>PS: Return cached data
    
    PS->>MONITOR: Log service error
    Note over PS,MONITOR: Error tracking
    
    PS-->>AG: Return fallback pricing
    AG-->>MA: Return price estimate
    Note over AG,MA: Graceful degradation
```

## 8. WebSocket Real-time Updates Sequence

```mermaid
sequenceDiagram
    participant MA as Mobile App
    participant WS as WebSocket Service
    participant REDIS as Redis Cache
    participant KAFKA as Kafka
    participant PS as Pricing Service

    MA->>WS: WebSocket connection
    Note over MA,WS: Establish real-time connection
    
    WS->>REDIS: Subscribe to user channel
    Note over WS,REDIS: Subscribe to updates
    
    PS->>KAFKA: Publish price update
    KAFKA->>WS: Stream price update
    WS->>REDIS: Check user subscriptions
    REDIS-->>WS: Return subscribed users
    WS->>MA: Send price update
    Note over WS,MA: Real-time price notification
    
    PS->>KAFKA: Publish driver update
    KAFKA->>WS: Stream driver update
    WS->>MA: Send driver status update
    Note over WS,MA: Real-time driver info
```

## Service Interaction Patterns

### 1. **Request-Response Pattern**
- Used for synchronous operations
- API Gateway routes requests to appropriate services
- Services return immediate responses
- Examples: Price estimation, user authentication

### 2. **Event-Driven Pattern**
- Used for asynchronous operations
- Services publish events to Kafka
- Other services consume and react to events
- Examples: Price updates, analytics collection

### 3. **Real-time Communication Pattern**
- WebSocket connections for live updates
- Redis pub/sub for message distribution
- Push notifications for mobile apps
- Examples: Price changes, driver locations

### 4. **Caching Pattern**
- Redis for high-speed data access
- Cache-aside pattern for frequently accessed data
- Cache invalidation on data updates
- Examples: Price quotes, user sessions

## Performance Considerations

### Latency Optimization
- Service calls: < 100ms
- Database queries: < 20ms
- Cache access: < 5ms
- WebSocket updates: < 50ms

### Throughput Optimization
- Concurrent request handling
- Connection pooling
- Async processing where possible
- Load balancing across service instances

### Error Handling
- Circuit breaker pattern
- Retry mechanisms with exponential backoff
- Graceful degradation
- Comprehensive error logging

---

*These sequence diagrams illustrate the complex interactions between services in the Equilibrium platform, ensuring reliable and performant dynamic pricing operations.*

# Analytical SQL Queries Guide

## Overview

This document provides comprehensive analytical SQL queries for the Equilibrium Dynamic Pricing Platform, focusing on operational reporting, performance analysis, and business intelligence.

## Complex Query: Top 5 Inefficient Surge Zones

### Objective
Identify zones with high average surge multiplier and low trip completion rate over the past month.

### Key Features Used
- **Common Table Expressions (CTEs)**: 6 nested CTEs for modular analysis
- **Window Functions**: RANK(), ROW_NUMBER(), DENSE_RANK(), PERCENT_RANK(), CUME_DIST()
- **Advanced Aggregation**: Multiple aggregation functions with conditional logic
- **Complex Joins**: Multi-table joins with spatial and temporal data
- **Statistical Functions**: CORR(), STDDEV(), PERCENTILE_CONT()

### Query Structure

```sql
-- Main Query Structure
WITH 
    zone_performance AS (...),           -- CTE 1: Basic zone metrics
    supply_demand_analysis AS (...),     -- CTE 2: Supply/demand patterns
    driver_location_analysis AS (...),   -- CTE 3: Driver behavior
    weather_impact AS (...),             -- CTE 4: Weather correlation
    inefficiency_analysis AS (...),      -- CTE 5: Score calculation
    final_analysis AS (...)              -- CTE 6: Ranking and window functions

SELECT ... FROM final_analysis
WHERE inefficiency_rank <= 5
ORDER BY inefficiency_rank;
```

## Additional Analytical Queries

### 1. Revenue Optimization Analysis

```sql
-- Identify zones with highest revenue potential
WITH revenue_analysis AS (
    SELECT 
        sz.zone_id,
        sz.zone_name,
        sz.city,
        
        -- Revenue metrics
        SUM(CASE WHEN pel.event_status = 'completed' THEN pel.final_fare ELSE 0 END) AS total_revenue,
        COUNT(CASE WHEN pel.event_status = 'completed' THEN 1 END) AS completed_trips,
        AVG(CASE WHEN pel.event_status = 'completed' THEN pel.final_fare END) AS avg_fare,
        
        -- Demand metrics
        COUNT(pel.log_id) AS total_requests,
        AVG(pel.surge_multiplier) AS avg_surge_multiplier,
        
        -- Efficiency metrics
        COUNT(CASE WHEN pel.event_status = 'completed' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(pel.log_id), 0) AS completion_rate,
        
        -- Revenue per request
        SUM(CASE WHEN pel.event_status = 'completed' THEN pel.final_fare ELSE 0 END) / 
        NULLIF(COUNT(pel.log_id), 0) AS revenue_per_request,
        
        -- Peak hour analysis
        COUNT(CASE WHEN EXTRACT(HOUR FROM pel.event_timestamp) BETWEEN 17 AND 19 THEN 1 END) AS evening_requests,
        COUNT(CASE WHEN EXTRACT(HOUR FROM pel.event_timestamp) BETWEEN 7 AND 9 THEN 1 END) AS morning_requests
        
    FROM surge_zones sz
    LEFT JOIN pricing_event_logs pel ON sz.zone_id = pel.pickup_zone_id
    WHERE 
        pel.event_timestamp >= CURRENT_DATE - INTERVAL '1 month'
        AND sz.is_active = true
    GROUP BY sz.zone_id, sz.zone_name, sz.city
    HAVING COUNT(pel.log_id) >= 100
)

SELECT 
    zone_name,
    city,
    ROUND(total_revenue, 2) AS total_revenue,
    completed_trips,
    ROUND(avg_fare, 2) AS avg_fare,
    total_requests,
    ROUND(completion_rate, 2) AS completion_rate,
    ROUND(revenue_per_request, 2) AS revenue_per_request,
    ROUND(avg_surge_multiplier, 3) AS avg_surge_multiplier,
    
    -- Revenue potential score
    ROUND(
        (total_revenue * 0.4) + 
        (completion_rate * 0.3) + 
        (revenue_per_request * 0.3), 2
    ) AS revenue_potential_score,
    
    -- Ranking
    RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank,
    RANK() OVER (ORDER BY revenue_per_request DESC) AS efficiency_rank
    
FROM revenue_analysis
ORDER BY revenue_potential_score DESC
LIMIT 10;
```

### 2. Driver Performance Analysis

```sql
-- Analyze driver performance and availability patterns
WITH driver_performance AS (
    SELECT 
        dle.driver_id,
        dle.zone_id,
        sz.zone_name,
        
        -- Activity metrics
        COUNT(dle.event_id) AS total_events,
        COUNT(CASE WHEN dle.is_available THEN 1 END) AS available_events,
        COUNT(CASE WHEN dle.event_type = 'location_update' THEN 1 END) AS location_updates,
        
        -- Availability rate
        COUNT(CASE WHEN dle.is_available THEN 1 END) * 100.0 / 
        NULLIF(COUNT(dle.event_id), 0) AS availability_rate,
        
        -- Response time metrics
        AVG(dle.response_time_ms) AS avg_response_time,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY dle.response_time_ms) AS p95_response_time,
        
        -- Geographic coverage
        COUNT(DISTINCT dle.s2_cell_id) AS unique_cells_covered,
        AVG(dle.accuracy) AS avg_location_accuracy,
        
        -- Time patterns
        COUNT(CASE WHEN EXTRACT(HOUR FROM dle.timestamp) BETWEEN 6 AND 18 THEN 1 END) AS daytime_events,
        COUNT(CASE WHEN EXTRACT(HOUR FROM dle.timestamp) BETWEEN 18 AND 6 THEN 1 END) AS nighttime_events,
        
        -- Weekend vs weekday
        COUNT(CASE WHEN EXTRACT(DOW FROM dle.timestamp) IN (0, 6) THEN 1 END) AS weekend_events,
        COUNT(CASE WHEN EXTRACT(DOW FROM dle.timestamp) BETWEEN 1 AND 5 THEN 1 END) AS weekday_events
        
    FROM driver_location_events dle
    JOIN surge_zones sz ON dle.zone_id = sz.zone_id
    WHERE 
        dle.timestamp >= CURRENT_DATE - INTERVAL '1 month'
        AND dle.is_processed = true
    GROUP BY dle.driver_id, dle.zone_id, sz.zone_name
    HAVING COUNT(dle.event_id) >= 100
),

driver_rankings AS (
    SELECT 
        *,
        -- Performance score calculation
        (
            (availability_rate * 0.4) +
            (LEAST(100, (1000 - avg_response_time) / 10) * 0.3) +
            (LEAST(100, unique_cells_covered * 2) * 0.2) +
            (LEAST(100, (100 - avg_location_accuracy) * 2) * 0.1)
        ) AS performance_score,
        
        -- Rankings
        RANK() OVER (PARTITION BY zone_id ORDER BY availability_rate DESC) AS availability_rank,
        RANK() OVER (PARTITION BY zone_id ORDER BY avg_response_time ASC) AS response_time_rank,
        RANK() OVER (PARTITION BY zone_id ORDER BY unique_cells_covered DESC) AS coverage_rank
        
    FROM driver_performance
)

SELECT 
    driver_id,
    zone_name,
    total_events,
    ROUND(availability_rate, 2) AS availability_rate,
    ROUND(avg_response_time, 0) AS avg_response_time_ms,
    ROUND(p95_response_time, 0) AS p95_response_time_ms,
    unique_cells_covered,
    ROUND(avg_location_accuracy, 2) AS avg_location_accuracy,
    ROUND(performance_score, 2) AS performance_score,
    
    -- Rankings
    availability_rank,
    response_time_rank,
    coverage_rank,
    
    -- Performance category
    CASE 
        WHEN performance_score >= 80 THEN 'Excellent'
        WHEN performance_score >= 60 THEN 'Good'
        WHEN performance_score >= 40 THEN 'Fair'
        ELSE 'Poor'
    END AS performance_category,
    
    -- Time pattern analysis
    ROUND(daytime_events * 100.0 / NULLIF(total_events, 0), 2) AS daytime_percentage,
    ROUND(weekend_events * 100.0 / NULLIF(total_events, 0), 2) AS weekend_percentage
    
FROM driver_rankings
WHERE performance_score IS NOT NULL
ORDER BY zone_name, performance_score DESC;
```

### 3. Surge Multiplier Trend Analysis

```sql
-- Analyze surge multiplier trends and patterns
WITH surge_trends AS (
    SELECT 
        DATE_TRUNC('hour', pel.event_timestamp) AS hour_bucket,
        sz.zone_id,
        sz.zone_name,
        sz.city,
        
        -- Surge metrics
        AVG(pel.surge_multiplier) AS avg_surge_multiplier,
        MAX(pel.surge_multiplier) AS max_surge_multiplier,
        MIN(pel.surge_multiplier) AS min_surge_multiplier,
        STDDEV(pel.surge_multiplier) AS surge_volatility,
        
        -- Request volume
        COUNT(pel.log_id) AS total_requests,
        COUNT(CASE WHEN pel.event_status = 'completed' THEN 1 END) AS completed_requests,
        
        -- Time context
        EXTRACT(HOUR FROM pel.event_timestamp) AS hour_of_day,
        EXTRACT(DOW FROM pel.event_timestamp) AS day_of_week,
        CASE WHEN EXTRACT(DOW FROM pel.event_timestamp) IN (0, 6) THEN 'Weekend' ELSE 'Weekday' END AS day_type
        
    FROM pricing_event_logs pel
    JOIN surge_zones sz ON pel.pickup_zone_id = sz.zone_id
    WHERE 
        pel.event_timestamp >= CURRENT_DATE - INTERVAL '1 month'
        AND sz.is_active = true
    GROUP BY 
        DATE_TRUNC('hour', pel.event_timestamp),
        sz.zone_id, sz.zone_name, sz.city,
        EXTRACT(HOUR FROM pel.event_timestamp),
        EXTRACT(DOW FROM pel.event_timestamp)
    HAVING COUNT(pel.log_id) >= 10
),

surge_patterns AS (
    SELECT 
        *,
        -- Moving averages for trend analysis
        AVG(avg_surge_multiplier) OVER (
            PARTITION BY zone_id 
            ORDER BY hour_bucket 
            ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING
        ) AS moving_avg_surge,
        
        -- Surge level classification
        CASE 
            WHEN avg_surge_multiplier >= 2.0 THEN 'Very High'
            WHEN avg_surge_multiplier >= 1.5 THEN 'High'
            WHEN avg_surge_multiplier >= 1.2 THEN 'Medium'
            ELSE 'Low'
        END AS surge_level,
        
        -- Volatility classification
        CASE 
            WHEN surge_volatility >= 0.5 THEN 'High Volatility'
            WHEN surge_volatility >= 0.2 THEN 'Medium Volatility'
            ELSE 'Low Volatility'
        END AS volatility_level
        
    FROM surge_trends
)

SELECT 
    zone_name,
    city,
    hour_bucket,
    hour_of_day,
    day_type,
    ROUND(avg_surge_multiplier, 3) AS avg_surge_multiplier,
    ROUND(moving_avg_surge, 3) AS moving_avg_surge,
    ROUND(surge_volatility, 3) AS surge_volatility,
    total_requests,
    completed_requests,
    surge_level,
    volatility_level,
    
    -- Trend analysis
    CASE 
        WHEN avg_surge_multiplier > moving_avg_surge * 1.1 THEN 'Rising'
        WHEN avg_surge_multiplier < moving_avg_surge * 0.9 THEN 'Falling'
        ELSE 'Stable'
    END AS trend_direction,
    
    -- Peak hour identification
    CASE 
        WHEN hour_of_day BETWEEN 7 AND 9 THEN 'Morning Rush'
        WHEN hour_of_day BETWEEN 17 AND 19 THEN 'Evening Rush'
        WHEN hour_of_day BETWEEN 22 AND 6 THEN 'Night'
        ELSE 'Regular'
    END AS time_period
    
FROM surge_patterns
WHERE surge_level IN ('High', 'Very High')
ORDER BY zone_name, hour_bucket;
```

### 4. Supply/Demand Imbalance Analysis

```sql
-- Identify supply/demand imbalances and optimization opportunities
WITH supply_demand_imbalance AS (
    SELECT 
        sds.zone_id,
        sz.zone_name,
        sz.city,
        DATE_TRUNC('hour', sds.snapshot_time) AS hour_bucket,
        
        -- Supply/demand metrics
        AVG(sds.available_drivers) AS avg_available_drivers,
        AVG(sds.active_requests) AS avg_active_requests,
        AVG(sds.supply_demand_ratio) AS avg_supply_demand_ratio,
        AVG(sds.surge_multiplier) AS avg_surge_multiplier,
        
        -- Imbalance indicators
        COUNT(CASE WHEN sds.supply_demand_ratio < 0.5 THEN 1 END) AS high_demand_periods,
        COUNT(CASE WHEN sds.supply_demand_ratio > 2.0 THEN 1 END) AS high_supply_periods,
        COUNT(CASE WHEN sds.surge_multiplier > 2.0 THEN 1 END) AS high_surge_periods,
        
        -- Time context
        EXTRACT(HOUR FROM sds.snapshot_time) AS hour_of_day,
        EXTRACT(DOW FROM sds.snapshot_time) AS day_of_week
        
    FROM supply_demand_snapshots sds
    JOIN surge_zones sz ON sds.zone_id = sz.zone_id
    WHERE 
        sds.snapshot_time >= CURRENT_DATE - INTERVAL '1 month'
        AND sz.is_active = true
    GROUP BY 
        sds.zone_id, sz.zone_name, sz.city,
        DATE_TRUNC('hour', sds.snapshot_time),
        EXTRACT(HOUR FROM sds.snapshot_time),
        EXTRACT(DOW FROM sds.snapshot_time)
    HAVING COUNT(sds.snapshot_id) >= 5
),

imbalance_analysis AS (
    SELECT 
        *,
        -- Imbalance score calculation
        (
            (high_demand_periods * 0.4) +
            (high_surge_periods * 0.3) +
            (LEAST(100, (1.0 - avg_supply_demand_ratio) * 100) * 0.3)
        ) AS imbalance_score,
        
        -- Imbalance classification
        CASE 
            WHEN avg_supply_demand_ratio < 0.5 THEN 'Critical Shortage'
            WHEN avg_supply_demand_ratio < 0.8 THEN 'High Demand'
            WHEN avg_supply_demand_ratio > 2.0 THEN 'Oversupply'
            WHEN avg_supply_demand_ratio > 1.5 THEN 'High Supply'
            ELSE 'Balanced'
        END AS imbalance_type,
        
        -- Time period classification
        CASE 
            WHEN hour_of_day BETWEEN 7 AND 9 THEN 'Morning Rush'
            WHEN hour_of_day BETWEEN 17 AND 19 THEN 'Evening Rush'
            WHEN hour_of_day BETWEEN 22 AND 6 THEN 'Night'
            ELSE 'Regular'
        END AS time_period
        
    FROM supply_demand_imbalance
)

SELECT 
    zone_name,
    city,
    hour_bucket,
    hour_of_day,
    time_period,
    ROUND(avg_available_drivers, 1) AS avg_available_drivers,
    ROUND(avg_active_requests, 1) AS avg_active_requests,
    ROUND(avg_supply_demand_ratio, 3) AS avg_supply_demand_ratio,
    ROUND(avg_surge_multiplier, 3) AS avg_surge_multiplier,
    high_demand_periods,
    high_supply_periods,
    high_surge_periods,
    ROUND(imbalance_score, 2) AS imbalance_score,
    imbalance_type,
    
    -- Recommendations
    CASE 
        WHEN imbalance_type = 'Critical Shortage' THEN 'URGENT: Increase driver incentives'
        WHEN imbalance_type = 'High Demand' THEN 'HIGH: Consider surge pricing'
        WHEN imbalance_type = 'Oversupply' THEN 'MEDIUM: Reduce driver allocation'
        WHEN imbalance_type = 'High Supply' THEN 'LOW: Monitor for efficiency'
        ELSE 'OPTIMAL: Maintain current levels'
    END AS recommendation
    
FROM imbalance_analysis
WHERE imbalance_type IN ('Critical Shortage', 'High Demand', 'Oversupply')
ORDER BY imbalance_score DESC, zone_name, hour_bucket;
```

## Performance Optimization

### Indexing Strategy

```sql
-- Essential indexes for analytical queries
CREATE INDEX CONCURRENTLY idx_pricing_logs_zone_timestamp 
ON pricing_event_logs(pickup_zone_id, event_timestamp);

CREATE INDEX CONCURRENTLY idx_pricing_logs_status_timestamp 
ON pricing_event_logs(event_status, event_timestamp);

CREATE INDEX CONCURRENTLY idx_supply_demand_zone_timestamp 
ON supply_demand_snapshots(zone_id, snapshot_time);

CREATE INDEX CONCURRENTLY idx_driver_location_zone_timestamp 
ON driver_location_events(zone_id, timestamp);

CREATE INDEX CONCURRENTLY idx_surge_zones_active 
ON surge_zones(is_active) WHERE is_active = true;

-- Composite indexes for complex queries
CREATE INDEX CONCURRENTLY idx_pricing_logs_complex 
ON pricing_event_logs(pickup_zone_id, event_status, event_timestamp);

CREATE INDEX CONCURRENTLY idx_supply_demand_complex 
ON supply_demand_snapshots(zone_id, snapshot_time, surge_multiplier);
```

### Query Optimization Tips

1. **Use EXPLAIN ANALYZE** to identify bottlenecks
2. **Partition large tables** by date for better performance
3. **Use materialized views** for frequently accessed aggregations
4. **Implement query result caching** for dashboard applications
5. **Consider columnar storage** for analytical workloads

### Monitoring Query Performance

```sql
-- Query performance monitoring
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements
WHERE query LIKE '%pricing_event_logs%'
ORDER BY total_time DESC
LIMIT 10;
```

This comprehensive analytical SQL guide provides the tools needed for deep operational analysis of the Equilibrium Dynamic Pricing Platform, enabling data-driven decision making and performance optimization.

-- Analytical SQL Query: Top 5 Inefficient Surge Zones
-- Objective: Identify zones with high average surge multiplier + low trip completion rate
-- Author: Equilibrium Platform Analytics Team
-- Date: 2025-01-16

-- =============================================================================
-- COMPLEX POSTGRESQL QUERY FOR OPERATIONAL REPORTING
-- =============================================================================

WITH 
-- CTE 1: Zone Performance Metrics
zone_performance AS (
    SELECT 
        sz.zone_id,
        sz.zone_name,
        sz.city,
        sz.zone_type,
        sz.base_fare,
        sz.maximum_surge_multiplier,
        
        -- Calculate average surge multiplier over past month
        AVG(pel.surge_multiplier) AS avg_surge_multiplier,
        
        -- Calculate trip completion rate
        COUNT(CASE WHEN pel.event_status = 'completed' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(CASE WHEN pel.event_status IN ('quoted', 'accepted', 'completed', 'cancelled') THEN 1 END), 0) AS completion_rate,
        
        -- Additional metrics for analysis
        COUNT(pel.log_id) AS total_requests,
        COUNT(CASE WHEN pel.event_status = 'completed' THEN 1 END) AS completed_trips,
        COUNT(CASE WHEN pel.event_status = 'cancelled' THEN 1 END) AS cancelled_trips,
        COUNT(CASE WHEN pel.event_status = 'expired' THEN 1 END) AS expired_quotes,
        
        -- Revenue metrics
        SUM(CASE WHEN pel.event_status = 'completed' THEN pel.final_fare ELSE 0 END) AS total_revenue,
        AVG(CASE WHEN pel.event_status = 'completed' THEN pel.final_fare END) AS avg_fare,
        
        -- Time-based analysis
        EXTRACT(HOUR FROM pel.event_timestamp) AS hour_of_day,
        EXTRACT(DOW FROM pel.event_timestamp) AS day_of_week,
        
        -- Surge analysis
        MAX(pel.surge_multiplier) AS max_surge_multiplier,
        MIN(pel.surge_multiplier) AS min_surge_multiplier,
        STDDEV(pel.surge_multiplier) AS surge_volatility,
        
        -- Demand patterns
        COUNT(CASE WHEN pel.surge_multiplier > 2.0 THEN 1 END) AS high_surge_events,
        COUNT(CASE WHEN pel.surge_multiplier > 1.5 THEN 1 END) AS medium_surge_events,
        COUNT(CASE WHEN pel.surge_multiplier <= 1.0 THEN 1 END) AS no_surge_events
        
    FROM surge_zones sz
    LEFT JOIN pricing_event_logs pel ON sz.zone_id = pel.pickup_zone_id
    WHERE 
        -- Past month filter
        pel.event_timestamp >= CURRENT_DATE - INTERVAL '1 month'
        AND pel.event_timestamp < CURRENT_DATE
        AND sz.is_active = true
    GROUP BY 
        sz.zone_id, sz.zone_name, sz.city, sz.zone_type, 
        sz.base_fare, sz.maximum_surge_multiplier
    HAVING 
        -- Only include zones with sufficient data
        COUNT(pel.log_id) >= 100
),

-- CTE 2: Supply/Demand Analysis
supply_demand_analysis AS (
    SELECT 
        sds.zone_id,
        
        -- Average supply/demand metrics
        AVG(sds.supply_demand_ratio) AS avg_supply_demand_ratio,
        AVG(sds.available_drivers) AS avg_available_drivers,
        AVG(sds.active_requests) AS avg_active_requests,
        
        -- Supply/demand volatility
        STDDEV(sds.supply_demand_ratio) AS supply_demand_volatility,
        
        -- Peak demand analysis
        MAX(sds.active_requests) AS peak_demand,
        MIN(sds.available_drivers) AS min_supply,
        
        -- Time-based supply/demand patterns
        AVG(CASE WHEN EXTRACT(HOUR FROM sds.snapshot_time) BETWEEN 7 AND 9 THEN sds.supply_demand_ratio END) AS morning_ratio,
        AVG(CASE WHEN EXTRACT(HOUR FROM sds.snapshot_time) BETWEEN 17 AND 19 THEN sds.supply_demand_ratio END) AS evening_ratio,
        AVG(CASE WHEN EXTRACT(HOUR FROM sds.snapshot_time) BETWEEN 22 AND 6 THEN sds.supply_demand_ratio END) AS night_ratio,
        
        -- Weekend vs weekday analysis
        AVG(CASE WHEN EXTRACT(DOW FROM sds.snapshot_time) IN (0, 6) THEN sds.supply_demand_ratio END) AS weekend_ratio,
        AVG(CASE WHEN EXTRACT(DOW FROM sds.snapshot_time) BETWEEN 1 AND 5 THEN sds.supply_demand_ratio END) AS weekday_ratio
        
    FROM supply_demand_snapshots sds
    WHERE 
        sds.snapshot_time >= CURRENT_DATE - INTERVAL '1 month'
        AND sds.snapshot_time < CURRENT_DATE
    GROUP BY sds.zone_id
),

-- CTE 3: Driver Location Analysis
driver_location_analysis AS (
    SELECT 
        dle.zone_id,
        
        -- Driver availability metrics
        AVG(CASE WHEN dle.is_available THEN 1.0 ELSE 0.0 END) AS driver_availability_rate,
        COUNT(DISTINCT CASE WHEN dle.is_available THEN dle.driver_id END) AS avg_available_drivers,
        COUNT(DISTINCT dle.driver_id) AS total_drivers,
        
        -- Response time analysis
        AVG(dle.response_time_ms) AS avg_response_time_ms,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY dle.response_time_ms) AS p95_response_time_ms,
        
        -- Driver activity patterns
        COUNT(CASE WHEN dle.event_type = 'location_update' THEN 1 END) AS location_updates,
        COUNT(CASE WHEN dle.event_type = 'status_change' THEN 1 END) AS status_changes,
        
        -- Geographic coverage
        COUNT(DISTINCT dle.s2_cell_id) AS unique_cells_covered,
        AVG(dle.accuracy) AS avg_location_accuracy
        
    FROM driver_location_events dle
    WHERE 
        dle.timestamp >= CURRENT_DATE - INTERVAL '1 month'
        AND dle.timestamp < CURRENT_DATE
        AND dle.is_processed = true
    GROUP BY dle.zone_id
),

-- CTE 4: Weather Impact Analysis (if available)
weather_impact AS (
    SELECT 
        sds.zone_id,
        
        -- Weather impact on surge
        AVG(CASE WHEN sds.weather_condition = 'rain' THEN sds.surge_multiplier END) AS avg_surge_in_rain,
        AVG(CASE WHEN sds.weather_condition = 'clear' THEN sds.surge_multiplier END) AS avg_surge_clear,
        AVG(CASE WHEN sds.weather_condition = 'snow' THEN sds.surge_multiplier END) AS avg_surge_snow,
        
        -- Temperature impact
        CORR(sds.temperature, sds.surge_multiplier) AS temp_surge_correlation,
        
        -- Precipitation impact
        AVG(CASE WHEN sds.precipitation_probability > 0.5 THEN sds.surge_multiplier END) AS avg_surge_high_precip,
        AVG(CASE WHEN sds.precipitation_probability <= 0.5 THEN sds.surge_multiplier END) AS avg_surge_low_precip
        
    FROM supply_demand_snapshots sds
    WHERE 
        sds.snapshot_time >= CURRENT_DATE - INTERVAL '1 month'
        AND sds.snapshot_time < CURRENT_DATE
        AND sds.weather_condition IS NOT NULL
    GROUP BY sds.zone_id
),

-- CTE 5: Inefficiency Score Calculation
inefficiency_analysis AS (
    SELECT 
        zp.zone_id,
        zp.zone_name,
        zp.city,
        zp.zone_type,
        zp.avg_surge_multiplier,
        zp.completion_rate,
        zp.total_requests,
        zp.completed_trips,
        zp.cancelled_trips,
        zp.total_revenue,
        zp.avg_fare,
        zp.surge_volatility,
        zp.high_surge_events,
        
        -- Supply/demand metrics
        sda.avg_supply_demand_ratio,
        sda.supply_demand_volatility,
        sda.peak_demand,
        sda.min_supply,
        sda.morning_ratio,
        sda.evening_ratio,
        sda.weekend_ratio,
        sda.weekday_ratio,
        
        -- Driver metrics
        dla.driver_availability_rate,
        dla.avg_available_drivers,
        dla.total_drivers,
        dla.avg_response_time_ms,
        dla.p95_response_time_ms,
        dla.unique_cells_covered,
        
        -- Weather metrics
        wi.avg_surge_in_rain,
        wi.avg_surge_clear,
        wi.temp_surge_correlation,
        
        -- Calculate inefficiency score
        -- Higher surge multiplier = more inefficient
        -- Lower completion rate = more inefficient
        -- Higher surge volatility = more inefficient
        -- Lower supply/demand ratio = more inefficient
        (
            -- Surge multiplier component (0-40 points)
            LEAST(40, (zp.avg_surge_multiplier - 1.0) * 20) +
            
            -- Completion rate component (0-30 points, inverted)
            LEAST(30, (100 - zp.completion_rate) * 0.3) +
            
            -- Surge volatility component (0-20 points)
            LEAST(20, zp.surge_volatility * 10) +
            
            -- Supply/demand ratio component (0-10 points, inverted)
            LEAST(10, GREATEST(0, (1.0 - sda.avg_supply_demand_ratio) * 10))
        ) AS inefficiency_score,
        
        -- Additional efficiency metrics
        zp.completion_rate / NULLIF(zp.avg_surge_multiplier, 0) AS efficiency_ratio,
        zp.total_revenue / NULLIF(zp.total_requests, 0) AS revenue_per_request,
        zp.completed_trips / NULLIF(zp.total_requests, 0) AS success_rate
        
    FROM zone_performance zp
    LEFT JOIN supply_demand_analysis sda ON zp.zone_id = sda.zone_id
    LEFT JOIN driver_location_analysis dla ON zp.zone_id = dla.zone_id
    LEFT JOIN weather_impact wi ON zp.zone_id = wi.zone_id
    WHERE 
        zp.completion_rate IS NOT NULL
        AND zp.avg_surge_multiplier IS NOT NULL
        AND zp.total_requests >= 100  -- Minimum data threshold
),

-- CTE 6: Final Ranking and Analysis
final_analysis AS (
    SELECT 
        zone_id,
        zone_name,
        city,
        zone_type,
        avg_surge_multiplier,
        completion_rate,
        inefficiency_score,
        efficiency_ratio,
        total_requests,
        completed_trips,
        cancelled_trips,
        total_revenue,
        avg_fare,
        surge_volatility,
        high_surge_events,
        avg_supply_demand_ratio,
        supply_demand_volatility,
        driver_availability_rate,
        avg_response_time_ms,
        unique_cells_covered,
        
        -- Window functions for ranking
        RANK() OVER (ORDER BY inefficiency_score DESC) AS inefficiency_rank,
        ROW_NUMBER() OVER (ORDER BY inefficiency_score DESC) AS row_number,
        DENSE_RANK() OVER (ORDER BY inefficiency_score DESC) AS dense_rank,
        
        -- Percentile rankings
        PERCENT_RANK() OVER (ORDER BY inefficiency_score DESC) AS inefficiency_percentile,
        CUME_DIST() OVER (ORDER BY inefficiency_score DESC) AS inefficiency_cumulative_dist,
        
        -- Comparative analysis
        LAG(inefficiency_score, 1) OVER (ORDER BY inefficiency_score DESC) AS prev_zone_score,
        LEAD(inefficiency_score, 1) OVER (ORDER BY inefficiency_score DESC) AS next_zone_score,
        
        -- Moving averages for trend analysis
        AVG(inefficiency_score) OVER (
            ORDER BY inefficiency_score DESC 
            ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING
        ) AS moving_avg_inefficiency,
        
        -- Zone type analysis
        RANK() OVER (PARTITION BY zone_type ORDER BY inefficiency_score DESC) AS rank_within_type,
        
        -- City analysis
        RANK() OVER (PARTITION BY city ORDER BY inefficiency_score DESC) AS rank_within_city
        
    FROM inefficiency_analysis
    WHERE inefficiency_score IS NOT NULL
)

-- =============================================================================
-- MAIN QUERY: TOP 5 INEFFICIENT SURGE ZONES
-- =============================================================================

SELECT 
    zone_name,
    city,
    zone_type,
    ROUND(avg_surge_multiplier, 3) AS average_multiplier,
    ROUND(completion_rate, 2) AS completion_rate,
    inefficiency_rank,
    ROUND(inefficiency_score, 2) AS inefficiency_score,
    ROUND(efficiency_ratio, 3) AS efficiency_ratio,
    
    -- Additional operational metrics
    total_requests,
    completed_trips,
    cancelled_trips,
    ROUND(total_revenue, 2) AS total_revenue,
    ROUND(avg_fare, 2) AS avg_fare,
    ROUND(surge_volatility, 3) AS surge_volatility,
    high_surge_events,
    
    -- Supply/demand insights
    ROUND(avg_supply_demand_ratio, 3) AS avg_supply_demand_ratio,
    ROUND(supply_demand_volatility, 3) AS supply_demand_volatility,
    
    -- Driver performance
    ROUND(driver_availability_rate, 3) AS driver_availability_rate,
    ROUND(avg_response_time_ms, 0) AS avg_response_time_ms,
    unique_cells_covered,
    
    -- Ranking context
    rank_within_type,
    rank_within_city,
    ROUND(inefficiency_percentile, 3) AS inefficiency_percentile,
    
    -- Performance indicators
    CASE 
        WHEN completion_rate < 70 THEN 'Critical'
        WHEN completion_rate < 80 THEN 'Poor'
        WHEN completion_rate < 90 THEN 'Fair'
        ELSE 'Good'
    END AS completion_status,
    
    CASE 
        WHEN avg_surge_multiplier > 2.0 THEN 'Very High'
        WHEN avg_surge_multiplier > 1.5 THEN 'High'
        WHEN avg_surge_multiplier > 1.2 THEN 'Medium'
        ELSE 'Low'
    END AS surge_level,
    
    -- Recommendations
    CASE 
        WHEN completion_rate < 70 AND avg_surge_multiplier > 2.0 THEN 'URGENT: High surge + low completion'
        WHEN completion_rate < 80 AND avg_surge_multiplier > 1.5 THEN 'HIGH: Review pricing strategy'
        WHEN surge_volatility > 0.5 THEN 'MEDIUM: High price volatility'
        WHEN driver_availability_rate < 0.7 THEN 'MEDIUM: Low driver availability'
        ELSE 'LOW: Monitor performance'
    END AS recommendation

FROM final_analysis
WHERE inefficiency_rank <= 5
ORDER BY inefficiency_rank;

-- =============================================================================
-- ADDITIONAL ANALYTICAL QUERIES FOR DEEPER INSIGHTS
-- =============================================================================

-- Query 2: Zone Type Analysis
/*
SELECT 
    zone_type,
    COUNT(*) AS total_zones,
    AVG(avg_surge_multiplier) AS avg_surge_multiplier,
    AVG(completion_rate) AS avg_completion_rate,
    AVG(inefficiency_score) AS avg_inefficiency_score,
    COUNT(CASE WHEN inefficiency_rank <= 5 THEN 1 END) AS zones_in_top5_inefficient
FROM final_analysis
GROUP BY zone_type
ORDER BY avg_inefficiency_score DESC;
*/

-- Query 3: City-wise Analysis
/*
SELECT 
    city,
    COUNT(*) AS total_zones,
    AVG(avg_surge_multiplier) AS avg_surge_multiplier,
    AVG(completion_rate) AS avg_completion_rate,
    AVG(inefficiency_score) AS avg_inefficiency_score,
    COUNT(CASE WHEN inefficiency_rank <= 5 THEN 1 END) AS zones_in_top5_inefficient
FROM final_analysis
GROUP BY city
ORDER BY avg_inefficiency_score DESC;
*/

-- Query 4: Time-based Inefficiency Trends
/*
SELECT 
    DATE_TRUNC('week', pel.event_timestamp) AS week,
    sz.zone_name,
    AVG(pel.surge_multiplier) AS avg_surge_multiplier,
    COUNT(CASE WHEN pel.event_status = 'completed' THEN 1 END) * 100.0 / 
    NULLIF(COUNT(CASE WHEN pel.event_status IN ('quoted', 'accepted', 'completed', 'cancelled') THEN 1 END), 0) AS completion_rate
FROM pricing_event_logs pel
JOIN surge_zones sz ON pel.pickup_zone_id = sz.zone_id
WHERE pel.event_timestamp >= CURRENT_DATE - INTERVAL '1 month'
GROUP BY DATE_TRUNC('week', pel.event_timestamp), sz.zone_name
HAVING COUNT(pel.log_id) >= 50
ORDER BY week DESC, completion_rate ASC;
*/

-- =============================================================================
-- PERFORMANCE OPTIMIZATION NOTES
-- =============================================================================

-- Indexes recommended for optimal performance:
-- CREATE INDEX CONCURRENTLY idx_pricing_logs_zone_timestamp ON pricing_event_logs(pickup_zone_id, event_timestamp);
-- CREATE INDEX CONCURRENTLY idx_pricing_logs_status_timestamp ON pricing_event_logs(event_status, event_timestamp);
-- CREATE INDEX CONCURRENTLY idx_supply_demand_zone_timestamp ON supply_demand_snapshots(zone_id, snapshot_time);
-- CREATE INDEX CONCURRENTLY idx_driver_location_zone_timestamp ON driver_location_events(zone_id, timestamp);
-- CREATE INDEX CONCURRENTLY idx_surge_zones_active ON surge_zones(is_active) WHERE is_active = true;

-- Query execution plan optimization:
-- - Use EXPLAIN ANALYZE to identify bottlenecks
-- - Consider partitioning tables by date for better performance
-- - Use materialized views for frequently accessed aggregations
-- - Implement query result caching for dashboard applications

-- Equilibrium Dynamic Pricing Platform Database Schema v2.0
-- PostgreSQL with PostGIS extension for geospatial data
-- Enhanced with advanced indexing, partitioning, and performance optimizations

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Create surge_zones table
CREATE TABLE IF NOT EXISTS surge_zones (
    zone_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_name VARCHAR(255) NOT NULL,
    city_id UUID NOT NULL,
    s2_cell_id BIGINT NOT NULL,
    polygon_geometry GEOMETRY(POLYGON, 4326) NOT NULL,
    base_fare DECIMAL(10,2) NOT NULL,
    max_surge_multiplier DECIMAL(3,2) DEFAULT 5.00,
    min_surge_multiplier DECIMAL(3,2) DEFAULT 1.00,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for surge_zones
CREATE INDEX IF NOT EXISTS idx_s2_cell ON surge_zones (s2_cell_id);
CREATE INDEX IF NOT EXISTS idx_city_active ON surge_zones (city_id, is_active);
CREATE INDEX IF NOT EXISTS idx_geometry ON surge_zones USING GIST (polygon_geometry);

-- Create supply_demand_snapshots table
CREATE TABLE IF NOT EXISTS supply_demand_snapshots (
    snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_id UUID NOT NULL REFERENCES surge_zones(zone_id),
    timestamp TIMESTAMP NOT NULL,
    supply_count INTEGER NOT NULL,
    demand_count INTEGER NOT NULL,
    surge_multiplier DECIMAL(3,2) NOT NULL,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for supply_demand_snapshots
CREATE INDEX IF NOT EXISTS idx_zone_timestamp ON supply_demand_snapshots (zone_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_timestamp ON supply_demand_snapshots (timestamp);

-- Create pricing_event_logs table
CREATE TABLE IF NOT EXISTS pricing_event_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_id UUID NOT NULL REFERENCES surge_zones(zone_id),
    driver_id VARCHAR(255),
    rider_id VARCHAR(255),
    event_type VARCHAR(50) NOT NULL, -- 'price_quote', 'ride_completed', 'ride_cancelled'
    base_fare DECIMAL(10,2) NOT NULL,
    surge_multiplier DECIMAL(3,2) NOT NULL,
    final_fare DECIMAL(10,2) NOT NULL,
    quote_timestamp TIMESTAMP NOT NULL,
    completion_timestamp TIMESTAMP,
    trip_duration INTEGER, -- seconds
    trip_distance DECIMAL(8,2), -- kilometers
    cancellation_reason VARCHAR(100),
    ml_model_version VARCHAR(50),
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for pricing_event_logs
CREATE INDEX IF NOT EXISTS idx_zone_timestamp ON pricing_event_logs (zone_id, quote_timestamp);
CREATE INDEX IF NOT EXISTS idx_event_type ON pricing_event_logs (event_type, quote_timestamp);
CREATE INDEX IF NOT EXISTS idx_completion ON pricing_event_logs (completion_timestamp);

-- Create cities table
CREATE TABLE IF NOT EXISTS cities (
    city_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    city_name VARCHAR(255) NOT NULL,
    country VARCHAR(100) NOT NULL,
    timezone VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert demo cities
INSERT INTO cities (city_id, city_name, country, timezone) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'San Francisco', 'USA', 'America/Los_Angeles')
ON CONFLICT (city_id) DO NOTHING;

-- Insert demo surge zones
INSERT INTO surge_zones (zone_id, zone_name, city_id, s2_cell_id, polygon_geometry, base_fare, max_surge_multiplier, min_surge_multiplier) VALUES
('downtown_financial', 'Downtown Financial District', '550e8400-e29b-41d4-a716-446655440000', 1234567890, 
 ST_GeomFromText('POLYGON((-122.4194 37.7749, -122.4094 37.7749, -122.4094 37.7849, -122.4194 37.7849, -122.4194 37.7749))', 4326),
 12.50, 3.00, 1.00),
('stadium_area', 'Stadium Area', '550e8400-e29b-41d4-a716-446655440000', 1234567891,
 ST_GeomFromText('POLYGON((-122.3893 37.7786, -122.3793 37.7786, -122.3793 37.7886, -122.3893 37.7886, -122.3893 37.7786))', 4326),
 15.00, 5.00, 1.00),
('airport', 'San Francisco Airport', '550e8400-e29b-41d4-a716-446655440000', 1234567892,
 ST_GeomFromText('POLYGON((-122.3790 37.6213, -122.3690 37.6213, -122.3690 37.6313, -122.3790 37.6313, -122.3790 37.6213))', 4326),
 25.00, 2.50, 1.00)
ON CONFLICT (zone_id) DO NOTHING;

-- Create a function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_surge_zones_updated_at BEFORE UPDATE ON surge_zones FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create a view for current zone status
CREATE OR REPLACE VIEW current_zone_status AS
SELECT 
    sz.zone_id,
    sz.zone_name,
    sz.city_id,
    sz.base_fare,
    sz.max_surge_multiplier,
    sz.min_surge_multiplier,
    sz.is_active,
    COALESCE(sds.supply_count, 0) as current_supply,
    COALESCE(sds.demand_count, 0) as current_demand,
    COALESCE(sds.surge_multiplier, 1.0) as current_multiplier,
    sds.timestamp as last_updated
FROM surge_zones sz
LEFT JOIN LATERAL (
    SELECT supply_count, demand_count, surge_multiplier, timestamp
    FROM supply_demand_snapshots
    WHERE zone_id = sz.zone_id
    ORDER BY timestamp DESC
    LIMIT 1
) sds ON true
WHERE sz.is_active = true;

-- Create users table for authentication
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for users
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users (is_active);

-- Create user_sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for user_sessions
CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions (token_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions (expires_at);

-- Create triggers for users table
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert demo users
INSERT INTO users (email, hashed_password, full_name, role) VALUES
('admin@equilibrium.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Admin User', 'admin'),
('driver@equilibrium.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Driver User', 'driver'),
('user@equilibrium.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Regular User', 'user')
ON CONFLICT (email) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO equilibrium;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO equilibrium;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO equilibrium;

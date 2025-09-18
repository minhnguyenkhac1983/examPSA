// MongoDB Initialization Script for Equilibrium Platform

// Create database
db = db.getSiblingDB('equilibrium');

// Create collections
db.createCollection('driver_locations');
db.createCollection('pricing_events');
db.createCollection('supply_demand_events');
db.createCollection('analytics_metrics');
db.createCollection('system_logs');

// Create indexes for driver_locations
db.driver_locations.createIndex({ "driver_id": 1 });
db.driver_locations.createIndex({ "location": "2dsphere" });
db.driver_locations.createIndex({ "timestamp": 1 });
db.driver_locations.createIndex({ "zone_id": 1 });

// Create indexes for pricing_events
db.pricing_events.createIndex({ "rider_id": 1 });
db.pricing_events.createIndex({ "zone_id": 1 });
db.pricing_events.createIndex({ "timestamp": 1 });
db.pricing_events.createIndex({ "event_type": 1 });

// Create indexes for supply_demand_events
db.supply_demand_events.createIndex({ "zone_id": 1 });
db.supply_demand_events.createIndex({ "timestamp": 1 });
db.supply_demand_events.createIndex({ "surge_multiplier": 1 });

// Create indexes for analytics_metrics
db.analytics_metrics.createIndex({ "metric_type": 1 });
db.analytics_metrics.createIndex({ "timestamp": 1 });
db.analytics_metrics.createIndex({ "zone_id": 1 });

// Create indexes for system_logs
db.system_logs.createIndex({ "service": 1 });
db.system_logs.createIndex({ "level": 1 });
db.system_logs.createIndex({ "timestamp": 1 });

// Insert sample data
db.driver_locations.insertMany([
  {
    driver_id: "driver_001",
    location: {
      type: "Point",
      coordinates: [-122.4194, 37.7749]
    },
    zone_id: "downtown_financial",
    status: "available",
    timestamp: new Date(),
    vehicle_type: "standard"
  },
  {
    driver_id: "driver_002",
    location: {
      type: "Point",
      coordinates: [-122.3893, 37.7786]
    },
    zone_id: "stadium_area",
    status: "busy",
    timestamp: new Date(),
    vehicle_type: "premium"
  }
]);

db.pricing_events.insertMany([
  {
    rider_id: "rider_001",
    zone_id: "downtown_financial",
    event_type: "price_quote",
    base_fare: 12.50,
    surge_multiplier: 1.2,
    final_fare: 15.00,
    timestamp: new Date(),
    confidence_score: 0.95
  },
  {
    rider_id: "rider_002",
    zone_id: "stadium_area",
    event_type: "ride_completed",
    base_fare: 15.00,
    surge_multiplier: 2.0,
    final_fare: 30.00,
    timestamp: new Date(),
    confidence_score: 0.88
  }
]);

db.supply_demand_events.insertMany([
  {
    zone_id: "downtown_financial",
    supply: 25,
    demand: 30,
    surge_multiplier: 1.2,
    timestamp: new Date()
  },
  {
    zone_id: "stadium_area",
    supply: 10,
    demand: 35,
    surge_multiplier: 2.0,
    timestamp: new Date()
  }
]);

// Create user for application
db.createUser({
  user: "equilibrium_user",
  pwd: "equilibrium_secure_password",
  roles: [
    {
      role: "readWrite",
      db: "equilibrium"
    }
  ]
});

print("MongoDB initialization completed successfully!");

"""
Equilibrium Analytics Service
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional

app = FastAPI(title="Equilibrium Analytics Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class AnalyticsRequest(BaseModel):
    metric_type: str
    time_range: str = "24h"  # 1h, 24h, 7d, 30d
    filters: Optional[Dict] = None

class AnalyticsResponse(BaseModel):
    metric_type: str
    time_range: str
    data: List[Dict]
    summary: Dict
    generated_at: str

# Mock analytics data generator
class AnalyticsGenerator:
    def __init__(self):
        self.metrics = {
            "pricing_trends": self._generate_pricing_trends,
            "demand_patterns": self._generate_demand_patterns,
            "revenue_analytics": self._generate_revenue_analytics,
            "user_behavior": self._generate_user_behavior,
            "driver_performance": self._generate_driver_performance,
            "geographic_insights": self._generate_geographic_insights
        }
    
    def generate_analytics(self, metric_type: str, time_range: str) -> Dict:
        """Generate analytics data for specified metric and time range"""
        if metric_type not in self.metrics:
            raise ValueError(f"Unknown metric type: {metric_type}")
        
        generator = self.metrics[metric_type]
        data = generator(time_range)
        
        return {
            "metric_type": metric_type,
            "time_range": time_range,
            "data": data["data"],
            "summary": data["summary"],
            "generated_at": datetime.now().isoformat()
        }
    
    def _generate_pricing_trends(self, time_range: str) -> Dict:
        """Generate pricing trends data"""
        hours = self._get_hours_for_range(time_range)
        data = []
        
        for i in range(hours):
            timestamp = datetime.now() - timedelta(hours=i)
            base_price = 15.0 + random.uniform(-3, 3)
            surge_multiplier = 1.0 + random.uniform(0, 1.5)
            final_price = base_price * surge_multiplier
            
            data.append({
                "timestamp": timestamp.isoformat(),
                "base_price": round(base_price, 2),
                "surge_multiplier": round(surge_multiplier, 2),
                "final_price": round(final_price, 2),
                "demand_level": random.choice(["low", "medium", "high", "very_high"])
            })
        
        summary = {
            "avg_base_price": round(sum(d["base_price"] for d in data) / len(data), 2),
            "avg_surge_multiplier": round(sum(d["surge_multiplier"] for d in data) / len(data), 2),
            "max_surge": round(max(d["surge_multiplier"] for d in data), 2),
            "total_data_points": len(data)
        }
        
        return {"data": data, "summary": summary}
    
    def _generate_demand_patterns(self, time_range: str) -> Dict:
        """Generate demand patterns data"""
        hours = self._get_hours_for_range(time_range)
        data = []
        
        for i in range(hours):
            timestamp = datetime.now() - timedelta(hours=i)
            hour = timestamp.hour
            
            # Simulate demand patterns based on time of day
            if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
                base_demand = random.uniform(80, 100)
            elif 22 <= hour or hour <= 6:  # Night time
                base_demand = random.uniform(20, 40)
            else:  # Regular hours
                base_demand = random.uniform(40, 80)
            
            data.append({
                "timestamp": timestamp.isoformat(),
                "demand_level": base_demand,
                "supply_level": random.uniform(30, 90),
                "surge_multiplier": 1.0 + (base_demand - 50) / 100,
                "zone": random.choice(["downtown", "airport", "suburbs", "university"])
            })
        
        summary = {
            "avg_demand": round(sum(d["demand_level"] for d in data) / len(data), 2),
            "avg_supply": round(sum(d["supply_level"] for d in data) / len(data), 2),
            "peak_demand": round(max(d["demand_level"] for d in data), 2),
            "total_data_points": len(data)
        }
        
        return {"data": data, "summary": summary}
    
    def _generate_revenue_analytics(self, time_range: str) -> Dict:
        """Generate revenue analytics data"""
        hours = self._get_hours_for_range(time_range)
        data = []
        
        for i in range(hours):
            timestamp = datetime.now() - timedelta(hours=i)
            rides = random.randint(50, 200)
            avg_fare = random.uniform(12, 25)
            revenue = rides * avg_fare
            
            data.append({
                "timestamp": timestamp.isoformat(),
                "total_rides": rides,
                "avg_fare": round(avg_fare, 2),
                "total_revenue": round(revenue, 2),
                "commission_rate": 0.15,
                "net_revenue": round(revenue * 0.15, 2)
            })
        
        total_revenue = sum(d["total_revenue"] for d in data)
        total_rides = sum(d["total_rides"] for d in data)
        
        summary = {
            "total_revenue": round(total_revenue, 2),
            "total_rides": total_rides,
            "avg_fare": round(total_revenue / total_rides, 2) if total_rides > 0 else 0,
            "total_commission": round(total_revenue * 0.15, 2),
            "total_data_points": len(data)
        }
        
        return {"data": data, "summary": summary}
    
    def _generate_user_behavior(self, time_range: str) -> Dict:
        """Generate user behavior analytics"""
        hours = self._get_hours_for_range(time_range)
        data = []
        
        for i in range(hours):
            timestamp = datetime.now() - timedelta(hours=i)
            
            data.append({
                "timestamp": timestamp.isoformat(),
                "active_users": random.randint(100, 500),
                "new_registrations": random.randint(5, 25),
                "ride_requests": random.randint(80, 300),
                "completed_rides": random.randint(70, 280),
                "cancellation_rate": round(random.uniform(0.05, 0.15), 3),
                "avg_session_duration": random.randint(300, 1800)  # seconds
            })
        
        total_users = sum(d["active_users"] for d in data)
        total_rides = sum(d["ride_requests"] for d in data)
        total_completed = sum(d["completed_rides"] for d in data)
        
        summary = {
            "avg_active_users": round(total_users / len(data), 2),
            "total_ride_requests": total_rides,
            "completion_rate": round(total_completed / total_rides, 3) if total_rides > 0 else 0,
            "avg_cancellation_rate": round(sum(d["cancellation_rate"] for d in data) / len(data), 3),
            "total_data_points": len(data)
        }
        
        return {"data": data, "summary": summary}
    
    def _generate_driver_performance(self, time_range: str) -> Dict:
        """Generate driver performance analytics"""
        hours = self._get_hours_for_range(time_range)
        data = []
        
        for i in range(hours):
            timestamp = datetime.now() - timedelta(hours=i)
            
            data.append({
                "timestamp": timestamp.isoformat(),
                "active_drivers": random.randint(50, 150),
                "avg_rating": round(random.uniform(4.2, 4.8), 2),
                "avg_earnings_per_hour": round(random.uniform(15, 35), 2),
                "acceptance_rate": round(random.uniform(0.85, 0.95), 3),
                "completion_rate": round(random.uniform(0.90, 0.98), 3),
                "avg_response_time": random.randint(30, 120)  # seconds
            })
        
        summary = {
            "avg_active_drivers": round(sum(d["active_drivers"] for d in data) / len(data), 2),
            "avg_rating": round(sum(d["avg_rating"] for d in data) / len(data), 2),
            "avg_earnings": round(sum(d["avg_earnings_per_hour"] for d in data) / len(data), 2),
            "avg_acceptance_rate": round(sum(d["acceptance_rate"] for d in data) / len(data), 3),
            "total_data_points": len(data)
        }
        
        return {"data": data, "summary": summary}
    
    def _generate_geographic_insights(self, time_range: str) -> Dict:
        """Generate geographic insights data"""
        zones = ["downtown", "airport", "suburbs", "university", "business_district", "residential"]
        data = []
        
        for zone in zones:
            data.append({
                "zone": zone,
                "total_rides": random.randint(100, 500),
                "avg_fare": round(random.uniform(10, 30), 2),
                "demand_score": random.uniform(0.3, 1.0),
                "supply_score": random.uniform(0.4, 1.0),
                "surge_frequency": round(random.uniform(0.1, 0.4), 3),
                "popularity_rank": random.randint(1, len(zones))
            })
        
        # Sort by popularity
        data.sort(key=lambda x: x["popularity_rank"])
        
        summary = {
            "total_zones": len(zones),
            "most_popular_zone": data[0]["zone"],
            "highest_avg_fare": max(data, key=lambda x: x["avg_fare"])["zone"],
            "highest_demand": max(data, key=lambda x: x["demand_score"])["zone"],
            "total_data_points": len(data)
        }
        
        return {"data": data, "summary": summary}
    
    def _get_hours_for_range(self, time_range: str) -> int:
        """Get number of hours for time range"""
        range_map = {
            "1h": 1,
            "24h": 24,
            "7d": 168,  # 7 * 24
            "30d": 720   # 30 * 24
        }
        return range_map.get(time_range, 24)

# Initialize analytics generator
analytics_generator = AnalyticsGenerator()

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "analytics-service",
        "version": "1.0.0",
        "available_metrics": list(analytics_generator.metrics.keys())
    }

@app.post("/api/v1/analytics/generate", response_model=AnalyticsResponse)
async def generate_analytics(request: AnalyticsRequest):
    """Generate analytics data"""
    try:
        result = analytics_generator.generate_analytics(
            request.metric_type, 
            request.time_range
        )
        return AnalyticsResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics generation error: {str(e)}")

@app.get("/api/v1/analytics/metrics")
async def get_available_metrics():
    """Get available analytics metrics"""
    return {
        "available_metrics": list(analytics_generator.metrics.keys()),
        "supported_time_ranges": ["1h", "24h", "7d", "30d"],
        "metric_descriptions": {
            "pricing_trends": "Historical pricing data and surge patterns",
            "demand_patterns": "Demand and supply patterns over time",
            "revenue_analytics": "Revenue and financial metrics",
            "user_behavior": "User activity and engagement metrics",
            "driver_performance": "Driver performance and earnings data",
            "geographic_insights": "Location-based analytics and insights"
        }
    }

@app.get("/api/v1/analytics/dashboard")
async def get_dashboard_data():
    """Get comprehensive dashboard data"""
    dashboard_data = {}
    
    for metric_type in analytics_generator.metrics.keys():
        try:
            result = analytics_generator.generate_analytics(metric_type, "24h")
            dashboard_data[metric_type] = {
                "summary": result["summary"],
                "latest_data": result["data"][:5] if result["data"] else []
            }
        except Exception as e:
            dashboard_data[metric_type] = {"error": str(e)}
    
    return {
        "dashboard_data": dashboard_data,
        "generated_at": datetime.now().isoformat(),
        "time_range": "24h"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8009)

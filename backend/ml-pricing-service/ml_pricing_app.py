"""
Equilibrium ML-based Pricing Service
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
from enum import Enum
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import uvicorn
import json
import random
import asyncio
import time
import uuid
import logging
from dataclasses import dataclass
import redis.asyncio as redis
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import warnings
warnings.filterwarnings('ignore')

app = FastAPI(title="Equilibrium ML Pricing Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class PricingRequest(BaseModel):
    pickup_location: Dict[str, float]
    dropoff_location: Dict[str, float]
    vehicle_type: str = "standard"
    time_of_day: Optional[str] = None
    day_of_week: Optional[str] = None
    weather_condition: Optional[str] = None
    traffic_level: Optional[str] = None
    demand_level: Optional[str] = None
    supply_level: Optional[str] = None

class PricingResponse(BaseModel):
    base_fare: float
    distance_fare: float
    time_multiplier: float
    demand_multiplier: float
    weather_multiplier: float
    traffic_multiplier: float
    ml_prediction: float
    confidence_score: float
    final_fare: float
    breakdown: Dict[str, float]
    prediction_model: str
    timestamp: str

class MLModel:
    def __init__(self):
        self.model_name = "Equilibrium ML Pricing v1.0"
        self.feature_weights = {
            'distance': 0.25,
            'time_of_day': 0.20,
            'demand_level': 0.20,
            'weather': 0.15,
            'traffic': 0.10,
            'day_of_week': 0.10
        }
        self.base_fare = 8.50
        self.distance_rate = 2.5
        
    def predict_price(self, request: PricingRequest) -> Dict:
        """ML-based price prediction"""
        
        # Calculate distance
        distance = self._calculate_distance(
            request.pickup_location,
            request.dropoff_location
        )
        
        # Extract features
        features = self._extract_features(request, distance)
        
        # Apply ML model (simplified neural network simulation)
        prediction = self._neural_network_prediction(features)
        
        # Calculate multipliers
        time_multiplier = self._get_time_multiplier(request.time_of_day)
        demand_multiplier = self._get_demand_multiplier(request.demand_level)
        weather_multiplier = self._get_weather_multiplier(request.weather_condition)
        traffic_multiplier = self._get_traffic_multiplier(request.traffic_level)
        
        # Calculate final fare
        base_fare = self.base_fare
        distance_fare = distance * self.distance_rate
        
        ml_prediction = prediction * (base_fare + distance_fare)
        final_fare = ml_prediction * time_multiplier * demand_multiplier * weather_multiplier * traffic_multiplier
        
        # Calculate confidence score
        confidence = self._calculate_confidence(features)
        
        return {
            'base_fare': base_fare,
            'distance_fare': round(distance_fare, 2),
            'time_multiplier': round(time_multiplier, 2),
            'demand_multiplier': round(demand_multiplier, 2),
            'weather_multiplier': round(weather_multiplier, 2),
            'traffic_multiplier': round(traffic_multiplier, 2),
            'ml_prediction': round(ml_prediction, 2),
            'confidence_score': round(confidence, 2),
            'final_fare': round(final_fare, 2),
            'breakdown': {
                'base_fare': base_fare,
                'distance_fare': round(distance_fare, 2),
                'time_adjustment': round((time_multiplier - 1) * 100, 1),
                'demand_adjustment': round((demand_multiplier - 1) * 100, 1),
                'weather_adjustment': round((weather_multiplier - 1) * 100, 1),
                'traffic_adjustment': round((traffic_multiplier - 1) * 100, 1),
                'ml_adjustment': round((ml_prediction / (base_fare + distance_fare) - 1) * 100, 1)
            },
            'prediction_model': self.model_name,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_distance(self, pickup: Dict, dropoff: Dict) -> float:
        """Calculate distance between two points"""
        lat1, lon1 = pickup['latitude'], pickup['longitude']
        lat2, lon2 = dropoff['latitude'], dropoff['longitude']
        
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        
        a = (np.sin(dlat/2) * np.sin(dlat/2) + 
             np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * 
             np.sin(dlon/2) * np.sin(dlon/2))
        
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def _extract_features(self, request: PricingRequest, distance: float) -> Dict:
        """Extract features for ML model"""
        return {
            'distance': distance,
            'time_of_day': self._encode_time_of_day(request.time_of_day),
            'day_of_week': self._encode_day_of_week(request.day_of_week),
            'weather': self._encode_weather(request.weather_condition),
            'traffic': self._encode_traffic(request.traffic_level),
            'demand': self._encode_demand(request.demand_level),
            'supply': self._encode_supply(request.supply_level)
        }
    
    def _neural_network_prediction(self, features: Dict) -> float:
        """Simplified neural network prediction"""
        # Simulate neural network with weighted features
        weights = np.array([0.3, 0.2, 0.15, 0.15, 0.1, 0.05, 0.05])
        inputs = np.array([
            features['distance'] / 10,  # Normalize distance
            features['time_of_day'],
            features['day_of_week'],
            features['weather'],
            features['traffic'],
            features['demand'],
            features['supply']
        ])
        
        # Simple linear combination with activation
        output = np.dot(weights, inputs)
        activation = 1 / (1 + np.exp(-output))  # Sigmoid activation
        
        return 0.8 + (activation * 0.4)  # Scale to reasonable range
    
    def _calculate_confidence(self, features: Dict) -> float:
        """Calculate prediction confidence"""
        # Higher confidence for more complete data
        completeness = sum(1 for v in features.values() if v is not None) / len(features)
        base_confidence = 0.7 + (completeness * 0.3)
        
        # Add some randomness to simulate real ML uncertainty
        noise = random.uniform(-0.05, 0.05)
        return max(0.5, min(0.95, base_confidence + noise))
    
    def _encode_time_of_day(self, time_of_day: Optional[str]) -> float:
        """Encode time of day as numerical feature"""
        if not time_of_day:
            return 0.5  # Default neutral value
        
        time_encoding = {
            'early_morning': 0.3,  # 5-8 AM
            'morning': 0.4,        # 8-12 PM
            'afternoon': 0.6,      # 12-5 PM
            'evening': 0.8,        # 5-9 PM
            'night': 0.2,          # 9 PM-5 AM
            'rush_hour': 0.9       # Peak hours
        }
        return time_encoding.get(time_of_day, 0.5)
    
    def _encode_day_of_week(self, day_of_week: Optional[str]) -> float:
        """Encode day of week as numerical feature"""
        if not day_of_week:
            return 0.5
        
        day_encoding = {
            'monday': 0.7,
            'tuesday': 0.6,
            'wednesday': 0.6,
            'thursday': 0.7,
            'friday': 0.8,
            'saturday': 0.4,
            'sunday': 0.3
        }
        return day_encoding.get(day_of_week.lower(), 0.5)
    
    def _encode_weather(self, weather: Optional[str]) -> float:
        """Encode weather condition as numerical feature"""
        if not weather:
            return 1.0  # Default neutral
        
        weather_encoding = {
            'sunny': 1.0,
            'cloudy': 1.1,
            'rainy': 1.3,
            'stormy': 1.5,
            'snowy': 1.4,
            'foggy': 1.2
        }
        return weather_encoding.get(weather.lower(), 1.0)
    
    def _encode_traffic(self, traffic: Optional[str]) -> float:
        """Encode traffic level as numerical feature"""
        if not traffic:
            return 1.0
        
        traffic_encoding = {
            'light': 0.9,
            'moderate': 1.0,
            'heavy': 1.2,
            'severe': 1.4
        }
        return traffic_encoding.get(traffic.lower(), 1.0)
    
    def _encode_demand(self, demand: Optional[str]) -> float:
        """Encode demand level as numerical feature"""
        if not demand:
            return 1.0
        
        demand_encoding = {
            'low': 0.8,
            'medium': 1.0,
            'high': 1.3,
            'very_high': 1.6
        }
        return demand_encoding.get(demand.lower(), 1.0)
    
    def _encode_supply(self, supply: Optional[str]) -> float:
        """Encode supply level as numerical feature"""
        if not supply:
            return 1.0
        
        supply_encoding = {
            'low': 1.2,
            'medium': 1.0,
            'high': 0.9,
            'very_high': 0.8
        }
        return supply_encoding.get(supply.lower(), 1.0)
    
    def _get_time_multiplier(self, time_of_day: Optional[str]) -> float:
        """Get time-based pricing multiplier"""
        if not time_of_day:
            return 1.0
        
        time_multipliers = {
            'early_morning': 0.9,
            'morning': 1.1,
            'afternoon': 1.0,
            'evening': 1.2,
            'night': 1.3,
            'rush_hour': 1.4
        }
        return time_multipliers.get(time_of_day, 1.0)
    
    def _get_demand_multiplier(self, demand: Optional[str]) -> float:
        """Get demand-based pricing multiplier"""
        if not demand:
            return 1.0
        
        demand_multipliers = {
            'low': 0.8,
            'medium': 1.0,
            'high': 1.3,
            'very_high': 1.6
        }
        return demand_multipliers.get(demand, 1.0)
    
    def _get_weather_multiplier(self, weather: Optional[str]) -> float:
        """Get weather-based pricing multiplier"""
        if not weather:
            return 1.0
        
        weather_multipliers = {
            'sunny': 1.0,
            'cloudy': 1.05,
            'rainy': 1.2,
            'stormy': 1.4,
            'snowy': 1.3,
            'foggy': 1.1
        }
        return weather_multipliers.get(weather, 1.0)
    
    def _get_traffic_multiplier(self, traffic: Optional[str]) -> float:
        """Get traffic-based pricing multiplier"""
        if not traffic:
            return 1.0
        
        traffic_multipliers = {
            'light': 0.95,
            'moderate': 1.0,
            'heavy': 1.15,
            'severe': 1.3
        }
        return traffic_multipliers.get(traffic, 1.0)

# Initialize ML model
ml_model = MLModel()

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ml-pricing-service",
        "version": "1.0.0",
        "model_name": ml_model.model_name,
        "features": list(ml_model.feature_weights.keys())
    }

@app.post("/api/v1/ml-pricing/predict", response_model=PricingResponse)
async def predict_price(request: PricingRequest):
    """ML-based price prediction"""
    try:
        prediction = ml_model.predict_price(request)
        return PricingResponse(**prediction)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.get("/api/v1/ml-pricing/model-info")
async def get_model_info():
    """Get ML model information"""
    return {
        "model_name": ml_model.model_name,
        "feature_weights": ml_model.feature_weights,
        "base_fare": ml_model.base_fare,
        "distance_rate": ml_model.distance_rate,
        "supported_features": [
            "distance", "time_of_day", "day_of_week", 
            "weather_condition", "traffic_level", 
            "demand_level", "supply_level"
        ]
    }

@app.post("/api/v1/ml-pricing/batch-predict")
async def batch_predict(predictions: List[PricingRequest]):
    """Batch price prediction"""
    results = []
    for request in predictions:
        try:
            prediction = ml_model.predict_price(request)
            results.append(prediction)
        except Exception as e:
            results.append({"error": str(e)})
    
    return {"predictions": results, "total": len(results)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8007)

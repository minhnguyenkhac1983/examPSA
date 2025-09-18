#!/usr/bin/env python3
"""
Equilibrium Platform - API Gateway
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

import aiohttp
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
import uvicorn
import redis.asyncio as redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
redis_client: Optional[redis.Redis] = None

# Pydantic Models
class ServiceHealth(BaseModel):
    service: str
    status: str
    response_time: float
    last_check: datetime

class GatewayStats(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    services: List[ServiceHealth]

# Service configuration
SERVICES = {
    "pricing": {
        "url": "http://pricing-service:8001",
        "health_endpoint": "/health",
        "timeout": 5
    },
    "analytics": {
        "url": "http://analytics-service:8002",
        "health_endpoint": "/health",
        "timeout": 5
    },
    "geospatial": {
        "url": "http://geospatial-service:8003",
        "health_endpoint": "/health",
        "timeout": 5
    },
    "stream-processor": {
        "url": "http://stream-processor:8004",
        "health_endpoint": "/health",
        "timeout": 5
    },
    "websocket": {
        "url": "http://websocket-service:8005",
        "health_endpoint": "/health",
        "timeout": 5
    },
    "auth": {
        "url": "http://auth-service:8006",
        "health_endpoint": "/health",
        "timeout": 5
    },
    "ml-pricing": {
        "url": "http://ml-pricing-service:8007",
        "health_endpoint": "/health",
        "timeout": 5
    },
    "notification": {
        "url": "http://notification-service:8008",
        "health_endpoint": "/health",
        "timeout": 5
    },
    "i18n": {
        "url": "http://i18n-service:8009",
        "health_endpoint": "/health",
        "timeout": 5
    },
    "failure-handler": {
        "url": "http://failure-handler-service:8010",
        "health_endpoint": "/health",
        "timeout": 10
    }
}

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Equilibrium API Gateway...")
    
    # Initialize Redis connection
    global redis_client
    redis_url = os.getenv("REDIS_URL", "redis://:equilibrium_secure_password@redis:6379/0")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    
    logger.info("✅ API Gateway started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down API Gateway...")
    if redis_client:
        await redis_client.close()

# Create FastAPI app
app = FastAPI(
    title="Equilibrium API Gateway",
    description="API Gateway for Equilibrium Dynamic Pricing Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Rate limiting with fallback
async def check_rate_limit(request: Request) -> bool:
    """Check rate limit for client with fallback"""
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"
    
    try:
        if redis_client:
            current_requests = await redis_client.get(key)
            if current_requests and int(current_requests) > 100:  # 100 requests per minute
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            # Increment counter
            await redis_client.incr(key)
            await redis_client.expire(key, 60)  # 1 minute window
    except Exception as e:
        # Redis unavailable - allow request but log warning
        logger.warning(f"Rate limiting unavailable, allowing request: {e}")
    
    return True

# Health check for services
async def check_service_health(service_name: str, service_config: Dict) -> ServiceHealth:
    """Check health of a specific service"""
    start_time = datetime.now()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{service_config['url']}{service_config['health_endpoint']}",
                timeout=aiohttp.ClientTimeout(total=service_config['timeout'])
            ) as response:
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                return ServiceHealth(
                    service=service_name,
                    status="healthy" if response.status == 200 else "unhealthy",
                    response_time=response_time,
                    last_check=end_time
                )
    except Exception as e:
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        return ServiceHealth(
            service=service_name,
            status="error",
            response_time=response_time,
            last_check=end_time
        )

# API Endpoints
@app.get("/health")
async def health_check():
    """Gateway health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "service": "api-gateway"
    }

@app.get("/gateway/health", response_model=GatewayStats)
async def gateway_health():
    """Comprehensive gateway health check with fallback"""
    # Check all services
    service_healths = []
    for service_name, service_config in SERVICES.items():
        try:
            health = await check_service_health(service_name, service_config)
            service_healths.append(health)
        except Exception as e:
            # Service check failed - add unhealthy status
            service_healths.append(ServiceHealth(
                service=service_name,
                status="error",
                response_time=999.0,
                last_check=datetime.now()
            ))
    
    # Get gateway stats from Redis with fallback
    total_requests = 0
    successful_requests = 0
    failed_requests = 0
    total_response_time = 0
    
    try:
        if redis_client:
            total_requests = int(await redis_client.get("gateway:total_requests") or 0)
            successful_requests = int(await redis_client.get("gateway:successful_requests") or 0)
            failed_requests = int(await redis_client.get("gateway:failed_requests") or 0)
            total_response_time = float(await redis_client.get("gateway:total_response_time") or 0)
    except Exception as e:
        logger.warning(f"Could not fetch gateway stats from Redis: {e}")
        # Use default values when Redis is unavailable
    
    average_response_time = total_response_time / total_requests if total_requests > 0 else 0
    
    return GatewayStats(
        total_requests=total_requests,
        successful_requests=successful_requests,
        failed_requests=failed_requests,
        average_response_time=average_response_time,
        services=service_healths
    )

@app.get("/gateway/services")
async def list_services():
    """List all available services"""
    return {
        "services": list(SERVICES.keys()),
        "count": len(SERVICES),
        "timestamp": datetime.now().isoformat()
    }

# Proxy endpoints
@app.api_route("/pricing/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_pricing(request: Request, path: str):
    """Proxy requests to pricing service"""
    await check_rate_limit(request)
    
    service_url = SERVICES["pricing"]["url"]
    target_url = f"{service_url}/{path}"
    
    # Forward request
    async with aiohttp.ClientSession() as session:
        # Get request body
        body = await request.body()
        
        # Forward request
        async with session.request(
            method=request.method,
            url=target_url,
            headers=dict(request.headers),
            data=body,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            # Update stats
            if redis_client:
                await redis_client.incr("gateway:total_requests")
                if response.status < 400:
                    await redis_client.incr("gateway:successful_requests")
                else:
                    await redis_client.incr("gateway:failed_requests")
            
            # Return response
            content = await response.read()
            return Response(
                content=content,
                status_code=response.status,
                headers=dict(response.headers)
            )

@app.api_route("/analytics/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_analytics(request: Request, path: str):
    """Proxy requests to analytics service"""
    await check_rate_limit(request)
    
    service_url = SERVICES["analytics"]["url"]
    target_url = f"{service_url}/{path}"
    
    # Forward request
    async with aiohttp.ClientSession() as session:
        body = await request.body()
        
        async with session.request(
            method=request.method,
            url=target_url,
            headers=dict(request.headers),
            data=body,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            # Update stats
            if redis_client:
                await redis_client.incr("gateway:total_requests")
                if response.status < 400:
                    await redis_client.incr("gateway:successful_requests")
                else:
                    await redis_client.incr("gateway:failed_requests")
            
            content = await response.read()
            return Response(
                content=content,
                status_code=response.status,
                headers=dict(response.headers)
            )

@app.api_route("/geospatial/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_geospatial(request: Request, path: str):
    """Proxy requests to geospatial service"""
    await check_rate_limit(request)
    
    service_url = SERVICES["geospatial"]["url"]
    target_url = f"{service_url}/{path}"
    
    # Forward request
    async with aiohttp.ClientSession() as session:
        body = await request.body()
        
        async with session.request(
            method=request.method,
            url=target_url,
            headers=dict(request.headers),
            data=body,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            # Update stats
            if redis_client:
                await redis_client.incr("gateway:total_requests")
                if response.status < 400:
                    await redis_client.incr("gateway:successful_requests")
                else:
                    await redis_client.incr("gateway:failed_requests")
            
            content = await response.read()
            return Response(
                content=content,
                status_code=response.status,
                headers=dict(response.headers)
            )

@app.api_route("/stream/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_stream_processor(request: Request, path: str):
    """Proxy requests to stream processor service"""
    await check_rate_limit(request)
    
    service_url = SERVICES["stream-processor"]["url"]
    target_url = f"{service_url}/{path}"
    
    async with aiohttp.ClientSession() as session:
        body = await request.body()
        
        async with session.request(
            method=request.method,
            url=target_url,
            headers=dict(request.headers),
            data=body,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if redis_client:
                await redis_client.incr("gateway:total_requests")
                if response.status < 400:
                    await redis_client.incr("gateway:successful_requests")
                else:
                    await redis_client.incr("gateway:failed_requests")
            
            content = await response.read()
            return Response(
                content=content,
                status_code=response.status,
                headers=dict(response.headers)
            )

@app.api_route("/websocket/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_websocket(request: Request, path: str):
    """Proxy requests to websocket service"""
    await check_rate_limit(request)
    
    service_url = SERVICES["websocket"]["url"]
    target_url = f"{service_url}/{path}"
    
    async with aiohttp.ClientSession() as session:
        body = await request.body()
        
        async with session.request(
            method=request.method,
            url=target_url,
            headers=dict(request.headers),
            data=body,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if redis_client:
                await redis_client.incr("gateway:total_requests")
                if response.status < 400:
                    await redis_client.incr("gateway:successful_requests")
                else:
                    await redis_client.incr("gateway:failed_requests")
            
            content = await response.read()
            return Response(
                content=content,
                status_code=response.status,
                headers=dict(response.headers)
            )

@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_auth(request: Request, path: str):
    """Proxy requests to auth service"""
    await check_rate_limit(request)
    
    service_url = SERVICES["auth"]["url"]
    target_url = f"{service_url}/{path}"
    
    async with aiohttp.ClientSession() as session:
        body = await request.body()
        
        async with session.request(
            method=request.method,
            url=target_url,
            headers=dict(request.headers),
            data=body,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if redis_client:
                await redis_client.incr("gateway:total_requests")
                if response.status < 400:
                    await redis_client.incr("gateway:successful_requests")
                else:
                    await redis_client.incr("gateway:failed_requests")
            
            content = await response.read()
            return Response(
                content=content,
                status_code=response.status,
                headers=dict(response.headers)
            )

@app.api_route("/ml-pricing/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_ml_pricing(request: Request, path: str):
    """Proxy requests to ML pricing service"""
    await check_rate_limit(request)
    
    service_url = SERVICES["ml-pricing"]["url"]
    target_url = f"{service_url}/{path}"
    
    async with aiohttp.ClientSession() as session:
        body = await request.body()
        
        async with session.request(
            method=request.method,
            url=target_url,
            headers=dict(request.headers),
            data=body,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if redis_client:
                await redis_client.incr("gateway:total_requests")
                if response.status < 400:
                    await redis_client.incr("gateway:successful_requests")
                else:
                    await redis_client.incr("gateway:failed_requests")
            
            content = await response.read()
            return Response(
                content=content,
                status_code=response.status,
                headers=dict(response.headers)
            )

@app.api_route("/notification/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_notification(request: Request, path: str):
    """Proxy requests to notification service"""
    await check_rate_limit(request)
    
    service_url = SERVICES["notification"]["url"]
    target_url = f"{service_url}/{path}"
    
    async with aiohttp.ClientSession() as session:
        body = await request.body()
        
        async with session.request(
            method=request.method,
            url=target_url,
            headers=dict(request.headers),
            data=body,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if redis_client:
                await redis_client.incr("gateway:total_requests")
                if response.status < 400:
                    await redis_client.incr("gateway:successful_requests")
                else:
                    await redis_client.incr("gateway:failed_requests")
            
            content = await response.read()
            return Response(
                content=content,
                status_code=response.status,
                headers=dict(response.headers)
            )

@app.api_route("/i18n/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_i18n(request: Request, path: str):
    """Proxy requests to i18n service"""
    await check_rate_limit(request)
    
    service_url = SERVICES["i18n"]["url"]
    target_url = f"{service_url}/{path}"
    
    async with aiohttp.ClientSession() as session:
        body = await request.body()
        
        async with session.request(
            method=request.method,
            url=target_url,
            headers=dict(request.headers),
            data=body,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if redis_client:
                await redis_client.incr("gateway:total_requests")
                if response.status < 400:
                    await redis_client.incr("gateway:successful_requests")
                else:
                    await redis_client.incr("gateway:failed_requests")
            
            content = await response.read()
            return Response(
                content=content,
                status_code=response.status,
                headers=dict(response.headers)
            )

@app.api_route("/failure-handler/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_failure_handler(request: Request, path: str):
    """Proxy requests to failure handler service"""
    await check_rate_limit(request)
    
    service_url = SERVICES["failure-handler"]["url"]
    target_url = f"{service_url}/{path}"
    
    async with aiohttp.ClientSession() as session:
        body = await request.body()
        
        async with session.request(
            method=request.method,
            url=target_url,
            headers=dict(request.headers),
            data=body,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if redis_client:
                await redis_client.incr("gateway:total_requests")
                if response.status < 400:
                    await redis_client.incr("gateway:successful_requests")
                else:
                    await redis_client.incr("gateway:failed_requests")
            
            content = await response.read()
            return Response(
                content=content,
                status_code=response.status,
                headers=dict(response.headers)
            )

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

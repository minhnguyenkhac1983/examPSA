"""
Equilibrium Authentication Service
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import uvicorn
import hashlib
import secrets

app = FastAPI(title="Equilibrium Authentication Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security configuration
SECRET_KEY = "equilibrium-secret-key-2025"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# In-memory user storage (in production, use database)
users_db = {
    "admin@equilibrium.com": {
        "email": "admin@equilibrium.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
        "full_name": "Admin User",
        "role": "admin",
        "is_active": True
    },
    "driver@equilibrium.com": {
        "email": "driver@equilibrium.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
        "full_name": "Driver User",
        "role": "driver",
        "is_active": True
    },
    "user@equilibrium.com": {
        "email": "user@equilibrium.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
        "full_name": "Regular User",
        "role": "user",
        "is_active": True
    }
}

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "user"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    email: str
    full_name: str
    role: str
    is_active: bool

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    email: str = None

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(email: str):
    if email in users_db:
        user_dict = users_db[email]
        return user_dict

def authenticate_user(email: str, password: str):
    user = get_user(email)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = get_user(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    if not current_user["is_active"]:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "auth-service",
        "version": "1.0.0",
        "total_users": len(users_db)
    }

@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    """Register a new user"""
    if user.email in users_db:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Validate role
    if user.role not in ["user", "driver", "admin"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid role. Must be 'user', 'driver', or 'admin'"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    users_db[user.email] = {
        "email": user.email,
        "hashed_password": hashed_password,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": True
    }
    
    return UserResponse(
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=True
    )

@app.post("/api/v1/auth/login", response_model=Token)
async def login_user(user_credentials: UserLogin):
    """Login user and return access token"""
    user = authenticate_user(user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    """Get current user information"""
    return UserResponse(
        email=current_user["email"],
        full_name=current_user["full_name"],
        role=current_user["role"],
        is_active=current_user["is_active"]
    )

@app.post("/api/v1/auth/refresh", response_model=Token)
async def refresh_token(current_user: dict = Depends(get_current_active_user)):
    """Refresh access token"""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user["email"]}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@app.get("/api/v1/auth/users")
async def list_users(current_user: dict = Depends(get_current_active_user)):
    """List all users (admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    users = []
    for email, user_data in users_db.items():
        users.append({
            "email": user_data["email"],
            "full_name": user_data["full_name"],
            "role": user_data["role"],
            "is_active": user_data["is_active"]
        })
    
    return {"users": users}

@app.put("/api/v1/auth/users/{email}/status")
async def update_user_status(
    email: str, 
    is_active: bool,
    current_user: dict = Depends(get_current_active_user)
):
    """Update user status (admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    if email not in users_db:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    users_db[email]["is_active"] = is_active
    
    return {"message": f"User {email} status updated to {is_active}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006)

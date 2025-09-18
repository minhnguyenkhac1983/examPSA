# Authentication API Documentation

## Overview
The Authentication API handles user registration, login, and JWT token management for the Equilibrium platform.

## Base URL
```
https://api.equilibrium.com/api/v1/auth
```

## Endpoints

### 1. User Registration

**POST** `/register`

Register a new user account.

#### Request Body
```json
{
  "email": "user@example.com",
  "password": "secure_password_123",
  "user_type": "rider",
  "name": "John Doe",
  "phone": "+1234567890"
}
```

#### Response
```json
{
  "user_id": "user_abc123",
  "email": "user@example.com",
  "user_type": "rider",
  "name": "John Doe",
  "created_at": "2025-01-16T10:00:00Z",
  "message": "User registered successfully"
}
```

#### Error Responses
- `400 Bad Request`: Invalid request data or user already exists
- `422 Unprocessable Entity`: Validation errors

### 2. User Login

**POST** `/login`

Authenticate user and return JWT token.

#### Request Body
```json
{
  "email": "user@example.com",
  "password": "secure_password_123"
}
```

#### Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "user_abc123",
    "email": "user@example.com",
    "user_type": "rider",
    "name": "John Doe"
  }
}
```

#### Error Responses
- `401 Unauthorized`: Invalid credentials
- `400 Bad Request`: Invalid request data

### 3. Get User Information

**GET** `/me`

Get current user information.

#### Headers
```
Authorization: Bearer <jwt_token>
```

#### Response
```json
{
  "user_id": "user_abc123",
  "email": "user@example.com",
  "user_type": "rider",
  "name": "John Doe",
  "phone": "+1234567890",
  "created_at": "2025-01-16T10:00:00Z",
  "last_login": "2025-01-16T10:00:00Z"
}
```

#### Error Responses
- `401 Unauthorized`: Invalid or expired token

### 4. Refresh Token

**POST** `/refresh`

Refresh JWT token.

#### Headers
```
Authorization: Bearer <jwt_token>
```

#### Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 5. Logout

**POST** `/logout`

Logout user and invalidate token.

#### Headers
```
Authorization: Bearer <jwt_token>
```

#### Response
```json
{
  "message": "Successfully logged out"
}
```

### 6. Password Reset Request

**POST** `/password-reset-request`

Request password reset email.

#### Request Body
```json
{
  "email": "user@example.com"
}
```

#### Response
```json
{
  "message": "Password reset email sent"
}
```

### 7. Password Reset

**POST** `/password-reset`

Reset password with token.

#### Request Body
```json
{
  "token": "reset_token_abc123",
  "new_password": "new_secure_password_123"
}
```

#### Response
```json
{
  "message": "Password reset successfully"
}
```

## User Types

### Rider
- Can request rides
- Access to mobile app
- View pricing estimates

### Driver
- Can accept ride requests
- Access to driver app
- View heatmap data

### Admin
- Access to admin portal
- Manage system settings
- View analytics

## JWT Token Structure

### Header
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

### Payload
```json
{
  "user_id": "user_abc123",
  "email": "user@example.com",
  "user_type": "rider",
  "iat": 1642248000,
  "exp": 1642251600
}
```

## Rate Limits
- **Registration**: 5 requests per minute per IP
- **Login**: 10 requests per minute per IP
- **Other endpoints**: 60 requests per minute per user

## Security Features

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

### Token Security
- JWT tokens expire after 1 hour
- Refresh tokens expire after 7 days
- Tokens are invalidated on logout
- Rate limiting prevents brute force attacks

## SDK Examples

### Python
```python
import requests

# Register user
response = requests.post(
    "https://api.equilibrium.com/api/v1/auth/register",
    json={
        "email": "user@example.com",
        "password": "secure_password_123",
        "user_type": "rider",
        "name": "John Doe"
    }
)

# Login
response = requests.post(
    "https://api.equilibrium.com/api/v1/auth/login",
    json={
        "email": "user@example.com",
        "password": "secure_password_123"
    }
)
token = response.json()["access_token"]

# Get user info
response = requests.get(
    "https://api.equilibrium.com/api/v1/auth/me",
    headers={"Authorization": f"Bearer {token}"}
)
```

### JavaScript
```javascript
// Register user
const registerResponse = await fetch('https://api.equilibrium.com/api/v1/auth/register', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'secure_password_123',
    user_type: 'rider',
    name: 'John Doe'
  })
});

// Login
const loginResponse = await fetch('https://api.equilibrium.com/api/v1/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'secure_password_123'
  })
});
const {access_token} = await loginResponse.json();

// Get user info
const userResponse = await fetch('https://api.equilibrium.com/api/v1/auth/me', {
  headers: {'Authorization': `Bearer ${access_token}`}
});
```

## Error Codes

| Code | Description |
|------|-------------|
| `AUTH_001` | Invalid email format |
| `AUTH_002` | Password too weak |
| `AUTH_003` | User already exists |
| `AUTH_004` | Invalid credentials |
| `AUTH_005` | Token expired |
| `AUTH_006` | Token invalid |
| `AUTH_007` | Rate limit exceeded |
| `AUTH_008` | Account locked |

## Changelog

### v1.0.0 (2025-01-16)
- Initial release
- User registration and login
- JWT token management
- Password reset functionality
- Rate limiting and security features

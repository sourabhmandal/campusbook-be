# CampusBook Authentication API

A Django REST Framework implementation with class-based views for JWT authentication using Authlib concepts.

## Features

- **Class-based API Views**: Using Django REST Framework's APIView
- **JWT Authentication**: Custom JWT implementation with access and refresh tokens using RSA256 encryption
- **User Session Management**: Track user sessions and token validity
- **Security Features**: Login attempt tracking, password validation, IP logging
- **Custom User Model**: Extended user model with additional fields
- **Comprehensive Error Handling**: Consistent error response format

## API Endpoints

### Authentication Endpoints

#### 1. User Registration
**POST** `/users/auth/register/`

Request Body:
```json
{
    "email": "user@example.com",
    "username": "username",
    "password": "strongpassword",
    "password_confirm": "strongpassword", 
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890"
}
```

Response (201):
```json
{
    "data": {
        "user": {
            "id": "uuid",
            "email": "user@example.com",
            "username": "username",
            "first_name": "John",
            "last_name": "Doe",
            "full_name": "John Doe",
            "phone_number": "+1234567890",
            "is_email_verified": false,
            "is_profile_complete": true,
            "created_at": "2025-01-06T...",
            "last_login": null
        },
        "tokens": {
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "access_token_expires_at": "2025-01-06T...",
            "refresh_token_expires_at": "2025-01-13T...",
            "token_type": "Bearer",
            "session_id": "uuid"
        }
    },
    "message": "Registration successful",
    "status_code": 201,
    "timestamp": "2025-01-06T..."
}
```

#### 2. User Login
**POST** `/users/auth/login/`

Request Body:
```json
{
    "email": "user@example.com",
    "password": "strongpassword",
    "remember_me": false
}
```

Response (200): Same format as registration

#### 3. Token Refresh
**POST** `/users/auth/refresh/`

Request Body:
```json
{
    "refresh_token": "eyJ..."
}
```

Response (200):
```json
{
    "data": {
        "access_token": "eyJ...",
        "access_token_expires_at": "2025-01-06T...",
        "token_type": "Bearer"
    },
    "message": "Token refreshed successfully",
    "status_code": 200,
    "timestamp": "2025-01-06T..."
}
```

#### 4. User Logout
**POST** `/users/auth/logout/`

Request Body:
```json
{
    "refresh_token": "eyJ..."
}
```

Response (200):
```json
{
    "message": "Logout successful",
    "status_code": 200,
    "timestamp": "2025-01-06T..."
}
```

#### 5. Logout from All Devices
**POST** `/users/auth/logout-all/`

Headers: `Authorization: Bearer <access_token>`

Response (200):
```json
{
    "data": {
        "revoked_sessions": 3
    },
    "message": "Logged out from all devices successfully",
    "status_code": 200,
    "timestamp": "2025-01-06T..."
}
```

### User Profile Endpoints

#### 6. Get User Profile
**GET** `/users/profile/`

Headers: `Authorization: Bearer <access_token>`

Response (200):
```json
{
    "data": {
        "id": "uuid",
        "email": "user@example.com",
        "username": "username",
        "first_name": "John",
        "last_name": "Doe",
        "full_name": "John Doe",
        "phone_number": "+1234567890",
        "is_email_verified": false,
        "is_profile_complete": true,
        "created_at": "2025-01-06T...",
        "last_login": "2025-01-06T..."
    },
    "message": "Profile retrieved successfully",
    "status_code": 200,
    "timestamp": "2025-01-06T..."
}
```

#### 7. Update User Profile
**PUT** `/users/profile/`

Headers: `Authorization: Bearer <access_token>`

Request Body:
```json
{
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890"
}
```

Response (200): Same format as GET profile

#### 8. Change Password
**POST** `/users/profile/change-password/`

Headers: `Authorization: Bearer <access_token>`

Request Body:
```json
{
    "current_password": "oldpassword",
    "new_password": "newpassword",
    "new_password_confirm": "newpassword"
}
```

Response (200):
```json
{
    "message": "Password changed successfully. Please login again.",
    "status_code": 200,
    "timestamp": "2025-01-06T..."
}
```

## Architecture

### Class-Based Views
All API endpoints are implemented using Django REST Framework's `APIView` class:
- `LoginAPIView`: Handles user authentication
- `RegisterAPIView`: Handles user registration
- `LogoutAPIView`: Handles user logout
- `RefreshTokenAPIView`: Handles token refresh
- `UserProfileAPIView`: Handles profile CRUD operations
- `ChangePasswordAPIView`: Handles password changes
- `LogoutAllDevicesAPIView`: Handles logout from all devices

### JWT Authentication
Custom JWT authentication using PyJWT with the following features:
- RSA256 asymmetric encryption for enhanced security
- Access tokens (1 hour expiry)
- Refresh tokens (7 days expiry)
- Session tracking in database
- Automatic token cleanup
- IP address and user agent logging
- 2048-bit RSA key pairs

### Models
1. **User**: Custom user model extending AbstractUser
2. **UserSession**: Tracks JWT sessions and token validity
3. **LoginAttempt**: Security logging for login attempts

### Security Features
- Password validation using Django's built-in validators
- Login attempt tracking for security monitoring
- IP address logging
- Session management with automatic cleanup
- CORS configuration for frontend integration

## Setup Instructions

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Environment Configuration**:
Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

3. **Generate RSA Keys**:
```bash
python manage.py generate_jwt_keys
```

4. **Database Migration**:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Create Superuser**:
```bash
python manage.py createsuperuser
```

6. **Run Development Server**:
```bash
python manage.py runserver
```

## RSA Key Management

### Generate Keys
```bash
# Generate new RSA key pair
python manage.py generate_jwt_keys

# Generate with custom key size
python manage.py generate_jwt_keys --key-size 4096

# Print environment variable format
python manage.py generate_jwt_keys --print-env
```

### Verify Keys
```bash
# Verify current key configuration
python manage.py verify_jwt_keys
```

### Key Security
- **Development**: Private keys are stored in `keys/localhost/private.pem` (automatically added to .gitignore)
- **Development**: Public keys are stored in `keys/localhost/public.pem`
- **Production**: Use environment variables for secure key storage
- Keys are automatically generated if not found in development
- Rotate keys regularly for enhanced security

### Key Loading Priority
1. `keys/localhost/` directory (preferred for development)
2. Environment variables (`JWT_PRIVATE_KEY`, `JWT_PUBLIC_KEY`) for production
3. `keys/` directory (legacy support)
4. Auto-generation if no keys found (development only)

## Frontend Integration

The API is configured with CORS headers to work with frontend applications running on:
- `http://localhost:3000` (React default)
- `http://localhost:5173` (Vite default)

### JavaScript Example
```javascript
// Login
const loginResponse = await fetch('http://localhost:8000/users/auth/login/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        email: 'user@example.com',
        password: 'password'
    })
});

const loginData = await loginResponse.json();
const accessToken = loginData.data.tokens.access_token;

// Authenticated Request
const profileResponse = await fetch('http://localhost:8000/users/profile/', {
    headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
    }
});
```

## Error Response Format

All errors follow a consistent format:
```json
{
    "error": "ValidationError",
    "message": "Validation failed: email: This field is required",
    "status_code": 400,
    "timestamp": "2025-01-06T...",
    "path": "/users/auth/login/",
    "field_errors": {
        "email": ["This field is required."]
    }
}
```

## Admin Interface

Access the Django admin at `/admin/` to manage:
- Users and their profiles
- User sessions and token tracking
- Login attempts for security monitoring

## Testing

The API can be tested using the provided test script:
```bash
python test_api.py
```

This script tests all authentication endpoints and demonstrates proper API usage.

## Key Benefits

1. **Class-Based Design**: Follows DRF best practices with class-based views
2. **JWT Security**: Stateless authentication with proper token management
3. **Session Tracking**: Database-backed session management for security
4. **Extensible**: Easy to extend with additional authentication features
5. **Production Ready**: Includes logging, error handling, and security features

## Generate OpenSSL Keys

`openssl genrsa -out private.pem 2048 && openssl rsa -in private.pem -pubout -out public.pem`
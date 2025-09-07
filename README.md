# CampusBook

This repository is Backend of LMS and is free and open-source. The purpose of this project is to learn various scalability techniques during building Django backend.

Eventhough you are free to use this project as LMS. This project is not intended for any commercial use.
Hence Long Term Support of this repository is questionable

## Features

- **Class-based API Views**: Using Django REST Framework's APIView, model.Viewset
- **JWT Authentication**: Custom JWT implementation with access and refresh tokens using RSA256 encryption
- **User Session Management**: Track user sessions and token validity
- **Security Features**: Login attempt tracking, password validation, IP logging
- **Custom User Model**: Extended user model with additional fields
- **Comprehensive Error Handling**: Consistent error response format

## Architecture

### Class-Based Views
All API endpoints are implemented using Django REST Framework's `APIView` or `model.APIViewset` class:

### JWT Authentication
Custom JWT authentication using PyJWT with the following features:
- RSA256 asymmetric encryption for enhanced security
- Access tokens (1 hour expiry)
- Refresh tokens (7 days expiry)
- Session tracking in database
- Automatic token cleanup
- IP address and user agent logging
- 2048-bit RSA key pairs

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

## Generate OpenSSL Keys Manually

`openssl genrsa -out private.pem 2048 && openssl rsa -in private.pem -pubout -out public.pem`
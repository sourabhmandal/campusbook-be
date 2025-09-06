from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from django.db import transaction

from authentication.serializers import UserSerializer
from users.models import User
from .models import LoginAttempt
import logging
from .authentication import JWTTokenManager
from app.exceptions import SuccessResponse, ErrorResponse
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class LoginAPIView(APIView):
    """
    Password-based authentication operations.
    Handles login, registration, logout, token refresh, profile management, and password changes.
    """
    def post(self, request) -> Response:
        """
        Authenticate user and return JWT tokens.
        
        Request Body:
        {
            "email": "user@example.com",
            "password": "userpassword",
            "remember_me": false
        }
        """
        try:
            validation_result = self._validate_login_data(request.data)
            
            if 'errors' in validation_result:
                return ErrorResponse.create(
                    error="ValidationError",
                    message="Invalid login credentials",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    field_errors=validation_result['errors']
                )
            
            email = validation_result['email']
            password = validation_result['password']
            
            # Log login attempt
            self._log_login_attempt(email, request, success=False)
            
            # Authenticate user
            user = authenticate(
                request=request,
                username=email,
                password=password
            )
            
            if not user:
                # Check if user exists but credentials are wrong
                if User.objects.filter(email=email).exists():
                    error_msg = 'Invalid password.'
                    failure_reason = 'invalid_password'
                else:
                    error_msg = 'No account found with this email address.'
                    failure_reason = 'user_not_found'
                
                self._log_login_attempt(
                    email, request, success=False, 
                    failure_reason=failure_reason
                )
                return ErrorResponse.create(
                    error="AuthenticationError",
                    message=error_msg,
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            if not user.is_active:
                self._log_login_attempt(
                    email, request, success=False, 
                    failure_reason='account_disabled'
                )
                return ErrorResponse.create(
                    error="AuthenticationError",
                    message="This account has been disabled.",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            # Generate JWT tokens
            with transaction.atomic():
                token_data = JWTTokenManager.create_token_pair(user, request)
            
            # Log successful login
            self._log_login_attempt(email, request, success=True)
            
            # Serialize user data
            user_serializer = UserSerializer(user)
            
            # Prepare response data
            response_data = {
                'user': user_serializer.data,
                'tokens': token_data
            }
            
            logger.info(f"User {user.email} logged in successfully")
            
            return SuccessResponse.create(
                data=response_data,
                message="Login successful",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return ErrorResponse.create(
                error="AuthenticationError",
                message="Login failed due to server error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_client_ip(self, request) -> str:
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    def _log_login_attempt(
        self, 
        email: str, 
        request, 
        success: bool, 
        failure_reason: Optional[str] = None
    ) -> None:
        """Log login attempt for security monitoring."""
        try:
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            LoginAttempt.objects.create(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                failure_reason=failure_reason
            )
        except Exception as e:
            logger.warning(f"Failed to log login attempt: {str(e)}")

    def _validate_login_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate login request data."""
        errors = {}
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email:
            errors['email'] = ['Email is required.']
        elif '@' not in email:
            errors['email'] = ['Enter a valid email address.']
            
        if not password:
            errors['password'] = ['Password is required.']
            
        if errors:
            return {'errors': errors}
            
        return {'email': email.lower(), 'password': password, 'remember_me': data.get('remember_me', False)}

class RegisterAPIView(APIView):
    """
    Password-based authentication operations.
    Handles login, registration, logout, token refresh, profile management, and password changes.
    """
    def post(self, request) -> Response:
        """
        Register new user and return JWT tokens.
        
        Request Body:
        {
            "email": "user@example.com",
            "username": "username",
            "password": "strongpassword",
            "password_confirm": "strongpassword",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1234567890"
        }
        """
        try:
            validation_result = self._validate_registration_data(request.data)
            
            if 'errors' in validation_result:
                return ErrorResponse.create(
                    error="ValidationError",
                    message="Registration validation failed",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    field_errors=validation_result['errors']
                )
            
            # Create new user
            with transaction.atomic():
                user = User.objects.create_user(
                    email=validation_result['email'],
                    username=validation_result['username'],
                    password=validation_result['password'],
                    first_name=validation_result['first_name'],
                    last_name=validation_result['last_name'],
                    phone_number=validation_result['phone_number']
                )
                
                # Generate JWT tokens for automatic login
                token_data = JWTTokenManager.create_token_pair(user, request)
            
            # Serialize user data
            user_serializer = UserSerializer(user)
            
            # Prepare response data
            response_data = {
                'user': user_serializer.data,
                'tokens': token_data
            }
            
            logger.info(f"New user registered: {user.email}")
            
            return SuccessResponse.create(
                data=response_data,
                message="Registration successful",
                status_code=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return ErrorResponse.create(
                error="RegistrationError",
                message="Registration failed due to server error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _validate_registration_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate registration request data."""
        errors = {}
        
        email = data.get('email', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        password_confirm = data.get('password_confirm', '')
        
        # Email validation
        if not email:
            errors['email'] = ['Email is required.']
        elif '@' not in email:
            errors['email'] = ['Enter a valid email address.']
        elif User.objects.filter(email=email.lower()).exists():
            errors['email'] = ['A user with this email already exists.']
            
        # Username validation
        if not username:
            errors['username'] = ['Username is required.']
        elif User.objects.filter(username=username).exists():
            errors['username'] = ['A user with this username already exists.']
            
        # Password validation
        if not password:
            errors['password'] = ['Password is required.']
        else:
            try:
                validate_password(password)
            except ValidationError as e:
                errors['password'] = list(e.messages)
                
        # Password confirmation
        if password != password_confirm:
            errors['password_confirm'] = ['Passwords do not match.']
            
        if errors:
            return {'errors': errors}
            
        return {
            'email': email.lower(),
            'username': username,
            'password': password,
            'first_name': data.get('first_name', '').strip(),
            'last_name': data.get('last_name', '').strip(),
            'phone_number': data.get('phone_number', '').strip()
        }

class LogoutAPIView(APIView):
    """
    Password-based authentication operations.
    Handles login, registration, logout, token refresh, profile management, and password changes.
    """

    def post(self, request) -> Response:
        """
        Logout user by revoking refresh token.
        
        Request Body:
        {
            "refresh_token": "..."
        }
        """
        try:
            refresh_token = request.data.get('refresh_token')
            
            if not refresh_token:
                return ErrorResponse.create(
                    error="ValidationError",
                    message="Refresh token is required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Revoke the refresh token
            success = JWTTokenManager.revoke_token(refresh_token)
            
            if success:
                logger.info(f"User {request.user.email} logged out successfully")
                return SuccessResponse.create(
                    message="Logout successful",
                    status_code=status.HTTP_200_OK
                )
            else:
                return ErrorResponse.create(
                    error="InvalidToken",
                    message="Invalid refresh token",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return ErrorResponse.create(
                error="LogoutError",
                message="Logout failed due to server error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RefreshTokenAPIView(APIView):
    """
    Password-based authentication operations.
    Handles login, registration, logout, token refresh, profile management, and password changes.
    """
    def post(self, request) -> Response:
        """
        Refresh access token using refresh token.
        
        Request Body:
        {
            "refresh_token": "..."
        }
        """
        try:
            refresh_token = request.data.get('refresh_token')
            
            if not refresh_token:
                return ErrorResponse.create(
                    error="ValidationError",
                    message="Refresh token is required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate new access token
            token_data = JWTTokenManager.refresh_access_token(refresh_token, request)
            
            return SuccessResponse.create(
                data=token_data,
                message="Token refreshed successfully",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return ErrorResponse.create(
                error="TokenRefreshError",
                message="Failed to refresh token",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

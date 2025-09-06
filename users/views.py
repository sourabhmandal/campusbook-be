from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.db import transaction
import logging

from .serializers import (
    LoginSerializer, RegisterSerializer, UserSerializer,
    RefreshTokenSerializer, ChangePasswordSerializer
)
from .authentication import JWTTokenManager
from .exceptions import SuccessResponse, ErrorResponse

User = get_user_model()
logger = logging.getLogger(__name__)


class LoginAPIView(APIView):
    """
    Class-based API view for user authentication using email/username and password.
    
    Handles user login with JWT token generation and session management.
    """
    permission_classes = [AllowAny]
    
    def post(self, request) -> Response:
        """
        Authenticate user and return JWT tokens.
        
        Request Body:
        {
            "email": "user@example.com",
            "password": "userpassword",
            "remember_me": false
        }
        
        Returns:
        {
            "data": {
                "user": {...},
                "tokens": {
                    "access_token": "...",
                    "refresh_token": "...",
                    "access_token_expires_at": "...",
                    "refresh_token_expires_at": "...",
                    "token_type": "Bearer",
                    "session_id": "..."
                }
            },
            "message": "Login successful",
            "status_code": 200,
            "timestamp": "..."
        }
        """
        try:
            # Validate login credentials
            serializer = LoginSerializer(
                data=request.data,
                context={'request': request}
            )
            
            if not serializer.is_valid():
                return ErrorResponse.create(
                    error="ValidationError",
                    message="Invalid login credentials",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    field_errors=serializer.errors
                )
            
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            with transaction.atomic():
                token_data = JWTTokenManager.create_token_pair(user, request)
            
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


class RegisterAPIView(APIView):
    """
    Class-based API view for user registration.
    
    Handles new user registration with validation and automatic login.
    """
    permission_classes = [AllowAny]
    
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
        
        Returns:
        {
            "data": {
                "user": {...},
                "tokens": {
                    "access_token": "...",
                    "refresh_token": "...",
                    ...
                }
            },
            "message": "Registration successful",
            "status_code": 201,
            "timestamp": "..."
        }
        """
        try:
            # Validate registration data
            serializer = RegisterSerializer(data=request.data)
            
            if not serializer.is_valid():
                return ErrorResponse.create(
                    error="ValidationError",
                    message="Registration validation failed",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    field_errors=serializer.errors
                )
            
            # Create new user
            with transaction.atomic():
                user = serializer.save()
                
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


class LogoutAPIView(APIView):
    """
    Class-based API view for user logout.
    
    Handles user logout by revoking the current refresh token.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request) -> Response:
        """
        Logout user by revoking refresh token.
        
        Request Body:
        {
            "refresh_token": "..."
        }
        
        Returns:
        {
            "message": "Logout successful",
            "status_code": 200,
            "timestamp": "..."
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
    Class-based API view for refreshing access tokens.
    
    Handles access token refresh using valid refresh tokens.
    """
    permission_classes = [AllowAny]
    
    def post(self, request) -> Response:
        """
        Refresh access token using refresh token.
        
        Request Body:
        {
            "refresh_token": "..."
        }
        
        Returns:
        {
            "data": {
                "access_token": "...",
                "access_token_expires_at": "...",
                "token_type": "Bearer"
            },
            "message": "Token refreshed successfully",
            "status_code": 200,
            "timestamp": "..."
        }
        """
        try:
            # Validate refresh token
            serializer = RefreshTokenSerializer(data=request.data)
            
            if not serializer.is_valid():
                return ErrorResponse.create(
                    error="ValidationError",
                    message="Invalid refresh token format",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    field_errors=serializer.errors
                )
            
            refresh_token = serializer.validated_data['refresh_token']
            
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


class UserProfileAPIView(APIView):
    """
    Class-based API view for user profile management.
    
    Handles retrieving and updating user profile information.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request) -> Response:
        """
        Get current user profile.
        
        Returns:
        {
            "data": {
                "id": "...",
                "email": "...",
                "username": "...",
                "first_name": "...",
                "last_name": "...",
                "full_name": "...",
                "phone_number": "...",
                "is_email_verified": false,
                "is_profile_complete": true,
                "created_at": "...",
                "last_login": "..."
            },
            "message": "Profile retrieved successfully",
            "status_code": 200,
            "timestamp": "..."
        }
        """
        try:
            serializer = UserSerializer(request.user)
            
            return SuccessResponse.create(
                data=serializer.data,
                message="Profile retrieved successfully",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Profile retrieval error: {str(e)}")
            return ErrorResponse.create(
                error="ProfileError",
                message="Failed to retrieve profile",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request) -> Response:
        """
        Update user profile.
        
        Request Body:
        {
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1234567890"
        }
        
        Returns:
        {
            "data": {...},
            "message": "Profile updated successfully",
            "status_code": 200,
            "timestamp": "..."
        }
        """
        try:
            serializer = UserSerializer(
                request.user,
                data=request.data,
                partial=True
            )
            
            if not serializer.is_valid():
                return ErrorResponse.create(
                    error="ValidationError",
                    message="Profile validation failed",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    field_errors=serializer.errors
                )
            
            with transaction.atomic():
                user = serializer.save()
            
            logger.info(f"User {user.email} updated profile")
            
            return SuccessResponse.create(
                data=serializer.data,
                message="Profile updated successfully",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Profile update error: {str(e)}")
            return ErrorResponse.create(
                error="ProfileUpdateError",
                message="Failed to update profile",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChangePasswordAPIView(APIView):
    """
    Class-based API view for changing user password.
    
    Handles secure password changes with validation.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request) -> Response:
        """
        Change user password.
        
        Request Body:
        {
            "current_password": "oldpassword",
            "new_password": "newpassword",
            "new_password_confirm": "newpassword"
        }
        
        Returns:
        {
            "message": "Password changed successfully",
            "status_code": 200,
            "timestamp": "..."
        }
        """
        try:
            serializer = ChangePasswordSerializer(
                data=request.data,
                context={'request': request}
            )
            
            if not serializer.is_valid():
                return ErrorResponse.create(
                    error="ValidationError",
                    message="Password validation failed",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    field_errors=serializer.errors
                )
            
            # Change password
            user = request.user
            new_password = serializer.validated_data['new_password']
            
            with transaction.atomic():
                user.set_password(new_password)
                user.save(update_fields=['password'])
                
                # Revoke all existing tokens for security
                JWTTokenManager.revoke_all_user_tokens(user)
            
            logger.info(f"User {user.email} changed password")
            
            return SuccessResponse.create(
                message="Password changed successfully. Please login again.",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Password change error: {str(e)}")
            return ErrorResponse.create(
                error="PasswordChangeError",
                message="Failed to change password",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LogoutAllDevicesAPIView(APIView):
    """
    Class-based API view for logging out from all devices.
    
    Revokes all active tokens/sessions for the user.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request) -> Response:
        """
        Logout user from all devices by revoking all tokens.
        
        Returns:
        {
            "data": {
                "revoked_sessions": 5
            },
            "message": "Logged out from all devices successfully",
            "status_code": 200,
            "timestamp": "..."
        }
        """
        try:
            # Revoke all user tokens
            revoked_count = JWTTokenManager.revoke_all_user_tokens(request.user)
            
            logger.info(f"User {request.user.email} logged out from all devices")
            
            return SuccessResponse.create(
                data={'revoked_sessions': revoked_count},
                message="Logged out from all devices successfully",
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Logout all devices error: {str(e)}")
            return ErrorResponse.create(
                error="LogoutAllError",
                message="Failed to logout from all devices",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

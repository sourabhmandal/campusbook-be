from typing import Optional, Dict, Any, Tuple
import jwt
import uuid
import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from .models import UserSession

# Get the User model
User = get_user_model()

logger = logging.getLogger(__name__)


class JWTAuthentication(BaseAuthentication):
    """
    Custom JWT Authentication class using Authlib concepts
    but implemented with PyJWT for better Django integration.
    """
    
    def authenticate(self, request: Request) -> Optional[Tuple[Any, Dict[str, Any]]]:
        """
        Authenticate user based on JWT token in Authorization header.
        
        Returns:
            Tuple of (user, token_data) if authentication successful
            None if no token provided
            
        Raises:
            AuthenticationFailed: If token is invalid or expired
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            return None
            
        try:
            # Extract token from "Bearer <token>" format
            auth_parts = auth_header.split()
            if len(auth_parts) != 2 or auth_parts[0].lower() != 'bearer':
                raise AuthenticationFailed('Invalid authorization header format')
                
            token = auth_parts[1]
            return self._authenticate_token(token, request)
            
        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError) as e:
            logger.warning(f"JWT authentication failed: {str(e)}")
            raise AuthenticationFailed('Invalid or expired token')
        except Exception as e:
            logger.error(f"Unexpected error in JWT authentication: {str(e)}")
            raise AuthenticationFailed('Authentication failed')
    
    def _authenticate_token(self, token: str, request: Request) -> Tuple[Any, Dict[str, Any]]:
        """
        Validate JWT token and return user.
        
        Args:
            token: JWT token string
            request: Django request object
            
        Returns:
            Tuple of (user, token_data)
            
        Raises:
            AuthenticationFailed: If token validation fails
        """
        try:
            # Decode and validate JWT token
            payload = jwt.decode(
                token,
                settings.JWT_PUBLIC_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Extract user information from token
            user_id = payload.get('user_id')
            token_type = payload.get('type')
            jti = payload.get('jti')
            
            if not user_id or token_type != 'access':
                raise AuthenticationFailed('Invalid token payload')
                
            # Get user from database
            try:
                user = User.objects.get(id=user_id, is_active=True)
            except User.DoesNotExist:
                raise AuthenticationFailed('User not found or inactive')
            
            # Verify token session exists and is active
            if not self._verify_token_session(jti, user):
                raise AuthenticationFailed('Token session invalid or expired')
            
            # Update last login IP
            self._update_user_login_info(user, request)
            
            return user, payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
    
    def _verify_token_session(self, jti: str, user: Any) -> bool:
        """
        Verify that the token session exists and is active.
        
        Args:
            jti: JWT ID from token
            user: User object
            
        Returns:
            True if session is valid, False otherwise
        """
        try:
            session = UserSession.objects.get(
                access_token_jti=jti,
                user=user,
                is_active=True
            )
            return not session.is_expired
        except UserSession.DoesNotExist:
            return False

    def _update_user_login_info(self, user: Any, request: Request) -> None:
        """
        Update user's last login information.
        
        Args:
            user: User object
            request: Django request object
        """
        try:
            ip_address = self._get_client_ip(request)
            User.objects.filter(id=user.id).update(
                last_login=timezone.now(),
                last_login_ip=ip_address
            )
        except Exception as e:
            logger.warning(f"Failed to update user login info: {str(e)}")
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request.
        
        Args:
            request: Django request object
            
        Returns:
            Client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip


class JWTTokenManager:
    """
    Manager class for creating and managing JWT tokens.
    """
    
    @staticmethod
    def create_token_pair(user: Any, request: Request) -> Dict[str, Any]:
        """
        Create access and refresh token pair for user.
        
        Args:
            user: User object
            request: Django request object
            
        Returns:
            Dictionary containing access_token, refresh_token, and metadata
        """
        now = timezone.now()
        access_jti = str(uuid.uuid4())
        refresh_jti = str(uuid.uuid4())
        
        # Create access token
        access_payload = {
            'user_id': str(user.id),
            'email': user.email,
            'type': 'access',
            'jti': access_jti,
            'iat': now.timestamp(),
            'exp': (now + settings.JWT_ACCESS_TOKEN_LIFETIME).timestamp(),
        }
        
        access_token = jwt.encode(
            access_payload,
            settings.JWT_PRIVATE_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        # Create refresh token
        refresh_payload = {
            'user_id': str(user.id),
            'type': 'refresh',
            'jti': refresh_jti,
            'iat': now.timestamp(),
            'exp': (now + settings.JWT_REFRESH_TOKEN_LIFETIME).timestamp(),
        }
        
        refresh_token = jwt.encode(
            refresh_payload,
            settings.JWT_PRIVATE_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        # Store session in database
        session = UserSession.objects.create(
            user=user,
            refresh_token=refresh_token,
            access_token_jti=access_jti,
            expires_at=now + settings.JWT_REFRESH_TOKEN_LIFETIME,
            ip_address=JWTAuthentication()._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'access_token_expires_at': (now + settings.JWT_ACCESS_TOKEN_LIFETIME).isoformat(),
            'refresh_token_expires_at': (now + settings.JWT_REFRESH_TOKEN_LIFETIME).isoformat(),
            'token_type': 'Bearer',
            'session_id': str(session.id)
        }
    
    @staticmethod
    def refresh_access_token(refresh_token: str, request: Request) -> Dict[str, Any]:
        """
        Create new access token using refresh token.
        
        Args:
            refresh_token: Refresh token string
            request: Django request object
            
        Returns:
            Dictionary containing new access_token and metadata
            
        Raises:
            AuthenticationFailed: If refresh token is invalid
        """
        try:
            # Decode refresh token
            payload = jwt.decode(
                refresh_token,
                settings.JWT_PUBLIC_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            if payload.get('type') != 'refresh':
                raise AuthenticationFailed('Invalid refresh token type')
            
            user_id = payload.get('user_id')
            
            # Get user and session
            user = User.objects.get(id=user_id, is_active=True)
            session = UserSession.objects.get(
                refresh_token=refresh_token,
                user=user,
                is_active=True
            )
            
            if session.is_expired:
                session.deactivate()
                raise AuthenticationFailed('Refresh token expired')
            
            # Create new access token
            now = timezone.now()
            access_jti = str(uuid.uuid4())
            
            access_payload = {
                'user_id': str(user.id),
                'email': user.email,
                'type': 'access',
                'jti': access_jti,
                'iat': now.timestamp(),
                'exp': (now + settings.JWT_ACCESS_TOKEN_LIFETIME).timestamp(),
            }
            
            access_token = jwt.encode(
                access_payload,
                settings.JWT_PRIVATE_KEY,
                algorithm=settings.JWT_ALGORITHM
            )
            
            # Update session with new access token JTI
            session.access_token_jti = access_jti
            session.save(update_fields=['access_token_jti'])
            
            return {
                'access_token': access_token,
                'access_token_expires_at': (now + settings.JWT_ACCESS_TOKEN_LIFETIME).isoformat(),
                'token_type': 'Bearer'
            }
            
        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
            raise AuthenticationFailed('Invalid or expired refresh token')
        except (User.DoesNotExist, UserSession.DoesNotExist):
            raise AuthenticationFailed('Invalid refresh token')
    
    @staticmethod
    def revoke_token(refresh_token: str) -> bool:
        """
        Revoke refresh token by deactivating the session.
        
        Args:
            refresh_token: Refresh token to revoke
            
        Returns:
            True if token was revoked successfully
        """
        try:
            session = UserSession.objects.get(
                refresh_token=refresh_token,
                is_active=True
            )
            session.deactivate()
            return True
        except UserSession.DoesNotExist:
            return False
    
    @staticmethod
    def revoke_all_user_tokens(user: Any) -> int:
        """
        Revoke all active tokens for a user.
        
        Args:
            user: User object
            
        Returns:
            Number of sessions revoked
        """
        return UserSession.objects.filter(
            user=user,
            is_active=True
        ).update(is_active=False)

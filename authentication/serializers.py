from typing import Dict, Any, Optional
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from users.models import User
from .models import LoginAttempt
import logging

logger = logging.getLogger(__name__)


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login with username/email and password.
    """
    email = serializers.EmailField(
        required=True,
        help_text="User's email address"
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="User's password"
    )
    remember_me = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Remember login session for extended period"
    )

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate login credentials and authenticate user.
        
        Args:
            attrs: Serializer input data
            
        Returns:
            Validated data with user object
            
        Raises:
            ValidationError: If authentication fails
        """
        email = attrs.get('email')
        password = attrs.get('password')
        request = self.context.get('request')

        if not email or not password:
            raise serializers.ValidationError({
                'non_field_errors': ['Email and password are required.']
            })

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
            raise serializers.ValidationError({
                'non_field_errors': [error_msg]
            })

        if not user.is_active:
            self._log_login_attempt(
                email, request, success=False, 
                failure_reason='account_disabled'
            )
            raise serializers.ValidationError({
                'non_field_errors': ['This account has been disabled.']
            })

        # Log successful login
        self._log_login_attempt(email, request, success=True)
        
        attrs['user'] = user
        return attrs

    def _log_login_attempt(
        self, 
        email: str, 
        request, 
        success: bool, 
        failure_reason: Optional[str] = None
    ) -> None:
        """
        Log login attempt for security monitoring.
        
        Args:
            email: Email used for login
            request: Django request object
            success: Whether login was successful
            failure_reason: Reason for failure if applicable
        """
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

    def _get_client_ip(self, request) -> str:
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Password (minimum 8 characters)"
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Confirm password"
    )
    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional phone number"
    )

    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number'
        ]
        extra_kwargs = {
            'email': {'help_text': 'User email address (must be unique)'},
            'username': {'help_text': 'Username (must be unique)'},
            'first_name': {'help_text': 'User first name'},
            'last_name': {'help_text': 'User last name'},
        }

    def validate_email(self, value: str) -> str:
        """Validate email uniqueness."""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value.lower()

    def validate_username(self, value: str) -> str:
        """Validate username uniqueness and format."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
        return value

    def validate_password(self, value: str) -> str:
        """Validate password strength."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate password confirmation."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': ['Passwords do not match.']
            })
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> User:
        """Create new user with validated data."""
        # Remove password_confirm as it's not needed for user creation
        validated_data.pop('password_confirm', None)
        
        # Create user with encrypted password
        user = User.objects.create_user(**validated_data)
        
        logger.info(f"New user registered: {user.email}")
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    is_profile_complete = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'phone_number', 'is_email_verified',
            'is_profile_complete', 'created_at', 'last_login'
        ]
        read_only_fields = [
            'id', 'email', 'is_email_verified', 'created_at', 'last_login'
        ]


class RefreshTokenSerializer(serializers.Serializer):
    """
    Serializer for token refresh requests.
    """
    refresh_token = serializers.CharField(
        required=True,
        help_text="Valid refresh token"
    )

    def validate_refresh_token(self, value: str) -> str:
        """Validate refresh token format."""
        if not value:
            raise serializers.ValidationError("Refresh token is required.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change requests.
    """
    current_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Current password"
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="New password (minimum 8 characters)"
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Confirm new password"
    )

    def validate_current_password(self, value: str) -> str:
        """Validate current password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value: str) -> str:
        """Validate new password strength."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate password confirmation."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': ['New passwords do not match.']
            })
        return attrs

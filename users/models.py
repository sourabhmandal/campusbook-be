from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from django.utils import timezone
from typing import Optional
import uuid

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Provides additional fields for user profile and authentication.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        help_text="User's email address, must be unique"
    )
    first_name = models.CharField(max_length=30, blank=False)
    last_name = models.CharField(max_length=30, blank=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    
    # Use email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return f"{self.email} ({self.get_full_name()})"
    
    def get_full_name(self) -> str:
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_profile_complete(self) -> bool:
        """Check if user profile is complete."""
        return bool(
            self.first_name and 
            self.last_name and 
            self.email and 
            self.is_email_verified
        )


class UserSession(models.Model):
    """
    Model to track user sessions and JWT tokens.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    refresh_token = models.TextField(unique=True)
    access_token_jti = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return f"Session for {self.user.email} - {self.created_at}"
    
    @property
    def is_expired(self) -> bool:
        """Check if the session is expired."""
        return timezone.now() > self.expires_at
    
    def deactivate(self) -> None:
        """Deactivate the session."""
        self.is_active = False
        self.save(update_fields=['is_active'])


class LoginAttempt(models.Model):
    """
    Model to track login attempts for security purposes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    success = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=255, blank=True, null=True)
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'login_attempts'
        verbose_name = 'Login Attempt'
        verbose_name_plural = 'Login Attempts'
        ordering = ['-attempted_at']
        indexes = [
            models.Index(fields=['email', 'attempted_at']),
            models.Index(fields=['ip_address', 'attempted_at']),
        ]
    
    def __str__(self) -> str:
        status = "Success" if self.success else "Failed"
        return f"{status} login attempt for {self.email} from {self.ip_address}"

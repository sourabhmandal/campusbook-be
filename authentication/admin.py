from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import UserSession, LoginAttempt

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """
    Admin interface for UserSession model.
    """
    list_display = [
        'user_email', 'created_at', 'expires_at', 'is_active',
        'is_expired_status', 'ip_address', 'short_user_agent'
    ]
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = [
        'id', 'user', 'refresh_token', 'access_token_jti',
        'created_at', 'expires_at', 'ip_address', 'user_agent'
    ]
    ordering = ['-created_at']
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def is_expired_status(self, obj):
        """Display expiration status with color coding."""
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Active</span>')
    is_expired_status.short_description = 'Status'
    
    def short_user_agent(self, obj):
        """Display shortened user agent."""
        if obj.user_agent:
            return obj.user_agent[:50] + '...' if len(obj.user_agent) > 50 else obj.user_agent
        return '-'
    short_user_agent.short_description = 'User Agent'
    
    def has_add_permission(self, request):
        """Disable adding sessions through admin."""
        return False


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """
    Admin interface for LoginAttempt model.
    """
    list_display = [
        'email', 'success_status', 'ip_address', 'attempted_at',
        'failure_reason', 'short_user_agent'
    ]
    list_filter = ['success', 'attempted_at', 'failure_reason']
    search_fields = ['email', 'ip_address']
    readonly_fields = [
        'id', 'email', 'ip_address', 'user_agent',
        'success', 'failure_reason', 'attempted_at'
    ]
    ordering = ['-attempted_at']
    
    def success_status(self, obj):
        """Display success status with color coding."""
        if obj.success:
            return format_html('<span style="color: green;">Success</span>')
        return format_html('<span style="color: red;">Failed</span>')
    success_status.short_description = 'Status'
    
    def short_user_agent(self, obj):
        """Display shortened user agent."""
        if obj.user_agent:
            return obj.user_agent[:50] + '...' if len(obj.user_agent) > 50 else obj.user_agent
        return '-'
    short_user_agent.short_description = 'User Agent'
    
    def has_add_permission(self, request):
        """Disable adding login attempts through admin."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable changing login attempts through admin."""
        return False

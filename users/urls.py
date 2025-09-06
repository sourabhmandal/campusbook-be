from django.urls import path
from .views import (
    LoginAPIView, RegisterAPIView, LogoutAPIView,
    RefreshTokenAPIView, UserProfileAPIView,
    ChangePasswordAPIView, LogoutAllDevicesAPIView
)

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', LoginAPIView.as_view(), name='login'),
    path('auth/register/', RegisterAPIView.as_view(), name='register'),
    path('auth/logout/', LogoutAPIView.as_view(), name='logout'),
    path('auth/refresh/', RefreshTokenAPIView.as_view(), name='refresh_token'),
    path('auth/logout-all/', LogoutAllDevicesAPIView.as_view(), name='logout_all'),
    
    # User profile endpoints
    path('profile/', UserProfileAPIView.as_view(), name='user_profile'),
    path('profile/change-password/', ChangePasswordAPIView.as_view(), name='change_password'),
]

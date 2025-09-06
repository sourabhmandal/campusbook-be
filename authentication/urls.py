from django.urls import path, include
from .views import LoginAPIView, RegisterAPIView, LogoutAPIView, RefreshTokenAPIView, UserProfileViewset

app_name = 'auth'

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='PasswordAuthenticationViewset'),
    path('register/', RegisterAPIView.as_view(), name='RegisterViewset'),
    path('logout/', LogoutAPIView.as_view(), name='LogoutViewset'),
    path('refresh/', RefreshTokenAPIView.as_view(), name='RefreshTokenViewset'),
]
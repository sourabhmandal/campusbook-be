from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework import viewsets
from django.db import transaction
from authentication.authentication import JWTTokenManager
from authentication.serializers import UserSerializer
from .models import User
import logging
from app.exceptions import SuccessResponse, ErrorResponse
from typing import Dict, Any

logger = logging.getLogger(__name__)

class UserProfileViewset(viewsets.ModelViewSet):
    """
    User profile management operations.
    Handles viewing and updating user profile information.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request) -> Response:
        """
        Change user password.
        
        Request Body:
        {
            "current_password": "oldpassword",
            "new_password": "newpassword",
            "new_password_confirm": "newpassword"
        }
        """
        try:
            validation_result = self._validate_password_change_data(request.data, request.user)
            
            if 'errors' in validation_result:
                return ErrorResponse.create(
                    error="ValidationError",
                    message="Password validation failed",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    field_errors=validation_result['errors']
                )
            
            # Change password
            user = request.user
            new_password = validation_result['new_password']
            
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

    @action(detail=False, methods=['post'], url_path='logout-all-devices')
    def logout_all_devices(self, request) -> Response:
        """
        Logout user from all devices by revoking all tokens.
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

    def _validate_password_change_data(self, data: Dict[str, Any], user: User) -> Dict[str, Any]:
        """Validate password change request data."""
        errors = {}
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        new_password_confirm = data.get('new_password_confirm', '')
        
        if not current_password:
            errors['current_password'] = ['Current password is required.']
        elif not user.check_password(current_password):
            errors['current_password'] = ['Current password is incorrect.']
            
        if not new_password:
            errors['new_password'] = ['New password is required.']
        else:
            try:
                validate_password(new_password)
            except ValidationError as e:
                errors['new_password'] = list(e.messages)
                
        if new_password != new_password_confirm:
            errors['new_password_confirm'] = ['New passwords do not match.']
            
        if errors:
            return {'errors': errors}
            
        return {'new_password': new_password}


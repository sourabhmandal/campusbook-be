from typing import Dict, Any, Optional
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context) -> Optional[Response]:
    """
    Custom exception handler that provides consistent error response format.
    
    Args:
        exc: The exception that was raised
        context: Context information about the view that raised the exception
        
    Returns:
        Response object with formatted error, or None to use default handler
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Log the exception
        logger.warning(
            f"API Exception: {type(exc).__name__} - {str(exc)} "
            f"Path: {context.get('request', {}).get('path', 'Unknown')}"
        )
        
        # Create custom error response format
        custom_response_data = {
            'error': type(exc).__name__,
            'message': _extract_error_message(response.data),
            'status_code': response.status_code,
            'timestamp': timezone.now().isoformat(),
            'path': context.get('request', {}).get('path', ''),
        }
        
        # Add field-specific errors if they exist
        if isinstance(response.data, dict):
            field_errors = {}
            for key, value in response.data.items():
                if key not in ['detail', 'non_field_errors']:
                    field_errors[key] = value
            
            if field_errors:
                custom_response_data['field_errors'] = field_errors
        
        response.data = custom_response_data
    
    return response


def _extract_error_message(error_data) -> str:
    """
    Extract a meaningful error message from DRF error data.
    
    Args:
        error_data: Error data from DRF exception
        
    Returns:
        Formatted error message string
    """
    if isinstance(error_data, str):
        return error_data
    
    if isinstance(error_data, list) and error_data:
        return str(error_data[0])
    
    if isinstance(error_data, dict):
        # Check for common error keys
        if 'detail' in error_data:
            return _extract_error_message(error_data['detail'])
        
        if 'non_field_errors' in error_data:
            return _extract_error_message(error_data['non_field_errors'])
        
        # If it's field errors, create a summary message
        field_errors = []
        for field, errors in error_data.items():
            if isinstance(errors, list):
                field_errors.append(f"{field}: {errors[0]}")
            else:
                field_errors.append(f"{field}: {errors}")
        
        if field_errors:
            return "Validation failed: " + ", ".join(field_errors)
    
    return "An error occurred"


class SuccessResponse:
    """
    Utility class for creating consistent success response format.
    """
    
    @staticmethod
    def create(
        data: Any = None,
        message: str = "Success",
        status_code: int = status.HTTP_200_OK,
        headers: Optional[Dict[str, str]] = None
    ) -> Response:
        """
        Create a standardized success response.
        
        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            headers: Optional response headers
            
        Returns:
            Response object with formatted success data
        """
        response_data = {
            'data': data,
            'message': message,
            'status_code': status_code,
            'timestamp': timezone.now().isoformat(),
        }
        
        return Response(
            data=response_data,
            status=status_code,
            headers=headers
        )


class ErrorResponse:
    """
    Utility class for creating consistent error response format.
    """
    
    @staticmethod
    def create(
        error: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        field_errors: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Response:
        """
        Create a standardized error response.
        
        Args:
            error: Error type/name
            message: Error message
            status_code: HTTP status code
            field_errors: Field-specific validation errors
            headers: Optional response headers
            
        Returns:
            Response object with formatted error data
        """
        response_data = {
            'error': error,
            'message': message,
            'status_code': status_code,
            'timestamp': timezone.now().isoformat(),
        }
        
        if field_errors:
            response_data['field_errors'] = field_errors
        
        return Response(
            data=response_data,
            status=status_code,
            headers=headers
        )

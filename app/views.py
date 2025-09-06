from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import connection
from django.conf import settings
import os


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for container health monitoring.
    
    Returns:
        Response with health status and basic system information
    """
    try:
        # Check database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Basic system info
    health_data = {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "timestamp": timezone.now().isoformat(),
        "version": "1.0.0",  # You can make this dynamic
        "database": db_status,
        "debug": settings.DEBUG,
        "environment": os.getenv("ENVIRONMENT", "development"),
    }
    
    status_code = status.HTTP_200_OK if health_data["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(health_data, status=status_code)

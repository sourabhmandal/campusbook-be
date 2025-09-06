#!/bin/bash

# Exit on any error
set -e

echo "Starting CampusBook Backend..."

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Generate JWT keys if they don't exist
echo "Generating JWT keys..."
python manage.py generate_jwt_keys

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if specified
if [[ -n "$DJANGO_SUPERUSER_USERNAME" && -n "$DJANGO_SUPERUSER_EMAIL" && -n "$DJANGO_SUPERUSER_PASSWORD" ]]; then
    echo "Creating superuser..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"
fi

echo "Starting Gunicorn server..."
exec "$@"

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a test user for API testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='test@example.com',
            help='Email address for the test user'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='TestPass123!',
            help='Password for the test user'
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'User with email {email} already exists')
            )
            return
        
        user = User.objects.create_user(
            email=email,
            username=email.split('@')[0],
            password=password,
            first_name='Test',
            last_name='User',
            phone_number='+1234567890'
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created test user: {user.email}')
        )
        self.stdout.write(f'Email: {email}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write(f'Username: {user.username}')

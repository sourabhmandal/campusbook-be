from django.core.management.base import BaseCommand
from django.conf import settings
import jwt
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Verify JWT RSA key configuration'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Verifying JWT RSA key configuration...\n')
        
        try:
            # Check if keys are configured
            private_key = getattr(settings, 'JWT_PRIVATE_KEY', None)
            public_key = getattr(settings, 'JWT_PUBLIC_KEY', None)
            algorithm = getattr(settings, 'JWT_ALGORITHM', None)
            
            if not private_key:
                self.stdout.write(
                    self.style.ERROR('❌ JWT_PRIVATE_KEY not configured')
                )
                return
            
            if not public_key:
                self.stdout.write(
                    self.style.ERROR('❌ JWT_PUBLIC_KEY not configured')
                )
                return
            
            if algorithm != 'RS256':
                self.stdout.write(
                    self.style.WARNING(f'⚠️  JWT_ALGORITHM is {algorithm}, expected RS256')
                )
            
            self.stdout.write(f'✅ JWT_ALGORITHM: {algorithm}')
            self.stdout.write(f'✅ Private key loaded ({len(private_key)} characters)')
            self.stdout.write(f'✅ Public key loaded ({len(public_key)} characters)')
            
            # Test token creation and verification
            self.stdout.write('\n🧪 Testing token creation and verification...')
            
            test_payload = {
                'user_id': 'test-user-123',
                'email': 'test@example.com',
                'type': 'access',
                'jti': 'test-jti-123',
                'iat': datetime.utcnow().timestamp(),
                'exp': (datetime.utcnow() + timedelta(minutes=5)).timestamp(),
            }
            
            # Create token
            token = jwt.encode(test_payload, private_key, algorithm=algorithm)
            self.stdout.write(f'✅ Token created successfully')
            self.stdout.write(f'   Token length: {len(token)} characters')
            
            # Verify token
            decoded_payload = jwt.decode(token, public_key, algorithms=[algorithm])
            self.stdout.write(f'✅ Token verified successfully')
            
            # Check payload
            if decoded_payload['user_id'] == test_payload['user_id']:
                self.stdout.write(f'✅ Payload verification successful')
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Payload verification failed')
                )
                return
            
            self.stdout.write('\n' + '='*50)
            self.stdout.write(
                self.style.SUCCESS('🎉 JWT RSA configuration is working correctly!')
            )
            self.stdout.write('='*50)
            
            # Display key information
            self.stdout.write('\n📋 Key Information:')
            self.stdout.write(f'   Algorithm: {algorithm}')
            self.stdout.write(f'   Private key present: Yes')
            self.stdout.write(f'   Public key present: Yes')
            
            # Security recommendations
            self.stdout.write('\n🔒 Security Recommendations:')
            self.stdout.write('   • Store private key securely (environment variables)')
            self.stdout.write('   • Never commit private keys to version control')
            self.stdout.write('   • Rotate keys regularly in production')
            self.stdout.write('   • Use strong key sizes (2048+ bits)')
            self.stdout.write('   • Monitor key usage and access')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ JWT configuration test failed: {str(e)}')
            )
            self.stdout.write('\n🔧 Troubleshooting:')
            self.stdout.write('   1. Run: python manage.py generate_jwt_keys')
            self.stdout.write('   2. Check your .env file configuration')
            self.stdout.write('   3. Ensure keys/ directory exists with valid PEM files')
            self.stdout.write('   4. Verify JWT_PRIVATE_KEY and JWT_PUBLIC_KEY in settings')

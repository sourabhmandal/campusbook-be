from django.core.management.base import BaseCommand
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import os


class Command(BaseCommand):
    help = 'Generate RSA key pair for JWT authentication'

    def add_arguments(self, parser):
        parser.add_argument(
            '--key-size',
            type=int,
            default=2048,
            help='RSA key size in bits (default: 2048)'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='keys/localhost',
            help='Output directory for key files (default: keys/localhost)'
        )
        parser.add_argument(
            '--print-env',
            action='store_true',
            help='Print keys in environment variable format'
        )

    def handle(self, *args, **options):
        key_size = options['key_size']
        output_dir = options['output_dir']
        print_env = options['print_env']
        
        self.stdout.write(f'Generating {key_size}-bit RSA key pair...')
        
        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )
        
        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Serialize public key
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Create output directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            self.stdout.write(f'Created directory: {output_dir}')
        
        # Write keys to files
        private_key_path = os.path.join(output_dir, 'private.pem')
        public_key_path = os.path.join(output_dir, 'public.pem')
        
        with open(private_key_path, 'wb') as f:
            f.write(private_pem)
        
        with open(public_key_path, 'wb') as f:
            f.write(public_pem)
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ RSA key pair generated successfully!')
        )
        self.stdout.write(f'Private key: {private_key_path}')
        self.stdout.write(f'Public key: {public_key_path}')
        
        if print_env:
            self.stdout.write('\n' + '='*60)
            self.stdout.write('Environment Variable Format:')
            self.stdout.write('='*60)
            
            # Convert to environment variable format
            private_env = private_pem.decode('utf-8').replace('\n', '\\n')
            public_env = public_pem.decode('utf-8').replace('\n', '\\n')
            
            self.stdout.write(f'JWT_PRIVATE_KEY="{private_env}"')
            self.stdout.write(f'JWT_PUBLIC_KEY="{public_env}"')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Security Notes:')
        self.stdout.write('='*60)
        self.stdout.write('🔒 Keep the private key secret and secure')
        self.stdout.write('🔒 Never commit private keys to version control')
        self.stdout.write('🔒 Use environment variables in production')
        self.stdout.write('🔒 Rotate keys regularly in production')
        self.stdout.write('📝 The public key can be shared safely')
        
        # Add to .gitignore if not already present
        gitignore_path = '.gitignore'
        gitignore_entries = [
            'keys/localhost/',
            'keys/',
            '*.pem',
            '.env'
        ]
        
        try:
            with open(gitignore_path, 'r') as f:
                content = f.read()
            
            entries_to_add = []
            for entry in gitignore_entries:
                if entry not in content:
                    entries_to_add.append(entry)
            
            if entries_to_add:
                with open(gitignore_path, 'a') as f:
                    f.write('\n# JWT Keys and Environment\n')
                    for entry in entries_to_add:
                        f.write(f'{entry}\n')
                
                self.stdout.write(f'✅ Updated .gitignore with security entries')
        
        except FileNotFoundError:
            # Create .gitignore if it doesn't exist
            with open(gitignore_path, 'w') as f:
                f.write('# JWT Keys and Environment\n')
                for entry in gitignore_entries:
                    f.write(f'{entry}\n')
            
            self.stdout.write(f'✅ Created .gitignore with security entries')

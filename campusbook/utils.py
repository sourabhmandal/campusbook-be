"""
Utility functions for the campusbook project.
"""
from typing import Tuple
import os
from pathlib import Path


class RSAKeyGenerator:
    """
    Utility class to generate and manage RSA key pairs for JWT signing and verification.
    Ensures keys are generated only when needed and cached for subsequent use.
    """
    
    @staticmethod
    def generate_rsa_key_pair() -> Tuple[str, str]:
        """
        Generate RSA key pair for JWT signing and verification.
        
        Returns:
            Tuple[str, str]: (private_key_pem, public_key_pem)
        """
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Serialize private key to PEM format
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        # Serialize public key to PEM format
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        return private_pem, public_pem

    @staticmethod
    def get_or_generate_keys() -> Tuple[str, str]:
        """
        Get existing RSA keys from environment variables or files, 
        or generate new ones if they don't exist.
        
        Returns:
            Tuple[str, str]: (private_key_pem, public_key_pem)
        """
        # Try to get keys from environment variables first
        private_key_env = os.getenv('JWT_PRIVATE_KEY')
        public_key_env = os.getenv('JWT_PUBLIC_KEY')
        
        if private_key_env and public_key_env:
            return private_key_env, public_key_env
        
        # Try to read keys from files
        base_dir = Path(__file__).resolve().parent.parent
        keys_dir = base_dir / 'keys'
        private_key_file = keys_dir / 'private_key.pem'
        public_key_file = keys_dir / 'public_key.pem'
        
        if private_key_file.exists() and public_key_file.exists():
            try:
                private_key = private_key_file.read_text().strip()
                public_key = public_key_file.read_text().strip()
                return private_key, public_key
            except Exception:
                pass  # Fall back to generation
        
        # Generate new keys if none exist
        return RSAKeyGenerator.generate_rsa_key_pair()

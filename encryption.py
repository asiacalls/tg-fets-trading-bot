from cryptography.fernet import Fernet
import base64
import hashlib
from typing import Optional
from config import ENCRYPTION_KEY

class KeyEncryption:
    def __init__(self):
        """Initialize encryption with the key from config"""
        # Generate a proper Fernet key from the config
        key_bytes = hashlib.sha256(ENCRYPTION_KEY.encode()).digest()
        self.fernet = Fernet(base64.urlsafe_b64encode(key_bytes))
    
    def encrypt_private_key(self, private_key: str) -> str:
        """Encrypt a private key"""
        try:
            # Remove 0x prefix if present
            clean_key = private_key.replace('0x', '')
            
            # Encrypt the private key
            encrypted_bytes = self.fernet.encrypt(clean_key.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            print(f"Error encrypting private key: {e}")
            raise
    
    def decrypt_private_key(self, encrypted_key: str) -> str:
        """Decrypt a private key"""
        try:
            # Decrypt the private key
            decrypted_bytes = self.fernet.decrypt(encrypted_key.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            print(f"Error decrypting private key: {e}")
            raise
    
    def validate_private_key(self, private_key: str) -> bool:
        """Validate private key format"""
        try:
            # Remove 0x prefix if present
            clean_key = private_key.replace('0x', '').strip()
            
            # Check length (64 characters for private key)
            if len(clean_key) != 64:
                return False
            
            # Check if it's valid hexadecimal
            try:
                int(clean_key, 16)
                return True
            except ValueError:
                return False
        except Exception:
            return False
    
    def generate_encryption_key(self) -> str:
        """Generate a new encryption key (for testing/development)"""
        return Fernet.generate_key().decode()



from cryptography.fernet import Fernet
from core.config import settings

_cipher = Fernet(settings.ENCRYPTION_KEY.encode())

def encrypt(data: str) -> str:
    """Encrypt a string and return a base64-encoded ciphertext string."""
    encrypted_bytes = _cipher.encrypt(data.encode())
    return encrypted_bytes.decode()

def decrypt(data: str) -> str:
    """Decrypt a base64-encoded ciphertext string back to plaintext."""
    decrypted_bytes = _cipher.decrypt(data.encode())
    return decrypted_bytes.decode()
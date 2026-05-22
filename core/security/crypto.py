from cryptography.fernet import Fernet
from core.config import settings
import base64

def _get_fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY

    if not key:
        raise ValueError("ENCRYPTION_KEY not set in configuration")
    
    if len(key)==64:
        key = base64.urlsafe_b64encode(bytes.fromhex(key))
    
    return Fernet(key)

def encrypt(data: str)->str:
    if data is None:
        return data
    
    f = _get_fernet()
    encrypted_bytes = f.encrypt(data.encode("utf-8"))
    return base64.urlsafe_b64encode(encrypted_bytes).decode("utf-8")

def decrypt(data: str)->str:
    if data is None:
        return data
    
    f = _get_fernet()
    encrypted_data = base64.urlsafe_b64decode(data.encode("utf-8"))
    decrypted_data = f.decrypt(encrypted_data)
    return decrypted_data.decode("utf-8")

    
    
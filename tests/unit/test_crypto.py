import pytest
from core.security.crypto import encrypt, decrypt

def test_round_trip_encrypt_decrypt():
    """Encrypted data should decrypt back to the original."""

    original = "Modified line 42 in main.py"
    encrypted = encrypt(original)
    decrypted = decrypt(encrypted)

    assert decrypted == original


def test_encrypted_data_is_not_plaintext():
    """Encrypted string should not match the original."""
    original = "User edited line 42 in main.py"
    encrypted = encrypt(original)

    assert encrypted != original
    assert "edited line 42" not in encrypted
    assert "main.py" not in encrypted

def test_empty_string_encryption():
    """Empty strings should encrypt and decrypt without error."""

    encrypted = encrypt("")
    decrypted = decrypt(encrypted)

    assert decrypted == ""

def test_unicode_and_special_chars():
    """Unicode and special characters should round-trip correctly."""

    original = "Héllo Wörld! 你好 🌍 \n\t<script>alert('xss')</script>"
    encrypted = encrypt(original)
    decrypted = decrypt(encrypted)

    assert decrypted == original

def test_invalid_ciphertext_raises_error():
    """Trying to decrypt garbage should raise an exception."""

    from cryptography.fernet import InvalidToken

    with pytest.raises(InvalidToken):
        decrypt("this-is-not-a-valid-ciphertext")
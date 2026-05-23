import pytest
from core.security.crypto import encrypt, decrypt


def test_round_trip_encrypt_decrypt(encryption_key):
    """Encrypted data should decrypt back to the original."""
    original = "User edited line 42 in main.py"
    encrypted = encrypt(original)
    decrypted = decrypt(encrypted)

    assert decrypted == original


def test_encrypted_data_is_not_plaintext(encryption_key):
    """Encrypted string should not contain the original plaintext."""
    original = "User edited line 42 in main.py"
    encrypted = encrypt(original)

    assert encrypted != original
    assert "edited line 42" not in encrypted
    assert "main.py" not in encrypted


def test_encryption_is_non_deterministic(encryption_key):
    """Same plaintext should encrypt to different ciphertexts (random IV)."""
    original = "Hello World"
    encrypted_one = encrypt(original)
    encrypted_two = encrypt(original)

    assert encrypted_one != encrypted_two
    assert decrypt(encrypted_one) == original
    assert decrypt(encrypted_two) == original


def test_empty_string_encryption(encryption_key):
    """Empty strings should encrypt and decrypt without error."""
    encrypted = encrypt("")
    decrypted = decrypt(encrypted)

    assert decrypted == ""


def test_none_input_returns_none():
    """encrypt(None) should return None safely."""
    assert encrypt(None) is None
    assert decrypt(None) is None


def test_unicode_and_special_chars(encryption_key):
    """Unicode and special characters should round-trip correctly."""
    original = "Héllo Wörld! 你好 🌍 \n\t<script>alert('xss')</script>"
    encrypted = encrypt(original)
    decrypted = decrypt(encrypted)

    assert decrypted == original


def test_invalid_ciphertext_raises_error(encryption_key):
    """Trying to decrypt garbage should raise an exception."""
    with pytest.raises(Exception):
        decrypt("not-a-valid-ciphertext-at-all")

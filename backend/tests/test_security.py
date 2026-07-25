"""Тесты паролей, токенов и шифрования секретов."""

from __future__ import annotations

import pytest

from app.core.crypto import decrypt_secret, encrypt_secret, mask_secret
from app.core.security import create_token, decode_token, hash_password, verify_password


def test_password_hash_is_not_reversible() -> None:
    password = "очень-секретный-пароль-123"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("другой-пароль", hashed) is False


def test_long_password_is_not_truncated() -> None:
    """bcrypt обрезает пароль на 72 байтах — предварительный SHA-256 это снимает."""
    base = "а" * 100
    hashed = hash_password(base + "конец-один")

    assert verify_password(base + "конец-один", hashed) is True
    assert verify_password(base + "конец-два", hashed) is False


def test_token_roundtrip() -> None:
    token = create_token("user-id-1", "access")
    payload = decode_token(token, expected_type="access")

    assert payload["sub"] == "user-id-1"
    assert payload["type"] == "access"


def test_token_type_is_checked() -> None:
    import jwt

    token = create_token("user-id-1", "refresh")
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token, expected_type="access")


def test_secret_encryption_roundtrip() -> None:
    secret = "sk-ant-api03-example-key"
    encrypted = encrypt_secret(secret)

    assert secret.encode() not in encrypted
    assert decrypt_secret(encrypted) == secret


def test_mask_hides_most_of_the_key() -> None:
    mask = mask_secret("sk-ant-api03-1234567890abcdef")

    assert mask.startswith("sk-ant-")
    assert mask.endswith("cdef")
    assert "api03" not in mask

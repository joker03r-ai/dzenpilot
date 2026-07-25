"""Шифрование секретов интеграций.

API-ключи никогда не хранятся в открытом виде и никогда не отдаются во frontend —
наружу уходит только маска вида `sk-ant-…a1b2`.
"""

from __future__ import annotations

import base64
import hashlib
import json
from functools import lru_cache
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class SecretDecryptionError(RuntimeError):
    """Не удалось расшифровать секрет: сменился ключ или данные повреждены."""


@lru_cache
def _fernet() -> Fernet:
    key = (settings.app_encryption_key or "").strip()
    if key:
        try:
            return Fernet(key.encode("utf-8"))
        except (ValueError, TypeError) as exc:
            raise RuntimeError(
                "APP_ENCRYPTION_KEY задан неверно. Сгенерируйте ключ командой: "
                'python -c "from cryptography.fernet import Fernet; '
                'print(Fernet.generate_key().decode())"'
            ) from exc
    # Резервный вариант для локальной разработки: ключ выводится из SECRET_KEY.
    derived = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(derived))


def encrypt_secret(value: str) -> bytes:
    return _fernet().encrypt(value.encode("utf-8"))


def decrypt_secret(token: bytes | None) -> str | None:
    if not token:
        return None
    try:
        return _fernet().decrypt(bytes(token)).decode("utf-8")
    except InvalidToken as exc:
        raise SecretDecryptionError(
            "Не удалось расшифровать сохранённый ключ. "
            "Возможно, изменился APP_ENCRYPTION_KEY — подключите сервис заново."
        ) from exc


def encrypt_json(data: dict[str, Any]) -> bytes:
    return encrypt_secret(json.dumps(data, ensure_ascii=False))


def decrypt_json(token: bytes | None) -> dict[str, Any]:
    raw = decrypt_secret(token)
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def mask_secret(value: str | None, visible_prefix: int = 7, visible_suffix: int = 4) -> str:
    """Превращает ключ в безопасную для показа маску."""
    if not value:
        return "не задан"
    if len(value) <= visible_prefix + visible_suffix:
        return "*" * len(value)
    return f"{value[:visible_prefix]}…{value[-visible_suffix:]}"

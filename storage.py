# storage.py
"""
Secure token storage wrapper:
- Primary: python-keyring
- Fallback: encrypted local file using cryptography.

For production, you should use a stronger KDF (PBKDF2/scrypt) and harden
passphrase handling. This file is intentionally minimal for a local demo.
"""
import json
import os
from pathlib import Path
import base64
from typing import Optional

try:
    import keyring  # type: ignore
    _KEYRING_AVAILABLE = True
except Exception:
    _KEYRING_AVAILABLE = False

from cryptography.fernet import Fernet

FALLBACK_FILE = Path.home() / ".local_agent_tokens.json"


def _derive_key_from_password(password: str) -> bytes:
    """
    Very simple KDF (NOT for production use).
    Derives a 32-byte key from the password and encodes as urlsafe base64.
    """
    return base64.urlsafe_b64encode(password.encode("utf-8").ljust(32, b"0")[:32])


class TokenStore:
    def __init__(self, key_name: str = "local_agent_token"):
        self.key_name = key_name

    def set(self, data: dict, fallback_password: Optional[str] = None) -> bool:
        payload = json.dumps(data)
        if _KEYRING_AVAILABLE:
            keyring.set_password("local_agent", self.key_name, payload)
            return True

        # Fallback to encrypted file
        if not fallback_password:
            raise RuntimeError(
                "Keyring not available. Provide a fallback password to encrypt tokens."
            )
        key = _derive_key_from_password(fallback_password)
        f = Fernet(key)
        token = f.encrypt(payload.encode("utf-8"))
        FALLBACK_FILE.write_bytes(token)
        return True

    def get(self, fallback_password: Optional[str] = None) -> Optional[dict]:
        if _KEYRING_AVAILABLE:
            payload = keyring.get_password("local_agent", self.key_name)
            if not payload:
                return None
            return json.loads(payload)

        if not FALLBACK_FILE.exists():
            return None
        if not fallback_password:
            raise RuntimeError(
                "Keyring not available. Provide fallback password to decrypt tokens."
            )
        key = _derive_key_from_password(fallback_password)
        f = Fernet(key)
        token = FALLBACK_FILE.read_bytes()
        payload = f.decrypt(token)
        return json.loads(payload.decode("utf-8"))

    def delete(self) -> None:
        if _KEYRING_AVAILABLE:
            keyring.delete_password("local_agent", self.key_name)
        else:
            try:
                FALLBACK_FILE.unlink()
            except FileNotFoundError:
                pass

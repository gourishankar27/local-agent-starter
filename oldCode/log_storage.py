# log_storage.py
"""
Encrypted log storage for the Local Agent desktop app.

- Stores all logs in a single encrypted file.
- Encryption key is derived from a password that YOU provide.
- Without the correct password, logs cannot be read.

Note: This uses a simple KDF similar to storage.py and is meant for
local usage only. For production-grade security, you'd want a strong KDF
like PBKDF2 or scrypt with salt and proper secret handling.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from cryptography.fernet import Fernet, InvalidToken

# Encrypted log file lives in your home directory by default
DEFAULT_LOG_FILE = Path.home() / ".local_agent_history.enc"


def _derive_key_from_password(password: str) -> bytes:
    """
    Derive a 32-byte key from the password and encode as urlsafe base64.

    This is intentionally simple and mirrors the approach in storage.py.
    For strong security, use a real KDF like PBKDF2 or scrypt instead.
    """
    return base64.urlsafe_b64encode(password.encode("utf-8").ljust(32, b"0")[:32])


@dataclass
class LogEntry:
    timestamp: str
    event_type: str
    meta: Dict[str, Any]
    preview: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "meta": self.meta,
            "preview": self.preview,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "LogEntry":
        return LogEntry(
            timestamp=data.get("timestamp", ""),
            event_type=data.get("event_type", ""),
            meta=data.get("meta", {}) or {},
            preview=data.get("preview", "") or "",
        )


class EncryptedLogStore:
    def __init__(self, path: Path | None = None):
        self.path = path or DEFAULT_LOG_FILE

    def _fernet(self, password: str) -> Fernet:
        key = _derive_key_from_password(password)
        return Fernet(key)

    def load_logs(self, password: str) -> List[LogEntry]:
        """
        Decrypt and return the list of LogEntry objects.

        If the log file does not exist, returns an empty list.
        If the password is wrong or file is corrupted, raises ValueError.
        """
        if not self.path.exists():
            return []

        f = self._fernet(password)
        token = self.path.read_bytes()
        try:
            data = f.decrypt(token)
        except InvalidToken as e:
            raise ValueError("Incorrect password or corrupted log file.") from e

        try:
            raw = json.loads(data.decode("utf-8"))
        except json.JSONDecodeError:
            return []

        if not isinstance(raw, list):
            return []

        entries: List[LogEntry] = []
        for item in raw:
            if isinstance(item, dict):
                entries.append(LogEntry.from_dict(item))
        return entries

    def save_logs(self, entries: List[LogEntry], password: str) -> None:
        """
        Encrypt and write the given list of LogEntry objects to disk.
        """
        f = self._fernet(password)
        raw = [e.to_dict() for e in entries]
        data = json.dumps(raw, ensure_ascii=False, indent=2).encode("utf-8")
        token = f.encrypt(data)
        self.path.write_bytes(token)

    def append_log(self, entry: LogEntry, password: str) -> None:
        """
        Append a new log entry and rewrite the encrypted log file.
        """
        logs = self.load_logs(password)
        logs.append(entry)
        self.save_logs(logs, password)

    @staticmethod
    def create_entry(event_type: str, meta: Dict[str, Any], preview: str) -> LogEntry:
        return LogEntry(
            timestamp=datetime.utcnow().isoformat(timespec="seconds") + "Z",
            event_type=event_type,
            meta=meta,
            preview=preview,
        )

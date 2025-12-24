# utils.py
"""
Small utilities for environment variables and credential paths.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def env(name: str, default=None):
    """Get an environment variable with an optional default."""
    return os.getenv(name, default)


def get_credentials_path() -> str | None:
    """
    Return the path to the Google OAuth credentials file if it exists,
    otherwise return None.
    """
    p = env("GOOGLE_OAUTH_CREDENTIALS")
    if p:
        ps = Path(p)
        if ps.exists():
            return str(ps)
    return None

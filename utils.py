# utils.py
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

def env(name, default=None):
    return os.getenv(name, default)

def get_credentials_path():
    p = env('GOOGLE_OAUTH_CREDENTIALS')
    if p:
        ps = Path(p)
        if ps.exists():
            return str(ps)
    return None

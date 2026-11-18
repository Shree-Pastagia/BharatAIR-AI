"""Secure local configuration for the XKDR API."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def get_xkdr_api_key() -> str:
    """Return the locally configured key without ever logging it."""
    key = os.getenv("XKDR_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "XKDR_API_KEY is not configured. Copy .env.example to .env and add "
            "your personal key from https://airquality.xkdr.org/signup."
        )
    return key

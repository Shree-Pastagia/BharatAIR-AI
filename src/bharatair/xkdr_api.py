"""Small authenticated client for the XKDR India Air Quality API."""

from __future__ import annotations

from typing import Any

import requests

from .config import get_xkdr_api_key


BASE_URL = "https://airquality.xkdr.org"


def get_json(endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fetch one JSON endpoint. Credentials are sent only as an auth header."""
    path = endpoint.lstrip("/")
    response = requests.get(
        f"{BASE_URL}/{path}",
        headers={"Authorization": f"Bearer {get_xkdr_api_key()}"},
        params=params,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()

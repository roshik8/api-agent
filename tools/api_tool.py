import json
import os
from typing import Any, Optional

import httpx
from langchain_core.tools import tool

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TIMEOUT = 10.0


def _format_response(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        data = response.text
    return json.dumps(data, ensure_ascii=False)


@tool
def create_user(name: str, email: Optional[str] = None) -> str:
    """Create a new user by sending name and optional email to the user API."""
    print(f"[TOOL] create_user called with name={name!r}, email={email!r}")
    url = f"{API_BASE_URL}/users"
    payload = {"name": name, "email": email or None}
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.post(url, json=payload)
    except httpx.RequestError:
        result = "API недоступен: не удалось подключиться к серверу."
        print(f"[TOOL] create_user returning {result!r}")
        return result
    if response.status_code in (404, 422):
        result = f"Ошибка {response.status_code}: {_format_response(response)}"
        print(f"[TOOL] create_user returning {result!r}")
        return result
    response.raise_for_status()
    result = _format_response(response)
    print(f"[TOOL] create_user returning {result!r}")
    return result


@tool
def get_user(user_id: int) -> str:
    """Fetch a user by id from the user API."""
    print(f"[TOOL] get_user called with user_id={user_id}")
    url = f"{API_BASE_URL}/users/{user_id}"
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(url)
    except httpx.RequestError:
        result = "API недоступен: не удалось подключиться к серверу."
        print(f"[TOOL] get_user returning {result!r}")
        return result
    if response.status_code in (404, 422):
        result = f"Ошибка {response.status_code}: {_format_response(response)}"
        print(f"[TOOL] get_user returning {result!r}")
        return result
    response.raise_for_status()
    result = _format_response(response)
    print(f"[TOOL] get_user returning {result!r}")
    return result


@tool
def update_user_status(user_id: int, status: str) -> str:
    """Update an existing user's status through the user API."""
    print(f"[TOOL] update_user_status called with user_id={user_id}, status={status!r}")
    url = f"{API_BASE_URL}/users/{user_id}"
    payload = {"status": status}
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.patch(url, json=payload)
    except httpx.RequestError:
        result = "API недоступен: не удалось подключиться к серверу."
        print(f"[TOOL] update_user_status returning {result!r}")
        return result
    if response.status_code in (404, 422):
        result = f"Ошибка {response.status_code}: {_format_response(response)}"
        print(f"[TOOL] update_user_status returning {result!r}")
        return result
    response.raise_for_status()
    result = _format_response(response)
    print(f"[TOOL] update_user_status returning {result!r}")
    return result


@tool
def list_users() -> str:
    """List all users and return count and status breakdown from the user API."""
    print("[TOOL] list_users called")
    url = f"{API_BASE_URL}/users"
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(url)
    except httpx.RequestError:
        result = "API недоступен: не удалось подключиться к серверу."
        print(f"[TOOL] list_users returning {result!r}")
        return result
    if response.status_code in (404, 422):
        result = f"Ошибка {response.status_code}: {_format_response(response)}"
        print(f"[TOOL] list_users returning {result!r}")
        return result
    response.raise_for_status()
    result = _format_response(response)
    print(f"[TOOL] list_users returning {result!r}")
    return result


TOOLS = [create_user, get_user, update_user_status, list_users]

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()


class Status(str, Enum):
    active = "active"
    inactive = "inactive"
    banned = "banned"


class User(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    status: Status
    created_at: str


class CreateUser(BaseModel):
    name: str = Field(..., min_length=1)
    email: Optional[str] = None


class UpdateStatus(BaseModel):
    status: Status


# In-memory storage
_users: Dict[int, User] = {}
_next_id: int = 1


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@app.get("/health")
def health():
    """Return service health status."""
    return {"status": "ok"}


@app.post("/users", response_model=User, status_code=201)
def create_user(payload: CreateUser):
    """Create a new user with status 'active' and current timestamp."""
    global _next_id
    user = User(
        id=_next_id,
        name=payload.name,
        email=payload.email,
        status=Status.active,
        created_at=_now_iso(),
    )
    _users[_next_id] = user
    _next_id += 1
    return user


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    """Retrieve a user by id. Returns 404 if not found."""
    user = _users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    return user


@app.patch("/users/{user_id}", response_model=User)
def patch_user_status(user_id: int, payload: UpdateStatus):
    """Update only the status of an existing user. Validates allowed statuses."""
    user = _users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    updated = user.copy(update={"status": payload.status})
    _users[user_id] = updated
    return updated


@app.get("/users")
def list_users():
    """Return all users and statistics: count and breakdown by status."""
    users_list: List[User] = list(_users.values())
    by_status = {s.value: 0 for s in Status}
    for u in users_list:
        by_status[u.status.value] += 1
    return {"users": users_list, "count": len(users_list), "by_status": by_status}

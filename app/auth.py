import hashlib
import secrets
from fastapi import Header, HTTPException
from .config import settings
from . import database


def generate_api_key() -> str:
    return f"{settings.api_key_prefix}{secrets.token_urlsafe(32)}"


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def get_current_user(authorization: str = Header()):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid Authorization header format")

    token = authorization[7:]
    token_hash = hash_api_key(token)

    async with database.pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, email, display_name, is_active FROM users WHERE api_key_hash = $1",
            token_hash,
        )

    if not user or not user["is_active"]:
        raise HTTPException(401, "Invalid or inactive API key")

    return dict(user)

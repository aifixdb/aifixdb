from fastapi import APIRouter, HTTPException, Depends
from ..auth import generate_api_key, hash_api_key, get_current_user
from .. import database
from ..schemas import RegisterRequest, RegisterResponse, RegenerateKeyResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(req: RegisterRequest):
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)

    async with database.pool.acquire() as conn:
        existing = await conn.fetchval(
            "SELECT 1 FROM users WHERE email = $1", req.email
        )
        if existing:
            raise HTTPException(409, "Email already registered")

        row = await conn.fetchrow(
            "INSERT INTO users (email, display_name, api_key_hash) VALUES ($1, $2, $3) RETURNING id",
            req.email,
            req.display_name,
            key_hash,
        )

    return RegisterResponse(user_id=row["id"], api_key=api_key)


@router.post("/regenerate-key", response_model=RegenerateKeyResponse)
async def regenerate_key(user=Depends(get_current_user)):
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)

    async with database.pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET api_key_hash = $1 WHERE id = $2",
            key_hash,
            user["id"],
        )

    return RegenerateKeyResponse(api_key=api_key)

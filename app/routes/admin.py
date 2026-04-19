from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from .. import database
from ..config import settings

router = APIRouter(prefix="/admin", tags=["admin"])


async def require_admin(authorization: str = Header()):
    if not settings.admin_token:
        raise HTTPException(503, "Admin token not configured")
    if authorization != f"Bearer {settings.admin_token}":
        raise HTTPException(403, "Invalid admin token")


@router.get("/users", dependencies=[Depends(require_admin)])
async def list_users():
    async with database.pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, email, display_name, is_active, created_at,
                      (SELECT COUNT(*) FROM problems WHERE submitted_by = users.id) as problem_count
               FROM users ORDER BY created_at DESC"""
        )
    return [
        {
            "id": str(r["id"]),
            "email": r["email"],
            "display_name": r["display_name"],
            "is_active": r["is_active"],
            "created_at": r["created_at"].isoformat(),
            "problem_count": r["problem_count"],
        }
        for r in rows
    ]


@router.post("/users/{user_id}/block", dependencies=[Depends(require_admin)])
async def block_user(user_id: UUID):
    async with database.pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE users SET is_active = false WHERE id = $1", user_id
        )
    if result == "UPDATE 0":
        raise HTTPException(404, "User not found")
    return {"message": "User blocked"}


@router.post("/users/{user_id}/unblock", dependencies=[Depends(require_admin)])
async def unblock_user(user_id: UUID):
    async with database.pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE users SET is_active = true WHERE id = $1", user_id
        )
    if result == "UPDATE 0":
        raise HTTPException(404, "User not found")
    return {"message": "User unblocked"}


@router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(user_id: UUID):
    async with database.pool.acquire() as conn:
        await conn.execute("DELETE FROM votes WHERE user_id = $1", user_id)
        await conn.execute(
            "UPDATE problems SET submitted_by = NULL WHERE submitted_by = $1", user_id
        )
        result = await conn.execute("DELETE FROM users WHERE id = $1", user_id)
    if result == "DELETE 0":
        raise HTTPException(404, "User not found")
    return {"message": "User deleted"}


@router.delete("/problems/{problem_id}", dependencies=[Depends(require_admin)])
async def delete_problem(problem_id: UUID):
    async with database.pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM votes WHERE problem_id = $1", problem_id
        )
        result = await conn.execute(
            "DELETE FROM problems WHERE id = $1", problem_id
        )
    if result == "DELETE 0":
        raise HTTPException(404, "Problem not found")
    return {"message": "Problem deleted"}

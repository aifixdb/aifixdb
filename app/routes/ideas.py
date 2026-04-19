from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from ..auth import get_current_user
from .. import database

router = APIRouter(prefix="/ideas", tags=["ideas"])


class IdeaCreate(BaseModel):
    title: str = Field(max_length=300)
    description: str | None = None


class IdeaVote(BaseModel):
    vote: int = Field(ge=-1, le=1)


@router.post("", status_code=201)
async def create_idea(idea: IdeaCreate, user=Depends(get_current_user)):
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO ideas (title, description, submitted_by) VALUES ($1, $2, $3) RETURNING id, title",
            idea.title, idea.description, user["id"],
        )
    return {"id": str(row["id"]), "title": row["title"], "message": "Idea submitted."}


@router.get("")
async def list_ideas(
    sort: str = "votes",
    limit: int = Query(default=50, le=100),
):
    order = "(votes_up - votes_down) DESC" if sort == "votes" else "created_at DESC"

    async with database.pool.acquire() as conn:
        rows = await conn.fetch(
            f"""SELECT i.id, i.title, i.description, i.status,
                       (i.votes_up - i.votes_down) as votes,
                       u.display_name as submitted_by,
                       i.created_at
                FROM ideas i
                LEFT JOIN users u ON i.submitted_by = u.id
                ORDER BY {order}
                LIMIT $1""",
            limit,
        )

    return [
        {
            "id": str(r["id"]),
            "title": r["title"],
            "description": r["description"],
            "status": r["status"],
            "votes": r["votes"],
            "submitted_by": r["submitted_by"],
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]


@router.post("/{idea_id}/vote")
async def vote_idea(idea_id: UUID, req: IdeaVote, user=Depends(get_current_user)):
    async with database.pool.acquire() as conn:
        exists = await conn.fetchval("SELECT 1 FROM ideas WHERE id = $1", idea_id)
        if not exists:
            raise HTTPException(404, "Idea not found")

        if req.vote == 0:
            old = await conn.fetchrow(
                "DELETE FROM idea_votes WHERE idea_id = $1 AND user_id = $2 RETURNING vote_type",
                idea_id, user["id"],
            )
            if old:
                col = "votes_up" if old["vote_type"] == 1 else "votes_down"
                await conn.execute(
                    f"UPDATE ideas SET {col} = {col} - 1 WHERE id = $1", idea_id
                )
        else:
            old = await conn.fetchrow(
                "SELECT vote_type FROM idea_votes WHERE idea_id = $1 AND user_id = $2",
                idea_id, user["id"],
            )
            if old:
                if old["vote_type"] != req.vote:
                    await conn.execute(
                        "UPDATE idea_votes SET vote_type = $1 WHERE idea_id = $2 AND user_id = $3",
                        req.vote, idea_id, user["id"],
                    )
                    if req.vote == 1:
                        await conn.execute(
                            "UPDATE ideas SET votes_up = votes_up + 1, votes_down = votes_down - 1 WHERE id = $1",
                            idea_id,
                        )
                    else:
                        await conn.execute(
                            "UPDATE ideas SET votes_down = votes_down + 1, votes_up = votes_up - 1 WHERE id = $1",
                            idea_id,
                        )
            else:
                await conn.execute(
                    "INSERT INTO idea_votes (idea_id, user_id, vote_type) VALUES ($1, $2, $3)",
                    idea_id, user["id"], req.vote,
                )
                col = "votes_up" if req.vote == 1 else "votes_down"
                await conn.execute(
                    f"UPDATE ideas SET {col} = {col} + 1 WHERE id = $1", idea_id
                )

        votes = await conn.fetchval(
            "SELECT (votes_up - votes_down) FROM ideas WHERE id = $1", idea_id
        )

    return {"votes": votes}

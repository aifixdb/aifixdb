from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from ..auth import get_current_user
from .. import database
from ..schemas import VoteRequest, VoteResponse

router = APIRouter(tags=["votes"])


@router.post("/problems/{problem_id}/vote", response_model=VoteResponse)
async def vote(problem_id: UUID, req: VoteRequest, user=Depends(get_current_user)):
    async with database.pool.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT 1 FROM problems WHERE id = $1", problem_id
        )
        if not exists:
            raise HTTPException(404, "Problem not found")

        if req.vote == 0:
            old = await conn.fetchrow(
                "DELETE FROM votes WHERE problem_id = $1 AND user_id = $2 RETURNING vote_type",
                problem_id,
                user["id"],
            )
            if old:
                col = "votes_up" if old["vote_type"] == 1 else "votes_down"
                await conn.execute(
                    f"UPDATE problems SET {col} = {col} - 1 WHERE id = $1",
                    problem_id,
                )
        else:
            old = await conn.fetchrow(
                "SELECT vote_type FROM votes WHERE problem_id = $1 AND user_id = $2",
                problem_id,
                user["id"],
            )

            if old:
                if old["vote_type"] != req.vote:
                    await conn.execute(
                        "UPDATE votes SET vote_type = $1 WHERE problem_id = $2 AND user_id = $3",
                        req.vote,
                        problem_id,
                        user["id"],
                    )
                    if req.vote == 1:
                        await conn.execute(
                            "UPDATE problems SET votes_up = votes_up + 1, votes_down = votes_down - 1 WHERE id = $1",
                            problem_id,
                        )
                    else:
                        await conn.execute(
                            "UPDATE problems SET votes_down = votes_down + 1, votes_up = votes_up - 1 WHERE id = $1",
                            problem_id,
                        )
            else:
                await conn.execute(
                    "INSERT INTO votes (problem_id, user_id, vote_type) VALUES ($1, $2, $3)",
                    problem_id,
                    user["id"],
                    req.vote,
                )
                col = "votes_up" if req.vote == 1 else "votes_down"
                await conn.execute(
                    f"UPDATE problems SET {col} = {col} + 1 WHERE id = $1",
                    problem_id,
                )

        votes = await conn.fetchval(
            "SELECT (votes_up - votes_down) FROM problems WHERE id = $1",
            problem_id,
        )

    return VoteResponse(votes=votes)

import json
import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from ..auth import get_current_user
from .. import database
from ..schemas import (
    ProblemCreate,
    ProblemResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)

router = APIRouter(prefix="/problems", tags=["problems"])


@router.post("", status_code=201)
async def create_problem(problem: ProblemCreate, user=Depends(get_current_user)):
    env_json = json.dumps(problem.environment) if problem.environment else None

    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO problems (title, error_message, stack, context, solution, environment, submitted_by)
               VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7)
               RETURNING id, title""",
            problem.title,
            problem.error_message,
            problem.stack,
            problem.context,
            problem.solution,
            env_json,
            user["id"],
        )

    return {"id": str(row["id"]), "title": row["title"], "message": "Problem added."}


@router.get("/{problem_id}", response_model=ProblemResponse)
async def get_problem(problem_id: UUID):
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT p.id, p.title, p.error_message, p.stack, p.context, p.solution,
                      p.environment, u.display_name as submitted_by,
                      (p.votes_up - p.votes_down) as votes, p.created_at
               FROM problems p
               LEFT JOIN users u ON p.submitted_by = u.id
               WHERE p.id = $1""",
            problem_id,
        )

    if not row:
        raise HTTPException(404, "Problem not found")

    env = json.loads(row["environment"]) if row["environment"] else None

    return ProblemResponse(
        id=row["id"],
        title=row["title"],
        error_message=row["error_message"],
        stack=list(row["stack"]),
        context=row["context"],
        solution=row["solution"],
        environment=env,
        submitted_by=row["submitted_by"],
        votes=row["votes"],
        created_at=row["created_at"],
    )


@router.get("")
async def list_problems(
    q: str | None = None,
    stack: list[str] = Query(default=[]),
    sort: str = "newest",
    limit: int = Query(default=20, le=100),
    offset: int = 0,
):
    conditions = []
    params: list = []
    idx = 1

    if q:
        conditions.append(f"search_vector @@ plainto_tsquery('english', ${idx})")
        params.append(q)
        idx += 1

    if stack:
        conditions.append(f"stack && ${idx}")
        params.append(stack)
        idx += 1

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    if sort == "votes":
        order = "(votes_up - votes_down) DESC"
    elif q and sort == "relevance":
        order = f"ts_rank(search_vector, plainto_tsquery('english', $1)) DESC"
    else:
        order = "created_at DESC"

    count_params = list(params)
    params.extend([limit, offset])

    async with database.pool.acquire() as conn:
        rows = await conn.fetch(
            f"""SELECT id, title, stack, (votes_up - votes_down) as votes, created_at
                FROM problems {where}
                ORDER BY {order}
                LIMIT ${idx} OFFSET ${idx + 1}""",
            *params,
        )
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM problems {where}",
            *count_params,
        )

    return {
        "results": [
            {
                "id": str(r["id"]),
                "title": r["title"],
                "stack": list(r["stack"]),
                "votes": r["votes"],
                "created_at": r["created_at"].isoformat(),
            }
            for r in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/search", response_model=SearchResponse)
async def search_problems(req: SearchRequest):
    start = time.monotonic()

    conditions = []
    score_parts = []
    params: list = []
    idx = 1

    if req.error_text:
        conditions.append(
            f"(error_message IS NOT NULL AND similarity(error_message, ${idx}) > 0.05)"
        )
        score_parts.append(f"COALESCE(similarity(error_message, ${idx}), 0) * 3.0")
        params.append(req.error_text)
        idx += 1

    if req.stack:
        conditions.append(f"stack && ${idx}")
        score_parts.append(
            f"COALESCE((SELECT COUNT(*)::float FROM unnest(stack) s WHERE s = ANY(${idx})), 0) * 2.0"
        )
        params.append(req.stack)
        idx += 1

    if req.context:
        conditions.append(
            f"search_vector @@ plainto_tsquery('english', ${idx})"
        )
        score_parts.append(
            f"ts_rank(search_vector, plainto_tsquery('english', ${idx})) * 1.0"
        )
        params.append(req.context)
        idx += 1

    if not conditions:
        raise HTTPException(
            400, "At least one search field required (error_text, stack, or context)"
        )

    score_expr = " + ".join(score_parts)
    where = " OR ".join(conditions)
    params.append(req.limit)

    async with database.pool.acquire() as conn:
        rows = await conn.fetch(
            f"""SELECT id, title, error_message, stack, solution,
                       ({score_expr}) as relevance_score,
                       (votes_up - votes_down) as votes
                FROM problems
                WHERE {where}
                ORDER BY relevance_score DESC
                LIMIT ${idx}""",
            *params,
        )

    elapsed = (time.monotonic() - start) * 1000

    return SearchResponse(
        results=[
            SearchResult(
                id=r["id"],
                title=r["title"],
                error_message=r["error_message"],
                stack=list(r["stack"]),
                solution=r["solution"],
                relevance_score=round(float(r["relevance_score"]), 3),
                votes=r["votes"],
            )
            for r in rows
        ],
        total=len(rows),
        query_time_ms=round(elapsed, 2),
    )

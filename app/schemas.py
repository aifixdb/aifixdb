from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


# --- Auth ---


class RegisterRequest(BaseModel):
    email: str
    display_name: str | None = None


class RegisterResponse(BaseModel):
    user_id: UUID
    api_key: str
    message: str = "API key generated. Save it — you cannot retrieve it later."


class RegenerateKeyResponse(BaseModel):
    api_key: str
    message: str = "New key active. Old key revoked."


# --- Problems ---


class ProblemCreate(BaseModel):
    title: str = Field(max_length=300)
    error_message: str | None = None
    stack: list[str] = []
    context: str | None = None
    solution: str
    environment: dict | None = None


class ProblemResponse(BaseModel):
    id: UUID
    title: str
    error_message: str | None
    stack: list[str]
    context: str | None
    solution: str
    environment: dict | None
    submitted_by: str | None
    votes: int
    created_at: datetime


# --- Search ---


class SearchRequest(BaseModel):
    error_text: str | None = None
    stack: list[str] | None = None
    context: str | None = None
    limit: int = Field(default=5, le=50)


class SearchResult(BaseModel):
    id: UUID
    title: str
    error_message: str | None
    stack: list[str]
    solution: str
    relevance_score: float
    votes: int


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
    query_time_ms: float


# --- Votes ---


class VoteRequest(BaseModel):
    vote: int = Field(ge=-1, le=1)


class VoteResponse(BaseModel):
    votes: int

import secrets
import time
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from ..auth import generate_api_key, hash_api_key, get_current_user
from .. import database
from ..config import settings
from ..schemas import RegisterRequest, RegenerateKeyResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Anti-bot: max 3 registrations per hour per IP
_register_hits: dict[str, list[float]] = defaultdict(list)

DISPOSABLE_DOMAINS = {
    "tempmail.com", "temp-mail.org", "guerrillamail.com", "guerrillamail.net",
    "mailinator.com", "yopmail.com", "throwaway.email", "trashmail.com",
    "10minutemail.com", "minutemail.com", "tempail.com", "fakeinbox.com",
    "sharklasers.com", "guerrillamailblock.com", "grr.la", "dispostable.com",
    "maildrop.cc", "mailnesia.com", "tempr.email", "discard.email",
    "mailcatch.com", "temp-mail.io", "emailondeck.com", "33mail.com",
    "getnada.com", "mohmal.com", "tmpmail.net", "tmpmail.org",
}


def _check_register_rate(ip: str):
    now = time.monotonic()
    hits = _register_hits[ip]
    _register_hits[ip] = [t for t in hits if now - t < 3600]
    if len(_register_hits[ip]) >= 3:
        raise HTTPException(429, "Too many registrations. Try again in 1 hour.")
    _register_hits[ip].append(now)


def _check_disposable_email(email: str):
    domain = email.rsplit("@", 1)[-1].lower()
    if domain in DISPOSABLE_DOMAINS:
        raise HTTPException(400, "Disposable email addresses are not allowed.")


@router.post("/register", status_code=201)
async def register(req: RegisterRequest, request: Request):
    ip = request.headers.get("cf-connecting-ip") or request.client.host

    _check_register_rate(ip)
    _check_disposable_email(req.email)

    verify_token = secrets.token_urlsafe(32)

    async with database.pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id, is_active, verify_token FROM users WHERE email = $1", req.email
        )

        if existing:
            if existing["is_active"]:
                raise HTTPException(409, "Email already registered and verified.")
            # Resend verification
            verify_token = secrets.token_urlsafe(32)
            await conn.execute(
                "UPDATE users SET verify_token = $1 WHERE id = $2",
                verify_token, existing["id"],
            )
        else:
            # Create inactive user (no API key yet)
            await conn.execute(
                "INSERT INTO users (email, display_name, api_key_hash, is_active, verify_token) VALUES ($1, $2, $3, false, $4)",
                req.email,
                req.display_name,
                "pending",  # placeholder, real key generated on verify
                verify_token,
            )

    # Send verification email
    try:
        from ..email import send_verification_email
        send_verification_email(req.email, verify_token)
    except Exception as e:
        raise HTTPException(500, f"Failed to send verification email: {e}")

    return {"message": "Verification email sent. Check your inbox."}


@router.get("/verify", response_class=HTMLResponse)
async def verify_email(token: str):
    async with database.pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, email, is_active FROM users WHERE verify_token = $1",
            token,
        )

        if not user:
            return HTMLResponse(_verify_page("Invalid or expired verification link.", None), status_code=400)

        if user["is_active"]:
            return HTMLResponse(_verify_page("Email already verified.", None))

        # Generate real API key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)

        await conn.execute(
            "UPDATE users SET is_active = true, api_key_hash = $1, verify_token = NULL WHERE id = $2",
            key_hash, user["id"],
        )

    return HTMLResponse(_verify_page("Email verified!", api_key))


def _verify_page(message: str, api_key: str | None) -> str:
    key_html = ""
    if api_key:
        key_html = f"""
        <div style="background:#0a0a0a;border:1px solid #333;border-radius:6px;padding:1rem;margin:1rem 0">
            <div style="color:#888;font-size:13px;margin-bottom:4px">Your API key:</div>
            <div style="font-family:monospace;color:#7eb8ff;font-size:1.1rem;word-break:break-all;user-select:all">{api_key}</div>
        </div>
        <p style="color:#e8a83a;font-size:13px">Save this key now — you cannot retrieve it later.</p>
        """

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>aifixdb — Verification</title></head>
<body style="font-family:sans-serif;background:#0a0a0a;color:#e0e0e0;display:flex;justify-content:center;padding:3rem 1rem">
<div style="max-width:440px;width:100%;text-align:center">
    <h1 style="color:#7eb8ff;font-size:1.8rem">aifixdb</h1>
    <p style="font-size:1.1rem;margin:1rem 0">{message}</p>
    {key_html}
    <a href="/" style="color:#7eb8ff;font-size:14px">Back to aifixdb</a>
</div></body></html>"""


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

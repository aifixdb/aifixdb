import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .config import settings


def send_verification_email(to_email: str, token: str):
    """Send verification email via SES."""
    verify_url = f"{settings.public_url}/api/v1/auth/verify?token={token}"

    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:2rem;background:#0a0a0a;color:#e0e0e0;border-radius:8px">
        <h2 style="color:#7eb8ff;margin-bottom:1rem">aifixdb</h2>
        <p>Click the button below to verify your email and get your API key:</p>
        <p style="text-align:center;margin:2rem 0">
            <a href="{verify_url}" style="background:#7eb8ff;color:#0a0a0a;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600">
                Verify Email
            </a>
        </p>
        <p style="color:#888;font-size:13px">Or copy this link: {verify_url}</p>
        <p style="color:#555;font-size:12px;margin-top:2rem">If you didn't register at aifixdb, ignore this email.</p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "aifixdb — Verify your email"
    msg["From"] = settings.smtp_sender
    msg["To"] = to_email
    msg.attach(MIMEText(f"Verify your email: {verify_url}", "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_pass)
        server.sendmail(settings.smtp_sender, to_email, msg.as_string())

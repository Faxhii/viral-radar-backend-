from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class EmailSchema(BaseModel):
    email: List[EmailStr]

conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', ''),
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', ''),
    MAIL_FROM = os.getenv('MAIL_FROM', 'noreply@viralcreator.com'),
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587)),
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

async def send_login_notification(email: str):
    """
    Sends a login notification email to the user.
    """
    if not os.getenv('MAIL_USERNAME') or not os.getenv('MAIL_PASSWORD'):
        print("Email credentials not set. Skipping email sending.")
        return

    html = f"""
    <p>Hello,</p>
    <p>A new sign-in to your Viral Creator account was detected.</p>
    <p>If this was you, you can ignore this email.</p>
    <br>
    <p>Regards,</p>
    <p>Viral Creator Team</p>
    """

    message = MessageSchema(
        subject="New Sign-in Detected",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        print(f"Login notification sent to {email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

async def send_verification_email(email: str, token: str):
    """
    Sends a verification email with a link to verify the account.
    """
    if not os.getenv('MAIL_USERNAME') or not os.getenv('MAIL_PASSWORD'):
        print("Email credentials not set. Skipping verification email.")
        return

    # Assuming backend runs on port 8000, modify this URL based on your deployment
    # Ideally should point to Frontend URL which then calls Backend
    # For now, let's point to a backend endpoint which redirects or shows success
    # verification_link = f"http://localhost:8000/auth/verify?token={token}"
    
    # Better approach: Point to FRONTEND
    # If using local dev: http://localhost:3000/verify?token=...
    verification_link = f"http://localhost:3000/verify?token={token}"

    html = f"""
    <p>Welcome to Viral Creator!</p>
    <p>Please click the link below to verify your email address and activate your account:</p>
    <br>
    <a href="{verification_link}" style="padding: 10px 20px; background-color: #a855f7; color: white; text-decoration: none; border-radius: 5px;">Verify Email</a>
    <br><br>
    <p>Or copy this link: {verification_link}</p>
    <p>If you did not sign up, please ignore this email.</p>
    """

    message = MessageSchema(
        subject="Verify your Viral Creator Account",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        print(f"Verification email sent to {email}")
    except Exception as e:
        print(f"Failed to send verification email: {e}")


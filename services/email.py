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

async def send_verification_email(email: str, otp: str):
    """
    Sends a verification email with the OTP to verify the account.
    """
    if not os.getenv('MAIL_USERNAME') or not os.getenv('MAIL_PASSWORD'):
        print("Email credentials not set. Skipping verification email.")
        return

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>Verify your Viral Creator Account</h2>
        <p>Welcome to Viral Creator!</p>
        <p>Use the following verification code to activate your account:</p>
        <div style="background-color: #f3f4f6; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
            <h1 style="color: #a855f7; letter-spacing: 5px; margin: 0;">{otp}</h1>
        </div>
        <p>This code will expire in 10 minutes.</p>
        <p>If you did not sign up, please ignore this email.</p>
    </div>
    """

    message = MessageSchema(
        subject="Your Verification Code - Viral Creator",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        print(f"Verification OTP sent to {email}")
    except Exception as e:
        print(f"Failed to send verification email: {e}")


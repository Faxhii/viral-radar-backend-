import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv('RESEND_API_KEY')

async def send_login_notification(email: str):
    """
    Sends a login notification email to the user.
    """
    if not resend.api_key:
        print("Resend API Key not set. Skipping email sending.")
        return

    html = f"""
    <p>Hello,</p>
    <p>A new sign-in to your Viral Creator account was detected.</p>
    <p>If this was you, you can ignore this email.</p>
    <br>
    <p>Regards,</p>
    <p>Viral Creator Team</p>
    """

    try:
        r = resend.Emails.send({
            "from": "Viral Creator <onboarding@resend.dev>",
            "to": email,
            "subject": "New Sign-in Detected",
            "html": html
        })
        print(f"Login notification sent to {email}. ID: {r.get('id')}")
    except Exception as e:
        print(f"Failed to send email: {e}")

async def send_verification_email(email: str, otp: str):
    """
    Sends a verification email with the OTP to verify the account.
    """
    if not resend.api_key:
        print("Resend API Key not set. Skipping verification email.")
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

    try:
        r = resend.Emails.send({
            "from": "Viral Creator <onboarding@resend.dev>",
            "to": email,
            "subject": "Your Verification Code - Viral Creator",
            "html": html
        })
        print(f"Verification OTP sent to {email}. ID: {r.get('id')}")
    except Exception as e:
        print(f"Failed to send verification email: {e}")


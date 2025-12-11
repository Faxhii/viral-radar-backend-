import asyncio
import os
from dotenv import load_dotenv
from services.email import send_login_notification

load_dotenv()

async def test_email():
    print("Testing email sending...")
    email = input("Enter recipient email: ")
    
    print(f"Sending test email to {email} using credentials:")
    print(f"User: {os.getenv('MAIL_USERNAME')}")
    print(f"Server: {os.getenv('MAIL_SERVER')}")
    
    try:
        await send_login_notification(email)
        print("Test complete. Check your inbox.")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_email())

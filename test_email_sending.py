import asyncio
import os
from dotenv import load_dotenv
from services.email import send_login_notification

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

async def test_email():
    print(f"Loading .env from: {env_path}")
    print("Testing email sending...")
    
    mail_user = os.getenv('MAIL_USERNAME')
    mail_server = os.getenv('MAIL_SERVER')
    
    if not mail_user or not mail_server:
        print("\n[ERROR] Missing email credentials in .env file!")
        print("Please ensure your backend/.env file contains:")
        print("MAIL_USERNAME=your_email@gmail.com")
        print("MAIL_PASSWORD=your_app_password")
        print("MAIL_FROM=your_email@gmail.com")
        print("MAIL_PORT=587")
        print("MAIL_SERVER=smtp.gmail.com")
        return

    email = input("Enter recipient email: ")
    
    print(f"Sending test email to {email} using credentials:")
    print(f"User: {mail_user}")
    print(f"Server: {mail_server}")
    
    try:
        await send_login_notification(email)
        print("Test complete. Check your inbox.")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_email())

from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from models import User, PlanType
import hmac
import hashlib
import json
import os

router = APIRouter(
    prefix="/api/payments",
    tags=["payments"]
)

# You should set this in your .env file
LEMON_SQUEEZY_WEBHOOK_SECRET = os.getenv("LEMON_SQUEEZY_WEBHOOK_SECRET", "your-secret-here")

@router.post("/webhook")
async def lemon_squeezy_webhook(request: Request, x_signature: str = Header(None)):
    """
    Handle Lemon Squeezy webhooks for subscription creation/updates.
    """
    if not x_signature:
        raise HTTPException(status_code=401, detail="No signature header")

    # Get raw body
    raw_body = await request.body()
    
    # Verify signature
    # HMAC SHA256 of the raw body using the secret
    digest = hmac.new(
        LEMON_SQUEEZY_WEBHOOK_SECRET.encode('utf-8'),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(digest, x_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse JSON
    data = json.loads(raw_body)
    event_name = data.get("meta", {}).get("event_name")
    payload = data.get("data", {})
    attributes = payload.get("attributes", {})
    
    print(f"Received Webhook: {event_name}")

    if event_name in ["subscription_created", "subscription_updated"]:
        # Extract user info
        # We assume the 'custom_data' field in checkout contained the user_id
        # OR we match by email. Email is safer if custom_data isn't guaranteed.
        email = attributes.get("user_email")
        customer_id = attributes.get("customer_id")
        subscription_id = payload.get("id")
        status = attributes.get("status") # active, past_due, etc.
        
        print(f"Processing subscription for email: {email}, Status: {status}")

        if not email:
            print("No email found in webhook")
            return {"status": "ignored", "reason": "no_email"}

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.lemon_squeezy_customer_id = str(customer_id)
                user.lemon_squeezy_subscription_id = str(subscription_id)
                
                if status == "active":
                    user.plan = PlanType.PRO
                    print(f"Upgraded user {email} to PRO")
                elif status in ["expired", "cancelled", "unpaid"]:
                    user.plan = PlanType.FREE
                    print(f"Downgraded user {email} to FREE")
                
                db.commit()
            else:
                print(f"User not found for email: {email}")
        except Exception as e:
            print(f"Error processing webhook: {e}")
        finally:
            db.close()

    return {"status": "received"}

@router.post("/simulate")
async def simulate_payment(
    email: str, 
    plan: PlanType, 
    secret: str,
    db: Session = Depends(get_db)
):
    """
    DEBUG ONLY: Simulate a payment webhook to upgrade a user.
    """
    # Simple security check
    if secret != LEMON_SQUEEZY_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
        
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.plan = plan
    # Set dummy IDs for the UI to look "active"
    user.lemon_squeezy_customer_id = "test_cust_123"
    user.lemon_squeezy_subscription_id = "test_sub_123"
    
    db.commit()
    return {"status": "success", "message": f"User {email} upgraded to {plan}"}

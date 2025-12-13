from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, PlanType
from pydantic import BaseModel
import razorpay
import os
import hmac
import hashlib
import utils
import time

router = APIRouter(
    prefix="/api/razorpay",
    tags=["razorpay"]
)

# Initialize Razorpay Client
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    print("Warning: Razorpay keys not found in environment variables")
    # For dev safety, we can initialize with dummy if not present to avoid crash on import
    # but calls will fail
    client = razorpay.Client(auth=("dummy", "dummy"))
else:
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

class OrderCreateRequest(BaseModel):
    plan_id: str  # e.g., "pro-monthly"
    amount: int   # Amount in paise (e.g., 2900 for ₹29.00)
    currency: str = "INR"

class PaymentVerificationRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str
    plan: str # "pro"

@router.post("/order")
async def create_order(
    request: OrderCreateRequest,
    current_user: User = Depends(utils.get_current_user)
):
    """
    Create a Razorpay order.
    Amount should be in paise.
    """
    try:
        # Create a unique receipt ID
        receipt = f"rcpt_{current_user.id}_{int(time.time())}"
        
        data = {
            "amount": request.amount,
            "currency": request.currency,
            "receipt": receipt,
            "notes": {
                "plan": request.plan_id,
                "user_id": str(current_user.id),
                "email": current_user.email
            }
        }
        order = client.order.create(data=data)
        return order
    except Exception as e:
        print(f"Razorpay Order Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/verify")
async def verify_payment(
    request: PaymentVerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(utils.get_current_user)
):
    """
    Verify Razorpay payment signature and upgrade user.
    """
    # Verify signature
    params_dict = {
        'razorpay_order_id': request.razorpay_order_id,
        'razorpay_payment_id': request.razorpay_payment_id,
        'razorpay_signature': request.razorpay_signature
    }

    try:
        client.utility.verify_payment_signature(params_dict)
    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment verification failed"
        )

    # Verification successful
    try:
        # Update user plan
        # In a real app, verify details from order_id against DB or Razorpay API
        
        if request.plan == 'pro':
            current_user.plan = PlanType.PRO
            current_user.credits += 40.0 # Add 40 credits
        elif request.plan == 'agency':
            current_user.plan = PlanType.AGENCY
            current_user.credits += 100.0 # Add 100 credits
        elif request.plan == 'starter':
            # Starter Pack: Just add credits, don't change plan type (or keep as is)
            current_user.credits += 15.0 # Add 15 credits
            
        db.commit()
        db.refresh(current_user)
            
        return {"status": "success", "message": f"Payment verified. Upgraded to {request.plan} and credits added."}
            
    except Exception as e:
        print(f"Error updating user plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing subscription update"
        )



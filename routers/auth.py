from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import schemas, models, utils, database

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    try:
        print(f"Registering user: {user.email}")
        db_user = db.query(models.User).filter(models.User.email == user.email).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = utils.get_password_hash(user.password)
        new_user = models.User(
            email=user.email,
            hashed_password=hashed_password,
            full_name=user.full_name,
            primary_platform=user.primary_platform,
            credits=3.0 # Default free credits
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

@router.post("/google")
def google_auth(token_data: schemas.GoogleToken, db: Session = Depends(database.get_db)):
    try:
        # Verify the token
        # Specify the CLIENT_ID of the app that accesses the backend:
        # id_info = id_token.verify_oauth2_token(token_data.token, google_requests.Request(), CLIENT_ID)
        # For now, we accept any valid Google token (since we verify the email/sub)
        id_info = id_token.verify_oauth2_token(token_data.token, google_requests.Request())

        email = id_info['email']
        sub = id_info['sub']
        picture = id_info.get('picture')
        name = id_info.get('name')

        print(f"Google Auth: {email} ({sub})")

        # Check if user exists
        user = db.query(models.User).filter(models.User.email == email).first()
        
        if not user:
            # Create new user
            print("Creating new Google user")
            user = models.User(
                email=email,
                full_name=name,
                google_sub=sub,
                picture=picture,
                credits=3.0, # Default free credits
                plan=models.PlanType.FREE
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Link Google account if not linked
            if not user.google_sub:
                user.google_sub = sub
            if not user.picture:
                user.picture = picture
            db.commit()
            db.refresh(user)

        # Create access token
        access_token_expires = timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = utils.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    except ValueError as e:
        print(f"Token verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid Google token")

@router.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not user.hashed_password or not utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserOut)
async def read_users_me(current_user: models.User = Depends(utils.get_current_user)):
    return current_user

@router.put("/me", response_model=schemas.UserOut)
async def update_user_me(
    user_update: schemas.UserUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(utils.get_current_user)
):
    # Update fields if provided
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.primary_platform is not None:
        current_user.primary_platform = user_update.primary_platform
    if user_update.primary_category is not None:
        current_user.primary_category = user_update.primary_category
    if user_update.avg_length is not None:
        current_user.avg_length = user_update.avg_length
        
    db.commit()
    db.refresh(current_user)
    return current_user

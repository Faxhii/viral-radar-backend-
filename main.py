from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, SessionLocal, get_db
from .routers import videos, auth, payments
from .models import User, PlanType, Video, Analysis, Review
from .schemas import ReviewCreate, ReviewOut
from typing import List
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
import os

# Create tables (for MVP, we can just do this on startup)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ViralRadar.in API")

# Mount uploads directory
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev to fix CORS issues
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def read_root():
    return {"message": "Welcome to ViralRadar.in API"}

@app.get("/reviews", response_model=List[ReviewOut])
def get_reviews(db: Session = Depends(get_db)):
    return db.query(Review).filter(Review.is_approved == True).order_by(Review.created_at.desc()).all()

@app.post("/reviews", response_model=ReviewOut)
def create_review(review: ReviewCreate, db: Session = Depends(get_db)):
    db_review = Review(**review.dict())
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

app.include_router(auth.router)
app.include_router(videos.router)
app.include_router(payments.router)

from sqladmin import Admin, ModelView

# Admin Views
class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.plan, User.is_superuser, User.created_at]
    can_create = True
    can_edit = True
    can_delete = True
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"

class VideoAdmin(ModelView, model=Video):
    column_list = [Video.id, Video.owner, Video.source_type, Video.created_at]
    icon = "fa-solid fa-video"

class AnalysisAdmin(ModelView, model=Analysis):
    column_list = [Analysis.id, Analysis.status, Analysis.overall_score, Analysis.created_at]
    icon = "fa-solid fa-chart-line"

class ReviewAdmin(ModelView, model=Review):
    column_list = [Review.id, Review.name, Review.rating, Review.is_approved, Review.created_at]
    icon = "fa-solid fa-star"

# Setup Admin
admin = Admin(app, engine)
admin.add_view(UserAdmin)
admin.add_view(VideoAdmin)
admin.add_view(AnalysisAdmin)
admin.add_view(ReviewAdmin)

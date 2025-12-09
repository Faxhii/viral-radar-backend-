from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal, get_db
from routers import videos, auth, payments
from models import User, PlanType, Video, Analysis, Review
from schemas import ReviewCreate, ReviewOut
from typing import List
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
import os

# Create tables (for MVP, we can just do this on startup)
Base.metadata.create_all(bind=engine)

from sqlalchemy import text
def run_migrations():
    try:
        with engine.connect() as connection:
            connection.execution_options(isolation_level="AUTOCOMMIT")
            print("Checking for schema migrations...")
            # Check for credits column
            try:
                result = connection.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='credits'"))
                if not result.fetchone():
                    print("Migrating: Adding 'credits' column to users table...")
                    connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS credits FLOAT DEFAULT 3.0"))
                    print("Migration successful: 'credits' column added.")
                else:
                    print("Schema check: 'credits' column exists.")
            except Exception as e:
                print(f"Migration warning (credits): {e}")
                
    except Exception as e:
        print(f"Migration failed: {e}")

run_migrations()

app = FastAPI(title="ViralRadar.in API")

# Mount uploads directory
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Configure CORS
origins = [
    "http://localhost:3000",
    "https://viral-radar.vercel.app",
    "https://viral-radar-backend.up.railway.app",
    "https://viralradar.in",
    "https://www.viralradar.in"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/debug/migrate")
def force_migrate(db: Session = Depends(get_db)):
    from sqlalchemy import text
    try:
        # PostgreSQL syntax for adding columns if they don't exist
        db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_sub VARCHAR UNIQUE;"))
        db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS picture VARCHAR;"))
        db.commit()
        return {"status": "success", "message": "Migration run successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/")
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
    category = "Accounts"

class VideoAdmin(ModelView, model=Video):
    column_list = [Video.id, Video.owner, Video.source_type, Video.created_at]
    icon = "fa-solid fa-video"
    category = "Content"

class AnalysisAdmin(ModelView, model=Analysis):
    column_list = [Analysis.id, Analysis.status, Analysis.overall_score, Analysis.created_at]
    icon = "fa-solid fa-chart-line"
    category = "Content"

class ReviewAdmin(ModelView, model=Review):
    column_list = [Review.id, Review.name, Review.rating, Review.is_approved, Review.created_at]
    icon = "fa-solid fa-star"
    category = "Content"

# Setup Admin Authentication
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        # Get credentials from env or use defaults
        expected_username = os.getenv("ADMIN_USERNAME", "admin")
        expected_password = os.getenv("ADMIN_PASSWORD", "change_this_password")

        if username == expected_username and password == expected_password:
            request.session.update({"token": "valid_token"})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        return True

authentication_backend = AdminAuth(secret_key=os.getenv("SECRET_KEY", "supersecretkey"))

# Setup Admin
admin = Admin(app, engine, authentication_backend=authentication_backend, title="ViralRadar Admin")
admin.add_view(UserAdmin)
admin.add_view(VideoAdmin)
admin.add_view(AnalysisAdmin)
admin.add_view(ReviewAdmin)

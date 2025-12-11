from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base

class PlanType(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    AGENCY = "agency"

class AnalysisStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    plan = Column(Enum(PlanType), default=PlanType.FREE)
    credits = Column(Float, default=3.0)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Profile fields
    full_name = Column(String, nullable=True)
    primary_platform = Column(String, nullable=True)
    primary_category = Column(String, nullable=True)
    avg_length = Column(String, nullable=True)
    google_sub = Column(String, unique=True, nullable=True)
    picture = Column(String, nullable=True)
    
    # Payment fields
    lemon_squeezy_customer_id = Column(String, nullable=True)
    lemon_squeezy_subscription_id = Column(String, nullable=True)

    videos = relationship("Video", back_populates="owner")
    analyses = relationship("Analysis", back_populates="user")
    plan_usage = relationship("PlanUsage", back_populates="user", uselist=False)

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    source_type = Column(String) # "upload" or "link"
    source_url = Column(String, nullable=True)
    title = Column(String, nullable=True) # Original filename or video title
    storage_path = Column(String, nullable=True)
    script_content = Column(String, nullable=True)
    duration = Column(Integer, nullable=True) # in seconds
    platform_guess = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="videos")
    analyses = relationship("Analysis", back_populates="video")

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    video_id = Column(Integer, ForeignKey("videos.id"))
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.QUEUED)
    
    overall_score = Column(Integer, nullable=True)
    subscores = Column(JSON, nullable=True)
    insights = Column(JSON, nullable=True)
    optimized_assets = Column(JSON, nullable=True)
    checklist = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="analyses")
    video = relationship("Video", back_populates="analyses")

class PlanUsage(Base):
    __tablename__ = "plan_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))
    analyses_used = Column(Integer, default=0)
    
    user = relationship("User", back_populates="plan_usage")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    role = Column(String)
    content = Column(String)
    rating = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_approved = Column(Boolean, default=True) # Auto-approve for now

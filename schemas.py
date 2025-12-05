from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import PlanType, AnalysisStatus

# User Schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    full_name: Optional[str] = None
    primary_platform: Optional[str] = None

class UserLogin(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    primary_platform: Optional[str] = None
    primary_category: Optional[str] = None
    avg_length: Optional[str] = None

class UserOut(UserBase):
    id: int
    plan: PlanType
    created_at: datetime
    full_name: Optional[str]
    primary_platform: Optional[str]
    primary_category: Optional[str]
    avg_length: Optional[str]

    class Config:
        from_attributes = True

# Video Schemas
class VideoBase(BaseModel):
    source_url: Optional[str] = None

class VideoCreate(VideoBase):
    pass

class ScriptCreate(BaseModel):
    script_content: str
    platform: str
    category: str

class VideoOut(VideoBase):
    id: int
    user_id: int
    source_type: str
    duration: Optional[int]
    platform_guess: Optional[str]
    created_at: datetime
    
    # Analysis Data
    viral_score: Optional[int] = None
    status: Optional[AnalysisStatus] = None
    analysis_id: Optional[int] = None
    video_url: Optional[str] = None
    title: Optional[str] = None

    class Config:
        from_attributes = True

# Analysis Schemas
class AnalysisBase(BaseModel):
    pass

class AnalysisOut(AnalysisBase):
    id: int
    video_id: int
    status: AnalysisStatus
    overall_score: Optional[int]
    subscores: Optional[Dict[str, Any]]
    insights: Optional[Dict[str, Any]]
    optimized_assets: Optional[Dict[str, Any]]
    checklist: Optional[Dict[str, Any]]
    checklist: Optional[Dict[str, Any]]
    created_at: datetime
    video_url: Optional[str] = None
    source_type: Optional[str] = None
    script_content: Optional[str] = None
    duration: Optional[int] = None # Video duration in seconds

    class Config:
        from_attributes = True

# Review Schemas
class ReviewBase(BaseModel):
    name: str
    role: str
    content: str
    rating: int

class ReviewCreate(ReviewBase):
    pass

class ReviewOut(ReviewBase):
    id: int
    created_at: datetime
    is_approved: bool

    class Config:
        from_attributes = True

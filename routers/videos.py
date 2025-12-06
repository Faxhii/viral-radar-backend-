from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Response
from sqlalchemy.orm import Session
from typing import List
import shutil
import os
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from database import get_db, SessionLocal
from models import Video, Analysis, User, AnalysisStatus, PlanType
from schemas import VideoOut, VideoCreate, AnalysisOut, ScriptCreate
from services.video_processor import download_video, extract_audio, extract_frames
from services.gemini_analyzer import analyze_video_content, analyze_script_content
from dependencies import get_current_user

router = APIRouter(
    prefix="/api/videos",
    tags=["videos"]
)

UPLOAD_DIR = "uploads"

def process_analysis(analysis_id: int, video_path: str):
    """
    Background task to run the full analysis pipeline.
    """
    db = SessionLocal()
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            return

        analysis.status = AnalysisStatus.PROCESSING
        db.commit()

        # 1. Extract Audio & Frames (if needed for local processing, but we use Gemini File API now)
        # We might still want frames for UI later, but for now let's skip to save time if Gemini handles video.
        # But wait, we might want to show frames in the report.
        # Let's extract frames for the UI.
        # frames = extract_frames(video_path)
        
        # 2. Analyze with Gemini
        analysis.status = AnalysisStatus.ANALYZING
        db.commit()
        
        # Context for Gemini
        context = {
            "platform": analysis.video.platform_guess or "Unknown",
            "category": analysis.user.primary_category if analysis.user else "General"
        }
        
        if analysis.video.source_type == "script":
            result = analyze_script_content(analysis.video.script_content, context)
        else:
            result = analyze_video_content(video_path, None, None, context)
        
        # 3. Save Results
        analysis.overall_score = result.get("overall_score")
        analysis.subscores = result.get("subscores")
        analysis.insights = result.get("insights")
        analysis.optimized_assets = result.get("optimized_assets")
        analysis.checklist = result.get("checklist")
        analysis.status = AnalysisStatus.COMPLETED
        db.commit()

    except Exception as e:
        import traceback
        print(f"CRITICAL ANALYSIS FAILURE ID {analysis_id}: {e}")
        traceback.print_exc() # This prints to stderr which Railway captures
        
        with open("error.log", "a") as f:
            f.write(f"Analysis ID {analysis_id} Failed:\n")
            traceback.print_exc(file=f)
            f.write("\n")
        print(f"Analysis Failed: {e}")
        analysis.status = AnalysisStatus.FAILED
        db.commit()
    finally:
        db.close()

from datetime import datetime, timedelta
from sqlalchemy import func

def check_credits(user: User, required_credits: float):
    if user.credits < required_credits:
        raise HTTPException(
            status_code=403, 
            detail=f"Insufficient credits. Required: {required_credits}, Available: {user.credits}. Please upgrade your plan."
        )

def deduct_credits(user: User, amount: float, db: Session):
    check_credits(user, amount)
    user.credits -= amount
    db.commit()
    db.refresh(user)
    print(f"Deducted {amount} credits from User {user.email}. New balance: {user.credits}")

@router.post("/upload", response_model=AnalysisOut)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check Minimum Balance (assume worst case 2.0 initially or just allow check inside)
    # We don't know duration yet, but max cost is 2.0. Min is 1.0.
    # Let's verify user has at least 1.0 credit before uploading to save bandwidth.
    check_credits(current_user, 1.0) 

    user_id = current_user.id
    
    try:
        # Save file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Check duration
        duration = 0
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(file_path)
            duration = clip.duration
            clip.close()
            
            if duration > 1500: # 25 minutes * 60 seconds
                os.remove(file_path)
                raise HTTPException(status_code=400, detail="Video exceeds the 25-minute limit.")
        except ImportError:
            print("moviepy not installed, skipping duration check")
        except Exception as e:
            print(f"Error checking duration: {e}")
            
        # Determing Cost
        cost = 2.0 if duration > 60 else 1.0
        
        # Deduct Credits
        deduct_credits(current_user, cost, db)
            
        # Create Video record
        video = Video(
            user_id=user_id,
            source_type="upload",
            title=file.filename, # Save original filename as title
            storage_path=file_path,
            platform_guess="Unknown",
            duration=duration
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        
        # Create Analysis record
        analysis = Analysis(
            user_id=user_id,
            video_id=video.id,
            status=AnalysisStatus.QUEUED
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        # Trigger background processing
        background_tasks.add_task(process_analysis, analysis.id, file_path)
        
        print(f"Upload successful. Created Analysis ID: {analysis.id} for User ID: {user_id}")
        return analysis
    except Exception as e:
        print(f"Upload failed with error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def process_link_import(analysis_id: int, video_id: int, url: str):
    """
    Background task to download video and then trigger analysis.
    """
    db = SessionLocal()
    try:
        print(f"Starting background download for Analysis {analysis_id}, URL: {url}")
        
        # Update status to PROCESSING (covers downloading)
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis:
            analysis.status = AnalysisStatus.PROCESSING
            db.commit()

        # Download
        info = download_video(url)
        duration = info.get('duration', 0)
        
        # Determing Cost
        cost = 2.0 if duration > 60 else 1.0
        
        # We need to deduct credits NOW. But we don't have the user object in this session easily unless we query.
        # Also, what if they don't have credits? FAILED state?
        user = db.query(User).filter(User.id == analysis.user_id).first()
        if user.credits < cost:
             print(f"Insufficient credits for background task. User has {user.credits}, needs {cost}")
             analysis.status = AnalysisStatus.FAILED
             # Optional: Add error message to insights?
             db.commit()
             return

        # Deduct
        user.credits -= cost
        db.commit()
        
        # Update Video record
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.storage_path = info['path']
            video.duration = duration
            video.title = info['title'] # Save YouTube/TikTok title
            video.platform_guess = info['platform']
            db.commit()
            
            db.close()
            
            # Call process_analysis (it will open its own session)
            process_analysis(analysis_id, info['path'])
            return

    except Exception as e:
        print(f"Link Import Failed: {e}")
        db = SessionLocal()
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis:
            analysis.status = AnalysisStatus.FAILED
        db.commit()
        db.close()

@router.post("/link", response_model=AnalysisOut)
async def import_link(
    link_data: VideoCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check Minimum Balance
    check_credits(current_user, 1.0) # Ensure at least 1 credit to start

    user_id = current_user.id
    
    # Create Video record (placeholder)
    video = Video(
        user_id=user_id,
        source_type="link",
        source_url=link_data.source_url,
        platform_guess="Unknown"
        # storage_path and duration will be filled later
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    
    # Create Analysis record
    analysis = Analysis(
        user_id=user_id,
        video_id=video.id,
        status=AnalysisStatus.QUEUED
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    
    # Trigger background processing
    background_tasks.add_task(process_link_import, analysis.id, video.id, link_data.source_url)
    
    print(f"Link import queued. Analysis ID: {analysis.id}")
    return analysis

@router.post("/script", response_model=AnalysisOut)
async def analyze_script(
    script_data: ScriptCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Cost: 0.5 Credits
    deduct_credits(current_user, 0.5, db)

    user_id = current_user.id
    
    # Create Video record (as a container for the script)
    video = Video(
        user_id=user_id,
        source_type="script",
        script_content=script_data.script_content,
        platform_guess=script_data.platform,
        # No storage path or duration for scripts
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    
    # Create Analysis record
    analysis = Analysis(
        user_id=user_id,
        video_id=video.id,
        status=AnalysisStatus.QUEUED
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    
    # Trigger background processing
    # We pass None as video_path since it's a script
    background_tasks.add_task(process_analysis, analysis.id, None)
    
    return analysis

@router.get("/{analysis_id}", response_model=AnalysisOut)
def get_analysis(analysis_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    print(f"Get Analysis Request: ID={analysis_id}, User={current_user.id}")
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    print(f"Returning analysis {analysis_id}: Score={analysis.overall_score}, Status={analysis.status}")
    if analysis.insights:
        print(f"Insights type: {type(analysis.insights)}")
    
    # Convert to Pydantic model to add extra fields
    # Note: Pydantic v2 uses model_validate, but we might be on v1 or v2 shim.
    # Let's try manual dict creation or just return the object if we didn't add video_url to Analysis model.
    # But we added it to Schema.
    # Let's use the schema to create the object.
    
    analysis_data = AnalysisOut.model_validate(analysis)
    
    if analysis.video:
        if analysis.video.storage_path:
            filename = os.path.basename(analysis.video.storage_path)
            analysis_data.video_url = f"/uploads/{filename}"
        
        analysis_data.source_type = analysis.video.source_type
        analysis_data.script_content = analysis.video.script_content
        
    return analysis_data

@router.get("/{analysis_id}/report.pdf")
def get_analysis_pdf(analysis_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id).first()
    if not analysis or analysis.status != AnalysisStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Analysis not found or not completed")
        
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    p.setFont("Helvetica-Bold", 24)
    p.drawString(50, height - 50, "ViralVision AI Analysis Report")
    
    # Score
    p.setFont("Helvetica", 14)
    p.drawString(50, height - 80, f"Overall Viral Score: {analysis.overall_score}/100")
    
    y = height - 110
    
    # Executive Summary
    if analysis.insights and analysis.insights.get('executive_summary'):
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Executive Summary:")
        y -= 20
        p.setFont("Helvetica", 10)
        # Simple text wrapping (very basic)
        summary = analysis.insights.get('executive_summary')
        # Split by words and wrap manually for MVP
        words = summary.split()
        line = ""
        for word in words:
            if len(line + word) < 80:
                line += word + " "
            else:
                p.drawString(50, y, line)
                y -= 15
                line = word + " "
        p.drawString(50, y, line)
        y -= 30

    # Subscores
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Detailed Breakdown:")
    y -= 20
    p.setFont("Helvetica", 10)
    
    if analysis.subscores:
        for key, data in analysis.subscores.items():
            # Check if y is too low, new page
            if y < 100:
                p.showPage()
                y = height - 50
                p.setFont("Helvetica", 10)
                
            p.setFont("Helvetica-Bold", 10)
            p.drawString(50, y, f"{key.replace('_', ' ').title()} (Score: {data.get('score')})")
            y -= 15
            p.setFont("Helvetica", 10)
            
            # Analysis text
            analysis_text = data.get('analysis', '')
            if analysis_text:
                p.drawString(60, y, f"Analysis: {analysis_text[:90]}...") # Truncate for MVP PDF
                y -= 15
            
            # Tips
            tips = data.get('tips', [])
            if tips:
                for tip in tips[:2]: # Show top 2 tips
                    p.drawString(60, y, f"- {tip}")
                    y -= 15
            y -= 10
            
    # Insights (Strengths/Weaknesses)
    if y < 150:
        p.showPage()
        y = height - 50

    y -= 10
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Key Insights:")
    y -= 20
    p.setFont("Helvetica", 10)
    if analysis.insights:
        p.drawString(50, y, "Strengths:")
        y -= 15
        for item in analysis.insights.get('strengths', [])[:3]:
            p.drawString(70, y, f"- {item}")
            y -= 15
        y -= 10
        p.drawString(50, y, "Weaknesses:")
        y -= 15
        for item in analysis.insights.get('weaknesses', [])[:3]:
            p.drawString(70, y, f"- {item}")
            y -= 15
            
    # Script Rewrite (if available)
    if analysis.optimized_assets and analysis.optimized_assets.get('full_script_rewrite'):
        p.showPage()
        y = height - 50
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Viral Script Rewrite (10/10 Version)")
        y -= 30
        p.setFont("Helvetica", 10)
        
        rewrite = analysis.optimized_assets.get('full_script_rewrite')
        # Basic text wrapping for the script
        lines = rewrite.split('\n')
        for line_text in lines:
            words = line_text.split()
            current_line = ""
            for word in words:
                if len(current_line + word) < 90:
                    current_line += word + " "
                else:
                    if y < 50:
                        p.showPage()
                        y = height - 50
                        p.setFont("Helvetica", 10)
                    p.drawString(50, y, current_line)
                    y -= 15
                    current_line = word + " "
            
            if y < 50:
                p.showPage()
                y = height - 50
                p.setFont("Helvetica", 10)
            p.drawString(50, y, current_line)
            y -= 15 # Extra space for newline
            
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return Response(content=buffer.getvalue(), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=analysis_{analysis_id}.pdf"})

@router.get("/", response_model=List[VideoOut])
def get_videos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    print(f"Fetching videos for user_id: {current_user.id}")
    videos = db.query(Video).filter(Video.user_id == current_user.id).order_by(Video.created_at.desc()).offset(skip).limit(limit).all()
    print(f"Found {len(videos)} videos")
    
    results = []
    for video in videos:
        # Get latest analysis
        analysis = db.query(Analysis).filter(Analysis.video_id == video.id).order_by(Analysis.created_at.desc()).first()
        
        video_data = VideoOut.model_validate(video)
        if analysis:
            video_data.viral_score = analysis.overall_score
            video_data.status = analysis.status
            video_data.analysis_id = analysis.id
            
            # Smart Title Extraction
            if analysis.optimized_assets and analysis.optimized_assets.get('titles'):
                titles = analysis.optimized_assets.get('titles')
                if isinstance(titles, list) and len(titles) > 0:
                    video_data.title = titles[0]
            
            # Fallback for scripts if no AI title yet
            if not video_data.title and video.source_type == 'script':
                 # Maybe use first few words of script?
                 pass
            
            # Fallback for videos using original title
            if not video_data.title and video.title:
                video_data.title = video.title
            
        if video.storage_path:
             filename = os.path.basename(video.storage_path)
             video_data.video_url = f"/uploads/{filename}"
             
        video_data.source_type = video.source_type
             
        results.append(video_data)
        
    return results

@router.get("/stats/overview")
def get_video_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    videos = db.query(Video).filter(Video.user_id == current_user.id).all()
    total_videos = len(videos)
    
    total_score = 0
    analyzed_count = 0
    
    for video in videos:
        analysis = db.query(Analysis).filter(Analysis.video_id == video.id).order_by(Analysis.created_at.desc()).first()
        if analysis and analysis.overall_score:
            total_score += analysis.overall_score
            analyzed_count += 1
            
    avg_score = round(total_score / analyzed_count) if analyzed_count > 0 else 0
    
    # Determine growth potential based on avg score
    if avg_score >= 80:
        growth_potential = "High"
    elif avg_score >= 50:
        growth_potential = "Medium"
    else:
        growth_potential = "Low"
        
    return {
        "total_analyzed": total_videos,
        "avg_score": avg_score,
        "growth_potential": growth_potential
    }

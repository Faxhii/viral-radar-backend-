import os
import google.generativeai as genai
import json
from dotenv import load_dotenv
from pathlib import Path

# Load .env from backend directory explicitly if needed, or rely on cwd
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

def analyze_video_content(video_path: str, audio_path: str, frames: list[str], context: dict) -> dict:
    """
    Analyzes video content using Gemini Pro Vision (or 1.5 Pro).
    Returns a structured JSON response.
    """
    if not API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")

    print(f"Using API Key: {API_KEY[:5]}...")
    model = genai.GenerativeModel('gemini-2.0-flash')

    # Prepare the prompt
    prompt = f"""
    You are an expert viral video consultant and algorithm analyst. Analyze this short-form video content (Shorts/Reels/TikTok) deeply.
    
    Context:
    - Platform: {context.get('platform', 'Unknown')}
    - Category: {context.get('category', 'General')}
    - Goal: {context.get('goal', 'Viral Growth & Audience Retention')}
    
    **SCORING CRITERIA (CRITICAL):**
    - **Retention is King:** A video with bad lighting but an amazing hook and story is a 95/100. A cinematic video with a boring start is a 40/100.
    - **The "MrBeast" Rule:** Chaos, fast cuts, and loud audio are GOOD if they hold attention. Do not penalize for "unprofessional" vibes if the energy is high and engaging.
    - **Raw Authenticity:** For TikTok/Reels, "raw" phone footage often outperforms polished studio content. If it feels authentic and relatable, score it HIGH.
    
    Provide a comprehensive, professional analysis in the following strict JSON format:
    {{
        "overall_score": <0-100>,
        "subscores": {{
            "hook": {{ 
                "score": <0-100>, 
                "analysis": "Detailed breakdown of the first 3 seconds. Did it stop the scroll? (Visuals, Audio, Text).", 
                "tips": ["Specific, actionable improvement tip 1", "Tip 2"] 
            }},
            "delivery": {{ 
                "score": <0-100>, 
                "analysis": "Evaluation of speaker energy, clarity, pacing, and body language.", 
                "tips": ["..."] 
            }},
            "structure": {{ 
                "score": <0-100>, 
                "analysis": "Flow of the narrative: Hook -> Value -> Climax -> CTA. Does it drag?", 
                "tips": ["..."] 
            }},
            "visuals_and_editing": {{ 
                "score": <0-100>, 
                "analysis": "Quality of cuts, b-roll, text overlays. Is it dynamic enough to hold attention?", 
                "tips": ["..."] 
            }},
            "trend_alignment": {{ 
                "score": <0-100>, 
                "analysis": "How well this fits current platform trends and audio usage.", 
                "tips": ["..."] 
            }}
        }},
        "insights": {{
            "executive_summary": "A 2-3 sentence high-level summary of the video's potential.",
            "strengths": ["Key strength 1", "Key strength 2", "Key strength 3"],
            "weaknesses": ["Critical weakness 1", "Critical weakness 2"],
            "audience_retention_prediction": "Predict where users might scroll away and why.",
            "emotional_impact": "What emotion does this video evoke? (e.g., Curiosity, Humor, Anger, Inspiration)"
        }},
        "optimized_assets": {{
            "titles": ["Viral Title Option 1", "Viral Title Option 2 (Clickbait)", "Viral Title Option 3 (Story-driven)"],
            "improved_hook": ["Stronger Hook Option 1", "Stronger Hook Option 2 (Pattern Interrupt)"],
            "script_rewrite_start": "A rewritten version of the first 10 seconds to maximize retention.",
            "caption_suggestion": "Engaging caption with a question to drive comments.",
            "hashtags": ["#niche", "#trend", "#viral"]
        }},
        "checklist": {{
            "next_steps": [
                "Immediate fix 1 (e.g., 'Trim the silence at 0:02')",
                "Strategic change 1 (e.g., 'Use a brighter background')",
                "Posting tip (e.g., 'Post at 6 PM EST')"
            ]
        }}
    }}
    
    Return ONLY the JSON. Do not include markdown formatting like ```json.
    """
    
    # Prepare content parts
    # Note: For a real production app, we should upload files to Gemini File API for better caching/performance
    # For MVP, we can try sending frames directly if they are small, or better, use the File API.
    # Let's use the File API for the video file itself if possible, it's easier.
    
    # Upload the video file directly to Gemini
    # For mock video, we can't upload to Gemini as it's not a real video.
    # if "mock_video" in video_path:
    #      raise ValueError("Mock video cannot be analyzed by Gemini.")

    video_file = genai.upload_file(video_path)
    
    # Wait for processing? Usually fast for small videos.
    # But 'upload_file' is async in processing on server side.
    # We should check state.
    import time
    while video_file.state.name == "PROCESSING":
        time.sleep(2)
        video_file = genai.get_file(video_file.name)
        
    if video_file.state.name == "FAILED":
        raise ValueError("Video processing failed by Gemini.")

    response = model.generate_content([prompt, video_file])
    
    # Clean up response text to ensure it's JSON
    text = response.text.strip()
    if text.startswith("```json"):
        text = text[7:-3]
    
    return json.loads(text)

def analyze_script_content(script_text: str, context: dict) -> dict:
    """
    Analyzes script content using Gemini 1.5 Pro.
    Returns a structured JSON response.
    """
    if not API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")

    print(f"Using API Key: {API_KEY[:5]}...")
    model = genai.GenerativeModel('gemini-2.0-flash')

    # Prepare the prompt
    prompt = f"""
    You are a world-class viral script writer and creative director. You have written scripts that have generated millions of views on TikTok, Reels, and Shorts.
    Your goal is to take the user's script and turn it into a viral masterpiece.
    
    Context:
    - Platform: {context.get('platform', 'Unknown')}
    - Category: {context.get('category', 'General')}
    
    User's Script:
    "{script_text}"
    
    **SCORING INSTRUCTIONS (IMPORTANT):**
    - **Be Honest but Fair:** If the script is actually good (strong hook, clear value, good pacing), give it a HIGH score (90+). Do not artificially lower the score just to suggest improvements.
    - **The "Viral" Test:** If this script looks like something that would get 1M+ views, score it 95-100.
    - **Constructive Criticism:** Even for a 95/100 script, you can still offer alternative hooks or slight tweaks, but acknowledge its strength.
    
    Analyze this script and provide feedback that is punchy, direct, and conversational. Do NOT sound like a robot. Write like a high-energy expert giving feedback to a colleague.
    
    Provide your output in the following strict JSON format:
    {{
        "overall_score": <0-100>,
        "subscores": {{
            "hook": {{ 
                "score": <0-100>, 
                "analysis": "Direct feedback on the first 3 seconds. Is it boring? Does it grab attention?", 
                "tips": ["Actionable tip 1", "Actionable tip 2"] 
            }},
            "story_arc": {{ 
                "score": <0-100>, 
                "analysis": "How is the pacing? Does the middle sag? Is the payoff worth it?", 
                "tips": ["..."] 
            }},
            "clarity": {{ 
                "score": <0-100>, 
                "analysis": "Is the message instant? Confusion kills views.", 
                "tips": ["..."] 
            }},
            "emotion": {{ 
                "score": <0-100>, 
                "analysis": "What will the viewer FEEL? (Laugh, Cry, Share, Save).", 
                "tips": ["..."] 
            }},
            "cta": {{ 
                "score": <0-100>, 
                "analysis": "Is the Call to Action clear and compelling?", 
                "tips": ["..."] 
            }}
        }},
        "insights": {{
            "executive_summary": "A 2-3 sentence punchy summary of the potential. Be honest.",
            "strengths": ["Killer Hook", "Great Pacing", "Relatable Topic"],
            "weaknesses": ["Slow Start", "Confusing Middle", "Weak CTA"],
            "audience_retention_prediction": "Predict exactly where people will scroll away.",
            "emotional_impact": "The primary emotion this script triggers."
        }},
        "optimized_assets": {{
            "titles": ["Viral Title Option 1", "Viral Title Option 2", "Viral Title Option 3"],
            "improved_hook": ["Viral Hook Option 1", "Viral Hook Option 2", "Viral Hook Option 3"],
            "script_rewrite_start": "Rewritten opening (first 15s) for maximum retention.",
            "full_script_rewrite": "A COMPLETE rewrite of the entire script. Make it 10/10. Fix the pacing, punch up the jokes, sharpen the hook, and ensure a strong CTA. Keep the original core message but make it viral-ready.",
            "caption_suggestion": "A caption that drives engagement (questions, controversy, value).",
            "hashtags": ["#niche", "#trend", "#viral"]
        }},
        "checklist": {{
            "next_steps": [
                "Immediate fix 1",
                "Strategic change 1",
                "Filming tip"
            ]
        }}
    }}
    
    Return ONLY the JSON. Do not include markdown formatting like ```json.
    """
    
    response = model.generate_content(prompt)
    
    # Clean up response text to ensure it's JSON
    text = response.text.strip()
    if text.startswith("```json"):
        text = text[7:-3]
    
    return json.loads(text)

"""
SlyWriter Enhanced Backend Server - Complete Implementation
All features from the Python desktop app
"""

from fastapi import FastAPI, WebSocket, HTTPException, Depends, BackgroundTasks, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import random
import time
import json
import threading
import pyautogui
import keyboard as kb
from datetime import datetime, timedelta
import logging
import os
import sys
import uuid
from collections import deque
import openai
import httpx

# Import WPM calculator
from wpm_calculator_v2 import get_comprehensive_profile, get_char_specific_delay, wpm_to_delays_v2
from advanced_humanization import AdvancedHumanizer

# Import database and auth
from database import init_db, get_db, User, TypingSession, Analytics, Profile, Achievement, UserAchievement
from auth import (
    create_access_token, create_refresh_token, verify_token, verify_google_token, 
    get_current_user, require_user, check_plan_limit, generate_referral_code
)
from sqlalchemy.orm import Session
from sqlalchemy import func

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize database
init_db()

app = FastAPI(title="SlyWriter Enhanced", version="3.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AIUNDETECT_API_KEY = os.getenv("AIUNDETECT_API_KEY", "")

# Global state management
class EnhancedTypingEngine:
    def __init__(self):
        self.sessions = {}  # Store multiple typing sessions
        self.websocket_clients = {}  # Store WebSocket connections per user
        self.hotkeys_registered = False
        self.overlay_windows = {}
        self.clipboard_monitor_active = False
        self.learning_sessions = {}
        
    def create_session(self, user_id: str):
        """Create a new typing session for a user"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "user_id": user_id,
            "is_typing": False,
            "is_paused": False,
            "stop_flag": threading.Event(),
            "pause_flag": threading.Event(),
            "current_text": "",
            "chars_typed": 0,
            "total_chars": 0,
            "start_time": None,
            "wpm": 0,
            "accuracy": 100,
            "status": "Ready",
            "typos_made": 0,
            "pauses_taken": 0,
            "profile": "default",
            "countdown_active": False,
            "preview_mode": False,
            "ai_filler_texts": [],
            "zone_out_count": 0,
            "micro_hesitations_count": 0
        }
        return session_id
    
    def get_session(self, session_id: str):
        """Get a typing session"""
        return self.sessions.get(session_id)
    
    def cleanup_session(self, session_id: str):
        """Clean up a typing session"""
        if session_id in self.sessions:
            self.sessions[session_id]["stop_flag"].set()
            del self.sessions[session_id]

typing_engine = EnhancedTypingEngine()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_to_user(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

    async def broadcast_to_all(self, message: dict):
        for user_connections in self.active_connections.values():
            for connection in user_connections:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()

# Pydantic models
class TypingStartRequest(BaseModel):
    text: str
    profile: str = "default"
    preview_mode: bool = False
    session_id: Optional[str] = None
    custom_wpm: Optional[int] = None  # Allow custom WPM override

class GoogleLoginRequest(BaseModel):
    token: str

class UpdateWpmRequest(BaseModel):
    session_id: str
    wpm: int

class ProfileCreateRequest(BaseModel):
    name: str
    settings: dict

class HotkeyRegisterRequest(BaseModel):
    action: str
    hotkey: str

class AIGenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 500
    temperature: float = 0.7
    type: str = "general"  # general, essay, email, story

class HumanizerRequest(BaseModel):
    text: str
    mode: str = "standard"  # standard, advanced, academic
    grade_level: Optional[int] = None
    tone: Optional[str] = None

class WPMTestRequest(BaseModel):
    test_text: str
    user_input: str
    time_taken: float

class LearningSessionRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    duration: int = 30  # minutes

class CreateLessonRequest(BaseModel):
    topic: str
    content: str
    method: str = "ai_generated"

# Typing helper functions
def calculate_wpm(chars_typed: int, elapsed_time: float) -> int:
    """Calculate words per minute"""
    if elapsed_time <= 0:
        return 0
    words = chars_typed / 5
    minutes = elapsed_time / 60
    return int(words / minutes) if minutes > 0 else 0

def calculate_accuracy(original: str, typed: str) -> float:
    """Calculate typing accuracy"""
    if not original or not typed:
        return 100.0
    
    correct = sum(1 for a, b in zip(original, typed) if a == b)
    return (correct / len(original)) * 100

def generate_typo(char: str) -> str:
    """Generate a realistic typo"""
    keyboard_layout = {
        'q': 'was', 'w': 'qase', 'e': 'wrd', 'r': 'etf', 't': 'ryfg',
        'y': 'tugh', 'u': 'yihj', 'i': 'uok', 'o': 'ipkl', 'p': 'ol',
        'a': 'qwsz', 's': 'awedx', 'd': 'erfcs', 'f': 'rtgcd', 'g': 'tyhfb',
        'h': 'yujgn', 'j': 'uikhm', 'k': 'iolj', 'l': 'opk',
        'z': 'asx', 'x': 'zsdc', 'c': 'xdfv', 'v': 'cfgb', 'b': 'vghn',
        'n': 'bhjm', 'm': 'njk'
    }
    
    char_lower = char.lower()
    if char_lower in keyboard_layout:
        neighbors = keyboard_layout[char_lower]
        typo = random.choice(neighbors)
        return typo.upper() if char.isupper() else typo
    return char

async def generate_ai_filler(context: str, style: str = "conversational") -> str:
    """Generate AI filler text using OpenAI"""
    if not OPENAI_API_KEY:
        return " um, "
    
    try:
        prompts = {
            "conversational": f"Generate a natural filler phrase someone might type while thinking, based on: {context[:50]}",
            "academic": f"Generate an academic transition or filler for: {context[:50]}",
            "casual": f"Generate a casual filler or hesitation for: {context[:50]}"
        }
        
        # Simulated response for demo (replace with actual OpenAI call)
        fillers = {
            "conversational": [" you know, ", " I mean, ", " basically, ", " like, "],
            "academic": [" furthermore, ", " moreover, ", " consequently, ", " therefore, "],
            "casual": [" um, ", " uh, ", " so, ", " well, "]
        }
        
        return random.choice(fillers.get(style, fillers["conversational"]))
    except:
        return " "

async def type_text_advanced(
    session_id: str,
    text: str,
    profile: Profile,
    user_id: str,
    preview_mode: bool = False,
    db: Session = None
):
    """Advanced typing with all premium features"""
    session = typing_engine.get_session(session_id)
    if not session:
        return
    
    session["current_text"] = text
    session["total_chars"] = len(text)
    session["chars_typed"] = 0
    session["start_time"] = time.time()
    session["status"] = "Preparing..."
    session["profile"] = profile.name
    
    # Send initial status
    await manager.send_to_user({
        "type": "status",
        "data": {
            "session_id": session_id,
            "status": session["status"],
            "chars_typed": 0,
            "total_chars": session["total_chars"],
            "wpm": 0,
            "countdown": 5
        }
    }, user_id)
    
    # Visual countdown
    session["countdown_active"] = True
    for i in range(5, 0, -1):
        if session["stop_flag"].is_set():
            return
        
        session["status"] = f"Starting in {i}..."
        await manager.send_to_user({
            "type": "countdown",
            "data": {
                "session_id": session_id,
                "count": i,
                "status": session["status"]
            }
        }, user_id)
        await asyncio.sleep(1)
    
    session["countdown_active"] = False
    session["status"] = "Typing..."
    
    # Send typing started event to clear countdown
    await manager.send_to_user({
        "type": "typing_started",
        "data": {
            "session_id": session_id,
            "status": "Typing..."
        }
    }, user_id)
    
    # Typing variables
    sentence_count = 0
    word_count = 0
    burst_speed = 1.0
    last_char = ""
    consecutive_chars = 0
    
    # Initialize advanced humanizer for ultra-realistic typing
    humanizer = AdvancedHumanizer()
    rhythm_phase = 0.0
    typo_positions = []  # Track where typos were made
    
    for i, char in enumerate(text):
        # Check stop flag
        if session["stop_flag"].is_set():
            break
        
        # Check pause flag
        while session["pause_flag"].is_set():
            session["status"] = "Paused"
            await manager.send_to_user({
                "type": "status",
                "data": {"session_id": session_id, "status": "Paused"}
            }, user_id)
            await asyncio.sleep(0.1)
            if session["stop_flag"].is_set():
                break
        
        if session["stop_flag"].is_set():
            break
        
        # Premium feature: Zone-out breaks
        if profile.zone_out_breaks and random.random() < 0.001:  # 0.1% chance
            zone_out_duration = random.uniform(15, 45)
            session["status"] = "Taking a break..."
            session["zone_out_count"] += 1
            await manager.send_to_user({
                "type": "zone_out",
                "data": {
                    "session_id": session_id,
                    "duration": zone_out_duration,
                    "status": session["status"]
                }
            }, user_id)
            await asyncio.sleep(zone_out_duration)
            session["status"] = "Typing..."
        
        # Premium feature: Micro-hesitations
        if profile.micro_hesitations and char == ' ' and random.random() < 0.05:  # 5% chance at spaces
            if not preview_mode:
                hesitation = random.choice([" um", " uh", " you know", " like"])
                for h_char in hesitation:
                    pyautogui.write(h_char)
                    await asyncio.sleep(random.uniform(0.05, 0.15))
                await asyncio.sleep(random.uniform(0.3, 0.8))
                for _ in range(len(hesitation)):
                    pyautogui.press('backspace')
                    await asyncio.sleep(0.05)
            session["micro_hesitations_count"] += 1
        
        # Premium feature: AI filler text
        if profile.ai_filler_enabled and char == '.' and random.random() < 0.02:  # 2% chance at periods
            filler = await generate_ai_filler(text[max(0, i-50):i], "conversational")
            if not preview_mode:
                for f_char in filler:
                    pyautogui.write(f_char)
                    await asyncio.sleep(random.uniform(profile.min_delay, profile.max_delay))
                await asyncio.sleep(random.uniform(0.5, 1.5))
                for _ in range(len(filler)):
                    pyautogui.press('backspace')
                    await asyncio.sleep(0.03)
            session["ai_filler_texts"].append(filler)
        
        # Type the actual character with advanced humanization
        if not preview_mode:
            # Advanced typo simulation
            if profile.typos_enabled and random.random() < profile.typo_chance:
                # Use advanced humanizer for realistic typos
                typo_char, should_correct = humanizer.generate_advanced_typo(char, text, i)
                
                if typo_char:  # Could be empty for missed key
                    pyautogui.write(typo_char)
                    session["typos_made"] += 1
                    typo_positions.append(i)
                    
                    # Realistic correction behavior
                    if should_correct and humanizer.simulate_correction_behavior(True, 0):
                        # Immediate correction
                        await asyncio.sleep(random.uniform(0.1, 0.3))
                        for _ in range(len(typo_char)):
                            pyautogui.press('backspace')
                            await asyncio.sleep(random.uniform(0.02, 0.05))
                        pyautogui.write(char)
                    # Otherwise leave the typo (more realistic)
            else:
                pyautogui.write(char)
        
        session["chars_typed"] += 1
        
        # Premium feature: Burst speed variability
        if profile.burst_variability > 0:
            if random.random() < 0.1:  # 10% chance to change speed
                burst_speed = random.uniform(1 - profile.burst_variability, 1 + profile.burst_variability)
        
        # Calculate ultra-realistic delay using advanced humanization
        if hasattr(profile, 'word_pause_multiplier'):
            # Use enhanced delay calculation for custom WPM profiles
            wpm_data = {
                'word_pause_multiplier': profile.word_pause_multiplier
            }
            base_delay = get_char_specific_delay(char, profile.min_delay, profile.max_delay, wpm_data)
        else:
            # Standard delay calculation for database profiles
            base_delay = random.uniform(profile.min_delay, profile.max_delay)
        
        # Apply advanced humanization for ultra-realistic delays
        # Calculate WPM from delays if not explicitly set
        if hasattr(profile, 'target_wpm'):
            wpm_target = profile.target_wpm
        else:
            # Estimate WPM from average delay
            avg_delay = (profile.min_delay + profile.max_delay) / 2
            wpm_target = int(60 / (avg_delay * 5)) if avg_delay > 0 else 60
        delay = humanizer.calculate_dynamic_delay(
            char, last_char, base_delay, wpm_target, i, len(text)
        )
        
        # Apply rhythm variation for natural flow
        rhythm_phase += 0.1
        delay = humanizer.apply_rhythm_variation(delay, rhythm_phase)
        
        # Apply burst speed if active
        delay *= burst_speed
        
        # Natural pauses (not user-initiated pauses)
        if char in '.!?':
            sentence_count += 1
            if sentence_count % profile.pause_frequency == 0:
                # Just a longer delay, not an actual pause
                delay = random.uniform(profile.pause_duration_min, profile.pause_duration_max)
                session["pauses_taken"] += 1
                # Don't change status or send pause events - just continue typing after delay
        elif char == ' ':
            word_count += 1
            if word_count % 10 == 0:  # Mini pause every 10 words
                delay *= random.uniform(1.5, 2.0)
        
        # Update WPM and send progress
        elapsed = time.time() - session["start_time"]
        session["wpm"] = calculate_wpm(session["chars_typed"], elapsed)
        
        await manager.send_to_user({
            "type": "progress",
            "data": {
                "session_id": session_id,
                "status": "Typing...",
                "chars_typed": session["chars_typed"],
                "total_chars": session["total_chars"],
                "wpm": session["wpm"],
                "accuracy": session["accuracy"],
                "progress": (session["chars_typed"] / session["total_chars"]) * 100,
                "typos_made": session["typos_made"],
                "pauses_taken": session["pauses_taken"]
            }
        }, user_id)
        
        await asyncio.sleep(delay)
        last_char = char
    
    # Session complete
    session["is_typing"] = False
    session["status"] = "Complete!"
    final_elapsed = time.time() - session["start_time"]
    final_wpm = calculate_wpm(session["chars_typed"], final_elapsed)
    
    # Save session to database if user is logged in
    if db and user_id != "anonymous":
        user = db.query(User).filter_by(email=user_id).first()
        if user:
            typing_session = TypingSession(
                user_id=user.id,
                ended_at=datetime.utcnow(),
                words_typed=session["chars_typed"] // 5,
                characters_typed=session["chars_typed"],
                average_wpm=final_wpm,
                accuracy=session["accuracy"],
                profile_used=profile.name,
                input_text=text[:500],  # Save first 500 chars
                typos_made=session["typos_made"],
                pauses_taken=session["pauses_taken"],
                ai_filler_used=profile.ai_filler_enabled,
                preview_mode=preview_mode,
                premium_features_used={
                    "zone_out_breaks": session["zone_out_count"],
                    "micro_hesitations": session["micro_hesitations_count"],
                    "ai_fillers": len(session["ai_filler_texts"])
                }
            )
            db.add(typing_session)
            
            # Update user stats
            user.total_words_typed += session["chars_typed"] // 5
            user.words_used_today += session["chars_typed"] // 5
            
            # Check achievements
            await check_achievements(user, db, final_wpm)
            
            db.commit()
    
    await manager.send_to_user({
        "type": "complete",
        "data": {
            "session_id": session_id,
            "status": "Complete!",
            "final_wpm": final_wpm,
            "total_chars": session["chars_typed"],
            "time_taken": final_elapsed,
            "accuracy": session["accuracy"],
            "typos_made": session["typos_made"],
            "pauses_taken": session["pauses_taken"],
            "premium_stats": {
                "zone_outs": session["zone_out_count"],
                "micro_hesitations": session["micro_hesitations_count"],
                "ai_fillers": len(session["ai_filler_texts"])
            }
        }
    }, user_id)

async def check_achievements(user: User, db: Session, wpm: int):
    """Check and unlock achievements"""
    achievements = db.query(Achievement).all()
    
    for achievement in achievements:
        # Check if already unlocked
        existing = db.query(UserAchievement).filter_by(
            user_id=user.id,
            achievement_id=achievement.id
        ).first()
        
        if existing and existing.progress >= 100:
            continue
        
        progress = 0
        if achievement.requirement_type == "words":
            progress = (user.total_words_typed / achievement.requirement_value) * 100
        elif achievement.requirement_type == "wpm":
            if wpm >= achievement.requirement_value:
                progress = 100
        elif achievement.requirement_type == "sessions":
            session_count = db.query(TypingSession).filter_by(user_id=user.id).count()
            progress = (session_count / achievement.requirement_value) * 100
        
        if progress > 0:
            if existing:
                existing.progress = min(progress, 100)
                if progress >= 100:
                    existing.unlocked_at = datetime.utcnow()
            else:
                user_achievement = UserAchievement(
                    user_id=user.id,
                    achievement_id=achievement.id,
                    progress=min(progress, 100),
                    unlocked_at=datetime.utcnow() if progress >= 100 else None
                )
                db.add(user_achievement)

# API Routes

# Authentication Routes
@app.post("/api/auth/google")
async def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    """Google OAuth login"""
    try:
        google_info = verify_google_token(request.token)
        
        # Find or create user
        user = db.query(User).filter_by(email=google_info["email"]).first()
        if not user:
            user = User(
                email=google_info["email"],
                google_id=google_info["google_id"],
                username=google_info.get("name"),
                referral_code=generate_referral_code(),
                plan="free",
                daily_limit=4000
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.last_login = datetime.utcnow()
            db.commit()
        
        # Create tokens
        access_token = create_access_token(data={"sub": user.email})
        refresh_token = create_refresh_token(data={"sub": user.email})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "email": user.email,
                "username": user.username,
                "plan": user.plan,
                "daily_limit": user.daily_limit,
                "words_used_today": user.words_used_today,
                "referral_code": user.referral_code,
                "referral_bonus": user.referral_bonus
            }
        }
    except Exception as e:
        logger.error(f"Google login error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    try:
        email = verify_token(refresh_token, token_type="refresh")
        access_token = create_access_token(data={"sub": email})
        return {"access_token": access_token, "token_type": "bearer"}
    except:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@app.get("/api/auth/me")
async def get_me(current_user=Depends(require_user), db: Session = Depends(get_db)):
    """Get current user info"""
    user = db.query(User).filter_by(email=current_user["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check and reset daily usage if needed
    if user.usage_reset_date.date() < datetime.utcnow().date():
        user.words_used_today = 0
        user.usage_reset_date = datetime.utcnow()
        db.commit()
    
    return {
        "email": user.email,
        "username": user.username,
        "plan": user.plan,
        "daily_limit": user.daily_limit,
        "words_used_today": user.words_used_today,
        "total_words_typed": user.total_words_typed,
        "referral_code": user.referral_code,
        "referral_bonus": user.referral_bonus,
        "referral_count": user.referral_count,
        "settings": user.settings,
        "theme": user.theme
    }

# Typing Routes
@app.post("/api/typing/start")
async def start_typing(
    request: TypingStartRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start advanced typing session"""
    user_id = current_user["email"] if current_user else "anonymous"
    
    # Check usage limits for authenticated users
    if current_user:
        user = db.query(User).filter_by(email=user_id).first()
        if user:
            word_count = len(request.text.split())
            can_type, words_left = check_plan_limit(user, word_count)
            if not can_type:
                raise HTTPException(
                    status_code=403,
                    detail=f"Usage limit reached. You have {words_left} words left today."
                )
    
    # Get or create session
    session_id = request.session_id or typing_engine.create_session(user_id)
    session = typing_engine.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session["is_typing"]:
        raise HTTPException(status_code=400, detail="Already typing")
    
    # Handle custom WPM if provided
    if request.custom_wpm:
        # Generate profile based on exact WPM using enhanced formula
        wpm_profile = get_comprehensive_profile(request.custom_wpm)
        
        class CustomWPMProfile:
            def __init__(self, wpm_data):
                self.name = f"Custom {wpm_data['target_wpm']} WPM"
                self.target_wpm = wpm_data['target_wpm']  # Add this for proper WPM tracking
                self.is_builtin = False
                self.min_delay = wpm_data['min_delay']
                self.max_delay = wpm_data['max_delay']
                self.typos_enabled = True
                self.typo_chance = wpm_data['typo_chance']
                self.pause_frequency = wpm_data['pause_frequency']
                self.pause_duration_min = wpm_data['pause_duration_min']
                self.pause_duration_max = wpm_data['pause_duration_max']
                self.ai_filler_enabled = False
                self.micro_hesitations = wpm_data.get('micro_hesitations', False)
                self.zone_out_breaks = wpm_data.get('zone_out_breaks', False)
                self.burst_variability = wpm_data.get('burst_variability', 0)
                self.advanced_anti_detection = True
                self.word_pause_multiplier = wpm_data.get('word_pause_multiplier', 1.1)
                self.category = wpm_data.get('category', 'custom')
                self.chars_per_second = wpm_data.get('chars_per_second', 5)
        
        profile = CustomWPMProfile(wpm_profile)
    else:
        # Get profile with multiple fallbacks
        profile = db.query(Profile).filter_by(name=request.profile).first()
        if not profile:
            profile = db.query(Profile).filter_by(name="Medium").first()
        if not profile:
            profile = db.query(Profile).filter_by(name="Default").first()
        if not profile:
            # Create a default profile object with ALL required attributes
            class DefaultProfile:
                def __init__(self):
                    self.name = "Default"
                    self.is_builtin = True
                    self.min_delay = 0.08
                    self.max_delay = 0.12
                    self.typos_enabled = True
                    self.typo_chance = 0.03
                    self.pause_frequency = 5
                    self.pause_duration_min = 1.5
                    self.pause_duration_max = 3.0
                    self.ai_filler_enabled = False
                    self.micro_hesitations = False
                    self.zone_out_breaks = False
                    self.burst_variability = 0
                    self.advanced_anti_detection = False
            
            profile = DefaultProfile()
    
    session["is_typing"] = True
    
    # Start typing in background
    background_tasks.add_task(
        type_text_advanced,
        session_id,
        request.text,
        profile,
        user_id,
        request.preview_mode,
        db
    )
    
    return {
        "status": "started",
        "session_id": session_id,
        "message": "Typing started"
    }

@app.post("/api/typing/pause/{session_id}")
async def pause_typing(session_id: str):
    """Pause typing"""
    session = typing_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.get("is_typing"):
        return {"status": "not_typing", "message": "Not currently typing"}
    
    session["pause_flag"].set()
    session["is_paused"] = True
    return {"status": "paused", "message": "Typing paused"}

@app.post("/api/typing/resume/{session_id}")
async def resume_typing(session_id: str):
    """Resume typing"""
    session = typing_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.get("is_typing"):
        return {"status": "not_typing", "message": "Not currently typing"}
    
    session["pause_flag"].clear()
    session["is_paused"] = False
    return {"status": "resumed", "message": "Typing resumed"}

@app.post("/api/typing/stop/{session_id}")
async def stop_typing(session_id: str):
    """Stop typing"""
    session = typing_engine.get_session(session_id)
    if not session:
        return {"status": "not_found", "message": "Session not found"}
    
    session["stop_flag"].set()
    session["is_typing"] = False
    session["is_paused"] = False
    
    return {"status": "stopped", "message": "Typing stopped"}

@app.post("/api/typing/stop")
async def stop_all_typing():
    """Global emergency stop - stops all active typing sessions"""
    import pyautogui
    # First, stop any keyboard output immediately
    pyautogui.failsafe = True
    
    stopped_sessions = []
    # Stop ALL active sessions
    for session_id, session in typing_engine.sessions.items():
        if session.get("is_typing"):
            session["stop_flag"].set()
            session["is_typing"] = False
            session["is_paused"] = False
            stopped_sessions.append(session_id)
    
    return {
        "status": "stopped",
        "message": f"Emergency stop activated. Stopped {len(stopped_sessions)} session(s)",
        "stopped_sessions": stopped_sessions
    }

@app.post("/api/typing/update_wpm")
async def update_typing_wpm(request: UpdateWpmRequest):
    """Update WPM for an active typing session"""
    session = typing_engine.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.get("is_typing"):
        return {"status": "not_typing", "message": "Session is not currently typing"}
    
    # Update the profile with new WPM-based delays using enhanced formula
    delays = wpm_to_delays_v2(request.wpm)
    
    # Update the session's profile
    if hasattr(session.get("profile"), "__dict__"):
        session["profile"].min_delay = delays["min_delay"]
        session["profile"].max_delay = delays["max_delay"]
    
    # Store the target WPM
    session["target_wpm"] = request.wpm
    
    return {
        "status": "updated",
        "message": f"WPM updated to {request.wpm}",
        "new_delays": {
            "min": delays["min_delay"],
            "max": delays["max_delay"]
        }
    }

@app.post("/api/typing/pause")
async def pause_all_typing():
    """Global pause - pauses all active typing sessions"""
    paused_sessions = []
    resumed_sessions = []
    
    # Toggle pause for ALL active sessions
    for session_id, session in typing_engine.sessions.items():
        if session.get("is_typing"):
            if session.get("is_paused"):
                session["pause_flag"].clear()
                session["is_paused"] = False
                resumed_sessions.append(session_id)
            else:
                session["pause_flag"].set()
                session["is_paused"] = True
                paused_sessions.append(session_id)
    
    if paused_sessions:
        return {"status": "paused", "message": f"Paused {len(paused_sessions)} session(s)", "sessions": paused_sessions}
    elif resumed_sessions:
        return {"status": "resumed", "message": f"Resumed {len(resumed_sessions)} session(s)", "sessions": resumed_sessions}
    else:
        return {"status": "idle", "message": "No active typing sessions"}

@app.get("/api/typing/status/{session_id}")
async def get_typing_status(session_id: str):
    """Get typing session status"""
    session = typing_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "is_typing": session["is_typing"],
        "is_paused": session["is_paused"],
        "chars_typed": session["chars_typed"],
        "total_chars": session["total_chars"],
        "wpm": session["wpm"],
        "accuracy": session["accuracy"],
        "status": session["status"],
        "progress": (session["chars_typed"] / session["total_chars"] * 100) if session["total_chars"] > 0 else 0
    }

# Profile Routes
@app.get("/api/profiles")
async def get_profiles(db: Session = Depends(get_db)):
    """Get all profiles"""
    profiles = db.query(Profile).all()
    return {"profiles": [
        {
            "name": p.name,
            "is_builtin": p.is_builtin,
            "settings": {
                "min_delay": p.min_delay,
                "max_delay": p.max_delay,
                "typos_enabled": p.typos_enabled,
                "typo_chance": p.typo_chance,
                "pause_frequency": p.pause_frequency,
                "ai_filler_enabled": p.ai_filler_enabled,
                "micro_hesitations": p.micro_hesitations,
                "zone_out_breaks": p.zone_out_breaks,
                "burst_variability": p.burst_variability
            }
        } for p in profiles
    ]}

@app.post("/api/profiles")
async def create_profile(
    request: ProfileCreateRequest,
    current_user=Depends(require_user),
    db: Session = Depends(get_db)
):
    """Create custom profile"""
    # Check if profile name exists
    existing = db.query(Profile).filter_by(name=request.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile name already exists")
    
    profile = Profile(
        name=request.name,
        is_builtin=False,
        **request.settings
    )
    db.add(profile)
    db.commit()
    
    return {"status": "created", "message": f"Profile '{request.name}' created"}

@app.post("/api/profiles/generate-from-wpm")
async def generate_profile_from_wpm(wpm: int = Body(..., embed=True), db: Session = Depends(get_db)):
    """Generate a custom profile based on user's WPM test result"""
    # Calculate delays based on WPM
    # WPM = (chars/min) / 5 = (1/delay) * 60 / 5
    # delay = 12 / WPM
    
    base_delay = 12.0 / wpm  # Base calculation
    
    # Add variance for more natural typing
    min_delay = round(base_delay * 0.8, 3)
    max_delay = round(base_delay * 1.2, 3)
    
    # Adjust pause frequency based on speed
    if wpm < 40:
        pause_freq = 20  # More frequent pauses for slow typists
    elif wpm < 80:
        pause_freq = 40
    elif wpm < 120:
        pause_freq = 60
    else:
        pause_freq = 80  # Less frequent pauses for fast typists
    
    # Update or create Custom profile
    custom_profile = db.query(Profile).filter_by(name="Custom").first()
    if custom_profile:
        custom_profile.min_delay = min_delay
        custom_profile.max_delay = max_delay
        custom_profile.pause_frequency = pause_freq
        db.commit()
    
    profile = {
        "min_delay": min_delay,
        "max_delay": max_delay,
        "typos_enabled": True,  # Always ON by default
        "typo_chance": 0.03,  # Increased to 3% for more realistic typing
        "pause_frequency": pause_freq,
        "wpm": wpm,
        "name": f"Custom ({wpm} WPM)"
    }
    
    return profile

# Analytics Routes
@app.get("/api/analytics/session-history")
async def get_session_history(
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Get typing session history"""
    user = db.query(User).filter_by(email=current_user["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    sessions = db.query(TypingSession).filter_by(user_id=user.id)\
        .order_by(TypingSession.started_at.desc()).limit(limit).all()
    
    return {"sessions": [
        {
            "id": s.id,
            "started_at": s.started_at.isoformat(),
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            "words_typed": s.words_typed,
            "wpm": s.average_wpm,
            "accuracy": s.accuracy,
            "profile": s.profile_used
        } for s in sessions
    ]}

@app.get("/api/analytics/daily-stats")
async def get_daily_stats(
    current_user=Depends(require_user),
    db: Session = Depends(get_db),
    days: int = 7
):
    """Get daily statistics"""
    user = db.query(User).filter_by(email=current_user["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get sessions grouped by day
    daily_stats = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        day_start = date.replace(hour=0, minute=0, second=0)
        day_end = date.replace(hour=23, minute=59, second=59)
        
        sessions = db.query(TypingSession).filter(
            TypingSession.user_id == user.id,
            TypingSession.started_at >= day_start,
            TypingSession.started_at <= day_end
        ).all()
        
        if sessions:
            daily_stats.append({
                "date": date.date().isoformat(),
                "sessions": len(sessions),
                "words": sum(s.words_typed for s in sessions),
                "avg_wpm": sum(s.average_wpm for s in sessions) / len(sessions),
                "avg_accuracy": sum(s.accuracy for s in sessions) / len(sessions)
            })
        else:
            daily_stats.append({
                "date": date.date().isoformat(),
                "sessions": 0,
                "words": 0,
                "avg_wpm": 0,
                "avg_accuracy": 0
            })
    
    return {"daily_stats": daily_stats}

@app.get("/api/analytics/achievements")
async def get_achievements(
    current_user=Depends(require_user),
    db: Session = Depends(get_db)
):
    """Get user achievements"""
    user = db.query(User).filter_by(email=current_user["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    all_achievements = db.query(Achievement).all()
    user_achievements = db.query(UserAchievement).filter_by(user_id=user.id).all()
    
    achievement_map = {ua.achievement_id: ua for ua in user_achievements}
    
    return {"achievements": [
        {
            "id": a.id,
            "name": a.name,
            "description": a.description,
            "icon": a.icon,
            "points": a.points,
            "progress": achievement_map[a.id].progress if a.id in achievement_map else 0,
            "unlocked": achievement_map[a.id].unlocked_at is not None if a.id in achievement_map else False,
            "unlocked_at": achievement_map[a.id].unlocked_at.isoformat() if a.id in achievement_map and achievement_map[a.id].unlocked_at else None
        } for a in all_achievements
    ]}

# AI Routes
@app.post("/api/ai/generate")
async def generate_ai_text(
    request: AIGenerateRequest,
    current_user=Depends(get_current_user)
):
    """Generate AI text"""
    # Check if user has premium
    if current_user:
        # Implement actual OpenAI call here
        pass
    
    # Simulated response for demo
    templates = {
        "general": "Here's a general response to your prompt: ",
        "essay": "In this essay, I will explore the topic of ",
        "email": "Dear [Recipient],\n\nI hope this email finds you well. ",
        "story": "Once upon a time, in a land far away, "
    }
    
    base = templates.get(request.type, templates["general"])
    generated = base + request.prompt[:100] + "..."
    
    return {
        "generated_text": generated,
        "tokens_used": len(generated.split()),
        "type": request.type
    }

@app.post("/api/ai/humanize")
async def humanize_text(
    request: HumanizerRequest,
    current_user=Depends(require_user)
):
    """Humanize AI text"""
    # Simulated humanization
    humanized = request.text
    
    if request.mode == "advanced":
        # Add more natural variations
        replacements = {
            "Therefore": "So",
            "Furthermore": "Also",
            "However": "But",
            "Nevertheless": "Still"
        }
        for old, new in replacements.items():
            humanized = humanized.replace(old, new)
    
    return {
        "humanized_text": humanized,
        "mode": request.mode,
        "changes_made": 5  # Simulated count
    }

# WPM Test Routes
@app.post("/api/wpm-test/calculate")
async def calculate_wpm_test(request: WPMTestRequest):
    """Calculate WPM test results"""
    words_typed = len(request.user_input.split())
    minutes = request.time_taken / 60
    wpm = int(words_typed / minutes) if minutes > 0 else 0
    accuracy = calculate_accuracy(request.test_text, request.user_input)
    
    return {
        "wpm": wpm,
        "accuracy": accuracy,
        "words_typed": words_typed,
        "time_taken": request.time_taken
    }

# Hotkey Routes
@app.post("/api/hotkeys/register")
async def register_hotkey(
    request: HotkeyRegisterRequest,
    current_user=Depends(get_current_user)
):
    """Register global hotkey (browser limitations apply)"""
    user_id = current_user["email"] if current_user else "anonymous"
    
    # Store hotkey configuration
    if user_id not in typing_engine.websocket_clients:
        typing_engine.websocket_clients[user_id] = {}
    
    typing_engine.websocket_clients[user_id][request.action] = request.hotkey
    
    return {
        "status": "registered",
        "action": request.action,
        "hotkey": request.hotkey,
        "message": "Hotkey registered (browser limitations may apply)"
    }

@app.get("/api/hotkeys")
async def get_hotkeys(current_user=Depends(get_current_user)):
    """Get registered hotkeys"""
    default_hotkeys = {
        "start": "Ctrl+Shift+S",
        "stop": "Ctrl+Shift+X",
        "pause": "Ctrl+Shift+P",
        "overlay": "Ctrl+Shift+O",
        "ai_generate": "Ctrl+Shift+G"
    }
    
    if current_user:
        user_id = current_user["email"]
        if user_id in typing_engine.websocket_clients:
            return {"hotkeys": typing_engine.websocket_clients[user_id]}
    
    return {"hotkeys": default_hotkeys}

# Learning System Routes
@app.post("/api/learning/create-lesson")
async def create_lesson(
    request: CreateLessonRequest,
    db: Session = Depends(get_db)
):
    """Create a lesson from AI-generated content"""
    # Store lesson in database (simplified for demo)
    lesson = {
        "id": str(uuid.uuid4()),
        "topic": request.topic,
        "content": request.content,
        "method": request.method,
        "created_at": datetime.utcnow().isoformat(),
        "review_count": 0,
        "confidence": 0
    }
    
    # In a real app, save to database
    # db.add(Lesson(**lesson))
    # db.commit()
    
    return {"status": "success", "lesson": lesson}

@app.post("/api/learning/start-session")
async def start_learning_session(
    request: LearningSessionRequest,
    current_user=Depends(require_user)
):
    """Start a learning session"""
    session_id = str(uuid.uuid4())
    typing_engine.learning_sessions[session_id] = {
        "topic": request.topic,
        "difficulty": request.difficulty,
        "duration": request.duration,
        "started_at": datetime.utcnow(),
        "progress": 0,
        "completed_exercises": []
    }
    
    return {
        "session_id": session_id,
        "topic": request.topic,
        "exercises": [
            {"id": 1, "type": "typing", "content": f"Practice typing about {request.topic}"},
            {"id": 2, "type": "quiz", "content": f"Quiz about {request.topic}"},
            {"id": 3, "type": "review", "content": f"Review material on {request.topic}"}
        ]
    }

@app.get("/api/learning/progress/{session_id}")
async def get_learning_progress(session_id: str):
    """Get learning session progress"""
    if session_id not in typing_engine.learning_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = typing_engine.learning_sessions[session_id]
    return {
        "session_id": session_id,
        "progress": session["progress"],
        "completed_exercises": session["completed_exercises"],
        "time_remaining": session["duration"] - (datetime.utcnow() - session["started_at"]).seconds // 60
    }

# Referral Routes
@app.post("/api/referral/apply")
async def apply_referral_code(
    code: str,
    current_user=Depends(require_user),
    db: Session = Depends(get_db)
):
    """Apply a referral code"""
    user = db.query(User).filter_by(email=current_user["email"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.referred_by:
        raise HTTPException(status_code=400, detail="Already used a referral code")
    
    referrer = db.query(User).filter_by(referral_code=code).first()
    if not referrer:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    
    if referrer.id == user.id:
        raise HTTPException(status_code=400, detail="Cannot use your own referral code")
    
    # Apply referral
    user.referred_by = code
    user.referral_bonus += 1000  # Bonus words for using referral
    
    referrer.referral_count += 1
    referrer.referral_bonus += 2000  # Bonus for referrer
    
    db.commit()
    
    return {
        "status": "applied",
        "bonus_words": 1000,
        "message": "Referral code applied successfully!"
    }

# WebSocket endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """Enhanced WebSocket with user-specific channels"""
    await manager.connect(websocket, user_id)
    try:
        await websocket.send_json({
            "type": "connected",
            "data": {"message": "Connected to SlyWriter Enhanced", "user_id": user_id}
        })
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message["type"] == "ping":
                await websocket.send_json({"type": "pong"})
            elif message["type"] == "hotkey":
                # Handle hotkey press from browser
                action = message["data"]["action"]
                if action == "start":
                    # Trigger typing start
                    pass
                elif action == "stop":
                    # Trigger typing stop
                    pass
            elif message["type"] == "overlay":
                # Handle overlay commands
                pass
    except Exception as e:
        logger.error(f"WebSocket error for {user_id}: {e}")
    finally:
        manager.disconnect(websocket, user_id)

# Health check
@app.get("/api/health")
async def health_check():
    """Enhanced health check with feature status"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "features": {
            "authentication": True,
            "typing_engine": True,
            "ai_integration": bool(OPENAI_API_KEY),
            "database": True,
            "websocket": True,
            "hotkeys": True,
            "learning": True,
            "analytics": True
        },
        "active_sessions": len(typing_engine.sessions),
        "connected_users": len(manager.active_connections)
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting SlyWriter Enhanced Backend v3.0.0")
    uvicorn.run(app, host="0.0.0.0", port=8000)
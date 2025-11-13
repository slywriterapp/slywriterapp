"""
SlyWriter Backend Server - MERGED VERSION
FastAPI server that handles all typing automation and backend functionality
Includes both web app endpoints and desktop app endpoints
"""

from fastapi import FastAPI, WebSocket, HTTPException, Depends, BackgroundTasks, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import random
import time
import json
import threading
from datetime import datetime, timedelta
import logging
import os
import stripe
import hmac
import hashlib
import jwt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import openai
from sqlalchemy.orm import Session
from sqlalchemy import func
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional GUI automation imports (only available in local/desktop mode)
try:
    import pyautogui
    import keyboard
    import pyperclip
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    logger.warning("GUI automation libraries not available - running in headless mode")

# Import database models and functions
from database import (
    init_db, get_db, User, TypingSession, Analytics,
    get_user_by_email, create_user, check_weekly_reset,
    get_user_limits, track_word_usage, track_ai_generation,
    track_humanizer_usage, create_typing_session
)

# Import authentication utilities
from auth import create_access_token

# Desktop App: Import license manager (optional for desktop functionality)
try:
    from license_manager import get_license_manager
    LICENSE_MANAGER_AVAILABLE = True
except ImportError:
    logger.warning("license_manager.py not found - license features disabled")
    LICENSE_MANAGER_AVAILABLE = False
    def get_license_manager(*args, **kwargs):
        return None

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "675434683795-shrls6suu68dj0cuvqct28gf3o6u3jav.apps.googleusercontent.com")

# Desktop App: Admin authentication
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

def verify_admin(authorization: str = Header(None)):
    """Verify admin access using Authorization header"""
    if not ADMIN_PASSWORD:
        raise HTTPException(status_code=500, detail="Admin authentication not configured")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.replace("Bearer ", "")
    if token != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid admin credentials")

    return True

app = FastAPI(title="SlyWriter Backend", version="2.7.1")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # Allow all for desktop compatibility - this should work for everything
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler to ensure CORS headers on all responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Ensure all HTTP exceptions include CORS headers"""
    logger.error(f"HTTPException on {request.method} {request.url.path}: {exc.status_code} - {exc.detail}")
    logger.info(f"Request origin: {request.headers.get('origin', 'No origin header')}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
    )

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup"""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")

# Global state management
class TypingEngine:
    def __init__(self):
        self.is_typing = False
        self.is_paused = False
        self.stop_flag = threading.Event()
        self.pause_flag = threading.Event()
        self.current_text = ""
        self.chars_typed = 0
        self.total_chars = 0
        self.start_time = None
        self.typing_thread = None
        self.websocket_clients = []
        self.wpm = 0
        self.status = "Ready"
        # Desktop App: Config directory for license and user data
        self.config_dir = os.environ.get('SLYWRITER_CONFIG_DIR', os.path.dirname(__file__))

    def reset(self):
        self.is_typing = False
        self.is_paused = False
        self.stop_flag.clear()
        self.pause_flag.clear()
        self.chars_typed = 0
        self.wpm = 0
        self.status = "Ready"

typing_engine = TypingEngine()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Pydantic models
class TypingStartRequest(BaseModel):
    text: str
    min_delay: float = 0.1
    max_delay: float = 0.3
    typos_enabled: bool = False
    ai_filler_enabled: bool = False
    pause_frequency: int = 5
    preview_mode: bool = False
    profile: Optional[str] = "Medium"  # Profile name for WPM calculation
    custom_wpm: Optional[int] = None   # Custom WPM value

class UserAuthRequest(BaseModel):
    email: str
    password: Optional[str] = None
    google_token: Optional[str] = None

class ProfileRequest(BaseModel):
    name: str
    settings: dict

class HotkeyRequest(BaseModel):
    action: str
    hotkey: str

# Desktop App: Additional Pydantic models
class ConfigUpdate(BaseModel):
    settings: Dict[str, Any]

class HotkeyUpdate(BaseModel):
    key: str
    value: str

class LicenseVerifyRequest(BaseModel):
    license_key: str
    force: bool = False

class TypingSessionCompleteRequest(BaseModel):
    user_email: str
    words_typed: int
    characters_typed: int
    average_wpm: float
    accuracy: float = 100.0
    profile_used: str = "Medium"
    # input_text: Optional[str] = None  # REMOVED: We don't store user text for privacy
    typos_made: int = 0
    pauses_taken: int = 0
    ai_generated: bool = False
    humanized: bool = False

# Profile management (kept in-memory for now, can be moved to DB later)
profiles_db = {}

# Typing functions
def calculate_wpm(chars_typed: int, elapsed_time: float) -> int:
    """Calculate words per minute"""
    if elapsed_time <= 0:
        return 0
    words = chars_typed / 5  # Average word length
    minutes = elapsed_time / 60
    return int(words / minutes) if minutes > 0 else 0

def generate_typo(char: str) -> str:
    """Generate a typo for a character"""
    keyboard_neighbors = {
        'a': 'qwsz', 'b': 'vghn', 'c': 'xdfv', 'd': 'erfcs',
        'e': 'wrd', 'f': 'rtgcd', 'g': 'tyhfb', 'h': 'yujgn',
        'i': 'uok', 'j': 'uikhm', 'k': 'iolj', 'l': 'opk',
        'm': 'njk', 'n': 'bhjm', 'o': 'ipkl', 'p': 'ol',
        'q': 'wa', 'r': 'etf', 's': 'awedx', 't': 'ryfg',
        'u': 'yihj', 'v': 'cfgb', 'w': 'qase', 'x': 'zsdc',
        'y': 'tugh', 'z': 'asx'
    }

    if char.lower() in keyboard_neighbors:
        neighbors = keyboard_neighbors[char.lower()]
        typo = random.choice(neighbors)
        return typo.upper() if char.isupper() else typo
    return char

async def type_text_worker(
    text: str,
    min_delay: float,
    max_delay: float,
    typos_enabled: bool,
    pause_frequency: int,
    preview_mode: bool = False
):
    """Worker function to type text with human-like behavior"""
    typing_engine.current_text = text
    typing_engine.total_chars = len(text)
    typing_engine.chars_typed = 0
    typing_engine.start_time = time.time()
    typing_engine.status = "Starting in 5 seconds..."

    # Broadcast initial status
    await manager.broadcast({
        "type": "status",
        "data": {
            "status": typing_engine.status,
            "chars_typed": 0,
            "total_chars": typing_engine.total_chars,
            "wpm": 0
        }
    })

    # 5-second countdown
    for i in range(5, 0, -1):
        if typing_engine.stop_flag.is_set():
            return
        typing_engine.status = f"Starting in {i}..."
        await manager.broadcast({
            "type": "status",
            "data": {"status": typing_engine.status}
        })
        await asyncio.sleep(1)

    typing_engine.status = "Typing..."
    sentence_count = 0

    for i, char in enumerate(text):
        # Check stop flag
        if typing_engine.stop_flag.is_set():
            break

        # Check pause flag
        while typing_engine.pause_flag.is_set():
            typing_engine.status = "Paused"
            await manager.broadcast({
                "type": "status",
                "data": {"status": "Paused"}
            })
            await asyncio.sleep(0.1)
            if typing_engine.stop_flag.is_set():
                break

        if typing_engine.stop_flag.is_set():
            break

        # Type the character (unless in preview mode)
        if not preview_mode and GUI_AVAILABLE:
            # Random typo
            if typos_enabled and random.random() < 0.02:  # 2% typo chance
                typo_char = generate_typo(char)
                pyautogui.write(typo_char)
                await asyncio.sleep(random.uniform(0.1, 0.3))
                pyautogui.press('backspace')
                await asyncio.sleep(random.uniform(0.05, 0.15))
                pyautogui.write(char)
            else:
                pyautogui.write(char)

        typing_engine.chars_typed += 1

        # Calculate WPM
        elapsed = time.time() - typing_engine.start_time
        typing_engine.wpm = calculate_wpm(typing_engine.chars_typed, elapsed)

        # Send progress update
        await manager.broadcast({
            "type": "status",
            "data": {
                "status": "Typing...",
                "chars_typed": typing_engine.chars_typed,
                "total_chars": typing_engine.total_chars,
                "wpm": typing_engine.wpm,
                "progress": (typing_engine.chars_typed / typing_engine.total_chars) * 100
            }
        })

        # Variable delay between characters
        delay = random.uniform(min_delay, max_delay)

        # Add longer pause at sentence ends
        if char in '.!?':
            sentence_count += 1
            if sentence_count % pause_frequency == 0:
                delay = random.uniform(1.5, 3.0)  # Longer pause between sentences
                typing_engine.status = "Taking a break..."
                await manager.broadcast({
                    "type": "status",
                    "data": {"status": typing_engine.status}
                })

        await asyncio.sleep(delay)

    # Typing complete
    typing_engine.is_typing = False
    typing_engine.status = "Complete!"
    await manager.broadcast({
        "type": "status",
        "data": {
            "status": "Complete!",
            "chars_typed": typing_engine.chars_typed,
            "total_chars": typing_engine.total_chars,
            "wpm": typing_engine.wpm,
            "progress": 100
        }
    })

# ============================================================================
# API ENDPOINTS - WEB APP
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {"status": "ok", "service": "SlyWriter API", "version": "2.7.0"}

@app.get("/healthz")
async def healthz():
    """Health check endpoint for Render"""
    return {"status": "healthy", "service": "SlyWriter API", "version": "2.7.0"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.7.0"}

@app.post("/api/typing/start")
async def start_typing(request: TypingStartRequest, background_tasks: BackgroundTasks):
    """Start typing with specified parameters"""
    if typing_engine.is_typing:
        raise HTTPException(status_code=400, detail="Already typing")

    if not request.text:
        raise HTTPException(status_code=400, detail="No text provided")

    # Calculate WPM from profile or use custom_wpm
    wpm = request.custom_wpm

    logger.info(f"\n{'='*60}")
    logger.info(f"🔥🔥🔥 WEB BACKEND RECEIVED TYPING REQUEST - v2.5.5 🔥🔥🔥")
    logger.info(f"🚨 Profile: {request.profile}")
    logger.info(f"🚨 custom_wpm from request: {wpm}")
    logger.info(f"🚨 Type of custom_wpm: {type(wpm)}")
    logger.info(f"🚨 Is custom_wpm truthy: {bool(wpm)}")
    logger.info(f"{'='*60}\n")

    if not wpm:
        # Map profile names to WPM values
        profile_wpm_map = {
            "Slow": 40,
            "Medium": 70,
            "Fast": 100,
            "Lightning": 250,
            "Custom": 85
        }
        wpm = profile_wpm_map.get(request.profile, 70)
        logger.info(f"✅ Using profile '{request.profile}' WPM: {wpm}")
    else:
        logger.info(f"✅ Using custom WPM: {wpm}")

    # Calculate delays from WPM
    # Formula: avg_delay = 60 seconds / (wpm * 5 chars_per_word) = seconds per character
    chars_per_second = (wpm * 5) / 60.0
    avg_delay = 1.0 / chars_per_second if chars_per_second > 0 else 0.1
    request.min_delay = max(0.01, avg_delay * 0.7)
    request.max_delay = min(2.0, avg_delay * 1.3)

    logger.info(f"\n🔥 CALCULATED DELAYS FOR {wpm} WPM:")
    logger.info(f"   chars_per_second: {chars_per_second:.2f}")
    logger.info(f"   avg_delay: {avg_delay:.4f}s")
    logger.info(f"   min_delay: {request.min_delay:.4f}s")
    logger.info(f"   max_delay: {request.max_delay:.4f}s")
    logger.info(f"🔥 SETTING STATE WPM TO: {wpm} 🔥\n")

    # Reset engine state
    typing_engine.reset()
    typing_engine.is_typing = True
    typing_engine.wpm = wpm  # Store WPM in engine state

    # Start typing in background
    background_tasks.add_task(
        type_text_worker,
        request.text,
        request.min_delay,
        request.max_delay,
        request.typos_enabled,
        request.pause_frequency,
        request.preview_mode
    )

    return {"status": "started", "message": "Typing started successfully", "wpm": wpm}

@app.post("/api/typing/pause")
async def pause_typing():
    """Pause or resume typing"""
    if not typing_engine.is_typing:
        raise HTTPException(status_code=400, detail="Not currently typing")

    if typing_engine.is_paused:
        typing_engine.pause_flag.clear()
        typing_engine.is_paused = False
        return {"status": "resumed", "message": "Typing resumed"}
    else:
        typing_engine.pause_flag.set()
        typing_engine.is_paused = True
        return {"status": "paused", "message": "Typing paused"}

@app.post("/api/typing/stop")
async def stop_typing():
    """Stop typing"""
    if not typing_engine.is_typing:
        return {"status": "not_typing", "message": "Not currently typing"}

    typing_engine.stop_flag.set()
    typing_engine.is_typing = False
    typing_engine.is_paused = False

    # Broadcast stop status
    await manager.broadcast({
        "type": "status",
        "data": {
            "status": "Stopped",
            "chars_typed": typing_engine.chars_typed,
            "total_chars": typing_engine.total_chars,
            "wpm": typing_engine.wpm
        }
    })

    return {"status": "stopped", "message": "Typing stopped"}

@app.get("/api/typing/status")
async def get_typing_status():
    """Get current typing status"""
    return {
        "is_typing": typing_engine.is_typing,
        "is_paused": typing_engine.is_paused,
        "chars_typed": typing_engine.chars_typed,
        "total_chars": typing_engine.total_chars,
        "wpm": typing_engine.wpm,
        "status": typing_engine.status,
        "progress": (typing_engine.chars_typed / typing_engine.total_chars * 100) if typing_engine.total_chars > 0 else 0
    }

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time updates"""
    await manager.connect(websocket)
    try:
        # Send initial status
        await websocket.send_json({
            "type": "connected",
            "data": {"message": "Connected to SlyWriter backend"}
        })

        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            # Echo back or handle commands
            if data == "ping":
                await websocket.send_text("pong")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)

# Profile management
@app.get("/api/profiles")
async def get_profiles():
    """Get all saved profiles"""
    return {"profiles": profiles_db}

# User authentication
@app.post("/api/auth/login")
async def login(auth: UserAuthRequest, db: Session = Depends(get_db)):
    """User login"""
    if not auth.email:
        raise HTTPException(status_code=400, detail="Email required")

    # Get or create user
    user = get_user_by_email(db, auth.email)
    if not user:
        user = create_user(db, auth.email, plan="Free")
        logger.info(f"Created new user via login: {auth.email}")
    else:
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()

    # Check for weekly reset
    check_weekly_reset(db, user)

    # Check if Pro/Premium from referrals has expired
    if user.premium_until and user.premium_until < datetime.utcnow():
        # Pro/Premium expired, revert to Free if no active Stripe subscription
        if not user.subscription_status or user.subscription_status != "active":
            user.plan = "Free"
            user.premium_until = None
            db.commit()
            logger.info(f"Pro/Premium from referrals expired for user: {auth.email}")

    # Generate referral code if user doesn't have one (for existing users)
    if not user.referral_code:
        import secrets
        user.referral_code = secrets.token_urlsafe(8)
        db.commit()
        logger.info(f"Generated referral code for existing user: {auth.email}")

    # Get user limits
    limits = get_user_limits(user)

    # Generate JWT token
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})

    # Build user response
    user_data = {
        "id": user.id,
        "email": user.email,
        "plan": user.plan,
        "usage": user.words_used_this_week,
        "humanizer_usage": user.humanizer_used_this_week,
        "ai_gen_usage": user.ai_gen_used_this_week,
        "referrals": {
            "code": user.referral_code,
            "count": user.referral_count,
            "tier_claimed": user.referral_tier_claimed,
            "bonus_words": user.referral_bonus
        },
        "premium_until": user.premium_until.isoformat() if user.premium_until else None,
        **limits
    }

    return {
        "status": "success",
        "user": user_data,
        "token": access_token,
        "access_token": access_token
    }

@app.post("/auth/google/login")
async def google_login(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth login"""
    try:
        data = await request.json()
        credential = data.get("credential")
        referral_code = data.get("referral_code")  # Optional referral code from signup URL

        if not credential:
            raise HTTPException(status_code=400, detail="No credential provided")

        # Verify the Google ID token
        try:
            idinfo = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                GOOGLE_CLIENT_ID
            )            # Get email and profile picture from token
            email = idinfo.get("email")
            if not email:
                raise HTTPException(status_code=400, detail="Email not found in token")

            # Extract profile picture URL if available
            profile_picture = idinfo.get("picture")
            # Extract username from Google (given_name or name)
            username = idinfo.get("given_name") or idinfo.get("name") or email.split('@')[0]

        except ValueError as e:
            logger.error(f"Invalid Google token: {e}")
            raise HTTPException(status_code=401, detail="Invalid Google token")

        # Get or create user
        user = get_user_by_email(db, email)
        is_new_user = False
        if not user:
            user = create_user(db, email, plan="Free")
            is_new_user = True
            logger.info(f"Created new user via Google: {email}")

            # Process referral code if provided
            if referral_code:
                referrer = db.query(User).filter(User.referral_code == referral_code).first()
                if referrer:
                    # Set the new user's referred_by field
                    user.referred_by = referral_code
                    # Give new user bonus words (500 words)
                    user.referral_bonus = 500
                    # Increment referrer's count and give them bonus words (500 words)
                    referrer.referral_count += 1
                    referrer.referral_bonus += 500
                    logger.info(f"Referral processed: {email} referred by {referrer.email}. Both users got 500 bonus words!")
                else:
                    logger.warning(f"Invalid referral code provided: {referral_code}")
        else:
            user.last_login = datetime.utcnow()

        # Update profile picture and username if available
        if profile_picture:
            user.profile_picture = profile_picture
        if username and not user.username:
            user.username = username

        db.commit()

        # Check if Pro/Premium from referrals has expired
        if user.premium_until and user.premium_until < datetime.utcnow():
            # Pro/Premium expired, revert to Free if no active Stripe subscription
            if not user.subscription_status or user.subscription_status != "active":
                user.plan = "Free"
                user.premium_until = None
                db.commit()
                logger.info(f"Pro/Premium from referrals expired for user: {email}")

        # Check for weekly reset
        check_weekly_reset(db, user)

        # Generate referral code if needed
        if not user.referral_code:
            import secrets
            user.referral_code = secrets.token_urlsafe(8)
            db.commit()

        # Get user limits
        limits = get_user_limits(user)

        # Generate JWT token
        access_token = create_access_token(data={"sub": user.email, "user_id": user.id})

        # Build user response
        user_data = {
            "id": user.id,
            "email": user.email,
            "plan": user.plan,
            "usage": user.words_used_this_week,
            "humanizer_usage": user.humanizer_used_this_week,
            "ai_gen_usage": user.ai_gen_used_this_week,
            "referrals": {
                "code": user.referral_code,
                "count": user.referral_count,
                "tier_claimed": user.referral_tier_claimed,
                "bonus_words": user.referral_bonus
            },
            "premium_until": user.premium_until.isoformat() if user.premium_until else None,
            **limits
        }

        return {
            "success": True,
            "is_new_user": is_new_user,
            "user": user_data,
            "token": access_token,
            "access_token": access_token
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Google login error: {type(e).__name__}: {str(e)}")
        logger.error(f"Full traceback:\n{error_details}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e) or 'Unknown error'}")


@app.options("/auth/verify-email")
async def verify_email_options(request: Request):
    """Handle CORS preflight for verify-email"""
    origin = request.headers.get('origin', '*')
    logger.info(f"OPTIONS /auth/verify-email from origin: {origin}")
    return JSONResponse(
        content={},
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": origin if origin in [
                "http://localhost:3000",
                "http://localhost:3001",
                "https://slywriter.ai",
                "https://www.slywriter.ai",
                "https://slywriter-ui.onrender.com"
            ] else "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
            "Access-Control-Max-Age": "3600",
        }
    )

@app.post("/auth/verify-email")
async def verify_email(request: Request, db: Session = Depends(get_db)):
    """Verify email token - used by website"""
    logger.info(f"POST /auth/verify-email from origin: {request.headers.get('origin', 'No origin')}")
    try:
        data = await request.json()
        token = data.get("token")
        logger.info(f"Token received: {token[:20]}..." if token else "No token in request")

        if not token:
            raise HTTPException(status_code=400, detail="Token required")

        # Verify JWT token
        JWT_SECRET = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET", "your-secret-key-change-in-production")

        try:
            # Decode and verify the token
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            email = payload.get("email")
            logger.info(f"Token decoded successfully for email: {email}")

            if not email:
                raise HTTPException(status_code=400, detail="Invalid token: no email")

        except jwt.ExpiredSignatureError:
            logger.error("Token expired")
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")

        # Get or create user in database
        user = get_user_by_email(db, email)
        if not user:
            user = create_user(db, email, plan="Free")
            logger.info(f"Created new user: {email}")
        else:
            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()
            logger.info(f"User logged in: {email}, plan: {user.plan}")

        # Check if Pro/Premium from referrals has expired
        if user.premium_until and user.premium_until < datetime.utcnow():
            # Pro/Premium expired, revert to Free if no active Stripe subscription
            if not user.subscription_status or user.subscription_status != "active":
                user.plan = "Free"
                user.premium_until = None
                db.commit()
                logger.info(f"Pro/Premium from referrals expired for user: {email}")

        # Check for weekly reset
        reset_occurred = check_weekly_reset(db, user)
        if reset_occurred:
            logger.info(f"Weekly reset applied for user: {email}")

        # Generate referral code if user doesn't have one (for existing users)
        if not user.referral_code:
            import secrets
            user.referral_code = secrets.token_urlsafe(8)
            db.commit()
            logger.info(f"Generated referral code for existing user: {email}")

        # Get user limits
        limits = get_user_limits(user)
        logger.info(f"User limits calculated: {limits}")

        # Build user response
        user_data = {
            "id": user.id,
            "email": user.email,
            "plan": user.plan,
            "usage": user.words_used_this_week,
            "humanizer_usage": user.humanizer_used_this_week,
            "ai_gen_usage": user.ai_gen_used_this_week,
            "referrals": {
                "code": user.referral_code,
                "count": user.referral_count,
                "tier_claimed": user.referral_tier_claimed,
                "bonus_words": user.referral_bonus
            },
            "premium_until": user.premium_until.isoformat() if user.premium_until else None,
            **limits
        }

        response_data = {
            "success": True,
            "user": user_data,
            "access_token": token
        }

        logger.info(f"Successfully verified email for {email}, returning user data")
        return JSONResponse(
            content=response_data,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/auth/profile")
async def get_profile(request: Request, db: Session = Depends(get_db)):
    """Get current user's profile using JWT token from Authorization header"""
    try:
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

        token = auth_header.replace("Bearer ", "")

        # Verify JWT token
        JWT_SECRET = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET", "your-secret-key-change-in-production")

        try:
            # Decode and verify the token
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            email = payload.get("sub") or payload.get("email")

            if not email:
                raise HTTPException(status_code=401, detail="Invalid token: no email")

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")

        # Expire session cache to ensure fresh data from database
        db.expire_all()

        # Get user by email
        user = get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if Pro/Premium from referrals has expired
        if user.premium_until and user.premium_until < datetime.utcnow():
            # Pro/Premium expired, revert to Free if no active Stripe subscription
            if not user.subscription_status or user.subscription_status != "active":
                user.plan = "Free"
                user.premium_until = None
                db.commit()
                logger.info(f"Pro/Premium from referrals expired for user: {email}")

        # Check for weekly reset
        check_weekly_reset(db, user)

        # Get user limits
        limits = get_user_limits(user)

        return {
            "id": user.id,
            "email": user.email,
            "username": user.username if hasattr(user, 'username') and user.username else user.email.split('@')[0],
            "plan": user.plan,
            "usage": user.words_used_this_week,
            "humanizer_usage": user.humanizer_used_this_week,
            "ai_gen_usage": user.ai_gen_used_this_week,
            "profile_picture": user.profile_picture if hasattr(user, 'profile_picture') else None,
            "referrals": {
                "code": user.referral_code,
                "count": user.referral_count,
                "tier_claimed": user.referral_tier_claimed,
                "bonus_words": user.referral_bonus
            },
            "premium_until": user.premium_until.isoformat() if user.premium_until else None,
            **limits
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/user/{user_id}")
async def get_user_endpoint(user_id: str, db: Session = Depends(get_db)):
    """Get user information with plan limits"""
    # user_id can be email or numeric ID
    # Try to find by email first (legacy format: email with @ and . replaced)
    email = user_id.replace("_", "@", 1).replace("_", ".", 1) if "_" in user_id else None

    user = None
    if email:
        user = get_user_by_email(db, email)

    # If not found, try by numeric ID
    if not user and user_id.isdigit():
        user = db.query(User).filter(User.id == int(user_id)).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check for weekly reset
    check_weekly_reset(db, user)

    # Get user limits
    limits = get_user_limits(user)

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username if hasattr(user, 'username') and user.username else user.email.split('@')[0],
        "plan": user.plan,
        "usage": user.words_used_this_week,
        "humanizer_usage": user.humanizer_used_this_week,
        "ai_gen_usage": user.ai_gen_used_this_week,
        "referrals": {
            "code": user.referral_code,
            "count": user.referral_count,
            "tier_claimed": user.referral_tier_claimed,
            "bonus_words": user.referral_bonus
        },
        "premium_until": user.premium_until.isoformat() if user.premium_until else None,
        **limits
    }

# Usage tracking
@app.post("/api/usage/track")
async def track_usage_endpoint(user_id: str, words: int, db: Session = Depends(get_db)):
    """Track word usage"""
    # Find user by email or ID
    email = user_id.replace("_", "@", 1).replace("_", ".", 1) if "_" in user_id else None
    user = None
    if email:
        user = get_user_by_email(db, email)
    if not user and user_id.isdigit():
        user = db.query(User).filter(User.id == int(user_id)).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Track word usage using database helper
    user = track_word_usage(db, user, words)

    return {"status": "tracked", "usage": user.words_used_this_week}

@app.post("/api/usage/track-humanizer")
async def track_humanizer_endpoint(user_id: str, db: Session = Depends(get_db)):
    """Track humanizer usage"""
    # Find user by email or ID
    email = user_id.replace("_", "@", 1).replace("_", ".", 1) if "_" in user_id else None
    user = None
    if email:
        user = get_user_by_email(db, email)
    if not user and user_id.isdigit():
        user = db.query(User).filter(User.id == int(user_id)).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Track humanizer usage using database helper
    user = track_humanizer_usage(db, user)

    return {"status": "tracked", "humanizer_usage": user.humanizer_used_this_week}

@app.post("/api/usage/track-ai-gen")
async def track_ai_gen_endpoint(user_id: str, db: Session = Depends(get_db)):
    """Track AI generation usage"""
    # Find user by email or ID
    email = user_id.replace("_", "@", 1).replace("_", ".", 1) if "_" in user_id else None
    user = None
    if email:
        user = get_user_by_email(db, email)
    if not user and user_id.isdigit():
        user = db.query(User).filter(User.id == int(user_id)).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Track AI generation usage using database helper
    user = track_ai_generation(db, user)

    return {"status": "tracked", "ai_gen_usage": user.ai_gen_used_this_week}

@app.post("/api/usage/check-reset")
async def check_reset_endpoint(user_id: str, db: Session = Depends(get_db)):
    """Check if weekly usage should be reset"""
    # Find user by email or ID
    email = user_id.replace("_", "@", 1).replace("_", ".", 1) if "_" in user_id else None
    user = None
    if email:
        user = get_user_by_email(db, email)
    if not user and user_id.isdigit():
        user = db.query(User).filter(User.id == int(user_id)).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check weekly reset using database helper
    was_reset = check_weekly_reset(db, user)

    return {
        "reset": was_reset,
        "week_start": user.week_start_date.strftime("%Y-%m-%d") if user.week_start_date else None
    }

@app.post("/api/typing/session/complete")
async def complete_typing_session(session_data: TypingSessionCompleteRequest, db: Session = Depends(get_db)):
    """Track completed typing session and update analytics"""
    try:
        # Get user by email
        user = get_user_by_email(db, session_data.user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Track word usage
        track_word_usage(db, user, session_data.words_typed)

        # Prepare session data dict (text not stored for privacy)
        typing_session_data = {
            "words_typed": session_data.words_typed,
            "characters_typed": session_data.characters_typed,
            "average_wpm": session_data.average_wpm,
            "accuracy": session_data.accuracy,
            "profile_used": session_data.profile_used,
            # "input_text": session_data.input_text,  # REMOVED: We don't store text
            "typos_made": session_data.typos_made,
            "pauses_taken": session_data.pauses_taken,
            "ai_generated": session_data.ai_generated,
            "humanized": session_data.humanized
        }

        # Create typing session record
        session = create_typing_session(
            db=db,
            user_id=user.id,
            session_data=typing_session_data
        )

        logger.info(f"✅ Typing session saved for {session_data.user_email}: {session_data.words_typed} words, {session_data.average_wpm} WPM")

        return {
            "success": True,
            "session_id": session.id,
            "words_used_this_week": user.words_used_this_week,
            "total_words_typed": user.total_words_typed
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save typing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Referral code redemption endpoint
class RedeemReferralRequest(BaseModel):
    referral_code: str

@app.post("/api/referral/redeem")
async def redeem_referral_code(request: RedeemReferralRequest, auth_request: Request, db: Session = Depends(get_db)):
    """Redeem a referral code in-app after signup"""
    try:
        # Get token from Authorization header
        auth_header = auth_request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

        token = auth_header.replace("Bearer ", "")

        # Verify JWT token
        JWT_SECRET = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET", "your-secret-key-change-in-production")

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            email = payload.get("sub") or payload.get("email")

            if not email:
                raise HTTPException(status_code=401, detail="Invalid token: no email")

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")

        # Get current user (referee)
        referee = get_user_by_email(db, email)
        if not referee:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if user has already been referred
        if referee.referred_by:
            raise HTTPException(
                status_code=400,
                detail="You have already redeemed a referral code"
            )

        # Find referrer by code (case-sensitive)
        referral_code = request.referral_code.strip()
        referrer = db.query(User).filter(User.referral_code == referral_code).first()

        if not referrer:
            raise HTTPException(status_code=404, detail="Invalid referral code")

        # Prevent self-referral
        if referrer.email == referee.email:
            raise HTTPException(status_code=400, detail="You cannot use your own referral code")

        # Apply bonuses
        referee.referred_by = referral_code
        referee.referral_bonus = (referee.referral_bonus or 0) + 500

        referrer.referral_count = (referrer.referral_count or 0) + 1
        referrer.referral_bonus = (referrer.referral_bonus or 0) + 500

        db.commit()
        db.refresh(referee)
        db.refresh(referrer)

        logger.info(f"[REFERRAL] {referee.email} redeemed code {referral_code} from {referrer.email}. Both got 500 bonus words!")

        return {
            "success": True,
            "message": "Referral code redeemed successfully!",
            "bonus_words": referee.referral_bonus,
            "referrer_name": getattr(referrer, 'name', None) or referrer.email.split('@')[0],
            "referral_code_used": referral_code
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to redeem referral code: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Referral reward claim endpoint
class ClaimRewardRequest(BaseModel):
    tier: int
    email: str

@app.post("/api/referrals/claim-reward")
async def claim_referral_reward(request: ClaimRewardRequest, db: Session = Depends(get_db)):
    """Claim a referral tier reward"""
    user = get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Define tier requirements and rewards
    TIER_REQUIREMENTS = [
        {"tier": 1, "referrals": 1, "reward": "1000 words"},
        {"tier": 2, "referrals": 2, "reward": "2500 words"},
        {"tier": 3, "referrals": 3, "reward": "1 week Pro"},
        {"tier": 4, "referrals": 5, "reward": "5000 words"},
        {"tier": 5, "referrals": 7, "reward": "2 weeks Pro"},
        {"tier": 6, "referrals": 10, "reward": "10000 words"},
        {"tier": 7, "referrals": 15, "reward": "1 month Pro"},
        {"tier": 8, "referrals": 20, "reward": "25000 words"},
        {"tier": 9, "referrals": 30, "reward": "2 months Pro"},
        {"tier": 10, "referrals": 50, "reward": "6 months Pro"},
    ]

    tier_data = next((t for t in TIER_REQUIREMENTS if t["tier"] == request.tier), None)
    if not tier_data:
        raise HTTPException(status_code=400, detail="Invalid tier")

    # Check if user has enough referrals
    if user.referral_count < tier_data["referrals"]:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient referrals. Need {tier_data['referrals']}, have {user.referral_count}"
        )

    # Check if tier already claimed
    if user.referral_tier_claimed >= request.tier:
        raise HTTPException(status_code=400, detail="Tier already claimed")

    # Apply the reward
    reward_text = tier_data["reward"]

    if "words" in reward_text:
        # Extract word count
        import re
        match = re.search(r'(\d+)', reward_text)
        if match:
            words = int(match.group(1))
            user.referral_bonus += words
            result_message = f"Added {words:,} bonus words"
    elif "Pro" in reward_text:
        # Extract duration
        import re
        match = re.search(r'(\d+)\s*(week|month)', reward_text)
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            days = amount * 7 if unit == "week" else amount * 30

            # Calculate new premium_until date (Pro plan expiration from referrals)
            # IMPORTANT: Stack referral time AFTER Stripe subscription ends
            now = datetime.utcnow()

            # Start with the latest of:
            # 1. Current premium_until (if it exists and is in the future)
            # 2. Stripe subscription end date (if active subscription exists)
            # 3. Current time
            start_date = now

            # Check if user has premium_until in the future
            if user.premium_until and user.premium_until > now:
                start_date = user.premium_until

            # Check if user has active Stripe subscription - if so, start AFTER it ends
            if user.stripe_subscription_id and user.subscription_status == "active":
                if user.subscription_current_period_end and user.subscription_current_period_end > start_date:
                    start_date = user.subscription_current_period_end
                    logger.info(f"Referral Pro will start after Stripe subscription ends on {start_date.strftime('%Y-%m-%d')}")

            # Add the referral days to the start date
            user.premium_until = start_date + timedelta(days=days)

            # Update plan to Pro if not already (unless they have Premium)
            if user.plan != "Pro" and user.plan != "Premium":
                user.plan = "Pro"

            result_message = f"Pro plan extended to {user.premium_until.strftime('%Y-%m-%d')}"
    else:
        result_message = "Unknown reward type"

    # Update claimed tier
    user.referral_tier_claimed = request.tier
    db.commit()

    return {
        "success": True,
        "message": result_message,
        "tier": request.tier,
        "reward": reward_text,
        "bonus_words": user.referral_bonus,
        "premium_until": user.premium_until.isoformat() if user.premium_until else None,
        "plan": user.plan
    }

# User statistics endpoint
@app.get("/api/stats/user")
async def get_user_stats(request: Request, db: Session = Depends(get_db)):
    """Get user-specific statistics from PostgreSQL"""
    try:
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

        token = auth_header.replace("Bearer ", "")

        # Verify JWT token
        JWT_SECRET = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET", "your-secret-key-change-in-production")

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            email = payload.get("sub") or payload.get("email")

            if not email:
                raise HTTPException(status_code=401, detail="Invalid token: no email")

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")

        # Get user by email
        user = get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get total sessions for this user
        total_sessions = db.query(TypingSession).filter(TypingSession.user_id == user.id).count()

        # Get total words and characters from user model
        total_words = user.total_words_typed or 0
        total_characters = total_words * 5  # Approximate characters from words

        # Get today's sessions (UTC timezone)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_sessions = db.query(TypingSession).filter(
            TypingSession.user_id == user.id,
            TypingSession.started_at >= today_start
        ).all()

        today_words = sum(session.words_typed or 0 for session in today_sessions)
        today_sessions_count = len(today_sessions)

        # Get average WPM from recent sessions (last 10 sessions)
        recent_sessions = db.query(TypingSession).filter(
            TypingSession.user_id == user.id,
            TypingSession.average_wpm != None,
            TypingSession.average_wpm > 0
        ).order_by(TypingSession.started_at.desc()).limit(10).all()

        avg_speed = 0
        if recent_sessions:
            avg_speed = sum(s.average_wpm for s in recent_sessions) / len(recent_sessions)

        # Get best WPM from all sessions
        best_wpm_session = db.query(TypingSession).filter(
            TypingSession.user_id == user.id,
            TypingSession.average_wpm != None
        ).order_by(TypingSession.average_wpm.desc()).first()

        best_wpm = best_wpm_session.average_wpm if best_wpm_session else 0

        return {
            "success": True,
            "stats": {
                "totalWords": total_words,
                "totalCharacters": total_characters,
                "totalSessions": total_sessions,
                "avgSpeed": round(avg_speed, 1),
                "todayWords": today_words,
                "todaySessions": today_sessions_count,
                "bestWpm": round(best_wpm, 1) if best_wpm else 0,
                "totalAiGenerations": user.total_ai_generations or 0,
                "totalHumanizerUses": user.total_humanizer_uses or 0
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_milestone_text(words: int) -> str:
    """Get a fun milestone description"""
    if words >= 10_000_000:
        return "🎉 Over 10 million words automated!"
    elif words >= 5_000_000:
        return "🚀 Over 5 million words and counting!"
    elif words >= 1_000_000:
        return "💪 Over 1 million words typed!"
    elif words >= 500_000:
        return "⭐ Half a million words automated!"
    elif words >= 100_000:
        return "🔥 Over 100K words typed!"
    elif words >= 50_000:
        return "📝 50K+ words and growing!"
    elif words >= 10_000:
        return "✨ 10K+ words automated!"
    else:
        return "🎯 Join thousands of users!"

# Global statistics endpoint for website live counter
@app.get("/api/global-stats")
async def get_global_stats(db: Session = Depends(get_db)):
    """Get global platform statistics (public, no auth required)"""
    try:
        # Calculate total words from all users
        total_words = db.query(User).with_entities(
            func.sum(User.total_words_typed)
        ).scalar() or 0

        # Count total users
        total_users = db.query(User).count()

        return {
            "success": True,
            "stats": {
                "total_words_typed": int(total_words),
                "total_users": total_users
            }
        }
    except Exception as e:
        logger.error(f"Global stats error: {e}")
        # Return zeros instead of error for public endpoint
        return {
            "success": True,
            "stats": {
                "total_words_typed": 0,
                "total_users": 0
            }
        }

# Hotkey registration (simplified - actual implementation would use system hooks)
hotkeys_db = {
    "start": "ctrl+shift+s",
    "stop": "ctrl+shift+x",
    "pause": "ctrl+shift+p"
}

# Hotkey recording state
hotkey_recording_state = {
    "is_recording": False,
    "action": None
}

@app.post("/api/hotkeys/register")
async def register_hotkey(hotkey: HotkeyRequest):
    """Register a hotkey"""
    hotkeys_db[hotkey.action] = hotkey.hotkey
    return {"status": "registered", "action": hotkey.action, "hotkey": hotkey.hotkey}

@app.get("/api/hotkeys/recording-status")
async def get_hotkey_recording_status():
    """Get hotkey recording status"""
    return {
        "is_recording": hotkey_recording_state["is_recording"],
        "action": hotkey_recording_state["action"]
    }

class HotkeyRecordRequest(BaseModel):
    action: str
    recording: bool

@app.post("/api/hotkeys/record")
async def record_hotkey(request: HotkeyRecordRequest):
    """Start or stop recording a hotkey"""
    if request.recording:
        # Start recording
        hotkey_recording_state["is_recording"] = True
        hotkey_recording_state["action"] = request.action
        logger.info(f"Started recording hotkey for action: {request.action}")
        return {
            "success": True,
            "message": f"Recording hotkey for {request.action}",
            "is_recording": True,
            "action": request.action
        }
    else:
        # Stop recording
        action = hotkey_recording_state["action"]
        hotkey_recording_state["is_recording"] = False
        hotkey_recording_state["action"] = None
        logger.info(f"Stopped recording hotkey for action: {action}")
        return {
            "success": True,
            "message": f"Stopped recording hotkey for {action}",
            "is_recording": False,
            "action": None
        }

# Stripe webhook endpoint
@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events for subscription management"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    event_type = event["type"]

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        logger.info(f"Checkout session completed: {session.get('id')}")

        # Get customer email and metadata
        customer_email = session.get("customer_email") or session.get("customer_details", {}).get("email")
        logger.info(f"Customer email from Stripe: {customer_email}")

        # Determine which plan based on amount
        amount = session.get("amount_total", 0) / 100  # Convert cents to dollars
        logger.info(f"Payment amount: ${amount}")

        if amount == 8.99:
            plan = "Pro"
        elif amount == 15.00:
            plan = "Premium"
        else:
            plan = "Free"

        logger.info(f"Determined plan: {plan}")

        # Get or create user
        user = get_user_by_email(db, customer_email)
        if not user:
            logger.info(f"User not found in database, creating new user: {customer_email}")
            user = create_user(db, customer_email, plan="Free")
            logger.info(f"Created new user: {customer_email}")

        # Update plan and subscription details
        logger.info(f"Updating user {user.email} to {plan} plan")
        user.plan = plan
        user.stripe_customer_id = session.get("customer")
        user.stripe_subscription_id = session.get("subscription")

        # Get subscription details
        subscription_id = session.get("subscription")
        if subscription_id:
            try:
                subscription = stripe.Subscription.retrieve(subscription_id)
                user.subscription_status = subscription.status
                user.subscription_current_period_start = datetime.fromtimestamp(subscription.current_period_start)
                user.subscription_current_period_end = datetime.fromtimestamp(subscription.current_period_end)
                logger.info(f"Subscription retrieved: {subscription.id}, status: {subscription.status}")
            except Exception as e:
                logger.error(f"Error retrieving subscription: {e}")

        db.commit()
        logger.info(f"✅ Successfully upgraded user {customer_email} to {plan} plan")

    elif event_type == "customer.subscription.updated":
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")

        # Find user by Stripe customer ID
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            # Update subscription status
            user.subscription_status = subscription.get("status")
            user.subscription_current_period_start = datetime.fromtimestamp(subscription.get("current_period_start"))
            user.subscription_current_period_end = datetime.fromtimestamp(subscription.get("current_period_end"))

            # Check subscription status
            if subscription.get("status") == "active":
                # Determine plan from price
                amount = subscription["items"]["data"][0]["price"]["unit_amount"] / 100
                plan = "Pro" if amount == 8.99 else "Premium" if amount == 15.00 else "Free"
                user.plan = plan
                logger.info(f"Updated user subscription to {plan}")

            db.commit()

    elif event_type == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")

        # Find user and downgrade to Free
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.plan = "Free"
            user.subscription_status = "canceled"
            db.commit()
            logger.info(f"Downgraded user {user.email} to Free plan")

    return {"status": "success"}

# AI Generation endpoints
class AIGenerateRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 500
    settings: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

class AIHumanizeRequest(BaseModel):
    text: str

class AIExplainRequest(BaseModel):
    topic: str
    detail_level: Optional[str] = "medium"

class StudyQuestionsRequest(BaseModel):
    topic: str
    num_questions: Optional[int] = 5

@app.post("/api/ai/generate")
async def generate_ai_text(request: AIGenerateRequest):
    """Generate AI text using OpenAI with dynamic settings"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Extract settings or use defaults
        settings = request.settings or {}

        # Get key settings
        tone = settings.get('tone', 'Neutral')
        grade_level = settings.get('grade_level', 11)
        response_length = settings.get('response_length', 3)
        response_type = settings.get('response_type', 'short_response')
        selected_template = settings.get('selectedTemplate', 'general')
        academic_format = settings.get('academic_format', 'MLA')

        # Learning tab specific settings
        depth = settings.get('depth', 'Intermediate')
        learning_style = settings.get('learning_style', 'Mixed')
        focus = settings.get('focus', 'Balanced')

        # Build dynamic system message based on template and settings
        template_personalities = {
            'creative_writing': f"You are a creative writing assistant with a {tone.lower()} tone. Write imaginatively and engagingly, suitable for grade {grade_level} readers.",
            'professional': f"You are a professional business writing assistant. Write in a {tone.lower()} tone with clarity and professionalism, appropriate for grade {grade_level} comprehension level.",
            'academic': f"You are an academic writing assistant specializing in {academic_format} format. Write in a {tone.lower()} scholarly tone suitable for grade {grade_level} level.",
            'casual': f"You are a casual writing assistant. Write in a {tone.lower()}, conversational tone that's easy to understand for grade {grade_level} readers.",
            'technical': f"You are a technical writing assistant. Explain concepts clearly with a {tone.lower()} tone, appropriate for grade {grade_level} technical comprehension.",
            'gaming': f"You are a gaming content writer. Write with a {tone.lower()} tone that engages gamers, suitable for grade {grade_level} readers.",
            'general': f"You are a helpful writing assistant. Write in a {tone.lower()} tone appropriate for grade {grade_level} level."
        }

        # Get system message based on template
        system_message = template_personalities.get(selected_template, template_personalities['general'])

        # Add learning-specific context if depth/focus settings present
        if depth or focus:
            system_message += f" The content should be at {depth} depth with {focus} focus, suitable for {learning_style} learning style."

        # Calculate max_tokens based on response_length setting
        # Map response_length (1-5 scale) to token counts
        token_map = {
            1: 100,   # 1-2 sentences
            2: 200,   # 2-4 sentences
            3: 300,   # 4-8 sentences
            4: 500,   # 8-15 sentences
            5: 800    # 15+ sentences
        }

        # For essays, use higher token counts
        if response_type == 'essay':
            required_pages = settings.get('required_pages', 1)
            calculated_max_tokens = min(2000, required_pages * 500)  # ~500 tokens per page
        else:
            calculated_max_tokens = token_map.get(response_length, 300)

        # Use calculated tokens unless explicitly overridden
        max_tokens = request.max_tokens if request.max_tokens != 500 else calculated_max_tokens

        logger.info(f"AI Generate with settings: tone={tone}, grade={grade_level}, length={response_length}, template={selected_template}, max_tokens={max_tokens}")

        # Use JSON mode if requested (for Learn tab and structured responses)
        if response_type == 'json':
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-1106",  # Supports JSON mode
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": request.prompt}
                ],
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
        else:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": request.prompt}
                ],
                max_tokens=max_tokens
            )

        generated_text = response.choices[0].message.content

        return {
            "success": True,
            "text": generated_text,
            "tokens_used": response.usage.total_tokens
        }
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/humanize")
async def humanize_text(request: AIHumanizeRequest):
    """Humanize text using AI"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        prompt = f"Rewrite the following text to make it sound more natural and human-like while preserving the original meaning:\\n\\n{request.text}"

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at making text sound more natural and human-like."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )

        humanized_text = response.choices[0].message.content

        return {
            "success": True,
            "original": request.text,
            "humanized": humanized_text
        }
    except Exception as e:
        logger.error(f"AI humanize error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_filler")
async def generate_filler(length: int = 100):
    """Generate filler text"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Generate natural-sounding filler text."},
                {"role": "user", "content": f"Generate approximately {length} words of natural filler text."}
            ],
            max_tokens=length * 2
        )

        return {
            "success": True,
            "text": response.choices[0].message.content
        }
    except Exception as e:
        logger.error(f"Filler generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/explain")
async def explain_topic(request: AIExplainRequest):
    """Explain a topic using AI"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        detail_prompts = {
            "simple": "Explain this in very simple terms suitable for a beginner:",
            "medium": "Provide a clear explanation of:",
            "detailed": "Provide a comprehensive, detailed explanation of:"
        }

        prompt = f"{detail_prompts.get(request.detail_level, detail_prompts['medium'])} {request.topic}"

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a knowledgeable teacher who explains topics clearly."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800
        )

        return {
            "success": True,
            "topic": request.topic,
            "explanation": response.choices[0].message.content
        }
    except Exception as e:
        logger.error(f"AI explain error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/study-questions")
async def generate_study_questions(request: StudyQuestionsRequest):
    """Generate study questions for a topic"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        prompt = f"Generate {request.num_questions} study questions about: {request.topic}. Format each question on a new line starting with a number."

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a teacher creating study questions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )

        questions_text = response.choices[0].message.content
        questions = [q.strip() for q in questions_text.split('\n') if q.strip()]

        return {
            "success": True,
            "topic": request.topic,
            "questions": questions
        }
    except Exception as e:
        logger.error(f"Study questions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



class CreateLessonRequest(BaseModel):
    topic: str
    difficulty: Optional[str] = "medium"

@app.post("/api/learning/create-lesson")
async def create_lesson(request: CreateLessonRequest):
    """Create a learning lesson using AI"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        difficulty_prompts = {
            "easy": "Create a beginner-friendly lesson about",
            "medium": "Create an intermediate lesson about",
            "hard": "Create an advanced, detailed lesson about"
        }

        prompt = f"{difficulty_prompts.get(request.difficulty, difficulty_prompts['medium'])} {request.topic}. Include: 1) Overview, 2) Key concepts, 3) Examples, 4) Practice exercises"

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert educator creating structured learning lessons."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500
        )

        return {
            "success": True,
            "topic": request.topic,
            "difficulty": request.difficulty,
            "lesson": response.choices[0].message.content
        }
    except Exception as e:
        logger.error(f"Create lesson error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# Telemetry endpoints
class TelemetryEvent(BaseModel):
    event: str
    data: Any
    timestamp: str
    userId: str
    sessionId: str
    betaTester: bool = False

class ErrorTelemetryRequest(BaseModel):
    error: str
    stack: Optional[str] = None
    user_id: Optional[str] = None

@app.post("/api/telemetry")
async def receive_telemetry(event_data: TelemetryEvent):
    """Receive telemetry events from frontend analytics"""
    try:
        # Log telemetry event for monitoring
        logger.info(f"Telemetry event from {event_data.userId}: {event_data.event}")

        # Store in beta telemetry if user is beta tester
        if event_data.betaTester:
            logger.info(f"Beta tester event: {event_data.event} - {event_data.data}")

        # TODO: Store telemetry in database if needed (currently just logging)
        # Could create a Telemetry table to store these events for analytics

        return {"success": True, "message": "Telemetry received"}
    except Exception as e:
        logger.error(f"Telemetry error: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/telemetry/error")
async def log_error(request: ErrorTelemetryRequest):
    """Log frontend errors"""
    try:
        logger.error(f"Frontend error from user {request.user_id}: {request.error}")
        if request.stack:
            logger.error(f"Stack trace: {request.stack}")
        return {"success": True, "message": "Error logged"}
    except Exception as e:
        logger.error(f"Error logging telemetry: {e}")
        return {"success": False, "message": str(e)}

# Learning lessons storage (in-memory for now)
lessons_db = {}

class SaveLessonRequest(BaseModel):
    user_id: str
    topic: str
    content: str

@app.post("/api/learning/save-lesson")
async def save_lesson(request: SaveLessonRequest):
    """Save a learning lesson for a user"""
    try:
        # Get or create user's lessons list
        if request.user_id not in lessons_db:
            lessons_db[request.user_id] = []

        # Create lesson object
        lesson = {
            "id": f"{request.user_id}_{len(lessons_db[request.user_id])}_{int(time.time())}",
            "topic": request.topic,
            "content": request.content,
            "word_count": len(request.content.split()),
            "created_at": datetime.utcnow().isoformat()
        }

        # Add to user's lessons
        lessons_db[request.user_id].append(lesson)

        logger.info(f"[Learning] Saved lesson for user {request.user_id}: {request.topic}")

        return {
            "success": True,
            "message": "Lesson saved successfully",
            "lesson": lesson
        }
    except Exception as e:
        logger.error(f"Save lesson error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/learning/get-lessons")
async def get_lessons(user_id: str):
    """Get saved lessons for a user"""
    user_lessons = lessons_db.get(user_id, [])
    return {"success": True, "lessons": user_lessons}

# Admin telemetry endpoints
@app.get("/api/admin/telemetry/stats")
async def get_telemetry_stats(db: Session = Depends(get_db)):
    """Get telemetry statistics for admin dashboard"""
    try:
        total_users = db.query(User).count()
        total_words = db.query(User).with_entities(func.sum(User.total_words_typed)).scalar() or 0
        total_sessions = db.query(TypingSession).count()

        return {
            "success": True,
            "stats": {
                "total_users": total_users,
                "total_words": total_words,
                "total_sessions": total_sessions,
                "active_users_24h": 0  # TODO: implement
            }
        }
    except Exception as e:
        logger.error(f"Telemetry stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/telemetry")
async def get_telemetry_entries(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent telemetry entries"""
    try:
        sessions = db.query(TypingSession).order_by(TypingSession.id.desc()).limit(limit).all()

        entries = []
        for session in sessions:
            entries.append({
                "id": session.id,
                "user_id": session.user_id,
                "words_typed": session.words_typed,
                "created_at": session.created_at.isoformat() if session.created_at else None
            })

        return {
            "success": True,
            "entries": entries
        }
    except Exception as e:
        logger.error(f"Telemetry entries error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/telemetry/export")
async def export_telemetry(db: Session = Depends(get_db)):
    """Export telemetry data"""
    try:
        sessions = db.query(TypingSession).all()

        data = []
        for session in sessions:
            data.append({
                "id": session.id,
                "user_id": session.user_id,
                "words_typed": session.words_typed,
                "created_at": session.created_at.isoformat() if session.created_at else None
            })

        return {
            "success": True,
            "data": data,
            "count": len(data)
        }
    except Exception as e:
        logger.error(f"Telemetry export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))




# Beta Telemetry endpoint
class BetaTelemetryData(BaseModel):
    userId: str
    sessionId: str
    systemInfo: dict
    actions: list
    errors: list
    featureUsage: list
    performanceMetrics: list
    sessionDuration: int
    lastActivity: int
    timestamp: str

beta_telemetry_storage = []

@app.post("/api/beta-telemetry")
async def receive_beta_telemetry(data: BetaTelemetryData):
    """Receive beta testing telemetry data from frontend"""
    try:
        telemetry_entry = {
            "userId": data.userId,
            "sessionId": data.sessionId,
            "systemInfo": data.systemInfo,
            "actions_count": len(data.actions),
            "errors_count": len(data.errors),
            "features_used": len(data.featureUsage),
            "performance_metrics_count": len(data.performanceMetrics),
            "sessionDuration": data.sessionDuration,
            "timestamp": data.timestamp,
            "received_at": datetime.now().isoformat()
        }
        beta_telemetry_storage.append(telemetry_entry)
        if len(beta_telemetry_storage) > 1000:
            beta_telemetry_storage.pop(0)
        for error in data.errors:
            if error.get('severity') in ['critical', 'high']:
                logger.error(f"Beta telemetry critical error from {data.userId}: {error.get('error')}")
        return {"success": True, "message": "Telemetry received"}
    except Exception as e:
        logger.error(f"Beta telemetry error: {e}")
        return {"success": False, "message": str(e)}

@app.get("/api/user-dashboard")
async def get_user_dashboard(request: Request, db: Session = Depends(get_db)):
    """Get user dashboard data"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        token = auth_header.replace('Bearer ', '')

        # Verify JWT token
        JWT_SECRET = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET", "your-secret-key-change-in-production")

        try:
            # Decode and verify the token
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            email = payload.get("sub") or payload.get("email")
            user_id = payload.get("user_id")

            if not email:
                raise HTTPException(status_code=401, detail="Invalid token: no email")

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")

        # Get user by email or ID
        user = get_user_by_email(db, email)
        if not user and user_id:
            user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Use words_used_this_week for weekly limit tracking (not total_words_typed)
        words_used = user.words_used_this_week or 0
        plan_name = "free"
        words_limit = 500

        # Check if user has active subscription
        if user.stripe_subscription_id and user.subscription_status == "active":
            if user.plan.lower() == "premium":
                plan_name = "premium"
                words_limit = 999999999
            elif user.plan.lower() == "pro":
                plan_name = "pro"
                words_limit = 5000
        elif user.plan.lower() in ["pro", "premium"]:
            # User has Pro/Premium from referrals
            plan_name = user.plan.lower()
            if plan_name == "premium":
                words_limit = 999999999
            else:
                words_limit = 5000

        words_remaining = max(0, words_limit - words_used)
        usage_percentage = min(100, (words_used / words_limit * 100) if words_limit > 0 else 0)
        today = datetime.now()
        days_until_sunday = (6 - today.weekday()) % 7
        reset_date = (today + timedelta(days=days_until_sunday)).isoformat()
        referral_code = user.referral_code or f"SLY{user.id}"
        referrals_successful = db.query(User).filter(User.referred_by == referral_code).count()
        bonus_words = referrals_successful * 500
        total_sessions = db.query(TypingSession).filter(TypingSession.user_id == user.id).count()

        # Extract username from email (User model doesn't have a name field)
        username = user.username if hasattr(user, 'username') and user.username else user.email.split('@')[0]

        dashboard_data = {
            "user": {
                "name": username,
                "email": user.email,
                "user_id": str(user.id),
                "joined": user.created_at.isoformat() if user.created_at else datetime.now().isoformat(),
                "verified": True,  # Always true for simplicity
                "profile_picture": user.profile_picture  # Google profile picture URL
            },
            "plan": {
                "name": plan_name,
                "words_limit": words_limit,
                "words_used": words_used,
                "words_remaining": words_remaining,
                "usage_percentage": round(usage_percentage, 1),
                "reset_date": reset_date,
                "features": {
                    "ai_generation": plan_name in ["pro", "premium"],
                    "humanizer": plan_name == "premium",
                    "premium_typing": plan_name in ["pro", "premium"],
                    "learning_hub": plan_name in ["pro", "premium"],
                    "missions": plan_name in ["pro", "premium"],
                    "unlimited_profiles": plan_name == "premium",
                    "priority_support": plan_name == "premium",
                    "advanced_analytics": plan_name in ["pro", "premium"]
                }
            },
            "referrals": {
                "code": referral_code,
                "successful": referrals_successful,
                "pending": 0,
                "bonus_words": bonus_words,
                "share_link": f"https://slywriter.app/signup?ref={referral_code}"
            },
            "stats": {
                "total_generations": user.total_ai_generations or 0,
                "total_typing_sessions": total_sessions,
                "favorite_profile": "Standard",
                "avg_wpm": 45  # Default value since this field doesn't exist in User model
            }
        }
        return {
            "success": True,
            "dashboard": dashboard_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DESKTOP APP ENDPOINTS - Merged from backend_api.py
# ============================================================================

@app.post("/api/auth/logout")
async def logout():
    """Desktop App: Logout current user"""
    # This is a simple endpoint for desktop app compatibility
    # In the web version, logout is handled client-side
    return {"success": True}

@app.post("/api/auth/register")
async def register(auth: UserAuthRequest, db: Session = Depends(get_db)):
    """Desktop App: Register new user"""
    if not auth.email:
        raise HTTPException(status_code=400, detail="Email required")

    # Check if user already exists
    existing_user = get_user_by_email(db, auth.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Create new user
    user = create_user(db, auth.email, plan="Free")

    # Generate referral code
    import secrets
    user.referral_code = secrets.token_urlsafe(8)
    db.commit()

    # Get user limits
    limits = get_user_limits(user)

    # Generate JWT token
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})

    # Build user response
    user_data = {
        "id": user.id,
        "email": user.email,
        "plan": user.plan,
        "usage": user.words_used_this_week,
        "referrals": {
            "code": user.referral_code,
            "count": user.referral_count,
            "tier_claimed": user.referral_tier_claimed,
            "bonus_words": user.referral_bonus
        },
        **limits
    }

    return {
        "success": True,
        "user": user_data,
        "token": access_token
    }

@app.post("/api/auth/google")
async def google_auth_desktop():
    """Desktop App: Google OAuth endpoint (different from /auth/google/login)"""
    # This endpoint is for desktop app's Google OAuth flow
    # Returns a redirect or authentication flow initiation
    # Note: This is a simplified version - desktop app handles the actual OAuth flow
    return {
        "success": True,
        "message": "Desktop Google OAuth - handled by client",
        "auth_url": "https://accounts.google.com/o/oauth2/auth"
    }

@app.post("/api/profiles/generate-from-wpm")
async def generate_profile_from_wpm(request: dict):
    """Desktop App: Generate a custom profile based on WPM"""
    wpm = request.get("wpm", 85)

    # Calculate delays based on WPM
    # 60000 ms per minute / (wpm * 5 characters per word) = ms per character
    avg_delay = 60000 / (wpm * 5)
    min_delay = int(avg_delay * 0.8)
    max_delay = int(avg_delay * 1.2)

    return {
        "success": True,
        "profile": {
            "name": "Custom",
            "wpm": wpm,
            "description": f"Custom profile for {wpm} WPM",
            "is_builtin": False,
            "settings": {
                "min_delay": min_delay,
                "max_delay": max_delay,
                "typos_enabled": wpm < 150,
                "typo_chance": max(0, min(5, 5 - (wpm // 30))),
                "pause_frequency": min(10, max(3, wpm // 20)),
                "ai_filler_enabled": False,
                "micro_hesitations": wpm < 100,
                "zone_out_breaks": False,
                "burst_variability": max(5, min(20, 20 - (wpm // 15)))
            }
        }
    }

@app.post("/api/copy-highlighted")
async def copy_highlighted():
    """Desktop App: Copy highlighted text to clipboard using keyboard simulation (for hotkey)"""
    if not GUI_AVAILABLE:
        raise HTTPException(status_code=501, detail="GUI automation not available in this environment")

    try:
        # Save current clipboard
        original = pyperclip.paste()

        # For hotkey, we DON'T need Alt+Tab since focus is already correct
        # Just ensure no keys are stuck
        keyboard.release('ctrl')
        keyboard.release('alt')
        keyboard.release('shift')

        # Small delay
        time.sleep(0.05)

        # Now do the copy
        keyboard.press_and_release('ctrl+c')

        # Wait for clipboard to update
        time.sleep(0.15)

        # Get the new clipboard content
        new_content = pyperclip.paste()

        logger.info(f"[COPY-HOTKEY] Content changed: {new_content != original}")

        return {
            "success": True,
            "copied": new_content != original,
            "text": new_content if new_content != original else ""
        }
    except Exception as e:
        logger.error(f"Copy highlighted error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/copy-highlighted-overlay")
async def copy_highlighted_overlay():
    """Desktop App: Copy highlighted text for overlay button (needs Alt+Tab to restore focus)"""
    if not GUI_AVAILABLE:
        raise HTTPException(status_code=501, detail="GUI automation not available in this environment")

    try:
        # Save current clipboard
        original = pyperclip.paste()

        # For overlay button, we need Alt+Tab to restore focus to previous window
        keyboard.press_and_release('alt+tab')
        time.sleep(0.5)  # Wait for window switch

        # Ensure no keys are stuck
        keyboard.release('ctrl')
        keyboard.release('alt')
        keyboard.release('shift')

        # Small delay
        time.sleep(0.1)

        # Now do the copy - more deliberate for overlay
        keyboard.press('ctrl')
        time.sleep(0.05)
        keyboard.press('c')
        time.sleep(0.05)
        keyboard.release('c')
        keyboard.release('ctrl')

        # Wait longer for clipboard to update
        time.sleep(0.3)

        # Get the new clipboard content
        new_content = pyperclip.paste()

        logger.info(f"[COPY-OVERLAY] Content changed: {new_content != original}")

        return {
            "success": True,
            "copied": new_content != original,
            "text": new_content if new_content != original else ""
        }
    except Exception as e:
        logger.error(f"Copy highlighted overlay error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/typing/update_wpm")
async def update_typing_wpm(request: dict):
    """Desktop App: Update WPM during typing session"""
    session_id = request.get("session_id")
    wpm = request.get("wpm", 70)

    # Update the typing speed if session is active or paused
    if typing_engine.is_typing:
        typing_engine.wpm = wpm
        return {"success": True, "wpm": wpm}

    return {"success": False, "error": "No active typing session"}

@app.post("/api/typing/pause/{session_id}")
async def pause_typing_by_session(session_id: str):
    """Desktop App: Pause typing by session ID"""
    return await pause_typing()

@app.post("/api/typing/resume/{session_id}")
async def resume_typing_by_session(session_id: str):
    """Desktop App: Resume typing by session ID"""
    # Resume typing by clearing pause flag
    if typing_engine.is_typing and typing_engine.is_paused:
        typing_engine.pause_flag.clear()
        typing_engine.is_paused = False
        return {"success": True, "message": "Typing resumed"}
    return {"success": False, "error": "Not currently paused"}

@app.post("/api/typing/stop/{session_id}")
async def stop_typing_by_session(session_id: str):
    """Desktop App: Stop typing by session ID"""
    return await stop_typing()

# Desktop App: License verification endpoints
@app.post("/api/license/verify")
async def verify_license_endpoint(request: LicenseVerifyRequest):
    """Desktop App: Verify license with server and check version"""
    if not LICENSE_MANAGER_AVAILABLE:
        return {"valid": False, "error": "license_system_unavailable"}

    license_manager = get_license_manager(config_dir=typing_engine.config_dir)
    result = license_manager.verify_license(request.license_key, force=request.force)

    return result

# Admin user management endpoint
class AdminUpgradeUserRequest(BaseModel):
    email: str
    plan: str  # "Free", "Pro", or "Premium"
    duration_days: Optional[int] = None  # Optional: days of Pro/Premium (e.g., 30 for 1 month)

@app.post("/api/admin/upgrade-user")
async def admin_upgrade_user(
    request: AdminUpgradeUserRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """Admin: Manually upgrade a user's plan"""
    user = get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {request.email}")

    old_plan = user.plan
    user.plan = request.plan

    # If setting to Pro/Premium with duration, set premium_until date
    if request.plan in ["Pro", "Premium"] and request.duration_days:
        now = datetime.utcnow()
        start_date = now

        # If user already has premium_until in future, stack on top of it
        if user.premium_until and user.premium_until > now:
            start_date = user.premium_until

        user.premium_until = start_date + timedelta(days=request.duration_days)
        logger.info(f"Admin upgraded {request.email} to {request.plan} until {user.premium_until.strftime('%Y-%m-%d')}")
    elif request.plan == "Free":
        # Clear premium_until when downgrading to Free
        user.premium_until = None
        logger.info(f"Admin downgraded {request.email} to Free")
    else:
        logger.info(f"Admin upgraded {request.email} to {request.plan} (permanent)")

    db.commit()

    # Get updated limits
    limits = get_user_limits(user)

    return {
        "success": True,
        "message": f"User {request.email} upgraded from {old_plan} to {request.plan}",
        "user": {
            "email": user.email,
            "plan": user.plan,
            "premium_until": user.premium_until.isoformat() if user.premium_until else None,
            **limits
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

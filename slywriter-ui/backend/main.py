"""
SlyWriter Backend Server
FastAPI server that handles all typing automation and backend functionality
"""

from fastapi import FastAPI, WebSocket, HTTPException, Depends, BackgroundTasks, Request
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

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional GUI automation imports (only available in local/desktop mode)
try:
    import pyautogui
    import keyboard
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

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "675434683795-shrls6suu68dj0cuvqct28gf3o6u3jav.apps.googleusercontent.com")

app = FastAPI(title="SlyWriter Backend", version="2.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://slywriter.ai",
        "https://www.slywriter.ai",
        "https://slywriter-ui.onrender.com"
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

# API Routes
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}

@app.post("/api/typing/start")
async def start_typing(request: TypingStartRequest, background_tasks: BackgroundTasks):
    """Start typing with specified parameters"""
    if typing_engine.is_typing:
        raise HTTPException(status_code=400, detail="Already typing")
    
    if not request.text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    # Reset engine state
    typing_engine.reset()
    typing_engine.is_typing = True

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

    return {"status": "started", "message": "Typing started successfully"}

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
@app.post("/api/profiles/save")
async def save_profile(profile: ProfileRequest):
    """Save a typing profile"""
    profiles_db[profile.name] = profile.settings
    return {"status": "saved", "message": f"Profile '{profile.name}' saved"}

@app.get("/api/profiles")
async def get_profiles():
    """Get all saved profiles"""
    return {"profiles": profiles_db}

@app.delete("/api/profiles/{name}")
async def delete_profile(name: str):
    """Delete a profile"""
    if name in profiles_db:
        del profiles_db[name]
        return {"status": "deleted", "message": f"Profile '{name}' deleted"}
    raise HTTPException(status_code=404, detail="Profile not found")

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
        "token": f"token_{user.id}"
    }

@app.post("/auth/google/login")
async def google_login(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth login"""
    try:
        data = await request.json()
        credential = data.get("credential")
        
        if not credential:
            raise HTTPException(status_code=400, detail="No credential provided")
        
        # Verify the Google ID token
        try:
            idinfo = id_token.verify_oauth2_token(
                credential, 
                google_requests.Request(), 
                GOOGLE_CLIENT_ID
            )
            
            # Get email from token
            email = idinfo.get("email")
            if not email:
                raise HTTPException(status_code=400, detail="Email not found in token")
                
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
        else:
            user.last_login = datetime.utcnow()
            db.commit()
        
        # Check for weekly reset
        check_weekly_reset(db, user)
        
        # Generate referral code if needed
        if not user.referral_code:
            import secrets
            user.referral_code = secrets.token_urlsafe(8)
            db.commit()
        
        # Get user limits
        limits = get_user_limits(user)
        
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
            "token": f"token_{user.id}",
            "access_token": f"token_{user.id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stripe/create-checkout")
async def create_checkout_session(request: Request):
    """Create Stripe checkout session with pre-filled email"""
    try:
        data = await request.json()
        email = data.get("email")
        plan = data.get("plan")  # "Pro" or "Premium"

        if not email or not plan:
            raise HTTPException(status_code=400, detail="Email and plan required")

        # Get the price ID based on plan
        STRIPE_PRICES = {
            "Pro": os.getenv("STRIPE_PRO_PRICE_ID"),
            "Premium": os.getenv("STRIPE_PREMIUM_PRICE_ID")
        }

        price_id = STRIPE_PRICES.get(plan)
        if not price_id:
            raise HTTPException(status_code=400, detail="Invalid plan")

        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            customer_email=email,  # Pre-fill email
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://www.slywriter.ai/upgrade-success',
            cancel_url='https://www.slywriter.ai/pricing',
        )

        return {"checkout_url": checkout_session.url}

    except Exception as e:
        logger.error(f"Checkout creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

            # Calculate new premium_until date (Pro plan expiration)
            current_end = user.premium_until if user.premium_until and user.premium_until > datetime.utcnow() else datetime.utcnow()
            user.premium_until = current_end + timedelta(days=days)

            # Update plan to Pro if not already
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

# Global statistics endpoint
@app.get("/api/stats/global")
async def get_global_stats(db: Session = Depends(get_db)):
    """Get global platform statistics"""
    # Calculate total words from all users
    total_words = db.query(User).with_entities(
        func.sum(User.total_words_typed)
    ).scalar() or 0

    # Count total users
    total_users = db.query(User).count()

    # Count total sessions
    total_sessions = db.query(TypingSession).count()

    return {
        "total_words_typed": total_words,
        "total_words_display": f"{total_words:,}",
        "total_users": total_users,
        "total_sessions": total_sessions,
        "milestone_text": get_milestone_text(total_words)
    }

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

# Hotkey registration (simplified - actual implementation would use system hooks)
hotkeys_db = {
    "start": "ctrl+shift+s",
    "stop": "ctrl+shift+x",
    "pause": "ctrl+shift+p"
}

@app.post("/api/hotkeys/register")
async def register_hotkey(hotkey: HotkeyRequest):
    """Register a hotkey"""
    hotkeys_db[hotkey.action] = hotkey.hotkey
    return {"status": "registered", "action": hotkey.action, "hotkey": hotkey.hotkey}

@app.get("/api/hotkeys")
async def get_hotkeys():
    """Get all registered hotkeys"""
    return {"hotkeys": hotkeys_db}

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

# Manual subscription sync endpoint (fallback if webhooks fail)
@app.post("/api/stripe/sync-subscription")
async def sync_subscription(request: Request, db: Session = Depends(get_db)):
    """Manually sync Stripe subscription for a user (fallback if webhook fails)"""
    try:
        data = await request.json()
        email = data.get("email")

        if not email:
            raise HTTPException(status_code=400, detail="Email required")

        logger.info(f"Manual subscription sync requested for: {email}")

        # Get or create user
        user = get_user_by_email(db, email)
        if not user:
            logger.info(f"User not found in database, creating new user: {email}")
            user = create_user(db, email, plan="Free")
            logger.info(f"Created new user: {email}")

        # Search for customer in Stripe by email
        customers = stripe.Customer.list(email=email, limit=1)

        if not customers.data:
            return {
                "success": False,
                "message": "No Stripe customer found with this email"
            }

        customer = customers.data[0]
        logger.info(f"Found Stripe customer: {customer.id}")

        # Get active subscriptions
        subscriptions = stripe.Subscription.list(customer=customer.id, status="active", limit=1)

        if not subscriptions.data:
            return {
                "success": False,
                "message": "No active subscription found"
            }

        subscription = subscriptions.data[0]
        logger.info(f"Found active subscription: {subscription.id}")

        # Determine plan from price
        price = subscription["items"]["data"][0]["price"]
        amount = price["unit_amount"] / 100

        if amount == 8.99:
            plan = "Pro"
        elif amount == 15.00:
            plan = "Premium"
        else:
            plan = "Free"

        # Update user
        user.plan = plan
        user.stripe_customer_id = customer.id
        user.stripe_subscription_id = subscription.id
        user.subscription_status = subscription.status
        user.subscription_current_period_start = datetime.fromtimestamp(subscription.current_period_start)
        user.subscription_current_period_end = datetime.fromtimestamp(subscription.current_period_end)

        db.commit()
        logger.info(f"✅ Manually synced {email} to {plan} plan")

        return {
            "success": True,
            "message": f"Successfully upgraded to {plan} plan",
            "plan": plan
        }

    except Exception as e:
        logger.error(f"Manual sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# AI Generation endpoints
class AIGenerateRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 500

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
    """Generate AI text using OpenAI"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful writing assistant."},
                {"role": "user", "content": request.prompt}
            ],
            max_tokens=request.max_tokens
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
        
        prompt = f"Rewrite the following text to make it sound more natural and human-like while preserving the original meaning:

{request.text}"
        
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
        questions = [q.strip() for q in questions_text.split('
') if q.strip()]
        
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



# Error telemetry endpoint
class ErrorTelemetryRequest(BaseModel):
    error: str
    stack: Optional[str] = None
    user_id: Optional[str] = None

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

@app.get("/api/learning/get-lessons")
async def get_lessons(user_id: str):
    """Get saved lessons for a user"""
    user_lessons = lessons_db.get(user_id, [])
    return {"success": True, "lessons": user_lessons}

@app.post("/api/learning/save-lesson")
async def save_lesson(user_id: str, lesson: dict):
    """Save a lesson for a user"""
    if user_id not in lessons_db:
        lessons_db[user_id] = []
    lessons_db[user_id].append(lesson)
    return {"success": True, "message": "Lesson saved"}

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
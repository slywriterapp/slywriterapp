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
import pyautogui
import keyboard
from datetime import datetime
import logging
import os
import stripe
import hmac
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

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

# User management
users_db = {}
profiles_db = {}

# Global statistics
global_stats = {
    "total_words_typed": 0,
    "total_users": 0,
    "total_sessions": 0
}

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
        if not preview_mode:
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

    # Increment global session counter
    global_stats["total_sessions"] += 1

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
async def login(auth: UserAuthRequest):
    """User login"""
    # Simplified auth for now
    if auth.email:
        user_id = auth.email.replace("@", "_").replace(".", "_")
        users_db[user_id] = {
            "email": auth.email,
            "plan": "Free",
            "usage": 0,
            "limit": 500
        }
        return {
            "status": "success",
            "user": users_db[user_id],
            "token": f"token_{user_id}"
        }
    raise HTTPException(status_code=400, detail="Invalid credentials")

@app.post("/auth/verify-email")
async def verify_email(request: Request):
    """Verify email token - used by website"""
    try:
        data = await request.json()
        token = data.get("token")

        if not token:
            raise HTTPException(status_code=400, detail="Token required")

        # Verify JWT token
        import jwt
        from datetime import datetime, timedelta

        # You should set this as an environment variable in production
        JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")

        try:
            # Decode and verify the token
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            email = payload.get("email")

            if not email:
                raise HTTPException(status_code=400, detail="Invalid token: no email")

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")

        # Create or get user
        user_id = email.replace("@", "_").replace(".", "_")

        if user_id not in users_db:
            users_db[user_id] = {
                "email": email,
                "plan": "Free",
                "usage": 0,
                "humanizer_usage": 0,
                "ai_gen_usage": 0
            }

        return {
            "success": True,
            "user": users_db[user_id],
            "access_token": token  # Return the same token back
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/auth/user/{user_id}")
async def get_user(user_id: str):
    """Get user information with plan limits"""
    if user_id in users_db:
        user = users_db[user_id]

        # Plan limits (words per WEEK)
        PLAN_LIMITS = {
            "Free": 500,
            "Pro": 5000,
            "Premium": -1  # -1 indicates unlimited
        }

        # Humanizer limits (uses per WEEK)
        HUMANIZER_LIMITS = {
            "Free": 0,
            "Pro": 3,
            "Premium": -1  # unlimited
        }

        # AI Generation limits (uses per WEEK)
        AI_GEN_LIMITS = {
            "Free": 3,
            "Pro": -1,  # unlimited
            "Premium": -1  # unlimited
        }

        # Add word limit to response
        plan = user.get("plan", "Free")
        word_limit = PLAN_LIMITS.get(plan, 500)
        humanizer_limit = HUMANIZER_LIMITS.get(plan, 0)
        ai_gen_limit = AI_GEN_LIMITS.get(plan, 3)

        # Get current usage (default to 0 if not tracked yet)
        current_usage = user.get("usage", 0)
        humanizer_usage = user.get("humanizer_usage", 0)
        ai_gen_usage = user.get("ai_gen_usage", 0)

        # Get week start date (for reset tracking)
        from datetime import datetime, timedelta
        week_start = user.get("week_start_date")
        if not week_start:
            # Initialize week start to last Monday
            today = datetime.now()
            days_since_monday = today.weekday()
            week_start = (today - timedelta(days=days_since_monday)).strftime("%Y-%m-%d")
            users_db[user_id]["week_start_date"] = week_start

        return {
            **user,
            "word_limit": word_limit,
            "word_limit_display": "Unlimited" if word_limit == -1 else f"{word_limit:,} words/week",
            "words_used": current_usage,
            "words_remaining": "Unlimited" if word_limit == -1 else max(0, word_limit - current_usage),
            "total_words_available": word_limit,  # Total words available this week (for website display)
            "humanizer_limit": humanizer_limit,
            "humanizer_limit_display": "Unlimited" if humanizer_limit == -1 else f"{humanizer_limit} uses/week",
            "humanizer_uses": humanizer_usage,
            "humanizer_remaining": "Unlimited" if humanizer_limit == -1 else max(0, humanizer_limit - humanizer_usage),
            "ai_gen_limit": ai_gen_limit,
            "ai_gen_limit_display": "Unlimited" if ai_gen_limit == -1 else f"{ai_gen_limit} uses/week",
            "ai_gen_uses": ai_gen_usage,
            "ai_gen_remaining": "Unlimited" if ai_gen_limit == -1 else max(0, ai_gen_limit - ai_gen_usage),
            "week_start_date": week_start
        }
    raise HTTPException(status_code=404, detail="User not found")

# Usage tracking
@app.post("/api/usage/track")
async def track_usage(user_id: str, words: int):
    """Track word usage"""
    if user_id in users_db:
        users_db[user_id]["usage"] = users_db[user_id].get("usage", 0) + words
        # Update global stats
        global_stats["total_words_typed"] += words
        return {"status": "tracked", "usage": users_db[user_id]["usage"]}
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/api/usage/track-humanizer")
async def track_humanizer(user_id: str):
    """Track humanizer usage"""
    if user_id in users_db:
        users_db[user_id]["humanizer_usage"] = users_db[user_id].get("humanizer_usage", 0) + 1
        return {"status": "tracked", "humanizer_usage": users_db[user_id]["humanizer_usage"]}
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/api/usage/track-ai-gen")
async def track_ai_gen(user_id: str):
    """Track AI generation usage"""
    if user_id in users_db:
        users_db[user_id]["ai_gen_usage"] = users_db[user_id].get("ai_gen_usage", 0) + 1
        return {"status": "tracked", "ai_gen_usage": users_db[user_id]["ai_gen_usage"]}
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/api/usage/check-reset")
async def check_reset(user_id: str):
    """Check if weekly usage should be reset"""
    from datetime import datetime, timedelta

    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    user = users_db[user_id]
    week_start = user.get("week_start_date")

    if not week_start:
        # First time - set to last Monday
        today = datetime.now()
        days_since_monday = today.weekday()
        week_start = (today - timedelta(days=days_since_monday)).strftime("%Y-%m-%d")
        users_db[user_id]["week_start_date"] = week_start
        return {"reset": False, "week_start": week_start}

    # Check if we've passed Monday since week_start
    week_start_date = datetime.strptime(week_start, "%Y-%m-%d")
    today = datetime.now()
    days_since_week_start = (today - week_start_date).days

    # If it's been 7+ days since week start, reset
    if days_since_week_start >= 7:
        # Find next Monday
        days_since_monday = today.weekday()
        new_week_start = (today - timedelta(days=days_since_monday)).strftime("%Y-%m-%d")

        # Reset all usage counters
        users_db[user_id]["usage"] = 0
        users_db[user_id]["humanizer_usage"] = 0
        users_db[user_id]["ai_gen_usage"] = 0
        users_db[user_id]["week_start_date"] = new_week_start

        logger.info(f"Reset weekly usage for user {user_id}")
        return {"reset": True, "week_start": new_week_start}

    return {"reset": False, "week_start": week_start}

# Global statistics endpoint
@app.get("/api/stats/global")
async def get_global_stats():
    """Get global platform statistics"""
    return {
        "total_words_typed": global_stats["total_words_typed"],
        "total_words_display": f"{global_stats['total_words_typed']:,}",
        "total_users": len(users_db),
        "total_sessions": global_stats["total_sessions"],
        "milestone_text": get_milestone_text(global_stats["total_words_typed"])
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
async def stripe_webhook(request: Request):
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

        # Get customer email and metadata
        customer_email = session.get("customer_email") or session.get("customer_details", {}).get("email")

        # Determine which plan based on amount
        amount = session.get("amount_total", 0) / 100  # Convert cents to dollars

        if amount == 8.99:
            plan = "Pro"
        elif amount == 15.00:
            plan = "Premium"
        else:
            plan = "Free"

        # Find user by email and update plan
        for user_id, user_data in users_db.items():
            if user_data.get("email") == customer_email:
                users_db[user_id]["plan"] = plan
                users_db[user_id]["stripe_customer_id"] = session.get("customer")
                users_db[user_id]["subscription_id"] = session.get("subscription")
                logger.info(f"Upgraded user {customer_email} to {plan} plan")
                break

    elif event_type == "customer.subscription.updated":
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")

        # Find user by Stripe customer ID
        for user_id, user_data in users_db.items():
            if user_data.get("stripe_customer_id") == customer_id:
                # Check subscription status
                if subscription.get("status") == "active":
                    # Determine plan from price
                    amount = subscription["items"]["data"][0]["price"]["unit_amount"] / 100
                    plan = "Pro" if amount == 8.99 else "Premium" if amount == 15.00 else "Free"
                    users_db[user_id]["plan"] = plan
                    logger.info(f"Updated user subscription to {plan}")
                break

    elif event_type == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")

        # Find user and downgrade to Free
        for user_id, user_data in users_db.items():
            if user_data.get("stripe_customer_id") == customer_id:
                users_db[user_id]["plan"] = "Free"
                logger.info(f"Downgraded user to Free plan")
                break

    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
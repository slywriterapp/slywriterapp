"""
SlyWriter Backend Server
FastAPI server that handles all typing automation and backend functionality
"""

from fastapi import FastAPI, WebSocket, HTTPException, Depends, BackgroundTasks
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SlyWriter Backend", version="2.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
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
            "plan": "premium",
            "usage": 0,
            "limit": 100000
        }
        return {
            "status": "success",
            "user": users_db[user_id],
            "token": f"token_{user_id}"
        }
    raise HTTPException(status_code=400, detail="Invalid credentials")

@app.get("/api/auth/user/{user_id}")
async def get_user(user_id: str):
    """Get user information with plan limits"""
    if user_id in users_db:
        user = users_db[user_id]

        # Plan limits (words per day)
        PLAN_LIMITS = {
            "Free": 10000,
            "Basic": 10000,
            "Pro": 50000,
            "Premium": -1  # -1 indicates unlimited
        }

        # Add word limit to response
        plan = user.get("plan", "Free")
        word_limit = PLAN_LIMITS.get(plan, 10000)

        return {
            **user,
            "word_limit": word_limit,
            "word_limit_display": "Unlimited" if word_limit == -1 else f"{word_limit:,} words/day"
        }
    raise HTTPException(status_code=404, detail="User not found")

# Usage tracking
@app.post("/api/usage/track")
async def track_usage(user_id: str, words: int):
    """Track word usage"""
    if user_id in users_db:
        users_db[user_id]["usage"] += words
        return {"status": "tracked", "usage": users_db[user_id]["usage"]}
    raise HTTPException(status_code=404, detail="User not found")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
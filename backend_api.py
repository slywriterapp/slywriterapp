# backend_api.py - FastAPI backend for SlyWriter
# This wraps existing Python functionality in a REST API

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import json
import threading
import time
from datetime import datetime

# Import existing modules
import typing_engine as engine
import premium_typing
import auth  # Changed - import module directly
from config import *
try:
    import sly_config
except ImportError:
    # Fallback if sly_config doesn't exist
    class sly_config:
        @staticmethod
        def load_config():
            return {
                "settings": {
                    "hotkeys": {},
                    "theme": "dark"
                }
            }
        @staticmethod
        def save_config(config):
            pass

try:
    from account_usage import AccountUsageManager
except ImportError:
    # Create a simple fallback
    class AccountUsageManager:
        def __init__(self, email):
            self.email = email
        def is_premium(self):
            return True  # Default to premium for testing
        def has_words_remaining(self):
            return True
        def get_words_used(self):
            return 0
        def get_word_limit(self):
            return 10000
        def get_reset_time(self):
            return "24:00"

# Initialize FastAPI app
app = FastAPI(title="SlyWriter API", version="2.0.0")

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state management
class AppState:
    def __init__(self):
        self.typing_active = False
        self.typing_paused = False
        self.current_session = None
        self.usage_manager = None
        self.user = auth.get_saved_user()  # Try to load saved user
        self.config = sly_config.load_config()
        self.websocket_clients = []
        self.typing_progress = {
            'chars_typed': 0,
            'total_chars': 0,
            'wpm': 0,
            'status': 'ready'
        }

state = AppState()

# Pydantic models for request/response
class TypingRequest(BaseModel):
    text: str
    min_delay: float = 0.05
    max_delay: float = 0.15
    typos_enabled: bool = False
    pause_frequency: int = 5
    preview_only: bool = False
    ai_filler_enabled: bool = False

class ConfigUpdate(BaseModel):
    settings: Dict[str, Any]

class HotkeyUpdate(BaseModel):
    key: str
    value: str

# API Endpoints

@app.get("/")
async def root():
    return {"status": "SlyWriter API Running", "version": "2.0.0"}

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "typing_active": state.typing_active,
        "user_authenticated": state.user is not None
    }

# Authentication endpoints
@app.post("/api/auth/google")
async def google_auth():
    """Authenticate with Google OAuth - triggers browser flow"""
    try:
        # This will open browser for OAuth
        user_info = auth.sign_in_with_google()
        state.user = user_info
        
        # Initialize usage manager
        if user_info:
            state.usage_manager = AccountUsageManager(user_info.get('email'))
            
        return {
            "success": True,
            "user": {
                "email": user_info.get('email'),
                "name": user_info.get('name'),
                "picture": user_info.get('picture'),
                "is_premium": state.usage_manager.is_premium() if state.usage_manager else False
            }
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/api/auth/status")
async def auth_status():
    """Get current authentication status"""
    if state.user:
        return {
            "authenticated": True,
            "user": {
                "email": state.user.get('email'),
                "name": state.user.get('name'),
                "picture": state.user.get('picture'),
                "is_premium": state.usage_manager.is_premium() if state.usage_manager else False
            }
        }
    return {"authenticated": False}

@app.post("/api/auth/logout")
async def logout():
    """Logout current user"""
    state.user = None
    state.usage_manager = None
    return {"success": True}

# Typing control endpoints
@app.post("/api/typing/start")
async def start_typing(typing_req: TypingRequest, background_tasks: BackgroundTasks):
    """Start typing operation"""
    if state.typing_active:
        raise HTTPException(status_code=400, detail="Typing already in progress")
    
    # Check usage limits
    if state.usage_manager and not state.usage_manager.has_words_remaining():
        raise HTTPException(status_code=403, detail="Daily word limit reached. Upgrade to premium for unlimited typing.")
    
    state.typing_active = True
    state.typing_progress['status'] = 'typing'
    state.typing_progress['total_chars'] = len(typing_req.text)
    state.typing_progress['chars_typed'] = 0
    
    # Define callbacks for live updates
    def update_preview(text):
        state.typing_progress['chars_typed'] = len(text)
        # Note: We'll update websocket clients periodically instead
    
    def update_status(status):
        state.typing_progress['status'] = status
        # Note: We'll update websocket clients periodically instead
    
    # Start typing in background
    if typing_req.ai_filler_enabled and state.usage_manager and state.usage_manager.is_premium():
        # Use premium typing with AI filler
        background_tasks.add_task(
            run_premium_typing,
            typing_req.text,
            update_preview,
            update_status,
            typing_req
        )
    else:
        # Use regular typing engine
        background_tasks.add_task(
            run_regular_typing,
            typing_req.text,
            update_preview,
            update_status,
            typing_req
        )
    
    return {"success": True, "message": "Typing started"}

@app.post("/api/typing/stop")
async def stop_typing():
    """Stop typing operation"""
    if not state.typing_active:
        raise HTTPException(status_code=400, detail="No typing in progress")
    
    engine.stop_typing_func()
    state.typing_active = False
    state.typing_progress['status'] = 'stopped'
    await broadcast_status()
    
    return {"success": True, "message": "Typing stopped"}

@app.post("/api/typing/pause")
async def pause_typing():
    """Pause/resume typing operation"""
    if not state.typing_active:
        raise HTTPException(status_code=400, detail="No typing in progress")
    
    if state.typing_paused:
        engine.resume_typing()
        state.typing_paused = False
        state.typing_progress['status'] = 'typing'
        message = "Typing resumed"
    else:
        engine.pause_typing()
        state.typing_paused = True
        state.typing_progress['status'] = 'paused'
        message = "Typing paused"
    
    await broadcast_status()
    return {"success": True, "message": message}

@app.get("/api/typing/status")
async def typing_status():
    """Get current typing status"""
    return {
        "active": state.typing_active,
        "paused": state.typing_paused,
        "progress": state.typing_progress
    }

# Configuration endpoints
@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    return state.config

@app.post("/api/config")
async def update_config(config_update: ConfigUpdate):
    """Update configuration"""
    state.config.update(config_update.settings)
    sly_config.save_config(state.config)
    return {"success": True, "config": state.config}

@app.post("/api/config/hotkey")
async def update_hotkey(hotkey: HotkeyUpdate):
    """Update a specific hotkey"""
    if 'hotkeys' not in state.config['settings']:
        state.config['settings']['hotkeys'] = {}
    
    state.config['settings']['hotkeys'][hotkey.key] = hotkey.value
    sly_config.save_config(state.config)
    
    return {"success": True, "hotkeys": state.config['settings']['hotkeys']}

# Usage/Premium endpoints
@app.get("/api/usage")
async def get_usage():
    """Get usage statistics"""
    if not state.usage_manager:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "words_used": state.usage_manager.get_words_used(),
        "words_limit": state.usage_manager.get_word_limit(),
        "is_premium": state.usage_manager.is_premium(),
        "reset_time": state.usage_manager.get_reset_time()
    }

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time typing updates"""
    await websocket.accept()
    state.websocket_clients.append(websocket)
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "data": state.typing_progress
        })
        
        # Keep connection alive
        while True:
            await asyncio.sleep(1)
            # Ping to keep connection alive
            await websocket.send_json({"type": "ping"})
            
    except WebSocketDisconnect:
        state.websocket_clients.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in state.websocket_clients:
            state.websocket_clients.remove(websocket)

async def broadcast_status():
    """Broadcast status update to all websocket clients"""
    disconnected_clients = []
    
    for client in state.websocket_clients:
        try:
            await client.send_json({
                "type": "status",
                "data": state.typing_progress
            })
        except:
            disconnected_clients.append(client)
    
    # Remove disconnected clients
    for client in disconnected_clients:
        if client in state.websocket_clients:
            state.websocket_clients.remove(client)

# Helper functions
def run_regular_typing(text, preview_callback, status_callback, settings):
    """Run regular typing engine"""
    try:
        engine.start_typing_from_input(
            text=text,
            live_preview_callback=preview_callback,
            status_callback=status_callback,
            min_delay=settings.min_delay,
            max_delay=settings.max_delay,
            typos_on=settings.typos_enabled,
            pause_freq=settings.pause_frequency,
            preview_only=settings.preview_only
        )
    finally:
        state.typing_active = False
        state.typing_progress['status'] = 'completed'

def run_premium_typing(text, preview_callback, status_callback, settings):
    """Run premium typing with AI filler"""
    try:
        premium_typing.premium_type_with_filler(
            goal_text=text,
            live_preview_callback=preview_callback,
            status_callback=status_callback,
            min_delay=settings.min_delay,
            max_delay=settings.max_delay,
            typos_on=settings.typos_enabled,
            pause_freq=settings.pause_frequency,
            preview_only=settings.preview_only,
            stop_flag=engine._stop_flag,
            pause_flag=engine._pause_flag
        )
    finally:
        state.typing_active = False
        state.typing_progress['status'] = 'completed'

if __name__ == "__main__":
    import uvicorn
    print("Starting SlyWriter API on http://localhost:8000")
    print("API docs available at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
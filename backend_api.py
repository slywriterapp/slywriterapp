# backend_api.py - FastAPI backend for SlyWriter
# This wraps existing Python functionality in a REST API

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Header, Depends
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
import os
from dotenv import load_dotenv

# Import license manager
try:
    from license_manager import get_license_manager
    LICENSE_MANAGER_AVAILABLE = True
except ImportError:
    print("[Warning] license_manager.py not found - license features disabled")
    LICENSE_MANAGER_AVAILABLE = False
    def get_license_manager(*args, **kwargs):
        return None

# Load environment variables for OpenAI
# Use explicit path instead of find_dotenv() to support exec() execution
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env') if '__file__' in globals() else '.env')

# Admin authentication
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
app = FastAPI(title="SlyWriter API", version="2.5.4")

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Electron compatibility
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
        # Config directory for license and user data
        # Will be set by Electron when it starts the backend
        self.config_dir = os.environ.get('SLYWRITER_CONFIG_DIR', os.path.dirname(__file__))

state = AppState()

# Pydantic models for request/response
class TypingRequest(BaseModel):
    text: str
    profile: Optional[str] = "Default"
    preview_mode: bool = False
    custom_wpm: Optional[int] = None
    min_delay: Optional[float] = None
    max_delay: Optional[float] = None
    typos_enabled: bool = False
    pause_frequency: int = 5
    preview_only: bool = False  # Legacy, use preview_mode
    ai_filler_enabled: bool = False
    grammarly_mode: bool = False  # Delayed autocorrect-style corrections
    grammarly_delay: float = 2.0  # Delay before corrections (seconds)
    typo_rate: float = 2.0  # Percentage chance of typos

class ConfigUpdate(BaseModel):
    settings: Dict[str, Any]

class HotkeyUpdate(BaseModel):
    key: str
    value: str

# API Endpoints

@app.get("/")
async def root():
    return {"status": "SlyWriter API Running", "version": "2.5.4"}

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "typing_active": state.typing_active,
        "user_authenticated": state.user is not None
    }

@app.get("/api/typing/status")
async def get_typing_status():
    """Get current typing status"""
    return {
        "is_typing": state.typing_active,
        "session_id": state.current_session,
        "progress": state.typing_progress.get('progress', 0),
        "status": state.typing_progress.get('status', 'idle'),
        "chars_typed": state.typing_progress.get('chars_typed', 0),
        "total_chars": state.typing_progress.get('total_chars', 0),
        "wpm": state.typing_progress.get('wpm', 0)
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
        # Determine user's plan and word limit
        is_premium = state.usage_manager.is_premium() if state.usage_manager else False

        # Plan limits (words per day)
        PLAN_LIMITS = {
            "Free": 10000,
            "Basic": 10000,
            "Pro": 50000,
            "Premium": -1  # -1 indicates unlimited
        }

        # Determine current plan
        if is_premium:
            plan = "Premium"
        else:
            plan = "Free"

        word_limit = PLAN_LIMITS.get(plan, 10000)

        return {
            "authenticated": True,
            "user": {
                "email": state.user.get('email'),
                "name": state.user.get('name'),
                "picture": state.user.get('picture'),
                "is_premium": is_premium,
                "plan": plan,
                "word_limit": word_limit,
                "word_limit_display": "Unlimited" if word_limit == -1 else f"{word_limit:,} words/day"
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
        # If already typing, just return success instead of error
        # This prevents 400 errors when multiple start requests come in
        return {"status": "already_running", "session_id": state.current_session or "active"}
    
    # Check usage limits
    if state.usage_manager and not state.usage_manager.has_words_remaining():
        raise HTTPException(status_code=403, detail="Daily word limit reached. Upgrade to premium for unlimited typing.")
    
    # Calculate delays based on profile or custom WPM
    if typing_req.min_delay is None or typing_req.max_delay is None:
        # Calculate from profile or custom WPM
        wpm = typing_req.custom_wpm
        print(f"\n{'='*60}")
        print(f"🚨 BACKEND RECEIVED TYPING REQUEST - v2.5.3")
        print(f"Profile: {typing_req.profile}")
        print(f"custom_wpm from request: {wpm}")
        print(f"Type of custom_wpm: {type(wpm)}")
        print(f"Is custom_wpm truthy: {bool(wpm)}")
        print(f"{'='*60}\n")

        if not wpm:
            # Get WPM from profile
            profile_wpm_map = {
                "Ultra-Slow": 30,
                "Slow": 40,
                "Default": 60,
                "Medium": 70,
                "Fast": 100,
                "Lightning": 250
            }
            wpm = profile_wpm_map.get(typing_req.profile, 60)
            print(f"[DEBUG] custom_wpm was falsy, using profile {typing_req.profile} WPM: {wpm}")
        else:
            print(f"[DEBUG] custom_wpm was truthy, using custom WPM: {wpm}")
        
        # Calculate delays from WPM (60 / (wpm * 5) for average delay)
        avg_delay = 60.0 / (wpm * 5.0)  # 5 chars per word average
        typing_req.min_delay = max(0.01, avg_delay * 0.7)
        typing_req.max_delay = min(2.0, avg_delay * 1.3)
        print(f"[DEBUG] Calculated delays: min={typing_req.min_delay:.3f}s, max={typing_req.max_delay:.3f}s for {wpm} WPM")
    
    # Use preview_mode if set, otherwise fall back to preview_only
    if typing_req.preview_mode:
        typing_req.preview_only = True
    
    state.typing_active = True
    state.typing_progress['status'] = 'typing'
    state.typing_progress['total_chars'] = len(typing_req.text)
    state.typing_progress['chars_typed'] = 0
    state.typing_progress['progress'] = 0  # Start at 0%
    # Use the calculated WPM value
    state.typing_progress['wpm'] = wpm

    print(f"\n🔥 SETTING STATE WPM TO: {wpm} 🔥")
    print(f"[DEBUG] Starting typing with text length: {len(typing_req.text)} chars")
    print(f"[DEBUG] Text preview: {typing_req.text[:50]}...")
    print(f"[DEBUG] Profile: {typing_req.profile}, State WPM: {state.typing_progress['wpm']}")
    
    # Define callbacks for live updates
    def update_preview(text):
        state.typing_progress['chars_typed'] = len(text)
        progress = (len(text) / len(typing_req.text)) * 100 if typing_req.text else 0
        state.typing_progress['progress'] = min(100, progress)
        print(f"[DEBUG] Progress update: {len(text)}/{len(typing_req.text)} chars = {progress:.1f}%")
    
    def update_status(status):
        # Check if this is a typo update
        if isinstance(status, str) and status.startswith("TYPO_UPDATE:"):
            try:
                typo_count = int(status.split(":")[1])
                state.typing_progress['typos_made'] = typo_count
                # Broadcast typo update
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(broadcast_typo_update(typo_count))
            except:
                pass
            return
        
        state.typing_progress['status'] = status
        # Try to broadcast status if event loop is available
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(broadcast_status())
            else:
                # If no running loop, we're in a thread - schedule it
                asyncio.run_coroutine_threadsafe(broadcast_status(), loop)
        except RuntimeError:
            # No event loop available, skip broadcasting
            # The WebSocket polling will pick up the change
            pass
    
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
    
    return {"success": True, "message": "Typing started", "session_id": "active"}

@app.post("/api/typing/stop")
async def stop_typing():
    """Stop typing operation"""
    # Don't error if already stopped - just return success
    if not state.typing_active:
        return {"success": True, "message": "Typing already stopped"}
    
    engine.stop_typing_func()
    state.typing_active = False
    state.typing_progress['status'] = 'stopped'
    await broadcast_status()
    
    return {"success": True, "message": "Typing stopped"}

@app.post("/api/typing/pause")
async def pause_typing():
    """Pause/resume typing operation"""
    # Don't error if not typing - just return current state
    if not state.typing_active:
        return {"success": True, "message": "Not currently typing", "paused": False}
    
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
    return {"success": True, "message": message, "paused": state.typing_paused}

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

# Profile endpoints
@app.get("/api/profiles")
async def get_profiles():
    """Get available typing profiles"""
    profiles = [
        {
            "name": "Slow",
            "wpm": 40,
            "description": "Beginner typing speed",
            "is_builtin": True,
            "settings": {
                "min_delay": 150,
                "max_delay": 250,
                "typos_enabled": True,
                "typo_chance": 5,
                "pause_frequency": 3,
                "ai_filler_enabled": False,
                "micro_hesitations": True,
                "zone_out_breaks": False,
                "burst_variability": 20
            }
        },
        {
            "name": "Medium",
            "wpm": 70,
            "description": "Average typing speed",
            "is_builtin": True,
            "settings": {
                "min_delay": 85,
                "max_delay": 145,
                "typos_enabled": True,
                "typo_chance": 3,
                "pause_frequency": 5,
                "ai_filler_enabled": False,
                "micro_hesitations": True,
                "zone_out_breaks": False,
                "burst_variability": 15
            }
        },
        {
            "name": "Fast",
            "wpm": 100,
            "description": "Above average speed",
            "is_builtin": True,
            "settings": {
                "min_delay": 60,
                "max_delay": 100,
                "typos_enabled": True,
                "typo_chance": 2,
                "pause_frequency": 7,
                "ai_filler_enabled": False,
                "micro_hesitations": False,
                "zone_out_breaks": False,
                "burst_variability": 10
            }
        },
        {
            "name": "Lightning",
            "wpm": 250,
            "description": "Lightning fast speed",
            "is_builtin": True,
            "settings": {
                "min_delay": 24,
                "max_delay": 40,
                "typos_enabled": False,
                "typo_chance": 0,
                "pause_frequency": 10,
                "ai_filler_enabled": False,
                "micro_hesitations": False,
                "zone_out_breaks": False,
                "burst_variability": 5
            }
        },
        {
            "name": "Custom",
            "wpm": 85,
            "description": "Your custom speed (up to 500 WPM)",
            "is_builtin": False,
            "settings": {
                "min_delay": 70,
                "max_delay": 120,
                "typos_enabled": True,
                "typo_chance": 3,
                "pause_frequency": 5,
                "ai_filler_enabled": False,
                "micro_hesitations": True,
                "zone_out_breaks": False,
                "burst_variability": 15
            }
        }
    ]
    return {"profiles": profiles}

@app.post("/api/copy-highlighted")
async def copy_highlighted():
    """Copy highlighted text to clipboard using keyboard simulation (for hotkey)"""
    try:
        import keyboard
        import pyperclip
        import time
        
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
        
        print(f"[COPY-HOTKEY] Original clipboard: {original[:50] if original else 'empty'}...")
        print(f"[COPY-HOTKEY] New clipboard: {new_content[:50] if new_content else 'empty'}...")
        print(f"[COPY-HOTKEY] Content changed: {new_content != original}")
        
        return {
            "success": True,
            "copied": new_content != original,
            "text": new_content if new_content != original else ""
        }
    except Exception as e:
        print(f"Copy highlighted error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/copy-highlighted-overlay")
async def copy_highlighted_overlay():
    """Copy highlighted text for overlay button (needs Alt+Tab to restore focus)"""
    try:
        import keyboard
        import pyperclip
        import time
        
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
        
        print(f"[COPY-OVERLAY] Original clipboard: {original[:50] if original else 'empty'}...")
        print(f"[COPY-OVERLAY] New clipboard: {new_content[:50] if new_content else 'empty'}...")
        print(f"[COPY-OVERLAY] Content changed: {new_content != original}")
        
        return {
            "success": True,
            "copied": new_content != original,
            "text": new_content if new_content != original else ""
        }
    except Exception as e:
        print(f"Copy highlighted overlay error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/profiles/generate-from-wpm")
async def generate_profile_from_wpm(request: dict):
    """Generate a custom profile based on WPM"""
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

@app.post("/api/typing/update_wpm")
async def update_typing_wpm(request: dict):
    """Update WPM during typing session"""
    session_id = request.get("session_id")
    wpm = request.get("wpm", 70)
    
    # Update the typing speed if session is active or paused
    if state.typing_active:  # Check if typing session exists (active or paused)
        # Calculate new delays
        avg_delay = 60000 / (wpm * 5)
        state.current_wpm = wpm
        # The new WPM will be used when typing resumes if paused
        return {"success": True, "wpm": wpm}
    
    return {"success": False, "error": "No active typing session"}

@app.post("/api/typing/pause/{session_id}")
async def pause_typing_by_session(session_id: str):
    """Pause typing by session ID"""
    return await pause_typing()

@app.post("/api/typing/resume/{session_id}")
async def resume_typing_by_session(session_id: str):
    """Resume typing by session ID"""
    # Resume typing
    return {"success": True, "message": "Typing resumed"}

@app.post("/api/typing/stop/{session_id}")
async def stop_typing_by_session(session_id: str):
    """Stop typing by session ID"""
    return await stop_typing()

# Helper function to broadcast completion
async def broadcast_completion():
    """Broadcast typing completion to all WebSocket connections"""
    if hasattr(state, 'active_connections'):
        message = {
            "type": "typing_complete",
            "data": {
                "status": "completed",
                "progress": 100
            }
        }
        for websocket in state.active_connections:
            try:
                await websocket.send_json(message)
            except:
                pass


# WebSocket endpoint for real-time updates
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket connection for real-time typing updates"""
    await websocket.accept()
    if not hasattr(state, 'active_connections'):
        state.active_connections = set()
    state.active_connections.add(websocket)
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "data": state.typing_progress
        })
        
        while True:
            # Check for typing completion FIRST
            if hasattr(state, 'typing_complete') and state.typing_complete:
                print(f"[DEBUG WS] Sending typing_complete message")
                await websocket.send_json({
                    "type": "typing_complete",
                    "data": {
                        "status": "completed",
                        "progress": 100
                    }
                })
                state.typing_complete = False  # Reset flag
            
            # Send current status if typing
            if state.typing_active:
                progress_data = {
                    "status": state.typing_progress.get('status', 'typing'),
                    "progress": state.typing_progress.get('progress', 0),
                    "wpm": state.typing_progress.get('wpm', 0),
                    "chars_typed": state.typing_progress.get('chars_typed', 0),
                    "total_chars": state.typing_progress.get('total_chars', 0)
                }
                print(f"[DEBUG WS] Sending progress: {progress_data['progress']:.1f}% ({progress_data['chars_typed']}/{progress_data['total_chars']}) WPM: {progress_data['wpm']}")
                await websocket.send_json({
                    "type": "progress",
                    "data": progress_data
                })
            
            # Keep connection alive
            await asyncio.sleep(0.5)  # Check every 500ms
            
    except WebSocketDisconnect:
        if hasattr(state, 'active_connections'):
            state.active_connections.discard(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if hasattr(state, 'active_connections'):
            state.active_connections.discard(websocket)

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

async def broadcast_typo_update(typo_count):
    """Broadcast typo count update to all websocket clients"""
    disconnected_clients = []
    
    for client in state.websocket_clients:
        try:
            await client.send_json({
                "type": "typo",
                "data": {"typos_made": typo_count}
            })
        except:
            disconnected_clients.append(client)
    
    # Remove disconnected clients
    for client in disconnected_clients:
        if client in state.websocket_clients:
            state.websocket_clients.remove(client)

# Helper functions
def run_regular_typing(text, preview_callback, status_callback, typing_req):
    """Run regular typing engine"""
    import time
    start_time = time.time()
    
    try:
        # Start typing (this creates a thread and returns immediately)
        engine.start_typing_from_input(
            text=text,
            live_preview_callback=preview_callback,
            status_callback=status_callback,
            min_delay=typing_req.min_delay,
            max_delay=typing_req.max_delay,
            typos_on=typing_req.typos_enabled,
            pause_freq=typing_req.pause_frequency,
            preview_only=typing_req.preview_only,
            grammarly_mode=typing_req.grammarly_mode,
            grammarly_delay=typing_req.grammarly_delay,
            typo_rate=typing_req.typo_rate
        )
        
        # Wait for typing to complete by checking the typing thread
        if hasattr(engine, '_typing_thread') and engine._typing_thread:
            engine._typing_thread.join()  # Wait for the typing thread to finish
        
    finally:
        # Ensure minimum duration of 1 second to prevent UI flashing
        elapsed = time.time() - start_time
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        
        print(f"[DEBUG] Typing finished - setting typing_active=False, progress=100")
        state.typing_active = False
        state.typing_progress['status'] = '✅ Finished!'
        state.typing_progress['progress'] = 100
        state.typing_complete = True  # Flag for WebSocket to check

def run_premium_typing(text, preview_callback, status_callback, typing_req):
    """Run premium typing with AI filler"""
    import time
    start_time = time.time()
    
    try:
        # Premium typing might also use threading
        premium_typing.premium_type_with_filler(
            goal_text=text,
            live_preview_callback=preview_callback,
            status_callback=status_callback,
            min_delay=typing_req.min_delay,
            max_delay=typing_req.max_delay,
            typos_on=typing_req.typos_enabled,
            pause_freq=typing_req.pause_frequency,
            preview_only=typing_req.preview_only,
            stop_flag=engine._stop_flag,
            pause_flag=engine._pause_flag
        )
        
        # Wait for typing to complete
        if hasattr(engine, '_typing_thread') and engine._typing_thread:
            engine._typing_thread.join()  # Wait for the typing thread to finish
            
    finally:
        # Ensure minimum duration of 1 second to prevent UI flashing
        elapsed = time.time() - start_time
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        
        print(f"[DEBUG] Typing finished - setting typing_active=False, progress=100")
        state.typing_active = False
        state.typing_progress['status'] = '✅ Finished!'
        state.typing_progress['progress'] = 100
        state.typing_complete = True  # Flag for WebSocket to check

# Beta Telemetry Endpoints
class TelemetryData(BaseModel):
    userId: str
    sessionId: str
    systemInfo: Dict[str, Any]
    actions: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    featureUsage: List[Dict[str, Any]]
    performanceMetrics: List[Dict[str, Any]]
    sessionDuration: int
    lastActivity: int
    timestamp: str

# Store telemetry data in memory (for now - will move to database)
telemetry_storage = []
MAX_TELEMETRY_ENTRIES = 10000

@app.post("/api/beta-telemetry")
async def receive_telemetry(data: TelemetryData):
    """Receive telemetry data from beta testers"""
    try:
        # Store in memory
        telemetry_entry = {
            **data.dict(),
            "received_at": datetime.now().isoformat()
        }
        telemetry_storage.append(telemetry_entry)
        
        # Keep only recent entries
        if len(telemetry_storage) > MAX_TELEMETRY_ENTRIES:
            telemetry_storage.pop(0)
        
        # Save to file for persistence
        save_telemetry_to_file(telemetry_entry)
        
        return {"status": "success", "message": "Telemetry received"}
    except Exception as e:
        print(f"Telemetry error: {e}")
        return {"status": "error", "message": str(e)}

def save_telemetry_to_file(entry):
    """Save telemetry to JSON file for persistence"""
    try:
        filename = f"telemetry_data_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = os.path.join("telemetry_logs", filename)
        
        # Create directory if it doesn't exist
        os.makedirs("telemetry_logs", exist_ok=True)
        
        # Append to file
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
        else:
            data = []
        
        data.append(entry)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Failed to save telemetry to file: {e}")

@app.get("/api/admin/telemetry")
async def get_telemetry_data(limit: int = 100, authorized: bool = Depends(verify_admin)):
    """Admin endpoint to view telemetry data (requires admin authentication)"""
    return {
        "total_entries": len(telemetry_storage),
        "recent_entries": telemetry_storage[-limit:],
        "users": len(set(entry["userId"] for entry in telemetry_storage)),
        "sessions": len(set(entry["sessionId"] for entry in telemetry_storage))
    }

@app.get("/api/admin/telemetry/export")
async def export_telemetry(authorized: bool = Depends(verify_admin)):
    """Export all telemetry data (requires admin authentication)"""
    return telemetry_storage

# ============== LICENSE VERIFICATION ENDPOINTS ==============

class LicenseVerifyRequest(BaseModel):
    license_key: str
    force: bool = False

@app.post("/api/license/verify")
async def verify_license_endpoint(request: LicenseVerifyRequest):
    """Verify license with server and check version"""
    if not LICENSE_MANAGER_AVAILABLE:
        return {"valid": False, "error": "license_system_unavailable"}

    license_manager = get_license_manager(config_dir=state.config_dir)
    result = license_manager.verify_license(request.license_key, force=request.force)

    return result

@app.get("/api/license/status")
async def get_license_status():
    """Get current license status"""
    if not LICENSE_MANAGER_AVAILABLE:
        return {"valid": False, "error": "license_system_unavailable"}

    license_manager = get_license_manager(config_dir=state.config_dir)
    if not license_manager or not license_manager.license_data:
        return {"valid": False, "error": "not_verified"}

    return license_manager.license_data

@app.get("/api/license/features")
async def get_enabled_features():
    """Get list of enabled features for current license"""
    if not LICENSE_MANAGER_AVAILABLE:
        return {"ai_generation": False, "humanizer": False, "premium_typing": False}

    license_manager = get_license_manager(config_dir=state.config_dir)
    if not license_manager or not license_manager.license_data:
        return {"ai_generation": False, "humanizer": False, "premium_typing": False}

    return license_manager.license_data.get('features_enabled', {})

@app.get("/api/admin/telemetry/stats")
async def get_telemetry_stats():
    """Get telemetry statistics"""
    if not telemetry_storage:
        return {"message": "No telemetry data available"}

    # Calculate statistics
    total_users = len(set(entry["userId"] for entry in telemetry_storage))
    total_sessions = len(set(entry["sessionId"] for entry in telemetry_storage))
    total_actions = sum(len(entry.get("actions", [])) for entry in telemetry_storage)
    total_errors = sum(len(entry.get("errors", [])) for entry in telemetry_storage)

    # Most used features
    feature_counts = {}
    for entry in telemetry_storage:
        for feature in entry.get("featureUsage", []):
            name = feature.get("feature", "unknown")
            feature_counts[name] = feature_counts.get(name, 0) + feature.get("usageCount", 0)

    # Common errors
    error_types = {}
    for entry in telemetry_storage:
        for error in entry.get("errors", []):
            error_type = error.get("error", "unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1

    return {
        "total_users": total_users,
        "total_sessions": total_sessions,
        "total_actions": total_actions,
        "total_errors": total_errors,
        "most_used_features": dict(sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
        "common_errors": dict(sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:10]),
        "data_points": len(telemetry_storage)
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting SlyWriter API on http://localhost:8000")
    print("API docs available at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
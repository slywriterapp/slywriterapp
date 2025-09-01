"""
Add these endpoints to your Render server (slywriter_server.py or wherever your FastAPI app is)
These use PostgreSQL for storage instead of local files
"""

from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
from datetime import datetime
import logging

# Import the PostgreSQL telemetry handler
from telemetry_postgres import telemetry_db

logger = logging.getLogger(__name__)

# Add this to your existing FastAPI app
# app = FastAPI()  # You already have this

# Telemetry data model
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

# Helper function to verify admin password
def verify_admin_password(password: Optional[str] = None) -> bool:
    """Verify admin password from header or environment"""
    admin_password = os.environ.get('ADMIN_PASSWORD', 'slywriter-admin-brice')
    return password == admin_password

# Beta Telemetry Endpoints

@app.post("/api/beta-telemetry")
async def receive_telemetry(data: TelemetryData, background_tasks: BackgroundTasks):
    """
    Receive telemetry data from beta testers
    Stores in PostgreSQL database on Render
    """
    try:
        # Log receipt for debugging
        logger.info(f"Received telemetry from user: {data.userId}, session: {data.sessionId}")
        
        # Save to PostgreSQL in background to not block response
        background_tasks.add_task(telemetry_db.save_telemetry, data.dict())
        
        return {
            "status": "success",
            "message": "Telemetry received",
            "userId": data.userId,
            "sessionId": data.sessionId
        }
    except Exception as e:
        logger.error(f"Error receiving telemetry: {e}")
        # Still return success to not break client
        return {
            "status": "error",
            "message": str(e),
            "userId": data.userId
        }

@app.get("/api/admin/telemetry")
async def get_telemetry_data(
    limit: int = 100,
    x_admin_password: Optional[str] = Header(None)
):
    """
    Admin endpoint to view recent telemetry data
    Requires admin password in header
    """
    if not verify_admin_password(x_admin_password):
        raise HTTPException(status_code=401, detail="Invalid admin password")
    
    try:
        recent_entries = telemetry_db.get_recent_entries(limit)
        stats = telemetry_db.get_stats()
        
        return {
            "total_entries": stats.get('data_points', 0),
            "recent_entries": recent_entries,
            "users": stats.get('total_users', 0),
            "sessions": stats.get('total_sessions', 0)
        }
    except Exception as e:
        logger.error(f"Error getting telemetry data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/telemetry/stats")
async def get_telemetry_stats(
    x_admin_password: Optional[str] = Header(None)
):
    """
    Get telemetry statistics
    Shows aggregated data about usage
    """
    if not verify_admin_password(x_admin_password):
        raise HTTPException(status_code=401, detail="Invalid admin password")
    
    try:
        stats = telemetry_db.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting telemetry stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/telemetry/export")
async def export_telemetry(
    x_admin_password: Optional[str] = Header(None)
):
    """
    Export all telemetry data
    Returns complete dataset for analysis
    """
    if not verify_admin_password(x_admin_password):
        raise HTTPException(status_code=401, detail="Invalid admin password")
    
    try:
        all_data = telemetry_db.export_all_data()
        return all_data
    except Exception as e:
        logger.error(f"Error exporting telemetry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/telemetry/cleanup")
async def cleanup_old_telemetry(
    days: int = 90,
    x_admin_password: Optional[str] = Header(None)
):
    """
    Clean up old telemetry data
    Removes data older than specified days
    """
    if not verify_admin_password(x_admin_password):
        raise HTTPException(status_code=401, detail="Invalid admin password")
    
    try:
        telemetry_db.cleanup_old_data(days)
        return {
            "status": "success",
            "message": f"Cleaned up data older than {days} days"
        }
    except Exception as e:
        logger.error(f"Error cleaning up telemetry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/telemetry/health")
async def telemetry_health():
    """
    Check if telemetry system is working
    Public endpoint for monitoring
    """
    try:
        # Try to get connection
        conn = telemetry_db.get_connection()
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# User-specific endpoints (for privacy)

@app.get("/api/user/telemetry/{user_id}")
async def get_user_telemetry(
    user_id: str,
    user_token: Optional[str] = Header(None)
):
    """
    Get telemetry data for a specific user
    Users can request their own data
    """
    # In production, verify user_token matches user_id
    # For beta, we'll allow it
    
    try:
        conn = telemetry_db.get_connection()
        cur = conn.cursor()
        
        # Get user's sessions
        cur.execute("""
            SELECT * FROM telemetry_sessions
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 100
        """, (user_id,))
        
        sessions = cur.fetchall()
        cur.close()
        conn.close()
        
        return {
            "userId": user_id,
            "sessions": sessions,
            "export_date": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting user telemetry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/user/telemetry/{user_id}")
async def delete_user_telemetry(
    user_id: str,
    user_token: Optional[str] = Header(None)
):
    """
    Delete all telemetry data for a specific user
    GDPR compliance - right to erasure
    """
    # In production, verify user_token matches user_id
    # For beta, we'll allow it
    
    try:
        conn = telemetry_db.get_connection()
        cur = conn.cursor()
        
        # Delete user's data from all tables
        cur.execute("DELETE FROM telemetry_events WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM telemetry_errors WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM telemetry_features WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM telemetry_sessions WHERE user_id = %s", (user_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "message": f"All telemetry data for user {user_id} has been deleted"
        }
    except Exception as e:
        logger.error(f"Error deleting user telemetry: {e}")
        raise HTTPException(status_code=500, detail=str(e))
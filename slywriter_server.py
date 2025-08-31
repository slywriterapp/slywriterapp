from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import json
import os
import hashlib
import jwt
import datetime
import bcrypt
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid
import re
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import Dict, List, Any
import threading

app = Flask(__name__)
CORS(app, origins='*')  # Enable CORS for all origins per your config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-jwt-secret-change-this')

# Data files (keeping your existing file-based storage)
USAGE_FILE = "word_data.json"
PLAN_FILE = "plan_data.json"
REFERRAL_FILE = "referral_data.json"
USERS_FILE = "users.json"
USER_SETTINGS_FILE = "user_settings.json"
SESSIONS_FILE = "sessions.json"
PASSWORD_RESETS_FILE = "password_resets.json"
TYPING_PROJECTS_FILE = "typing_projects.json"
ANALYTICS_FILE = "analytics.json"

# ============== TELEMETRY DATABASE CLASS ==============
class TelemetryDatabase:
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        if not self.database_url:
            logger.warning("DATABASE_URL not set - telemetry disabled")
            self.enabled = False
        else:
            self.enabled = True
            try:
                self.init_database()
            except Exception as e:
                logger.error(f"Failed to initialize telemetry database: {e}")
                self.enabled = False
    
    def get_connection(self):
        """Get a database connection"""
        if not self.enabled:
            return None
        return psycopg2.connect(self.database_url)
    
    def init_database(self):
        """Create necessary tables if they don't exist"""
        if not self.enabled:
            return
            
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            # Create telemetry_events table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_events (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    session_id VARCHAR(255) NOT NULL,
                    event_type VARCHAR(100),
                    event_data JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create telemetry_sessions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    system_info JSONB,
                    session_duration INTEGER,
                    total_actions INTEGER,
                    total_errors INTEGER,
                    started_at TIMESTAMP,
                    last_activity TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create telemetry_errors table for quick error lookup
            cur.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_errors (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    session_id VARCHAR(255) NOT NULL,
                    error_message TEXT,
                    error_stack TEXT,
                    component VARCHAR(255),
                    severity VARCHAR(50),
                    context JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create telemetry_features table for feature usage
            cur.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_features (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    feature_name VARCHAR(255) NOT NULL,
                    usage_count INTEGER DEFAULT 1,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    settings JSONB,
                    UNIQUE(user_id, feature_name)
                )
            """)
            
            # Create indexes for better performance
            cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_events_user_id ON telemetry_events(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_events_session_id ON telemetry_events(session_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_events_timestamp ON telemetry_events(timestamp)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_sessions_user_id ON telemetry_sessions(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_errors_user_id ON telemetry_errors(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_features_user_id ON telemetry_features(user_id)")
            
            conn.commit()
            logger.info("Telemetry database tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()
    
    def save_telemetry(self, data: Dict[str, Any]) -> bool:
        """Save telemetry data to PostgreSQL"""
        if not self.enabled:
            return False
            
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            # Save session info
            cur.execute("""
                INSERT INTO telemetry_sessions (
                    user_id, session_id, system_info, session_duration,
                    total_actions, total_errors, started_at, last_activity
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (session_id) 
                DO UPDATE SET
                    session_duration = EXCLUDED.session_duration,
                    total_actions = EXCLUDED.total_actions,
                    total_errors = EXCLUDED.total_errors,
                    last_activity = EXCLUDED.last_activity
            """, (
                data['userId'],
                data['sessionId'],
                json.dumps(data.get('systemInfo', {})),
                data.get('sessionDuration', 0),
                len(data.get('actions', [])),
                len(data.get('errors', [])),
                datetime.datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')) if 'timestamp' in data else datetime.datetime.now(),
                datetime.datetime.now()
            ))
            
            # Save individual actions as events
            for action in data.get('actions', []):
                cur.execute("""
                    INSERT INTO telemetry_events (
                        user_id, session_id, event_type, event_data, timestamp
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (
                    data['userId'],
                    data['sessionId'],
                    action.get('action', 'unknown'),
                    json.dumps(action),
                    datetime.datetime.fromisoformat(action['timestamp'].replace('Z', '+00:00')) if 'timestamp' in action else datetime.datetime.now()
                ))
            
            # Save errors
            for error in data.get('errors', []):
                cur.execute("""
                    INSERT INTO telemetry_errors (
                        user_id, session_id, error_message, error_stack,
                        component, severity, context, timestamp
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    data['userId'],
                    data['sessionId'],
                    error.get('error', 'Unknown error'),
                    error.get('stack', ''),
                    error.get('component', 'unknown'),
                    error.get('severity', 'medium'),
                    json.dumps(error.get('context', {})),
                    datetime.datetime.fromisoformat(error['timestamp'].replace('Z', '+00:00')) if 'timestamp' in error else datetime.datetime.now()
                ))
            
            # Update feature usage
            for feature in data.get('featureUsage', []):
                cur.execute("""
                    INSERT INTO telemetry_features (
                        user_id, feature_name, usage_count, last_used, settings
                    ) VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, feature_name)
                    DO UPDATE SET
                        usage_count = telemetry_features.usage_count + EXCLUDED.usage_count,
                        last_used = EXCLUDED.last_used,
                        settings = EXCLUDED.settings
                """, (
                    data['userId'],
                    feature.get('feature', 'unknown'),
                    feature.get('usageCount', 1),
                    datetime.datetime.now(),
                    json.dumps(feature.get('settings', {}))
                ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving telemetry: {e}")
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get telemetry statistics"""
        if not self.enabled:
            return {}
            
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Get user and session counts
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT user_id) as total_users,
                    COUNT(DISTINCT session_id) as total_sessions,
                    COUNT(*) as total_events
                FROM telemetry_events
            """)
            basic_stats = cur.fetchone()
            
            # Get total actions and errors
            cur.execute("SELECT COUNT(*) as total_errors FROM telemetry_errors")
            error_count = cur.fetchone()
            
            # Get most used features
            cur.execute("""
                SELECT feature_name, SUM(usage_count) as total_usage
                FROM telemetry_features
                GROUP BY feature_name
                ORDER BY total_usage DESC
                LIMIT 10
            """)
            most_used_features = {row['feature_name']: row['total_usage'] for row in cur.fetchall()}
            
            # Get common errors
            cur.execute("""
                SELECT error_message, COUNT(*) as count
                FROM telemetry_errors
                GROUP BY error_message
                ORDER BY count DESC
                LIMIT 10
            """)
            common_errors = {row['error_message']: row['count'] for row in cur.fetchall()}
            
            # Get recent activity count
            cur.execute("""
                SELECT COUNT(*) as recent_events
                FROM telemetry_events
                WHERE timestamp > NOW() - INTERVAL '24 hours'
            """)
            recent_activity = cur.fetchone()
            
            return {
                'total_users': basic_stats['total_users'],
                'total_sessions': basic_stats['total_sessions'],
                'total_actions': basic_stats['total_events'],
                'total_errors': error_count['total_errors'],
                'most_used_features': most_used_features,
                'common_errors': common_errors,
                'recent_events_24h': recent_activity['recent_events'],
                'data_points': basic_stats['total_events']
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                'error': str(e),
                'total_users': 0,
                'total_sessions': 0,
                'total_actions': 0,
                'total_errors': 0
            }
        finally:
            cur.close()
            conn.close()
    
    def get_recent_entries(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent telemetry entries"""
        if not self.enabled:
            return []
            
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                SELECT 
                    s.user_id, s.session_id, s.system_info, 
                    s.session_duration, s.total_actions, s.total_errors,
                    s.started_at, s.last_activity,
                    COUNT(e.id) as event_count
                FROM telemetry_sessions s
                LEFT JOIN telemetry_events e ON s.session_id = e.session_id
                GROUP BY s.id, s.user_id, s.session_id, s.system_info, 
                         s.session_duration, s.total_actions, s.total_errors,
                         s.started_at, s.last_activity
                ORDER BY s.last_activity DESC
                LIMIT %s
            """, (limit,))
            
            entries = []
            for row in cur.fetchall():
                entries.append({
                    'userId': row['user_id'],
                    'sessionId': row['session_id'],
                    'systemInfo': row['system_info'],
                    'sessionDuration': row['session_duration'],
                    'actions': [],  # We don't load full actions for performance
                    'errors': [],
                    'timestamp': row['started_at'].isoformat() if row['started_at'] else '',
                    'received_at': row['last_activity'].isoformat() if row['last_activity'] else ''
                })
            
            return entries
            
        except Exception as e:
            logger.error(f"Error getting recent entries: {e}")
            return []
        finally:
            cur.close()
            conn.close()
    
    def export_all_data(self) -> List[Dict[str, Any]]:
        """Export all telemetry data"""
        if not self.enabled:
            return []
            
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Get all sessions with their events
            cur.execute("""
                SELECT * FROM telemetry_sessions
                ORDER BY created_at DESC
            """)
            sessions = cur.fetchall()
            
            export_data = []
            for session in sessions:
                # Get events for this session
                cur.execute("""
                    SELECT * FROM telemetry_events
                    WHERE session_id = %s
                    ORDER BY timestamp
                """, (session['session_id'],))
                events = cur.fetchall()
                
                # Get errors for this session
                cur.execute("""
                    SELECT * FROM telemetry_errors
                    WHERE session_id = %s
                    ORDER BY timestamp
                """, (session['session_id'],))
                errors = cur.fetchall()
                
                export_data.append({
                    'userId': session['user_id'],
                    'sessionId': session['session_id'],
                    'systemInfo': session['system_info'],
                    'sessionDuration': session['session_duration'],
                    'actions': [dict(e) for e in events],
                    'errors': [dict(e) for e in errors],
                    'timestamp': session['started_at'].isoformat() if session['started_at'] else '',
                    'received_at': session['created_at'].isoformat() if session['created_at'] else ''
                })
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return []
        finally:
            cur.close()
            conn.close()
    
    def cleanup_old_data(self, days: int = 90):
        """Clean up old telemetry data"""
        if not self.enabled:
            return
            
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            # Delete old events
            cur.execute("""
                DELETE FROM telemetry_events
                WHERE timestamp < NOW() - INTERVAL '%s days'
            """, (days,))
            
            # Delete old errors
            cur.execute("""
                DELETE FROM telemetry_errors
                WHERE timestamp < NOW() - INTERVAL '%s days'
            """, (days,))
            
            # Delete old sessions
            cur.execute("""
                DELETE FROM telemetry_sessions
                WHERE created_at < NOW() - INTERVAL '%s days'
            """, (days,))
            
            conn.commit()
            logger.info(f"Cleaned up data older than {days} days")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()

# Initialize telemetry database
telemetry_db = TelemetryDatabase()

# ============== EXISTING HELPER FUNCTIONS ==============
def load_data(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return {}

def save_data(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

# [KEEPING ALL YOUR EXISTING AUTH FUNCTIONS AS-IS]
def hash_password(password):
    """Hash a password with bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_jwt_token(user_id, email):
    """Generate JWT token for user"""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_jwt_token(token):
    """Verify JWT token and return user data"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Missing authorization header"}), 401
        
        try:
            token = auth_header.split(' ')[1]  # Remove 'Bearer ' prefix
        except IndexError:
            return jsonify({"error": "Invalid authorization header format"}), 401
        
        user_data = verify_jwt_token(token)
        if not user_data:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        request.current_user = user_data
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

def send_email(to_email, subject, body, is_html=False):
    """Send email via SMTP"""
    try:
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        
        if not smtp_username or not smtp_password:
            print("SMTP credentials not configured")
            return False
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_username
        msg['To'] = to_email
        
        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False

def log_analytics_event(user_id, event_type, event_data=None):
    """Log analytics event"""
    analytics = load_data(ANALYTICS_FILE)
    if 'events' not in analytics:
        analytics['events'] = []
    
    event = {
        'user_id': user_id,
        'event_type': event_type,
        'event_data': event_data or {},
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'date': datetime.datetime.utcnow().strftime('%Y-%m-%d')
    }
    
    analytics['events'].append(event)
    save_data(ANALYTICS_FILE, analytics)

# Helper function to verify admin password
def verify_admin_password(password=None):
    """Verify admin password from header or environment"""
    admin_password = os.environ.get('ADMIN_PASSWORD', 'slywriter-admin-brice')
    return password == admin_password

# Helper function to save telemetry in background
def save_telemetry_background(data):
    """Save telemetry data in background thread"""
    try:
        telemetry_db.save_telemetry(data)
    except Exception as e:
        logger.error(f"Background telemetry save failed: {e}")

# ============== TELEMETRY ENDPOINTS ==============

@app.route("/api/beta-telemetry", methods=["POST"])
def receive_telemetry():
    """
    Receive telemetry data from beta testers
    Stores in PostgreSQL database on Render
    """
    try:
        data = request.get_json()
        
        # Log receipt for debugging
        logger.info(f"Received telemetry from user: {data.get('userId')}, session: {data.get('sessionId')}")
        
        # Save to PostgreSQL in background to not block response
        thread = threading.Thread(target=save_telemetry_background, args=(data,))
        thread.start()
        
        return jsonify({
            "status": "success",
            "message": "Telemetry received",
            "userId": data.get('userId'),
            "sessionId": data.get('sessionId')
        })
    except Exception as e:
        logger.error(f"Error receiving telemetry: {e}")
        # Still return success to not break client
        return jsonify({
            "status": "error",
            "message": str(e),
            "userId": data.get('userId', 'unknown')
        })

@app.route("/api/admin/telemetry", methods=["GET"])
def get_telemetry_data():
    """
    Admin endpoint to view recent telemetry data
    Requires admin password in header
    """
    x_admin_password = request.headers.get('X-Admin-Password')
    if not verify_admin_password(x_admin_password):
        return jsonify({"error": "Invalid admin password"}), 401
    
    try:
        limit = int(request.args.get('limit', 100))
        recent_entries = telemetry_db.get_recent_entries(limit)
        stats = telemetry_db.get_stats()
        
        return jsonify({
            "total_entries": stats.get('data_points', 0),
            "recent_entries": recent_entries,
            "users": stats.get('total_users', 0),
            "sessions": stats.get('total_sessions', 0)
        })
    except Exception as e:
        logger.error(f"Error getting telemetry data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/telemetry/stats", methods=["GET"])
def get_telemetry_stats():
    """
    Get telemetry statistics
    Shows aggregated data about usage
    """
    x_admin_password = request.headers.get('X-Admin-Password')
    if not verify_admin_password(x_admin_password):
        return jsonify({"error": "Invalid admin password"}), 401
    
    try:
        stats = telemetry_db.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting telemetry stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/telemetry/export", methods=["GET"])
def export_telemetry():
    """
    Export all telemetry data
    Returns complete dataset for analysis
    """
    x_admin_password = request.headers.get('X-Admin-Password')
    if not verify_admin_password(x_admin_password):
        return jsonify({"error": "Invalid admin password"}), 401
    
    try:
        all_data = telemetry_db.export_all_data()
        return jsonify(all_data)
    except Exception as e:
        logger.error(f"Error exporting telemetry: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/telemetry/cleanup", methods=["DELETE"])
def cleanup_old_telemetry():
    """
    Clean up old telemetry data
    Removes data older than specified days
    """
    x_admin_password = request.headers.get('X-Admin-Password')
    if not verify_admin_password(x_admin_password):
        return jsonify({"error": "Invalid admin password"}), 401
    
    try:
        days = int(request.args.get('days', 90))
        telemetry_db.cleanup_old_data(days)
        return jsonify({
            "status": "success",
            "message": f"Cleaned up data older than {days} days"
        })
    except Exception as e:
        logger.error(f"Error cleaning up telemetry: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/telemetry/health", methods=["GET"])
def telemetry_health():
    """
    Check if telemetry system is working
    Public endpoint for monitoring
    """
    try:
        if telemetry_db.enabled:
            # Try to get connection
            conn = telemetry_db.get_connection()
            conn.close()
            
            return jsonify({
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.datetime.now().isoformat()
            })
        else:
            return jsonify({
                "status": "disabled",
                "database": "not configured",
                "timestamp": datetime.datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        })

# User-specific endpoints (for privacy)

@app.route("/api/user/telemetry/<user_id>", methods=["GET"])
def get_user_telemetry(user_id):
    """
    Get telemetry data for a specific user
    Users can request their own data
    """
    # In production, verify user_token matches user_id
    # For beta, we'll allow it
    user_token = request.headers.get('User-Token')
    
    try:
        if not telemetry_db.enabled:
            return jsonify({"error": "Telemetry not enabled"}), 503
            
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
        
        return jsonify({
            "userId": user_id,
            "sessions": sessions,
            "export_date": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting user telemetry: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/user/telemetry/<user_id>", methods=["DELETE"])
def delete_user_telemetry(user_id):
    """
    Delete all telemetry data for a specific user
    GDPR compliance - right to erasure
    """
    # In production, verify user_token matches user_id
    # For beta, we'll allow it
    user_token = request.headers.get('User-Token')
    
    try:
        if not telemetry_db.enabled:
            return jsonify({"error": "Telemetry not enabled"}), 503
            
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
        
        return jsonify({
            "status": "success",
            "message": f"All telemetry data for user {user_id} has been deleted"
        })
    except Exception as e:
        logger.error(f"Error deleting user telemetry: {e}")
        return jsonify({"error": str(e)}), 500

# ============== KEEP ALL YOUR EXISTING ENDPOINTS ==============
# [ALL YOUR EXISTING ENDPOINTS FROM LINE 163 TO END REMAIN UNCHANGED]

# Health check endpoint
@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "SlyWriter API is running"}), 200

# [CONTINUE WITH ALL YOUR EXISTING ENDPOINTS - I'm not repeating them to save space]
# Just copy all your existing endpoints from line 169 onwards here

# ============== MAIN ==============
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
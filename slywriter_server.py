from flask import Flask, request, jsonify, redirect, session, url_for
from flask_cors import CORS, cross_origin
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
import psycopg
from psycopg.rows import dict_row
import logging
from typing import Dict, List, Any
import threading
import requests
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import pathlib

app = Flask(__name__)

# Configure CORS properly for development and production
CORS(app,
     resources={r"/*": {"origins": "*"}},  # Allow all origins for flexibility
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=True)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-jwt-secret-change-this')

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'https://slywriterapp.onrender.com/auth/google/callback')

# For local testing, override redirect URI
if os.environ.get('ENV') == 'development':
    GOOGLE_REDIRECT_URI = 'http://localhost:5000/auth/google/callback'

# Session configuration for OAuth flow
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Data files (keeping your existing file-based storage)
USAGE_FILE = "word_data.json"
PLAN_FILE = "plan_data.json"
REFERRAL_FILE = "referral_data.json"
REFERRALS_FILE = "referrals.json"
USERS_FILE = "users.json"
USER_SETTINGS_FILE = "user_settings.json"
SESSIONS_FILE = "sessions.json"
PASSWORD_RESETS_FILE = "password_resets.json"
TYPING_PROJECTS_FILE = "typing_projects.json"
ANALYTICS_FILE = "analytics.json"
GLOBAL_STATS_FILE = "global_stats.json"

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
        return psycopg.connect(self.database_url)
    
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
        cur = conn.cursor(row_factory=dict_row)
        
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
        cur = conn.cursor(row_factory=dict_row)
        
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
        cur = conn.cursor(row_factory=dict_row)
        
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
    """Send email via SMTP with Gmail App Password"""
    try:
        # Use SMTP configuration from environment variables
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_username = os.environ.get('SMTP_USERNAME')  # No hardcoded default
        smtp_password = os.environ.get('SMTP_PASSWORD')  # App password from Google
        
        if not smtp_username or not smtp_password:
            logger.error("SMTP credentials not configured")
            logger.error(f"Username: {smtp_username}, Password configured: {bool(smtp_password)}")
            return False
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"SlyWriter <{smtp_username}>"
        msg['To'] = to_email
        
        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        # Connect to SMTP server
        logger.info(f"Connecting to SMTP server {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(1)  # Enable debug output
        server.starttls()  # Enable TLS encryption
        logger.info(f"Logging in as {smtp_username}")
        server.login(smtp_username, smtp_password)
        
        # Send the email
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed - check credentials: {e}")
        return False
    except smtplib.SMTPConnectError as e:
        logger.error(f"Failed to connect to SMTP server {smtp_server}:{smtp_port} - {e}")
        return False
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        return False

def send_welcome_email(email, name, verification_token):
    """Send welcome email for new users (both regular and Google Sign-In) with verification link"""
    subject = "Verify Your SlyWriter Account"
    
    # Use the exact same email template as regular registration
    verification_link = f"https://slywriter.ai/verify-email?token={verification_token}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to SlyWriter!</h1>
            </div>
            <div class="content">
                <h2>Hi {name},</h2>
                <p>Thank you for creating an account with SlyWriter! We're excited to have you on board.</p>
                <p>Please verify your email address by clicking the button below:</p>
                <center>
                    <a href="{verification_link}" class="button">Verify Email Address</a>
                </center>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; font-size: 12px; color: #666;">
                    {verification_link}
                </p>
                <p>This link will expire in 24 hours for security reasons.</p>
                <p>If you didn't create an account with SlyWriter, please ignore this email.</p>
                <p>Best regards,<br>The SlyWriter Team</p>
            </div>
            <div class="footer">
                <p>&copy; 2025 SlyWriter. All rights reserved.</p>
                <p>You're receiving this email because you signed up for SlyWriter.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(email, subject, html_body, is_html=True)

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
    admin_password = os.environ.get('ADMIN_PASSWORD', None)
    if not admin_password:
        logging.warning("ADMIN_PASSWORD not set in environment variables")
        return False
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
# ============== ORIGINAL SLYWRITER ENDPOINTS ==============

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "SlyWriter API is running"}), 200

# ---------------- AUTHENTICATION ----------------

@app.route("/auth/register", methods=["POST", "OPTIONS"])
def register():
    """Register new user account"""
    # Handle CORS preflight
    if request.method == "OPTIONS":
        return "", 200
    
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data received in request")
            return jsonify({"success": False, "error": "No data provided"}), 400
            
        logger.info(f"Registration attempt with data: {data}")
        
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        referral_code = data.get('referral_code', '').strip()
        
        # Validation
        if not email or not password or not name:
            logger.error(f"Missing fields - email: {bool(email)}, password: {bool(password)}, name: {bool(name)}")
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        logger.info(f"Validating email: {email}")
        if not validate_email(email):
            logger.error(f"Invalid email format: {email}")
            return jsonify({"success": False, "error": "Invalid email format"}), 400
        
        logger.info(f"Validating password strength")
        password_valid, password_message = validate_password(password)
        if not password_valid:
            logger.error(f"Invalid password: {password_message}")
            return jsonify({"success": False, "error": password_message}), 400
        
        logger.info("Validation passed, checking if user exists")
        
        # Check if user already exists
        users = load_data(USERS_FILE)
        if email in users:
            return jsonify({"success": False, "error": "Email already exists. Please login instead."}), 400
        
        # Create user
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(password)
        
        user_data = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'password_hash': hashed_password,
            'created_at': datetime.datetime.utcnow().isoformat(),
            'email_verified': False,
            'verification_token': secrets.token_urlsafe(32),
            'last_login': None,
            'status': 'active'
        }
        
        users[email] = user_data
        save_data(USERS_FILE, users)
        
        # Set default plan
        plans = load_data(PLAN_FILE)
        plans[user_id] = "free"
        save_data(PLAN_FILE, plans)
        
        # Initialize usage
        usage = load_data(USAGE_FILE)
        usage[user_id] = 0
        save_data(USAGE_FILE, usage)
        
        # Apply referral if provided
        if referral_code:
            try:
                ref_data = load_data(REFERRAL_FILE)
                code_map = ref_data.get("code_map", {})
                referrer_id = code_map.get(referral_code)
                
                if referrer_id and referrer_id != user_id:
                    ref_by_uid = ref_data.get("by_uid", {})
                    ref_by_uid[user_id] = referrer_id
                    ref_data["by_uid"] = ref_by_uid
                    save_data(REFERRAL_FILE, ref_data)
            except Exception as e:
                print(f"Referral application failed: {e}")
        
        # Generate token
        token = generate_jwt_token(user_id, email)
        
        # Send verification email with HTML formatting
        # Send verification email to Webflow site for professional branded experience
        verification_link = f"https://slywriter.ai/verify-email?token={user_data['verification_token']}"
        
        html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to SlyWriter!</h1>
            </div>
            <div class="content">
                <h2>Hi {name},</h2>
                <p>Thank you for signing up for SlyWriter! We're excited to have you on board.</p>
                <p>Please verify your email address by clicking the button below:</p>
                <center>
                    <a href="{verification_link}" class="button">Verify Email Address</a>
                </center>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background: #fff; padding: 10px; border: 1px solid #ddd;">
                    {verification_link}
                </p>
                <p>If you didn't create this account, please ignore this email.</p>
                <div class="footer">
                    <p>Best regards,<br>The SlyWriter Team</p>
                    <p>© 2025 SlyWriter. All rights reserved.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
        """
        
        plain_text = f"""
    Welcome to SlyWriter, {name}!
    
    Please verify your email address by clicking this link:
    {verification_link}
    
    If you didn't create this account, please ignore this email.
    
        Best regards,
        The SlyWriter Team
        """
        
        # Try HTML first, fallback to plain text
        if not send_email(email, "Welcome to SlyWriter - Verify Your Email", html_body, is_html=True):
            send_email(email, "Welcome to SlyWriter - Verify Your Email", plain_text, is_html=False)
        
        # Log registration
        log_analytics_event(user_id, 'user_registered', {'email': email, 'referral_code': referral_code})
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "email": email,
            "name": name,
            "token": token,
            "verified": False
        })
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"success": False, "error": f"Registration failed: {str(e)}"}), 500

@app.route("/auth/login", methods=["POST"])
def login():
    """Login existing user"""
    data = request.get_json()
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({"success": False, "error": "Missing email or password"}), 400
    
    # Find user
    users = load_data(USERS_FILE)
    user_data = users.get(email)
    
    if not user_data or not verify_password(password, user_data['password_hash']):
        return jsonify({"success": False, "error": "Invalid email or password"}), 401
    
    if user_data.get('status') != 'active':
        return jsonify({"success": False, "error": "Account is deactivated"}), 401
    
    # Update last login
    user_data['last_login'] = datetime.datetime.utcnow().isoformat()
    users[email] = user_data
    save_data(USERS_FILE, users)
    
    # Generate token
    token = generate_jwt_token(user_data['user_id'], email)
    
    # Get user plan
    plans = load_data(PLAN_FILE)
    user_plan = plans.get(user_data['user_id'], 'free')
    
    # Get usage
    usage = load_data(USAGE_FILE)
    words_used = usage.get(user_data['user_id'], 0)
    
    # Log login
    log_analytics_event(user_data['user_id'], 'user_login')
    
    return jsonify({
        "success": True,
        "user_id": user_data['user_id'],
        "email": email,
        "name": user_data['name'],
        "token": token,
        "verified": user_data.get('email_verified', False),
        "plan": user_plan,
        "words_used": words_used
    })

@app.route("/auth/verify-token", methods=["POST"])
def verify_token():
    """Verify JWT token and return user data"""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "error": "No token provided"}), 401
    
    token = auth_header.replace('Bearer ', '')
    
    # Verify the token
    payload = verify_jwt_token(token)
    
    if not payload:
        return jsonify({"success": False, "error": "Invalid or expired token"}), 401
    
    # Get user data
    users = load_data(USERS_FILE)
    user_data = users.get(payload.get('email'))
    
    if not user_data:
        return jsonify({"success": False, "error": "User not found"}), 404
    
    if user_data.get('status') != 'active':
        return jsonify({"success": False, "error": "Account is deactivated"}), 401
    
    # Get user plan and usage
    plans = load_data(PLAN_FILE)
    user_plan = plans.get(user_data['user_id'], 'free')
    
    usage = load_data(USAGE_FILE)
    words_used = usage.get(user_data['user_id'], 0)
    
    # Get word limits based on plan
    word_limits = {
        'free': 2000,      # Free users: 2,000 words
        'basic': 10000,    # Basic plan: 10,000 words
        'pro': 20000,      # Pro plan: 20,000 words
        'premium': 50000   # Premium plan: 50,000 words
    }
    
    return jsonify({
        "success": True,
        "user_id": user_data['user_id'],
        "email": payload.get('email'),
        "name": user_data['name'],
        "plan": user_plan,
        "words_used": words_used,
        "word_limit": word_limits.get(user_plan, 1000),
        "verified": user_data.get('email_verified', False)
    })

@app.route("/auth/google/login", methods=["POST"])
def google_login():
    """Handle Google OAuth login from frontend"""
    logger.info("=== GOOGLE LOGIN ATTEMPT ===")
    try:
        data = request.get_json()
        logger.info(f"Received data keys: {data.keys() if data else 'No data'}")
        token = data.get('credential')  # This is the Google ID token
        
        if not token:
            logger.error("No credential token provided in request")
            return jsonify({"success": False, "error": "No token provided"}), 400
        
        # Check if Google Client ID is configured
        if not GOOGLE_CLIENT_ID:
            logger.error("GOOGLE_CLIENT_ID not configured")
            # For development, accept the token without verification
            if os.environ.get('FLASK_ENV') == 'development':
                # Decode token without verification for dev
                import base64
                import json
                
                # JWT tokens have 3 parts separated by dots
                parts = token.split('.')
                if len(parts) != 3:
                    return jsonify({"success": False, "error": "Invalid token format"}), 401
                
                # Decode the payload (second part)
                payload = parts[1]
                # Add padding if needed
                payload += '=' * (4 - len(payload) % 4)
                decoded = base64.urlsafe_b64decode(payload)
                idinfo = json.loads(decoded)
                
                logger.info(f"Dev mode: Using decoded token info without verification")
            else:
                return jsonify({"success": False, "error": "Google OAuth not configured"}), 500
        else:
            # Verify the Google token
            try:
                # Verify the token with Google
                idinfo = id_token.verify_oauth2_token(
                    token, 
                    google_requests.Request(), 
                    GOOGLE_CLIENT_ID
                )
            except ValueError as e:
                logger.error(f"Google token verification failed: {str(e)}")
                return jsonify({"success": False, "error": "Invalid Google token"}), 401
        
        # Get user info from Google
        google_user_id = idinfo['sub']
        email = idinfo['email'].lower().strip()
        name = idinfo.get('name', '')
        picture = idinfo.get('picture', '')
        email_verified = idinfo.get('email_verified', False)
        
        # Check if user exists
        users = load_data(USERS_FILE)
        user_data = users.get(email)
        
        if user_data:
            # Existing user - update Google info
            logger.info(f"Existing Google user logging in: {email}")
            user_data['google_id'] = google_user_id
            user_data['picture'] = picture
            user_data['last_login'] = datetime.datetime.utcnow().isoformat()
            if email_verified and not user_data.get('email_verified'):
                user_data['email_verified'] = True
            users[email] = user_data
            save_data(USERS_FILE, users)
            
            user_id = user_data['user_id']
            is_new_user = False
        else:
            logger.info(f"NEW Google user signing up: {email}")
            # New user - create account
            user_id = str(uuid.uuid4())
            
            # Generate referral code
            referral_code = f"{name.split()[0].upper() if name else 'USER'}{secrets.token_hex(3).upper()}"
            
            # Generate verification token (even though Google users are pre-verified, we use it for the welcome email)
            verification_token = secrets.token_urlsafe(32)
            
            user_data = {
                'user_id': user_id,
                'email': email,
                'name': name,
                'google_id': google_user_id,
                'picture': picture,
                'password_hash': None,  # No password for Google users
                'created_at': datetime.datetime.utcnow().isoformat(),
                'last_login': datetime.datetime.utcnow().isoformat(),
                'email_verified': email_verified,
                'verification_token': verification_token,
                'status': 'active',
                'referral_code': referral_code,
                'auth_provider': 'google'
            }
            
            users[email] = user_data
            save_data(USERS_FILE, users)
            
            # Initialize user plan (free by default)
            plans = load_data(PLAN_FILE)
            plans[user_id] = 'free'
            save_data(PLAN_FILE, plans)
            
            # Initialize usage
            usage = load_data(USAGE_FILE)
            usage[user_id] = 0
            save_data(USAGE_FILE, usage)
            
            is_new_user = True
            
            # Send welcome email for new Google Sign-In users
            try:
                send_welcome_email(email, name, verification_token)
                logger.info(f"Welcome email sent to new Google user: {email}")
            except Exception as e:
                logger.error(f"Failed to send welcome email to {email}: {str(e)}")
                # Don't fail the registration if email fails
            
            # Log registration
            log_analytics_event(user_id, 'user_registered', {
                'email': email,
                'provider': 'google'
            })
        
        # Generate JWT token
        token = generate_jwt_token(user_id, email)
        
        # Get user plan
        plans = load_data(PLAN_FILE)
        user_plan = plans.get(user_id, 'free')
        
        # Get usage
        usage = load_data(USAGE_FILE)
        words_used = usage.get(user_id, 0)
        
        # Log login
        log_analytics_event(user_id, 'user_login', {'provider': 'google'})
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "token": token,
            "plan": user_plan,
            "words_used": words_used,
            "verified": email_verified,
            "is_new_user": is_new_user
        })
        
    except Exception as e:
        logger.error(f"Google login error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/auth/quick", methods=["POST"])
def quick_auth():
    """Simple auth bypass for development"""
    data = request.get_json()
    email = data.get('email', '').lower()
    
    # Auto-approve certain emails for development
    allowed_emails = ['slywriterteam@gmail.com', 'admin@slywriter.ai', 'test@slywriter.ai']
    allowed_domains = ['@slywriter']
    
    is_allowed = email in allowed_emails or any(domain in email for domain in allowed_domains)
    
    if is_allowed:
        user_id = f"quick-{hashlib.md5(email.encode()).hexdigest()[:8]}"
        
        # Generate token
        token = jwt.encode(
            {
                'user_id': user_id,
                'email': email,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        
        # Check if user exists, create if not
        users = load_data(USERS_FILE)
        if email not in users:
            users[email] = {
                'user_id': user_id,
                'email': email,
                'name': email.split('@')[0].replace('.', ' ').title(),
                'password_hash': None,
                'created_at': datetime.datetime.utcnow().isoformat(),
                'email_verified': True,
                'status': 'active',
                'auth_provider': 'quick'
            }
            save_data(USERS_FILE, users)
            
            # Set plan
            plans = load_data(PLAN_FILE)
            plans[user_id] = 'premium'
            save_data(PLAN_FILE, plans)
        
        return jsonify({
            'success': True,
            'token': token,
            'user_id': user_id,
            'email': email,
            'name': users[email]['name'],
            'plan': 'premium',
            'wordsRemaining': 999999,
            'wordsUsed': 0
        })
    
    return jsonify({'success': False, 'error': 'Email not authorized'}), 401

@app.route("/auth/logout", methods=["POST"])
@require_auth
def logout():
    """Logout user"""
    # In a full implementation, you'd invalidate the token in a blacklist
    log_analytics_event(request.current_user['user_id'], 'user_logout')
    return jsonify({"success": True, "message": "Logged out successfully"})

@app.route("/auth/profile", methods=["GET"])
@require_auth
def get_profile():
    """Get current user profile"""
    user_id = request.current_user['user_id']
    email = request.current_user['email']
    
    # Get user data
    users = load_data(USERS_FILE)
    user_data = None
    for user_email, data in users.items():
        if data['user_id'] == user_id:
            user_data = data
            break
    
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    
    # Get plan and usage
    plans = load_data(PLAN_FILE)
    usage = load_data(USAGE_FILE)
    
    return jsonify({
        "user_id": user_id,
        "email": email,
        "name": user_data['name'],
        "verified": user_data.get('email_verified', False),
        "plan": plans.get(user_id, 'free'),
        "words_used": usage.get(user_id, 0),
        "referral_code": user_data.get('referral_code', user_id[:8]),  # Use first 8 chars of user_id as fallback
        "created_at": user_data.get('created_at'),
        "last_login": user_data.get('last_login')
    })

@app.route("/auth/verify-email", methods=["GET", "POST", "OPTIONS"])
@cross_origin(origins=[
    "https://slywriter.ai",
    "https://www.slywriter.ai",
    "https://slywriter-site.webflow.io",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002"
])
def verify_email():
    """Verify user email address - supports both GET (from email link) and POST (from API)"""
    logger.info(f"verify_email called: method={request.method}, origin={request.headers.get('origin')}")

    # Handle GET request from email link
    if request.method == 'GET':
        token = request.args.get('token')
        logger.info(f"GET request, token from args: {token[:20] if token else 'None'}...")
    else:
        # Handle POST request from API
        data = request.get_json()
        logger.info(f"POST request, received data: {data}")
        token = data.get('token') if data else None
        logger.info(f"Extracted token: {token[:20] if token else 'None'}...")

    if not token:
        logger.error("No token provided")
        return jsonify({"success": False, "error": "Missing verification token"}), 400
    
    # Find user with this token
    users = load_data(USERS_FILE)
    user_email = None
    user_data = None

    logger.info(f"Searching for token in {len(users)} users")
    for email, data in users.items():
        if data.get('verification_token') == token:
            user_email = email
            user_data = data
            logger.info(f"Token matched for user: {email}")
            break

    if not user_data:
        logger.error(f"Token not found in users database")
        return jsonify({"success": False, "error": "Invalid verification token"}), 400
    
    # Mark as verified
    user_data['email_verified'] = True
    user_data['verification_token'] = None
    users[user_email] = user_data
    save_data(USERS_FILE, users)

    log_analytics_event(user_data['user_id'], 'email_verified')

    logger.info(f"Email verified successfully for {user_email}")
    return jsonify({"success": True, "message": "Email verified successfully"})

@app.route("/auth/test-create-verification-token", methods=["POST"])
@cross_origin(origins=["*"])
def test_create_verification_token():
    """TEST ENDPOINT - Create a verification token for testing"""
    data = request.get_json()
    email = data.get('email', 'test@example.com')

    # Generate token
    token = secrets.token_urlsafe(32)

    # Load or create test user
    users = load_data(USERS_FILE)
    if email not in users:
        users[email] = {
            'user_id': str(uuid.uuid4()),
            'email': email,
            'email_verified': False,
            'verification_token': token,
            'created_at': datetime.datetime.utcnow().isoformat()
        }
    else:
        users[email]['verification_token'] = token
        users[email]['email_verified'] = False

    save_data(USERS_FILE, users)

    verification_link = f"https://www.slywriter.ai/verify-email?token={token}"

    logger.info(f"Created test verification token for {email}: {token[:20]}...")
    return jsonify({
        "success": True,
        "email": email,
        "token": token,
        "verification_link": verification_link,
        "message": "Test token created. Click the verification_link to test."
    })

@app.route("/auth/forgot-password", methods=["POST"])
def forgot_password():
    """Request password reset"""
    data = request.get_json()
    email = data.get('email', '').lower().strip()
    
    if not email:
        return jsonify({"success": False, "error": "Missing email"}), 400
    
    users = load_data(USERS_FILE)
    user_data = users.get(email)
    
    # Always return success to prevent email enumeration
    if user_data:
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        reset_data = load_data(PASSWORD_RESETS_FILE)
        reset_data[reset_token] = {
            'email': email,
            'user_id': user_data['user_id'],
            'created_at': datetime.datetime.utcnow().isoformat(),
            'expires_at': (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat()
        }
        save_data(PASSWORD_RESETS_FILE, reset_data)
        
        # Send reset email
        reset_link = f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
        send_email(
            email,
            "SlyWriter Password Reset",
            f"""
            Hi {user_data['name']},
            
            You requested a password reset for your SlyWriter account.
            
            Click this link to reset your password:
            {reset_link}
            
            This link will expire in 1 hour.
            
            If you didn't request this reset, please ignore this email.
            
            Best regards,
            The SlyWriter Team
            """
        )
    
    return jsonify({"success": True, "message": "If the email exists, a reset link has been sent"})

@app.route("/auth/reset-password", methods=["POST"])
def reset_password():
    """Reset password with token"""
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')
    
    if not token or not new_password:
        return jsonify({"success": False, "error": "Missing token or password"}), 400
    
    # Validate password
    password_valid, password_message = validate_password(new_password)
    if not password_valid:
        return jsonify({"success": False, "error": password_message}), 400
    
    # Check token
    reset_data = load_data(PASSWORD_RESETS_FILE)
    token_data = reset_data.get(token)
    
    if not token_data:
        return jsonify({"success": False, "error": "Invalid reset token"}), 400
    
    # Check expiration
    expires_at = datetime.datetime.fromisoformat(token_data['expires_at'])
    if datetime.datetime.utcnow() > expires_at:
        return jsonify({"success": False, "error": "Reset token has expired"}), 400
    
    # Update password
    users = load_data(USERS_FILE)
    email = token_data['email']
    user_data = users.get(email)
    
    if user_data:
        user_data['password_hash'] = hash_password(new_password)
        users[email] = user_data
        save_data(USERS_FILE, users)
        
        # Remove used token
        del reset_data[token]
        save_data(PASSWORD_RESETS_FILE, reset_data)
        
        log_analytics_event(user_data['user_id'], 'password_reset')
        
        return jsonify({"success": True, "message": "Password reset successfully"})
    
    return jsonify({"success": False, "error": "User not found"}), 404

@app.route("/auth/change-password", methods=["POST"])
@require_auth
def change_password():
    """Change password for authenticated user"""
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({"success": False, "error": "Missing current or new password"}), 400
    
    # Validate new password
    password_valid, password_message = validate_password(new_password)
    if not password_valid:
        return jsonify({"success": False, "error": password_message}), 400
    
    # Get user
    users = load_data(USERS_FILE)
    email = request.current_user['email']
    user_data = users.get(email)
    
    if not user_data:
        return jsonify({"success": False, "error": "User not found"}), 404
    
    # Verify current password
    if not verify_password(current_password, user_data['password_hash']):
        return jsonify({"success": False, "error": "Current password is incorrect"}), 400
    
    # Update password
    user_data['password_hash'] = hash_password(new_password)
    users[email] = user_data
    save_data(USERS_FILE, users)
    
    log_analytics_event(user_data['user_id'], 'password_changed')
    
    return jsonify({"success": True, "message": "Password changed successfully"})

# ---------------- USER SETTINGS ----------------

@app.route("/settings", methods=["GET"])
@require_auth
def get_user_settings():
    """Get user settings"""
    user_id = request.current_user['user_id']
    settings = load_data(USER_SETTINGS_FILE)
    user_settings = settings.get(user_id, {})
    
    # Default settings
    default_settings = {
        'typing_settings': {
            'min_delay': 0.05,
            'max_delay': 0.15,
            'enable_typos': True,
            'pause_frequency': 50,
            'wpm': 60
        },
        'hotkeys': {
            'start': 'ctrl+alt+s',
            'stop': 'ctrl+alt+x',
            'pause': 'ctrl+alt+p',
            'overlay': 'ctrl+alt+o',
            'ai_generation': 'ctrl+alt+g'
        },
        'ai_settings': {
            'default_model': 'gpt-4o-mini',
            'humanizer_model': '1',
            'learning_mode': True,
            'review_mode': False
        },
        'theme': 'dark',
        'notifications': {
            'email_updates': True,
            'usage_alerts': True
        }
    }
    
    # Merge with user settings
    merged_settings = {**default_settings, **user_settings}
    return jsonify({"success": True, "settings": merged_settings})

@app.route("/settings", methods=["POST"])
@require_auth
def update_user_settings():
    """Update user settings"""
    user_id = request.current_user['user_id']
    new_settings = request.get_json()
    
    settings = load_data(USER_SETTINGS_FILE)
    settings[user_id] = new_settings
    save_data(USER_SETTINGS_FILE, settings)
    
    log_analytics_event(user_id, 'settings_updated')
    
    return jsonify({"success": True, "message": "Settings updated successfully"})

# ---------------- WORD USAGE ----------------

@app.route("/update_usage", methods=["POST"])
def update_usage():
    body = request.get_json()
    uid = body.get("user_id")
    amount = body.get("words", 0)

    if not uid:
        return jsonify({"error": "Missing user_id"}), 400

    data = load_data(USAGE_FILE)
    data[uid] = data.get(uid, 0) + amount
    save_data(USAGE_FILE, data)

    return jsonify({"status": "ok", "total_user_words": data[uid]})

@app.route("/get_usage", methods=["GET"])
def get_usage():
    uid = request.args.get("user_id")
    if not uid:
        return jsonify({"error": "Missing user_id"}), 400

    data = load_data(USAGE_FILE)
    return jsonify({"words": data.get(uid, 0)})

@app.route("/total_words", methods=["GET"])
def total_words():
    data = load_data(USAGE_FILE)
    total = sum(data.values())
    return jsonify({"total_words": total})

@app.route("/debug_all_users", methods=["GET"])
def debug_all_users():
    return jsonify(load_data(USAGE_FILE))

# ---------------- PLAN MANAGEMENT ----------------

@app.route("/get_plan", methods=["GET"])
def get_plan():
    uid = request.args.get("user_id")
    if not uid:
        return jsonify({"error": "Missing user_id"}), 400

    plans = load_data(PLAN_FILE)
    return jsonify({"plan": plans.get(uid, "free")})

@app.route("/set_plan", methods=["POST"])
def set_plan():
    body = request.get_json()
    uid = body.get("user_id")
    new_plan = body.get("plan")

    if not uid or new_plan not in ["free", "pro", "premium", "enterprise"]:
        return jsonify({"error": "Missing or invalid data"}), 400

    plans = load_data(PLAN_FILE)
    plans[uid] = new_plan
    save_data(PLAN_FILE, plans)

    return jsonify({"status": "ok", "plan": new_plan})

@app.route("/debug_all_plans", methods=["GET"])
def debug_all_plans():
    return jsonify(load_data(PLAN_FILE))

# ---------------- REFERRALS ----------------

@app.route("/get_referrals", methods=["GET"])
def get_referrals():
    uid = request.args.get("user_id")
    if not uid:
        return jsonify({"error": "Missing user_id"}), 400

    ref_data = load_data(REFERRAL_FILE)
    ref_by_uid = ref_data.get("by_uid", {})
    code_map = ref_data.get("code_map", {})

    # Get referral code for user (generate if not exists)
    user_code = None
    for code, owner in code_map.items():
        if owner == uid:
            user_code = code
            break

    if not user_code:
        # Generate code: short hash of user ID
        user_code = hashlib.sha256(uid.encode()).hexdigest()[:8]
        code_map[user_code] = uid
        ref_data["code_map"] = code_map
        save_data(REFERRAL_FILE, ref_data)

    # Count how many people this user referred
    referred_count = sum(1 for referrer in ref_by_uid.values() if referrer == uid)

    return jsonify({
        "referral_code": user_code,
        "referrals": referred_count
    })

@app.route("/apply_referral", methods=["POST"])
def apply_referral():
    body = request.get_json()
    new_user = body.get("user_id")
    referral_code = body.get("referral_code")

    if not new_user or not referral_code:
        return jsonify({"error": "Missing data"}), 400

    ref_data = load_data(REFERRAL_FILE)
    ref_by_uid = ref_data.get("by_uid", {})
    code_map = ref_data.get("code_map", {})

    if new_user in ref_by_uid:
        return jsonify({"status": "already_set"})

    referrer_uid = code_map.get(referral_code)
    if not referrer_uid or referrer_uid == new_user:
        return jsonify({"error": "Invalid referral code"}), 400

    ref_by_uid[new_user] = referrer_uid
    ref_data["by_uid"] = ref_by_uid
    save_data(REFERRAL_FILE, ref_data)

    return jsonify({"status": "ok", "referred_by": referrer_uid})

@app.route("/signup", methods=["GET"])
def signup_with_referral():
    referral_code = request.args.get("ref")
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    ref_data = load_data(REFERRAL_FILE)
    ref_by_uid = ref_data.get("by_uid", {})
    code_map = ref_data.get("code_map", {})

    # Apply referral if valid and not already set
    if referral_code:
        referrer_uid = code_map.get(referral_code)
        if not referrer_uid:
            return jsonify({"error": "Invalid referral code"}), 400
        if user_id == referrer_uid:
            return jsonify({"error": "Cannot refer yourself"}), 400
        if user_id not in ref_by_uid:
            ref_by_uid[user_id] = referrer_uid
            ref_data["by_uid"] = ref_by_uid
            save_data(REFERRAL_FILE, ref_data)

    # Redirect to app download
    return redirect("https://slywriter.com/download")

@app.route("/referral_bonus", methods=["POST"])
def referral_bonus():
    body = request.get_json()
    referrer_id = body.get("referrer_id")
    referred_id = body.get("referred_id")

    if not referrer_id or not referred_id:
        return jsonify({"error": "Missing user IDs"}), 400
    if referrer_id == referred_id:
        return jsonify({"error": "Self-referral not allowed"}), 400

    ref_data = load_data(REFERRAL_FILE)
    rewarded_pairs = ref_data.get("rewarded_pairs", [])
    pair_key = f"{referrer_id}→{referred_id}"

    if pair_key in rewarded_pairs:
        return jsonify({"status": "already_rewarded"}), 200

    # Grant word bonuses
    word_data = load_data(USAGE_FILE)
    word_data[referrer_id] = word_data.get(referrer_id, 0) + 1000
    word_data[referred_id] = word_data.get(referred_id, 0) + 1000
    save_data(USAGE_FILE, word_data)

    rewarded_pairs.append(pair_key)
    ref_data["rewarded_pairs"] = rewarded_pairs
    save_data(REFERRAL_FILE, ref_data)

    return jsonify({
        "status": "bonus_applied",
        "referrer_total": word_data[referrer_id],
        "referred_total": word_data[referred_id]
    })

@app.route("/debug_referrals", methods=["GET"])
def debug_referrals():
    return jsonify(load_data(REFERRAL_FILE))

# ---------------- AI FILLER GENERATION ----------------

@app.route('/generate_filler', methods=['POST'])
@cross_origin(origins=["*"])
def generate_filler():
    """
    Generate AI filler text - REQUIRES LICENSE
    Used by premium_typing.py for realistic fake edits
    """
    import openai

    data = request.get_json()
    prompt = data.get('prompt', '')
    license_key = data.get('license_key')  # NEW: Require license

    # License verification (optional for backward compatibility, but log it)
    if not license_key:
        logger.warning("[FILLER] No license key provided - allowing for backward compatibility")
        # TODO: Make this required in future version
    else:
        # Verify license and check if AI features are enabled
        try:
            payload = jwt.decode(license_key, JWT_SECRET, algorithms=["HS256"])
            user_email = payload.get("email")
        except:
            user_email = license_key

        if user_email:
            users = load_data(USERS_FILE)
            if user_email not in users:
                return jsonify({"error": "Invalid license"}), 403

            user_data = users[user_email]
            user_id = user_data.get('user_id')
            plans = load_data(PLAN_FILE)
            plan = plans.get(user_id, 'free').lower()

            # Check if premium features are available
            if plan == 'free':
                return jsonify({"error": "AI filler requires Pro or Premium plan"}), 403

            logger.info(f"[FILLER] Request from {user_email} ({plan})")

    try:
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    except KeyError:
        return jsonify({"error": "OpenAI key not set"}), 500

    try:
        # Use same model fallback as main text generation
        models_to_try = ['gpt-4.1-nano', 'gpt-5-nano', 'gpt-4o-mini']
        response = None
        
        for model in models_to_try:
            try:
                print(f"[FILLER] Trying model: {model}")
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": (
                            "You are a human typing a first draft. "
                            "Generate a single plausible but ultimately unused or rambling sentence, "
                            "or a short filler clause, that someone might type, hesitate, then erase while writing."
                        )},
                        {"role": "user", "content": prompt}
                    ],
                    max_completion_tokens=36
                )
                print(f"[FILLER] Successfully using model: {model}")
                break
            except Exception as model_error:
                print(f"[FILLER] Model {model} failed: {model_error}")
                continue
        
        if not response:
            raise Exception("All filler models failed to respond")
            
        filler = response.choices[0].message.content.strip()
        return jsonify({"filler": filler})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- AI TEXT GENERATION ----------------

@app.route('/ai_generate_text', methods=['POST'])
@app.route('/api/ai/generate', methods=['POST'])
def ai_generate_text():
    import openai
    
    # Check for OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("[AI] ERROR: OpenAI API key not found in environment variables")
        return jsonify({"success": False, "error": "OpenAI API key not configured on server"}), 500
    
    try:
        client = openai.OpenAI(api_key=api_key)
    except Exception as e:
        print(f"[AI] ERROR: Failed to initialize OpenAI client: {e}")
        return jsonify({"success": False, "error": f"Failed to initialize AI service: {str(e)}"}), 500

    data = request.get_json()
    prompt = data.get('prompt', '')
    settings = data.get('settings', {})
    user_id = data.get('user_id')
    
    print(f"[AI] Received request - prompt length: {len(prompt)}, settings: {settings}")
    
    if not prompt:
        return jsonify({"success": False, "error": "Missing prompt"}), 400

    try:
        # Enhanced system prompt to ensure adequate length
        system_prompt = (
            "You are a helpful writing assistant. IMPORTANT: Always generate comprehensive, "
            "detailed responses with proper depth and length. Never provide brief or short answers. "
            "Aim for at least 200-300 words minimum, with thorough explanations and examples."
        )
        
        # Try models in order (use valid OpenAI models)
        models_to_try = ['gpt-4o-mini', 'gpt-3.5-turbo', 'gpt-4-turbo-preview']
        model_to_use = None
        response = None
        
        for model in models_to_try:
            try:
                print(f"[AI] Trying model: {model}")
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000,  # Use max_tokens instead of max_completion_tokens
                    temperature=0.7
                )
                model_to_use = model
                print(f"[AI] Successfully using model: {model}")
                break
            except openai.APIError as model_error:
                print(f"[AI] Model {model} failed with API error: {model_error}")
                continue
            except Exception as model_error:
                print(f"[AI] Model {model} failed with error: {model_error}")
                continue
        
        if not response:
            error_msg = "All AI models failed. The OpenAI service may be temporarily unavailable."
            print(f"[AI] ERROR: {error_msg}")
            raise Exception(error_msg)
        
        generated_text = response.choices[0].message.content
        print(f"[AI] Raw OpenAI response using {model_to_use}: '{generated_text}'")
        
        if generated_text is None:
            print(f"[AI] WARNING: OpenAI returned None content")
            generated_text = ""
        else:
            generated_text = generated_text.strip()
            print(f"[AI] After strip - length: {len(generated_text)}")
        
        # Only retry once if text is very short (under 100 chars) - faster approach
        if len(generated_text) < 100:
            print(f"[AI] Text very short ({len(generated_text)} chars), single retry...")
            
            # Single retry with enhanced prompt
            enhanced_prompt = f"""Write a detailed, comprehensive response about: {prompt}

REQUIREMENTS: Minimum 300 words, multiple paragraphs, thorough explanations and examples."""
            
            try:
                retry_response = client.chat.completions.create(
                    model=model_to_use,  # Use the same model that worked
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": enhanced_prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.7
                )
                
                retry_text = retry_response.choices[0].message.content.strip()
                
                # Use the longer response
                if len(retry_text) > len(generated_text):
                    generated_text = retry_text
                    print(f"[AI] Retry successful ({len(retry_text)} chars)")
                else:
                    print(f"[AI] Using original ({len(generated_text)} chars)")
                    
            except Exception as retry_error:
                print(f"[AI] Retry failed: {retry_error}, using original")
        
        # Log final result and check if we actually have content
        print(f"[AI] Final text length: {len(generated_text)} chars")
        
        if len(generated_text) == 0:
            print(f"[AI] ERROR: Final generated text is empty after all attempts")
            return jsonify({
                "success": False,
                "error": f"AI model {model_to_use} returned empty content after retries"
            })
        
        return jsonify({
            "success": True,
            "text": generated_text
        })
        
    except openai.APIError as e:
        print(f"[AI] OpenAI API Error: {e}")
        return jsonify({
            "success": False, 
            "error": f"OpenAI API error: {str(e)}",
            "details": "The AI service encountered an error. Please try again."
        }), 500
    except Exception as e:
        print(f"[AI] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "error": f"Server error: {str(e)}",
            "details": "An unexpected error occurred processing your request."
        }), 500

@app.route('/ai_humanize_text', methods=['POST'])
@app.route('/api/ai/humanize', methods=['POST'])
def ai_humanize_text():
    import requests
    
    data = request.get_json()
    text = data.get('text', '')
    model = data.get('model', '1')  # Default to balanced
    user_id = data.get('user_id')
    
    if not text:
        return jsonify({"success": False, "error": "Missing text"}), 400
    
    try:
        # Get AIUndetect credentials from environment variables
        api_key = os.environ.get("AIUNDETECT_API_KEY")
        email = os.environ.get("AIUNDETECT_EMAIL")
        
        if not api_key or not email:
            return jsonify({"success": False, "error": "AIUndetect credentials not configured on server"}), 500
        
        headers = {
            'Authorization': api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': model,
            'mail': email,
            'data': text
        }
        
        response = requests.post(
            'https://aiundetect.com/api/v1/rewrite',
            headers=headers,
            json=payload,
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                humanized_text = result.get('data', '')
                
                # Ensure humanized text maintains reasonable length
                original_length = len(text)
                humanized_length = len(humanized_text)
                
                # If humanized text is less than 70% of original, reject it
                if humanized_length < (original_length * 0.7):
                    return jsonify({
                        "success": False,
                        "error": f"Humanized text too short ({humanized_length} chars vs {original_length} original). Please try again."
                    }), 400
                
                return jsonify({
                    "success": True,
                    "humanized_text": humanized_text
                })
            else:
                error_codes = {
                    1001: "Missing API key",
                    1002: "Rate limit exceeded", 
                    1003: "Invalid API Key",
                    1004: "Request parameter error",
                    1005: "Text language not supported",
                    1006: "You don't have enough words",
                    1007: "Server Error"
                }
                error_msg = error_codes.get(result.get('code'), f"Unknown error (code: {result.get('code')})")
                return jsonify({"success": False, "error": f"AIUndetect error: {error_msg}"}), 500
        else:
            return jsonify({"success": False, "error": f"HTTP {response.status_code}: {response.text}"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Balance check removed - admin use only

# ---------------- LEARNING MODE - CREATE LESSON ----------------

@app.route('/api/learning/create-lesson', methods=['POST'])
def create_learning_lesson():
    """Store a lesson created in learning mode"""
    print("[Learning] Create lesson endpoint called")
    
    data = request.get_json()
    if not data:
        print("[Learning] No JSON data received")
        return jsonify({"success": False, "error": "No data provided"}), 400
        
    topic = data.get('topic', '')
    content = data.get('content', '')
    method = data.get('method', 'ai_generated')
    
    print(f"[Learning] Topic: {topic[:50]}..., Content length: {len(content)}")
    
    if not topic or not content:
        return jsonify({"success": False, "error": "Missing topic or content"}), 400
    
    try:
        # Store lesson in a JSON file (or database if available)
        from datetime import datetime
        lesson_data = {
            'id': datetime.now().strftime('%Y%m%d%H%M%S'),
            'topic': topic,
            'content': content,
            'method': method,
            'created_at': datetime.now().isoformat(),
            'word_count': len(content.split()),
            'char_count': len(content)
        }
        
        # Load existing lessons
        lessons_file = 'learning_lessons.json'
        if os.path.exists(lessons_file):
            with open(lessons_file, 'r') as f:
                try:
                    lessons = json.load(f)
                except:
                    lessons = []
        else:
            lessons = []
        
        # Add new lesson
        lessons.append(lesson_data)
        
        # Keep only last 100 lessons
        if len(lessons) > 100:
            lessons = lessons[-100:]
        
        # Save lessons
        with open(lessons_file, 'w') as f:
            json.dump(lessons, f, indent=2)
        
        return jsonify({
            "success": True, 
            "lesson_id": lesson_data['id'],
            "message": "Lesson created successfully"
        })
        
    except Exception as e:
        print(f"[Learning] Error creating lesson: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Failed to save lesson: {str(e)}"}), 500

@app.route('/api/learning/get-lessons', methods=['GET'])
def get_learning_lessons():
    """Retrieve stored lessons from learning mode"""
    print("[Learning] Get lessons endpoint called")
    try:
        lessons_file = 'learning_lessons.json'
        if os.path.exists(lessons_file):
            with open(lessons_file, 'r') as f:
                try:
                    lessons = json.load(f)
                    # Return latest 20 lessons
                    return jsonify({
                        "success": True,
                        "lessons": lessons[-20:] if len(lessons) > 20 else lessons,
                        "total_count": len(lessons)
                    })
                except:
                    return jsonify({"success": True, "lessons": [], "total_count": 0})
        else:
            return jsonify({"success": True, "lessons": [], "total_count": 0})
    except Exception as e:
        print(f"Error retrieving lessons: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------- EDUCATIONAL CONTENT GENERATION ----------------

@app.route('/ai_generate_lesson', methods=['POST'])
def ai_generate_lesson():
    import openai
    try:
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    except KeyError:
        return jsonify({"success": False, "error": "OpenAI API key not configured on server"}), 500

    data = request.get_json()
    original_question = data.get('original_question', '')
    explanation_style = data.get('explanation_style', 'casual')
    difficulty_level = data.get('difficulty_level', 'intermediate')
    user_id = data.get('user_id')
    
    if not original_question:
        return jsonify({"success": False, "error": "Missing original question"}), 400

    try:
        # Build educational prompt based on style and difficulty
        prompt = _build_educational_prompt(original_question, explanation_style, difficulty_level)
        
        response = client.chat.completions.create(
            model='gpt-5-nano',
            messages=[
                {"role": "system", "content": "You are an expert educational content creator. Generate comprehensive, engaging lessons with step-by-step explanations."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=2000
        )
        
        lesson_content = response.choices[0].message.content.strip()
        
        # Parse the structured response
        lesson_data = _parse_lesson_content(lesson_content, original_question, explanation_style)
        
        return jsonify({
            "success": True,
            "lesson": lesson_data
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def _build_educational_prompt(question, style, difficulty):
    """Build a specialized prompt for educational content generation"""
    
    style_instructions = {
        'casual': "Explain like you're talking to a friend - use simple language, everyday examples, and a conversational tone.",
        'formal': "Use academic language with proper terminology, structured explanations, and scholarly examples.", 
        'analogy': "Focus heavily on analogies and metaphors to explain complex concepts. Use creative comparisons.",
        'visual': "Structure your explanation with clear bullet points, numbered steps, and visual descriptions."
    }
    
    difficulty_instructions = {
        'beginner': "Assume no prior knowledge. Define all terms and start with basics.",
        'intermediate': "Assume some background knowledge but explain key concepts clearly.",
        'advanced': "Use technical terminology and assume strong foundational knowledge."
    }
    
    prompt_parts = [
        f"Create a comprehensive educational lesson about: {question}",
        "",
        f"EXPLANATION STYLE: {style_instructions.get(style, style_instructions['casual'])}",
        f"DIFFICULTY LEVEL: {difficulty_instructions.get(difficulty, difficulty_instructions['intermediate'])}",
        "",
        "Please structure your response with these sections:",
        "",
        "STEP-BY-STEP EXPLANATION:",
        "Provide a detailed, step-by-step explanation of the topic.",
        "",
        "KEY POINTS:",
        "List 3-5 key takeaways (one per line, starting with '-')",
        "",
        "REAL-WORLD EXAMPLES:",
        "Provide 2-3 practical, real-world examples or applications",
        "",
        "FOLLOW-UP QUESTIONS:", 
        "Suggest 2-3 related questions for deeper exploration",
        "",
        "Make the content engaging, accurate, and educational. Use the specified style and difficulty level throughout."
    ]
    
    return "\n".join(prompt_parts)

def _parse_lesson_content(content, original_question, style):
    """Parse the AI-generated lesson content into structured data"""
    import datetime
    
    # Basic parsing - look for section headers
    sections = {
        'explanation': '',
        'key_points': [],
        'examples': [],
        'follow_up_questions': []
    }
    
    lines = content.split('\n')
    current_section = 'explanation'
    current_content = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for section headers
        if 'KEY POINTS:' in line.upper():
            if current_content:
                sections[current_section] = '\n'.join(current_content).strip()
                current_content = []
            current_section = 'key_points'
        elif 'REAL-WORLD EXAMPLES:' in line.upper() or 'EXAMPLES:' in line.upper():
            if current_content:
                if current_section == 'key_points':
                    sections[current_section] = [item.strip('- ') for item in current_content if item.strip()]
                else:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_content = []
            current_section = 'examples'
        elif 'FOLLOW-UP QUESTIONS:' in line.upper():
            if current_content:
                if current_section == 'key_points':
                    sections[current_section] = [item.strip('- ') for item in current_content if item.strip()]
                elif current_section == 'examples':
                    sections[current_section] = [item.strip() for item in current_content if item.strip()]
                else:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_content = []
            current_section = 'follow_up_questions'
        else:
            # Add content to current section
            if current_section == 'key_points' and line.startswith('-'):
                current_content.append(line)
            elif current_section in ['examples', 'follow_up_questions']:
                current_content.append(line)
            else:
                current_content.append(line)
    
    # Handle the last section
    if current_content:
        if current_section == 'key_points':
            sections[current_section] = [item.strip('- ') for item in current_content if item.strip()]
        elif current_section in ['examples', 'follow_up_questions']:
            sections[current_section] = [item.strip() for item in current_content if item.strip()]
        else:
            sections[current_section] = '\n'.join(current_content).strip()
    
    # Build lesson data structure
    lesson_data = {
        'original_question': original_question,
        'explanation_style': style,
        'explanation': sections['explanation'],
        'key_points': sections['key_points'],
        'examples': sections['examples'],
        'follow_up_questions': sections['follow_up_questions'],
        'timestamp': datetime.datetime.now().isoformat(),
        'marked_for_review': False
    }
    
    return lesson_data

@app.route('/ai_generate_quiz', methods=['POST'])
def ai_generate_quiz():
    import openai
    try:
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    except KeyError:
        return jsonify({"success": False, "error": "OpenAI API key not configured on server"}), 500

    data = request.get_json()
    lesson_content = data.get('lesson_content', '')
    original_question = data.get('original_question', '')
    quiz_type = data.get('quiz_type', 'multiple_choice')  # multiple_choice, true_false, short_answer
    num_questions = data.get('num_questions', 3)
    user_id = data.get('user_id')
    
    if not lesson_content:
        return jsonify({"success": False, "error": "Missing lesson content"}), 400

    try:
        prompt = _build_quiz_prompt(lesson_content, original_question, quiz_type, num_questions)
        
        response = client.chat.completions.create(
            model='gpt-5-nano',
            messages=[
                {"role": "system", "content": "You are an expert quiz creator. Generate well-crafted questions that test understanding of the provided content."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=1500
        )
        
        quiz_content = response.choices[0].message.content.strip()
        quiz_data = _parse_quiz_content(quiz_content, quiz_type, original_question)
        
        return jsonify({
            "success": True,
            "quiz": quiz_data
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def _build_quiz_prompt(lesson_content, original_question, quiz_type, num_questions):
    """Build prompt for quiz generation"""
    
    type_instructions = {
        'multiple_choice': f"Create {num_questions} multiple choice questions with 4 options each (A, B, C, D). Mark the correct answer.",
        'true_false': f"Create {num_questions} true/false questions about key concepts.",
        'short_answer': f"Create {num_questions} short answer questions that require 1-2 sentence responses."
    }
    
    prompt_parts = [
        f"Based on this lesson about '{original_question}', create a quiz to test comprehension:",
        "",
        "LESSON CONTENT:",
        lesson_content[:1000],  # Limit content length for prompt
        "",
        f"QUIZ REQUIREMENTS:",
        type_instructions.get(quiz_type, type_instructions['multiple_choice']),
        "",
        "Format your response exactly like this:",
        ""
    ]
    
    if quiz_type == 'multiple_choice':
        prompt_parts.extend([
            "QUESTION 1: [Question text]",
            "A) [Option A]",
            "B) [Option B]", 
            "C) [Option C]",
            "D) [Option D]",
            "CORRECT: [A/B/C/D]",
            "",
            "QUESTION 2: [Question text]",
            "[...continue pattern...]"
        ])
    elif quiz_type == 'true_false':
        prompt_parts.extend([
            "QUESTION 1: [Statement]",
            "CORRECT: [TRUE/FALSE]",
            "",
            "QUESTION 2: [Statement]", 
            "[...continue pattern...]"
        ])
    else:  # short_answer
        prompt_parts.extend([
            "QUESTION 1: [Question text]",
            "ANSWER: [Expected answer]",
            "",
            "QUESTION 2: [Question text]",
            "[...continue pattern...]"
        ])
    
    return "\n".join(prompt_parts)

def _parse_quiz_content(content, quiz_type, original_question):
    """Parse AI-generated quiz content into structured data"""
    import datetime
    
    questions = []
    lines = content.split('\n')
    current_question = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('QUESTION'):
            # Save previous question if exists
            if current_question:
                questions.append(current_question)
            
            # Start new question
            question_text = line.split(':', 1)[1].strip() if ':' in line else line
            current_question = {
                'question': question_text,
                'type': quiz_type
            }
            
            if quiz_type == 'multiple_choice':
                current_question['options'] = []
                
        elif quiz_type == 'multiple_choice' and line.startswith(('A)', 'B)', 'C)', 'D)')):
            if current_question:
                option_text = line[2:].strip()
                current_question['options'].append(option_text)
                
        elif line.startswith('CORRECT:'):
            if current_question:
                correct_answer = line.split(':', 1)[1].strip()
                current_question['correct_answer'] = correct_answer
                
        elif line.startswith('ANSWER:'):
            if current_question:
                answer = line.split(':', 1)[1].strip()
                current_question['expected_answer'] = answer
    
    # Add the last question
    if current_question:
        questions.append(current_question)
    
    quiz_data = {
        'original_question': original_question,
        'quiz_type': quiz_type,
        'questions': questions,
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    return quiz_data

# ---------------- MAIN ----------------

# ---------------- ADMIN ENDPOINTS ----------------

@app.route("/admin/set_user_pro", methods=["GET"])
def admin_set_user_pro():
    """Quick admin endpoint to set a user to pro plan"""
    uid = request.args.get("user_id")
    if not uid:
        return jsonify({"error": "Missing user_id parameter"}), 400
    
    plans = load_data(PLAN_FILE)
    plans[uid] = "pro"
    save_data(PLAN_FILE, plans)
    
    return jsonify({"status": "success", "user_id": uid, "plan": "pro", "message": f"User {uid} set to PRO plan"})

@app.route("/admin/user_status", methods=["GET"])  
def admin_user_status():
    """Get complete user status"""
    uid = request.args.get("user_id")
    if not uid:
        return jsonify({"error": "Missing user_id parameter"}), 400
    
    # Get usage
    usage_data = load_data(USAGE_FILE)
    words = usage_data.get(uid, 0)
    
    # Get plan
    plan_data = load_data(PLAN_FILE)
    plan = plan_data.get(uid, "free")
    
    return jsonify({
        "user_id": uid,
        "plan": plan, 
        "words_used": words,
        "status": "active"
    })

# ---------------- TYPING PROJECTS ----------------

@app.route("/projects", methods=["GET"])
@require_auth
def get_user_projects():
    """Get user's typing projects"""
    user_id = request.current_user['user_id']
    projects = load_data(TYPING_PROJECTS_FILE)
    user_projects = projects.get(user_id, [])
    
    return jsonify({"success": True, "projects": user_projects})

@app.route("/projects", methods=["POST"])
@require_auth
def create_project():
    """Create new typing project"""
    user_id = request.current_user['user_id']
    data = request.get_json()
    
    project = {
        'id': str(uuid.uuid4()),
        'name': data.get('name', 'Untitled Project'),
        'content': data.get('content', ''),
        'status': 'draft',
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'word_count': len(data.get('content', '').split()),
        'typing_settings': data.get('typing_settings', {}),
        'tags': data.get('tags', [])
    }
    
    projects = load_data(TYPING_PROJECTS_FILE)
    if user_id not in projects:
        projects[user_id] = []
    
    projects[user_id].append(project)
    save_data(TYPING_PROJECTS_FILE, projects)
    
    log_analytics_event(user_id, 'project_created', {'project_id': project['id']})
    
    return jsonify({"success": True, "project": project})

@app.route("/projects/<project_id>", methods=["GET"])
@require_auth
def get_project(project_id):
    """Get specific project"""
    user_id = request.current_user['user_id']
    projects = load_data(TYPING_PROJECTS_FILE)
    user_projects = projects.get(user_id, [])
    
    project = next((p for p in user_projects if p['id'] == project_id), None)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    return jsonify({"success": True, "project": project})

@app.route("/projects/<project_id>", methods=["PUT"])
@require_auth
def update_project(project_id):
    """Update project"""
    user_id = request.current_user['user_id']
    data = request.get_json()
    
    projects = load_data(TYPING_PROJECTS_FILE)
    user_projects = projects.get(user_id, [])
    
    project_index = next((i for i, p in enumerate(user_projects) if p['id'] == project_id), None)
    if project_index is None:
        return jsonify({"error": "Project not found"}), 404
    
    # Update project
    project = user_projects[project_index]
    project.update({
        'name': data.get('name', project['name']),
        'content': data.get('content', project['content']),
        'status': data.get('status', project['status']),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'word_count': len(data.get('content', project['content']).split()),
        'typing_settings': data.get('typing_settings', project.get('typing_settings', {})),
        'tags': data.get('tags', project.get('tags', []))
    })
    
    user_projects[project_index] = project
    projects[user_id] = user_projects
    save_data(TYPING_PROJECTS_FILE, projects)
    
    log_analytics_event(user_id, 'project_updated', {'project_id': project_id})
    
    return jsonify({"success": True, "project": project})

@app.route("/projects/<project_id>", methods=["DELETE"])
@require_auth
def delete_project(project_id):
    """Delete project"""
    user_id = request.current_user['user_id']
    
    projects = load_data(TYPING_PROJECTS_FILE)
    user_projects = projects.get(user_id, [])
    
    project_index = next((i for i, p in enumerate(user_projects) if p['id'] == project_id), None)
    if project_index is None:
        return jsonify({"error": "Project not found"}), 404
    
    # Remove project
    removed_project = user_projects.pop(project_index)
    projects[user_id] = user_projects
    save_data(TYPING_PROJECTS_FILE, projects)
    
    log_analytics_event(user_id, 'project_deleted', {'project_id': project_id})
    
    return jsonify({"success": True, "message": "Project deleted successfully"})

# ---------------- BILLING & SUBSCRIPTION ----------------

@app.route("/billing/plans", methods=["GET"])
def get_billing_plans():
    """Get available billing plans"""
    plans = {
        "free": {
            "name": "Free",
            "price": 0,
            "words_per_month": 1000,
            "features": ["Basic typing automation", "Limited AI generation", "5 projects"]
        },
        "pro": {
            "name": "Pro",
            "price": 9.99,
            "words_per_month": 50000,
            "features": ["Advanced typing automation", "Unlimited AI generation", "Unlimited projects", "Priority support"]
        },
        "premium": {
            "name": "Premium", 
            "price": 19.99,
            "words_per_month": 200000,
            "features": ["Everything in Pro", "Advanced humanization", "Learning mode", "Custom hotkeys", "Analytics"]
        },
        "enterprise": {
            "name": "Enterprise",
            "price": "Contact us",
            "words_per_month": "Unlimited",
            "features": ["Everything in Premium", "Team management", "SSO", "Custom integrations", "SLA"]
        }
    }
    
    return jsonify({"success": True, "plans": plans})

@app.route("/billing/subscribe", methods=["POST"])
@require_auth
def create_subscription():
    """Create new subscription (integrate with Stripe)"""
    user_id = request.current_user['user_id']
    data = request.get_json()
    plan_id = data.get('plan_id')
    
    if plan_id not in ['pro', 'premium', 'enterprise']:
        return jsonify({"success": False, "error": "Invalid plan"}), 400
    
    # In a real implementation, integrate with Stripe here
    # For now, just update the plan
    plans = load_data(PLAN_FILE)
    plans[user_id] = plan_id
    save_data(PLAN_FILE, plans)
    
    log_analytics_event(user_id, 'subscription_created', {'plan': plan_id})
    
    return jsonify({
        "success": True,
        "message": f"Subscribed to {plan_id} plan",
        "plan": plan_id
    })

@app.route("/billing/usage", methods=["GET"])
@require_auth
def get_billing_usage():
    """Get current month's usage and limits"""
    user_id = request.current_user['user_id']
    
    # Get plan and usage
    plans = load_data(PLAN_FILE)
    usage = load_data(USAGE_FILE)
    
    plan = plans.get(user_id, 'free')
    words_used = usage.get(user_id, 0)
    
    # Plan limits (words per month)
    limits = {
        'free': 2000,      # Free users: 2,000 words
        'basic': 10000,    # Basic plan: 10,000 words
        'pro': 20000,      # Pro plan: 20,000 words
        'premium': 50000,  # Premium plan: 50,000 words
        'enterprise': float('inf')  # Unlimited
    }
    
    limit = limits.get(plan, 1000)
    
    return jsonify({
        "success": True,
        "plan": plan,
        "words_used": words_used,
        "words_limit": limit if limit != float('inf') else "unlimited",
        "usage_percentage": (words_used / limit * 100) if limit != float('inf') else 0
    })

# ---------------- ANALYTICS & REPORTING ----------------

@app.route("/api/track-ai-generation", methods=["POST"])
@require_auth
def track_ai_generation():
    """Track words used in AI generation"""
    user_id = request.current_user['user_id']
    data = request.get_json()
    words_generated = data.get('words', 0)
    
    # Load current usage
    usage = load_data(USAGE_FILE)
    current_usage = usage.get(user_id, 0)
    
    # Get user plan and limits
    plans = load_data(PLAN_FILE)
    user_plan = plans.get(user_id, 'free')
    
    word_limits = {
        'free': 2000,
        'basic': 10000,
        'pro': 20000,
        'premium': 50000
    }
    
    limit = word_limits.get(user_plan, 2000)
    
    # Check if user has enough words
    if current_usage + words_generated > limit:
        return jsonify({
            "success": False,
            "error": "Insufficient words remaining",
            "words_remaining": max(0, limit - current_usage),
            "words_needed": words_generated,
            "plan": user_plan
        }), 403
    
    # Update usage
    usage[user_id] = current_usage + words_generated
    save_data(USAGE_FILE, usage)
    
    # Update global counter
    global_stats = load_data(GLOBAL_STATS_FILE)
    global_stats['total_words'] = global_stats.get('total_words', 0) + words_generated
    global_stats['total_generations'] = global_stats.get('total_generations', 0) + 1
    save_data(GLOBAL_STATS_FILE, global_stats)
    
    # Log analytics event
    log_analytics_event(user_id, 'ai_generation', {
        'words': words_generated,
        'plan': user_plan,
        'remaining': limit - usage[user_id]
    })
    
    return jsonify({
        "success": True,
        "words_used": words_generated,
        "total_used": usage[user_id],
        "words_remaining": limit - usage[user_id],
        "word_limit": limit
    })

@app.route("/api/global-stats", methods=["GET"])
def get_global_stats():
    """Get global statistics for website counter"""
    global_stats = load_data(GLOBAL_STATS_FILE)
    
    # Get total users count
    users = load_data(USERS_FILE)
    total_users = len(users)
    
    # Get active users (logged in within last 30 days)
    thirty_days_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=30)).isoformat()
    active_users = sum(1 for u in users.values() if u.get('last_login', '') > thirty_days_ago)
    
    return jsonify({
        "success": True,
        "stats": {
            "total_words": global_stats.get('total_words', 0),
            "total_generations": global_stats.get('total_generations', 0),
            "total_users": total_users,
            "active_users": active_users,
            "total_typing_sessions": global_stats.get('total_typing_sessions', 0)
        }
    })

@app.route("/api/user-dashboard", methods=["GET"])
@require_auth
def get_user_dashboard():
    """Get comprehensive user dashboard data"""
    user_id = request.current_user['user_id']
    
    # Get user data
    users = load_data(USERS_FILE)
    user_data = users.get(request.current_user['email'])
    
    # Get plan and usage
    plans = load_data(PLAN_FILE)
    user_plan = plans.get(user_id, 'free')
    
    usage = load_data(USAGE_FILE)
    words_used = usage.get(user_id, 0)
    
    # Word limits
    word_limits = {
        'free': 2000,
        'basic': 10000,
        'pro': 20000,
        'premium': 50000
    }
    
    limit = word_limits.get(user_plan, 2000)
    
    # Feature access based on plan
    features = {
        'ai_generation': True,  # All plans get AI generation
        'humanizer': user_plan != 'free',  # Only paid plans get humanizer
        'premium_typing': user_plan != 'free',  # Only paid plans get premium typing
        'learning_hub': True,  # All plans get learning hub
        'missions': True,  # All plans get missions
        'unlimited_profiles': user_plan != 'free',  # Free users limited to 3 profiles
        'priority_support': user_plan in ['pro', 'premium'],
        'advanced_analytics': user_plan in ['pro', 'premium']
    }
    
    # Get referral data
    referral_code = user_data.get('referral_code', '')
    referrals = load_data(REFERRALS_FILE)
    user_referrals = referrals.get(user_id, {})
    
    # Calculate bonus words from referrals
    referral_bonus = user_referrals.get('successful_referrals', 0) * 500  # 500 words per referral
    
    return jsonify({
        "success": True,
        "dashboard": {
            "user": {
                "name": user_data.get('name'),
                "email": request.current_user['email'],
                "user_id": user_id,
                "joined": user_data.get('created_at'),
                "verified": user_data.get('email_verified', False)
            },
            "plan": {
                "name": user_plan,
                "words_limit": limit,
                "words_used": words_used,
                "words_remaining": max(0, limit - words_used),
                "usage_percentage": min(100, (words_used / limit * 100)) if limit > 0 else 0,
                "reset_date": get_next_reset_date(),
                "features": features
            },
            "referrals": {
                "code": referral_code,
                "successful": user_referrals.get('successful_referrals', 0),
                "pending": user_referrals.get('pending_referrals', 0),
                "bonus_words": referral_bonus,
                "share_link": f"https://slywriterapp.com?ref={referral_code}"
            },
            "stats": {
                "total_generations": user_referrals.get('total_generations', 0),
                "total_typing_sessions": user_referrals.get('total_typing_sessions', 0),
                "favorite_profile": user_referrals.get('favorite_profile', 'Medium'),
                "avg_wpm": user_referrals.get('avg_wpm', 70)
            }
        }
    })

def get_next_reset_date():
    """Get the next monthly reset date"""
    now = datetime.datetime.utcnow()
    next_month = now.replace(day=1) + datetime.timedelta(days=32)
    return next_month.replace(day=1).isoformat()

@app.route("/analytics/dashboard", methods=["GET"])
@require_auth
def get_user_analytics():
    """Get user analytics dashboard data"""
    user_id = request.current_user['user_id']
    
    analytics = load_data(ANALYTICS_FILE)
    user_events = [e for e in analytics.get('events', []) if e['user_id'] == user_id]
    
    # Calculate metrics
    today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    this_week = [(datetime.datetime.utcnow() - datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    
    dashboard_data = {
        'words_today': sum(e.get('event_data', {}).get('words', 0) for e in user_events if e['date'] == today),
        'words_this_week': sum(e.get('event_data', {}).get('words', 0) for e in user_events if e['date'] in this_week),
        'projects_count': len(load_data(TYPING_PROJECTS_FILE).get(user_id, [])),
        'login_streak': calculate_login_streak(user_events),
        'activity_chart': generate_activity_chart(user_events, 30)  # Last 30 days
    }
    
    return jsonify({"success": True, "analytics": dashboard_data})

def calculate_login_streak(events):
    """Calculate consecutive login days"""
    login_dates = set()
    for event in events:
        if event['event_type'] == 'user_login':
            login_dates.add(event['date'])
    
    if not login_dates:
        return 0
    
    # Sort dates and check for consecutive days
    sorted_dates = sorted(login_dates, reverse=True)
    streak = 0
    current_date = datetime.datetime.utcnow().date()
    
    for date_str in sorted_dates:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        if (current_date - date_obj).days == streak:
            streak += 1
            current_date = date_obj
        else:
            break
    
    return streak

def generate_activity_chart(events, days):
    """Generate daily activity chart data"""
    chart_data = []
    for i in range(days):
        date = (datetime.datetime.utcnow() - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        day_events = [e for e in events if e['date'] == date]
        words = sum(e.get('event_data', {}).get('words', 0) for e in day_events)
        chart_data.append({'date': date, 'words': words})
    
    return list(reversed(chart_data))

@app.route("/analytics/export", methods=["GET"])
@require_auth
def export_user_data():
    """Export user data"""
    user_id = request.current_user['user_id']
    
    # Gather all user data
    users = load_data(USERS_FILE)
    projects = load_data(TYPING_PROJECTS_FILE)
    settings = load_data(USER_SETTINGS_FILE)
    analytics = load_data(ANALYTICS_FILE)
    
    # Find user data
    user_data = None
    for email, data in users.items():
        if data['user_id'] == user_id:
            user_data = data
            break
    
    export_data = {
        'user_profile': user_data,
        'projects': projects.get(user_id, []),
        'settings': settings.get(user_id, {}),
        'analytics': [e for e in analytics.get('events', []) if e['user_id'] == user_id],
        'exported_at': datetime.datetime.utcnow().isoformat()
    }
    
    return jsonify({"success": True, "data": export_data})

# ---------------- PUBLIC STATS & REFERRAL ENDPOINTS ----------------

@app.route("/api/public/global-words", methods=["GET"])
def get_global_word_count():
    """Get the total number of words typed by all users - public endpoint for website"""
    try:
        # Load word data from all users
        usage_data = load_data(USAGE_FILE)
        total_words = sum(usage_data.values())
        
        # Also get total users count
        users = load_data(USERS_FILE)
        total_users = len(users)
        
        # Get today's word count
        analytics = load_data(ANALYTICS_FILE)
        today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        today_words = sum(
            event.get('event_data', {}).get('words', 0) 
            for event in analytics.get('events', []) 
            if event.get('date') == today and 'words' in event.get('event_data', {})
        )
        
        return jsonify({
            "success": True,
            "data": {
                "total_words": total_words,
                "total_users": total_users,
                "words_today": today_words,
                "last_updated": datetime.datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        print(f"Error getting global word count: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve global stats"
        }), 500

@app.route("/api/referral/create-link", methods=["POST"])
@require_auth
def create_referral_link():
    """Create a unique referral link for the authenticated user"""
    try:
        user_id = request.current_user['user_id']
        email = request.current_user['email']
        name = request.current_user.get('name', 'User')
        
        # Check if user already has a referral code
        users = load_data(USERS_FILE)
        user_data = users.get(email)
        
        if user_data and user_data.get('referral_code'):
            referral_code = user_data['referral_code']
        else:
            # Generate unique referral code
            # Format: First 3 letters of name + random 6 character alphanumeric
            name_prefix = ''.join(filter(str.isalpha, name))[:3].upper()
            if not name_prefix:
                name_prefix = "USR"
            
            # Generate unique token
            unique_token = secrets.token_hex(3).upper()
            referral_code = f"{name_prefix}{unique_token}"
            
            # Save to user data
            if user_data:
                user_data['referral_code'] = referral_code
                users[email] = user_data
                save_data(USERS_FILE, users)
            
            # Save to referral mapping
            ref_data = load_data(REFERRAL_FILE)
            if 'code_map' not in ref_data:
                ref_data['code_map'] = {}
            ref_data['code_map'][referral_code] = user_id
            save_data(REFERRAL_FILE, ref_data)
        
        # Create the referral link
        referral_link = f"https://slywriterapp.com/?ref={referral_code}"
        
        # Get current referral stats
        ref_data = load_data(REFERRAL_FILE)
        referred_by = ref_data.get('referred_by', {})
        
        # Count successful referrals
        successful_referrals = sum(
            1 for uid, referrer in referred_by.items() 
            if referrer == user_id
        )
        
        # Calculate rewards based on tiers (from MissionTab.tsx)
        def get_referral_rewards(referrals):
            """Calculate total rewards based on referral tiers"""
            rewards = {
                "total_words": 0,
                "premium_days": 0,
                "current_tier": 0,
                "next_tier_referrals": 1,
                "next_tier_reward": "Extra 1,000 words"
            }
            
            # Tier rewards structure
            tiers = [
                {"tier": 1, "referrals": 1, "words": 1000, "premium_days": 0},
                {"tier": 2, "referrals": 2, "words": 2500, "premium_days": 0},
                {"tier": 3, "referrals": 3, "words": 0, "premium_days": 7},
                {"tier": 4, "referrals": 5, "words": 5000, "premium_days": 0},
                {"tier": 5, "referrals": 7, "words": 0, "premium_days": 14},
                {"tier": 6, "referrals": 10, "words": 10000, "premium_days": 0},
                {"tier": 7, "referrals": 15, "words": 0, "premium_days": 30},
                {"tier": 8, "referrals": 20, "words": 25000, "premium_days": 0},
                {"tier": 9, "referrals": 30, "words": 0, "premium_days": 60},
                {"tier": 10, "referrals": 50, "words": 0, "premium_days": 180}
            ]
            
            # Calculate cumulative rewards
            for tier in tiers:
                if referrals >= tier["referrals"]:
                    rewards["total_words"] += tier["words"]
                    rewards["premium_days"] += tier["premium_days"]
                    rewards["current_tier"] = tier["tier"]
                else:
                    # Found the next tier
                    rewards["next_tier_referrals"] = tier["referrals"]
                    if tier["words"] > 0:
                        rewards["next_tier_reward"] = f"Extra {tier['words']:,} words"
                    else:
                        days = tier["premium_days"]
                        if days == 7:
                            rewards["next_tier_reward"] = "1 week free Premium"
                        elif days == 14:
                            rewards["next_tier_reward"] = "2 weeks free Premium"
                        elif days == 30:
                            rewards["next_tier_reward"] = "1 month free Premium"
                        elif days == 60:
                            rewards["next_tier_reward"] = "2 months free Premium"
                        elif days == 180:
                            rewards["next_tier_reward"] = "6 months free Premium"
                    break
            
            return rewards
        
        rewards = get_referral_rewards(successful_referrals)
        
        return jsonify({
            "success": True,
            "data": {
                "referral_code": referral_code,
                "referral_link": referral_link,
                "successful_referrals": successful_referrals,
                "current_tier": rewards["current_tier"],
                "total_words_earned": rewards["total_words"],
                "premium_days_earned": rewards["premium_days"],
                "next_tier": {
                    "referrals_needed": rewards["next_tier_referrals"] - successful_referrals,
                    "reward": rewards["next_tier_reward"]
                },
                "charity_donated": successful_referrals * 0.10  # $0.10 per referral to charity
            }
        })
        
    except Exception as e:
        print(f"Error creating referral link: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to create referral link"
        }), 500

@app.route("/api/referral/validate", methods=["GET"])
def validate_referral_code():
    """Validate a referral code - public endpoint for signup page"""
    code = request.args.get('code', '').strip()
    
    if not code:
        return jsonify({
            "success": False,
            "error": "No referral code provided"
        }), 400
    
    ref_data = load_data(REFERRAL_FILE)
    code_map = ref_data.get('code_map', {})
    
    if code in code_map:
        # Get referrer info
        referrer_id = code_map[code]
        users = load_data(USERS_FILE)
        
        # Find referrer name
        referrer_name = "A friend"
        for email, user_data in users.items():
            if user_data.get('user_id') == referrer_id:
                referrer_name = user_data.get('name', 'A friend')
                break
        
        return jsonify({
            "success": True,
            "data": {
                "valid": True,
                "referrer_name": referrer_name,
                "bonus_message": "You'll both get 500 bonus words when you sign up!"
            }
        })
    else:
        return jsonify({
            "success": True,
            "data": {
                "valid": False
            }
        })

# ---------------- API DOCUMENTATION ENDPOINT ----------------

@app.route("/api/docs", methods=["GET"])
def api_documentation():
    """Returns a list of all available API endpoints"""
    endpoints = []
    
    # Collect all registered routes
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            endpoints.append({
                'endpoint': rule.rule,
                'methods': methods,
                'name': rule.endpoint
            })
    
    # Sort by endpoint path
    endpoints.sort(key=lambda x: x['endpoint'])
    
    # Organize by category
    categorized = {
        'Authentication': [],
        'Public API': [],
        'User API': [],
        'Admin API': [],
        'AI Services': [],
        'Learning': [],
        'Referral': [],
        'Telemetry': [],
        'Health & Stats': [],
        'Other': []
    }
    
    for ep in endpoints:
        path = ep['endpoint']
        if '/auth/' in path:
            categorized['Authentication'].append(ep)
        elif '/api/public/' in path:
            categorized['Public API'].append(ep)
        elif '/api/user/' in path or '/user-' in path:
            categorized['User API'].append(ep)
        elif '/admin/' in path or '/api/admin/' in path:
            categorized['Admin API'].append(ep)
        elif '/api/ai/' in path or '/humanize' in path:
            categorized['AI Services'].append(ep)
        elif '/learning/' in path:
            categorized['Learning'].append(ep)
        elif '/referral/' in path:
            categorized['Referral'].append(ep)
        elif '/telemetry' in path:
            categorized['Telemetry'].append(ep)
        elif '/health' in path or '/stats' in path or '/global-' in path:
            categorized['Health & Stats'].append(ep)
        else:
            categorized['Other'].append(ep)
    
    # Remove empty categories
    categorized = {k: v for k, v in categorized.items() if v}
    
    return jsonify({
        'success': True,
        'server_url': 'https://slywriterapp.onrender.com',
        'total_endpoints': len(endpoints),
        'endpoints_by_category': categorized,
        'all_endpoints': endpoints
    })

# ---------------- ENHANCED ADMIN ENDPOINTS ----------------

@app.route("/admin/dashboard", methods=["GET"])
def admin_dashboard():
    """Admin dashboard with key metrics"""
    # Basic auth check - in production use proper admin authentication
    api_key = request.headers.get('X-Admin-Key')
    if api_key != os.environ.get('ADMIN_API_KEY'):
        return jsonify({"error": "Unauthorized"}), 401
    
    users = load_data(USERS_FILE)
    usage = load_data(USAGE_FILE)
    plans = load_data(PLAN_FILE)
    analytics = load_data(ANALYTICS_FILE)
    
    metrics = {
        'total_users': len(users),
        'active_users_today': len([e for e in analytics.get('events', []) if e['event_type'] == 'user_login' and e['date'] == datetime.datetime.utcnow().strftime('%Y-%m-%d')]),
        'total_words': sum(usage.values()),
        'plan_distribution': {plan: len([u for u in plans.values() if u == plan]) for plan in ['free', 'pro', 'premium', 'enterprise']},
        'recent_registrations': len([u for u in users.values() if (datetime.datetime.utcnow() - datetime.datetime.fromisoformat(u['created_at'])).days <= 7])
    }
    
    return jsonify({"success": True, "metrics": metrics})

@app.route("/admin/users", methods=["GET"])
def admin_list_users():
    """List all users with pagination"""
    api_key = request.headers.get('X-Admin-Key')
    if api_key != os.environ.get('ADMIN_API_KEY'):
        return jsonify({"error": "Unauthorized"}), 401
    
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    search = request.args.get('search', '')
    
    users = load_data(USERS_FILE)
    plans = load_data(PLAN_FILE)
    usage = load_data(USAGE_FILE)
    
    # Convert to list and add extra data
    user_list = []
    for email, user_data in users.items():
        user_id = user_data['user_id']
        user_info = {
            **user_data,
            'plan': plans.get(user_id, 'free'),
            'words_used': usage.get(user_id, 0)
        }
        # Remove sensitive data
        user_info.pop('password_hash', None)
        user_info.pop('verification_token', None)
        
        # Apply search filter
        if search.lower() in email.lower() or search.lower() in user_data.get('name', '').lower():
            user_list.append(user_info)
    
    # Pagination
    total = len(user_list)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_users = user_list[start:end]
    
    return jsonify({
        "success": True,
        "users": paginated_users,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page
        }
    })

@app.route("/admin/users/<user_id>/plan", methods=["POST"])
def admin_update_user_plan(user_id):
    """Update user's plan"""
    api_key = request.headers.get('X-Admin-Key')
    if api_key != os.environ.get('ADMIN_API_KEY'):
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    new_plan = data.get('plan')
    
    if new_plan not in ['free', 'pro', 'premium', 'enterprise']:
        return jsonify({"error": "Invalid plan"}), 400
    
    plans = load_data(PLAN_FILE)
    plans[user_id] = new_plan
    save_data(PLAN_FILE, plans)
    
    log_analytics_event(user_id, 'plan_updated_by_admin', {'new_plan': new_plan})

    return jsonify({"success": True, "user_id": user_id, "plan": new_plan})

# ============== LICENSE VERIFICATION + VERSION CONTROL SYSTEM ==============

# Current app version (update this with each release)
CURRENT_APP_VERSION = "2.1.6"
MINIMUM_SUPPORTED_VERSION = "2.0.0"  # Versions below this MUST update

# File to store device registrations
DEVICES_FILE = "user_devices.json"

def load_devices():
    """Load device registrations"""
    if not os.path.exists(DEVICES_FILE):
        return {}
    try:
        with open(DEVICES_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_devices(devices):
    """Save device registrations"""
    with open(DEVICES_FILE, 'w') as f:
        json.dump(devices, f, indent=2)

def get_plan_device_limit(plan):
    """Get max devices allowed for plan"""
    limits = {
        "free": 1,
        "pro": 2,
        "premium": 3
    }
    return limits.get(plan.lower(), 1)

def version_compare(v1, v2):
    """Compare two version strings (e.g., '2.1.6' vs '2.0.0')"""
    def normalize(v):
        return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]
    return normalize(v1) < normalize(v2)

@app.route("/api/license/verify", methods=["POST", "OPTIONS"])
@cross_origin(origins=["*"])
def verify_license():
    """
    Comprehensive license verification with version checking
    Called on app startup and periodically during use
    """
    logger.info("=" * 60)
    logger.info("LICENSE VERIFICATION REQUEST")

    data = request.get_json()
    license_key = data.get('license_key')  # This is the user's email or JWT token
    machine_id = data.get('machine_id')
    app_version = data.get('app_version', '0.0.0')

    logger.info(f"License Key: {license_key[:20] if license_key else 'None'}...")
    logger.info(f"Machine ID: {machine_id}")
    logger.info(f"App Version: {app_version}")

    # Version check - CRITICAL
    needs_update = version_compare(app_version, MINIMUM_SUPPORTED_VERSION)
    update_available = version_compare(app_version, CURRENT_APP_VERSION)

    logger.info(f"Needs Update: {needs_update}")
    logger.info(f"Update Available: {update_available}")

    if needs_update:
        logger.warning(f"Version {app_version} is below minimum {MINIMUM_SUPPORTED_VERSION}")
        return jsonify({
            "valid": False,
            "error": "update_required",
            "message": f"Your app version ({app_version}) is outdated. Please update to continue.",
            "current_version": CURRENT_APP_VERSION,
            "minimum_version": MINIMUM_SUPPORTED_VERSION,
            "update_url": "https://github.com/slywriterapp/slywriterapp/releases/latest"
        }), 426  # 426 Upgrade Required

    # License key validation
    if not license_key:
        logger.error("No license key provided")
        return jsonify({
            "valid": False,
            "error": "missing_license",
            "message": "Please log in to verify your subscription"
        }), 400

    # Try to verify as JWT token first (from website login)
    user_email = None
    try:
        payload = jwt.decode(license_key, JWT_SECRET, algorithms=["HS256"])
        user_email = payload.get("email")
        logger.info(f"JWT verified, email: {user_email}")
    except:
        # If not JWT, treat as email directly
        user_email = license_key
        logger.info(f"Using license_key as email: {user_email}")

    if not user_email:
        logger.error("Could not extract email from license key")
        return jsonify({
            "valid": False,
            "error": "invalid_license",
            "message": "Invalid license key"
        }), 400

    # Load user data
    users = load_data(USERS_FILE)
    plans = load_data(PLAN_FILE)

    if user_email not in users:
        logger.error(f"User not found: {user_email}")
        return jsonify({
            "valid": False,
            "error": "user_not_found",
            "message": "Please sign up at https://www.slywriter.ai"
        }), 404

    user_data = users[user_email]
    user_id = user_data.get('user_id')
    plan = plans.get(user_id, 'free').lower()

    logger.info(f"User found: {user_email}, Plan: {plan}")

    # Device binding check
    if machine_id:
        devices = load_devices()
        user_devices_key = f"{user_email}:devices"
        user_devices = devices.get(user_devices_key, [])

        device_limit = get_plan_device_limit(plan)
        logger.info(f"Device limit for {plan}: {device_limit}")
        logger.info(f"Current devices: {len(user_devices)}")

        # Check if this machine is already registered
        machine_registered = any(d['machine_id'] == machine_id for d in user_devices)

        if not machine_registered:
            if len(user_devices) >= device_limit:
                logger.warning(f"Device limit reached: {len(user_devices)}/{device_limit}")
                return jsonify({
                    "valid": False,
                    "error": "device_limit_reached",
                    "message": f"Maximum {device_limit} device(s) allowed for {plan} plan. Please deactivate another device or upgrade.",
                    "current_devices": len(user_devices),
                    "max_devices": device_limit,
                    "devices": [
                        {"id": d['machine_id'][:8], "name": d.get('name', 'Unknown'), "last_seen": d.get('last_seen')}
                        for d in user_devices
                    ]
                }), 403

            # Register new device
            new_device = {
                "machine_id": machine_id,
                "name": data.get('device_name', f"Device {len(user_devices) + 1}"),
                "first_seen": datetime.datetime.utcnow().isoformat(),
                "last_seen": datetime.datetime.utcnow().isoformat(),
                "app_version": app_version
            }
            user_devices.append(new_device)
            devices[user_devices_key] = user_devices
            save_devices(devices)
            logger.info(f"Registered new device: {machine_id[:8]}")
        else:
            # Update last seen for existing device
            for device in user_devices:
                if device['machine_id'] == machine_id:
                    device['last_seen'] = datetime.datetime.utcnow().isoformat()
                    device['app_version'] = app_version
            devices[user_devices_key] = user_devices
            save_devices(devices)
            logger.info(f"Updated existing device: {machine_id[:8]}")

    # Get usage limits
    usage = load_data(USAGE_FILE)
    words_used = usage.get(user_id, 0)

    plan_limits = {
        "free": {"words": 500, "ai_gen": 3, "humanizer": 0},
        "pro": {"words": 5000, "ai_gen": -1, "humanizer": 3},
        "premium": {"words": -1, "ai_gen": -1, "humanizer": -1}
    }
    limits = plan_limits.get(plan, plan_limits["free"])

    # Build response
    response_data = {
        "valid": True,
        "user": {
            "email": user_email,
            "user_id": user_id,
            "plan": plan
        },
        "limits": {
            "words_per_week": limits["words"],
            "words_used": words_used,
            "words_remaining": "unlimited" if limits["words"] == -1 else max(0, limits["words"] - words_used),
            "ai_gen_per_week": limits["ai_gen"],
            "humanizer_per_week": limits["humanizer"]
        },
        "features_enabled": {
            "ai_generation": limits["ai_gen"] != 0,
            "humanizer": limits["humanizer"] != 0,
            "premium_typing": plan in ["pro", "premium"],
            "unlimited_words": limits["words"] == -1
        },
        "version_info": {
            "current_app_version": app_version,
            "latest_version": CURRENT_APP_VERSION,
            "update_available": update_available,
            "update_required": False,
            "update_url": "https://github.com/slywriterapp/slywriterapp/releases/latest"
        },
        "device_info": {
            "machine_id": machine_id[:8] if machine_id else None,
            "devices_used": len(load_devices().get(f"{user_email}:devices", [])),
            "devices_allowed": get_plan_device_limit(plan)
        }
    }

    logger.info("License verification SUCCESS")
    logger.info("=" * 60)

    log_analytics_event(user_id, 'license_verified', {
        'app_version': app_version,
        'machine_id': machine_id[:8] if machine_id else None,
        'plan': plan
    })

    return jsonify(response_data)

@app.route("/api/license/deactivate-device", methods=["POST"])
@cross_origin(origins=["*"])
def deactivate_device():
    """Deactivate a device to free up a slot"""
    data = request.get_json()
    license_key = data.get('license_key')
    machine_id_to_remove = data.get('machine_id')

    # Extract email from license
    try:
        payload = jwt.decode(license_key, JWT_SECRET, algorithms=["HS256"])
        user_email = payload.get("email")
    except:
        user_email = license_key

    if not user_email or not machine_id_to_remove:
        return jsonify({"success": False, "error": "Missing parameters"}), 400

    devices = load_devices()
    user_devices_key = f"{user_email}:devices"
    user_devices = devices.get(user_devices_key, [])

    # Remove the device
    user_devices = [d for d in user_devices if d['machine_id'] != machine_id_to_remove]
    devices[user_devices_key] = user_devices
    save_devices(devices)

    logger.info(f"Deactivated device {machine_id_to_remove[:8]} for {user_email}")

    return jsonify({
        "success": True,
        "message": "Device deactivated successfully",
        "devices_remaining": len(user_devices)
    })

# ============== AI FEATURES - MOVED TO SERVER ==============

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not set - AI features will be disabled")

@app.route("/api/ai/generate", methods=["POST"])
@cross_origin(origins=["*"])
def ai_generate():
    """
    AI text generation - MOVED FROM DESKTOP APP
    Requires valid license and checks usage limits
    """
    data = request.get_json()
    license_key = data.get('license_key')
    prompt = data.get('prompt')
    word_count = data.get('word_count', 500)
    tone = data.get('tone', 'professional')

    logger.info(f"AI Generate request: {prompt[:50] if prompt else 'None'}...")

    # Extract user email
    try:
        payload = jwt.decode(license_key, JWT_SECRET, algorithms=["HS256"])
        user_email = payload.get("email")
    except:
        user_email = license_key

    if not user_email or not prompt:
        return jsonify({"success": False, "error": "Missing parameters"}), 400

    # Verify user and check limits
    users = load_data(USERS_FILE)
    if user_email not in users:
        return jsonify({"success": False, "error": "User not found"}), 404

    user_data = users[user_email]
    user_id = user_data.get('user_id')
    plans = load_data(PLAN_FILE)
    plan = plans.get(user_id, 'free').lower()

    # Check AI generation limit
    plan_limits = {
        "free": 3,
        "pro": -1,  # unlimited
        "premium": -1
    }
    limit = plan_limits.get(plan, 0)

    if limit == 0:
        return jsonify({
            "success": False,
            "error": "feature_not_available",
            "message": "AI generation is not available on your plan. Please upgrade."
        }), 403

    # TODO: Track weekly usage (for now, allow if limit != 0)

    # Make OpenAI request
    if not OPENAI_API_KEY:
        return jsonify({
            "success": False,
            "error": "service_unavailable",
            "message": "AI service is temporarily unavailable"
        }), 503

    try:
        import openai
        openai.api_key = OPENAI_API_KEY

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a helpful writing assistant. Write in a {tone} tone."},
                {"role": "user", "content": f"Write approximately {word_count} words about: {prompt}"}
            ],
            max_tokens=word_count * 2,
            temperature=0.7
        )

        generated_text = response.choices[0].message.content.strip()

        # Track usage
        log_analytics_event(user_id, 'ai_generation_used', {
            'prompt_length': len(prompt),
            'generated_length': len(generated_text),
            'word_count': word_count,
            'plan': plan
        })

        logger.info(f"AI generation successful for {user_email}")

        return jsonify({
            "success": True,
            "text": generated_text,
            "words_generated": len(generated_text.split()),
            "plan": plan
        })

    except Exception as e:
        logger.error(f"AI generation failed: {e}")
        return jsonify({
            "success": False,
            "error": "generation_failed",
            "message": str(e)
        }), 500

@app.route("/api/ai/humanize", methods=["POST"])
@cross_origin(origins=["*"])
def ai_humanize():
    """
    AI text humanizer - MOVED FROM DESKTOP APP
    Makes AI-generated text sound more natural
    """
    data = request.get_json()
    license_key = data.get('license_key')
    text = data.get('text')

    logger.info(f"AI Humanize request: {text[:50] if text else 'None'}...")

    # Extract user email
    try:
        payload = jwt.decode(license_key, JWT_SECRET, algorithms=["HS256"])
        user_email = payload.get("email")
    except:
        user_email = license_key

    if not user_email or not text:
        return jsonify({"success": False, "error": "Missing parameters"}), 400

    # Verify user and check limits
    users = load_data(USERS_FILE)
    if user_email not in users:
        return jsonify({"success": False, "error": "User not found"}), 404

    user_data = users[user_email]
    user_id = user_data.get('user_id')
    plans = load_data(PLAN_FILE)
    plan = plans.get(user_id, 'free').lower()

    # Check humanizer limit
    plan_limits = {
        "free": 0,
        "pro": 3,
        "premium": -1
    }
    limit = plan_limits.get(plan, 0)

    if limit == 0:
        return jsonify({
            "success": False,
            "error": "feature_not_available",
            "message": "AI humanizer is not available on your plan. Please upgrade to Pro."
        }), 403

    # Make OpenAI request
    if not OPENAI_API_KEY:
        return jsonify({
            "success": False,
            "error": "service_unavailable",
            "message": "AI service is temporarily unavailable"
        }), 503

    try:
        import openai
        openai.api_key = OPENAI_API_KEY

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at making AI-generated text sound more natural and human-like. Rewrite the text to be more conversational, varied in sentence structure, and natural."},
                {"role": "user", "content": f"Humanize this text:\n\n{text}"}
            ],
            temperature=0.8
        )

        humanized_text = response.choices[0].message.content.strip()

        # Track usage
        log_analytics_event(user_id, 'humanizer_used', {
            'original_length': len(text),
            'humanized_length': len(humanized_text),
            'plan': plan
        })

        logger.info(f"Humanization successful for {user_email}")

        return jsonify({
            "success": True,
            "humanized_text": humanized_text,
            "plan": plan
        })

    except Exception as e:
        logger.error(f"Humanization failed: {e}")
        return jsonify({
            "success": False,
            "error": "humanization_failed",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
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

app = Flask(__name__)
CORS(app)  # Enable CORS for web app

# Security
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-jwt-secret-change-this')

# Data files
USAGE_FILE = "word_data.json"
PLAN_FILE = "plan_data.json"
REFERRAL_FILE = "referral_data.json"
USERS_FILE = "users.json"
USER_SETTINGS_FILE = "user_settings.json"
SESSIONS_FILE = "sessions.json"
PASSWORD_RESETS_FILE = "password_resets.json"
TYPING_PROJECTS_FILE = "typing_projects.json"
ANALYTICS_FILE = "analytics.json"

def load_data(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return {}

def save_data(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

# ---------------- SECURITY & AUTH UTILITIES ----------------

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

# ---------------- HEALTH CHECK ----------------

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "SlyWriter API is running"}), 200

# ---------------- AUTHENTICATION ----------------

@app.route("/auth/register", methods=["POST"])
def register():
    """Register new user account"""
    data = request.get_json()
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    name = data.get('name', '').strip()
    referral_code = data.get('referral_code', '').strip()
    
    # Validation
    if not email or not password or not name:
        return jsonify({"success": False, "error": "Missing required fields"}), 400
    
    if not validate_email(email):
        return jsonify({"success": False, "error": "Invalid email format"}), 400
    
    password_valid, password_message = validate_password(password)
    if not password_valid:
        return jsonify({"success": False, "error": password_message}), 400
    
    # Check if user already exists
    users = load_data(USERS_FILE)
    if email in users:
        return jsonify({"success": False, "error": "Email already registered"}), 400
    
    # Create user
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(password)
    
    user_data = {
        'user_id': user_id,
        'email': email,
        'name': name,
        'password_hash': hashed_password,
        'created_at': datetime.datetime.utcnow().isoformat(),
        'verified': False,
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
    
    # Send verification email
    verification_link = f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/verify-email?token={user_data['verification_token']}"
    send_email(
        email,
        "Welcome to SlyWriter - Verify Your Email",
        f"""
        Welcome to SlyWriter, {name}!
        
        Please verify your email address by clicking this link:
        {verification_link}
        
        If you didn't create this account, please ignore this email.
        
        Best regards,
        The SlyWriter Team
        """
    )
    
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
        "verified": user_data.get('verified', False),
        "plan": user_plan,
        "words_used": words_used
    })

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
        "verified": user_data.get('verified', False),
        "plan": plans.get(user_id, 'free'),
        "words_used": usage.get(user_id, 0),
        "created_at": user_data.get('created_at'),
        "last_login": user_data.get('last_login')
    })

@app.route("/auth/verify-email", methods=["POST"])
def verify_email():
    """Verify user email address"""
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({"success": False, "error": "Missing verification token"}), 400
    
    # Find user with this token
    users = load_data(USERS_FILE)
    user_email = None
    user_data = None
    
    for email, data in users.items():
        if data.get('verification_token') == token:
            user_email = email
            user_data = data
            break
    
    if not user_data:
        return jsonify({"success": False, "error": "Invalid verification token"}), 400
    
    # Mark as verified
    user_data['verified'] = True
    user_data['verification_token'] = None
    users[user_email] = user_data
    save_data(USERS_FILE, users)
    
    log_analytics_event(user_data['user_id'], 'email_verified')
    
    return jsonify({"success": True, "message": "Email verified successfully"})

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
def generate_filler():
    import openai
    try:
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    except KeyError:
        return jsonify({"error": "OpenAI key not set"}), 500

    data = request.get_json()
    prompt = data.get('prompt', '')

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
    try:
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    except KeyError:
        return jsonify({"success": False, "error": "OpenAI API key not configured on server"}), 500

    data = request.get_json()
    prompt = data.get('prompt', '')
    user_id = data.get('user_id')
    
    if not prompt:
        return jsonify({"success": False, "error": "Missing prompt"}), 400

    try:
        # Enhanced system prompt to ensure adequate length
        system_prompt = (
            "You are a helpful writing assistant. IMPORTANT: Always generate comprehensive, "
            "detailed responses with proper depth and length. Never provide brief or short answers. "
            "Aim for at least 200-300 words minimum, with thorough explanations and examples."
        )
        
        # Try models in order specified by user (start with working model)
        models_to_try = ['gpt-4.1-nano', 'gpt-5-nano', 'gpt-4o-mini']
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
                    max_completion_tokens=2000
                )
                model_to_use = model
                print(f"[AI] Successfully using model: {model}")
                break
            except Exception as model_error:
                print(f"[AI] Model {model} failed: {model_error}")
                continue
        
        if not response:
            raise Exception("All AI models failed to respond")
        
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
                    max_completion_tokens=2000
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
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

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
    
    # Plan limits
    limits = {
        'free': 1000,
        'pro': 50000,
        'premium': 200000,
        'enterprise': float('inf')
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)

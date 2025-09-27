# Authentication fixes for slywriter_server.py
# Add better error handling for duplicate emails and login errors

# 1. Fix for duplicate email registration (around line 1400)
# Replace the existing duplicate check with:

        # Check if email already exists
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, email_verified FROM users WHERE email = %s",
                    (email,)
                )
                existing_user = cursor.fetchone()

                if existing_user:
                    if existing_user['email_verified']:
                        # Fully registered user
                        return jsonify({
                            "success": False,
                            "error": "This email is already registered. Please login instead.",
                            "error_code": "EMAIL_EXISTS"
                        }), 409
                    else:
                        # User started registration but didn't verify
                        return jsonify({
                            "success": False,
                            "error": "This email is pending verification. Check your inbox or try again later.",
                            "error_code": "EMAIL_PENDING"
                        }), 409

# 2. Fix for login endpoint (around line 1100)
# Add better error messages:

@app.route("/auth/login", methods=["POST", "OPTIONS"])
def login():
    """Login with email and password"""
    # Handle CORS preflight
    if request.method == "OPTIONS":
        return "", 200

    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        email = data.get('email', '').lower().strip()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({"success": False, "error": "Email and password required"}), 400

        # Get user from database
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM users WHERE email = %s",
                    (email,)
                )
                user = cursor.fetchone()

                if not user:
                    return jsonify({
                        "success": False,
                        "error": "Invalid email or password"
                    }), 401

                # Check if email is verified
                if not user['email_verified']:
                    return jsonify({
                        "success": False,
                        "error": "Please verify your email before logging in",
                        "error_code": "EMAIL_NOT_VERIFIED"
                    }), 401

                # Verify password
                if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                    return jsonify({
                        "success": False,
                        "error": "Invalid email or password"
                    }), 401

                # Update last login
                cursor.execute(
                    "UPDATE users SET last_login = NOW() WHERE id = %s",
                    (user['id'],)
                )
                conn.commit()

                # Create JWT token
                token_payload = {
                    'user_id': user['id'],
                    'email': user['email'],
                    'name': user['name'],
                    'exp': datetime.utcnow() + datetime.timedelta(days=30)
                }
                token = jwt.encode(token_payload, JWT_SECRET, algorithm='HS256')

                return jsonify({
                    "success": True,
                    "token": token,
                    "user": {
                        "id": user['id'],
                        "email": user['email'],
                        "name": user['name'],
                        "plan": user['plan'],
                        "created_at": user['created_at'].isoformat() if user['created_at'] else None
                    }
                })

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Server error during login. Please try again."
        }), 500

# 3. Add to environment variables on Render:
# GOOGLE_CLIENT_ID = "1018522395159-5nv4kpb38jn9mbpusv7sdf009p98ttog.apps.googleusercontent.com"
# This is needed for Google Sign-In to work properly
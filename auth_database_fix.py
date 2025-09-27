# Fix for auth endpoints to use PostgreSQL database instead of files
# Replace the existing login and register endpoints in slywriter_server.py

@app.route("/auth/login", methods=["POST", "OPTIONS"])
def login():
    """Login existing user with database"""
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
            return jsonify({"success": False, "error": "Email and password are required"}), 400

        # Get user from PostgreSQL database
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM users WHERE email = %s",
                    (email,)
                )
                user = cursor.fetchone()

                if not user:
                    return jsonify({"success": False, "error": "Invalid email or password"}), 401

                # Check password
                if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                    return jsonify({"success": False, "error": "Invalid email or password"}), 401

                # Check if email is verified
                if not user.get('email_verified', False):
                    return jsonify({
                        "success": False,
                        "error": "Please verify your email before logging in",
                        "need_verification": True
                    }), 401

                # Update last login
                cursor.execute(
                    "UPDATE users SET last_login = NOW() WHERE id = %s",
                    (user['id'],)
                )
                conn.commit()

                # Generate JWT token
                token_payload = {
                    'user_id': user['id'],
                    'email': user['email'],
                    'name': user['name'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
                }
                token = jwt.encode(token_payload, JWT_SECRET, algorithm='HS256')

                # Get user's word balance
                cursor.execute(
                    "SELECT words_remaining FROM user_word_balance WHERE user_id = %s",
                    (user['id'],)
                )
                balance = cursor.fetchone()
                words_remaining = balance['words_remaining'] if balance else 10000

                return jsonify({
                    "success": True,
                    "token": token,
                    "user": {
                        "id": user['id'],
                        "email": user['email'],
                        "name": user['name'],
                        "plan": user.get('plan', 'free'),
                        "words_remaining": words_remaining,
                        "created_at": user['created_at'].isoformat() if user['created_at'] else None
                    }
                })

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"success": False, "error": "Server error during login"}), 500

@app.route("/auth/register", methods=["POST", "OPTIONS"])
def register():
    """Register new user with database"""
    # Handle CORS preflight
    if request.method == "OPTIONS":
        return "", 200

    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        name = data.get('name', '').strip()

        # Validation
        if not email or not password or not name:
            return jsonify({"success": False, "error": "All fields are required"}), 400

        # Check email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({"success": False, "error": "Invalid email format"}), 400

        # Check password strength
        if len(password) < 8:
            return jsonify({"success": False, "error": "Password must be at least 8 characters"}), 400

        # Check if email exists in database
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, email_verified FROM users WHERE email = %s",
                    (email,)
                )
                existing = cursor.fetchone()

                if existing:
                    if existing['email_verified']:
                        return jsonify({
                            "success": False,
                            "error": "This email is already registered. Please login instead."
                        }), 409
                    else:
                        return jsonify({
                            "success": False,
                            "error": "This email is pending verification. Please check your inbox."
                        }), 409

                # Hash password
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

                # Create user
                cursor.execute("""
                    INSERT INTO users (email, password_hash, name, email_verified, plan, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    RETURNING id
                """, (email, password_hash, name, False, 'free'))

                user_id = cursor.fetchone()['id']

                # Create initial word balance
                cursor.execute("""
                    INSERT INTO user_word_balance (user_id, words_remaining)
                    VALUES (%s, %s)
                """, (user_id, 10000))  # Free tier gets 10k words

                conn.commit()

                # Generate verification token
                verification_token = secrets.token_urlsafe(32)
                cursor.execute("""
                    UPDATE users SET verification_token = %s
                    WHERE id = %s
                """, (verification_token, user_id))
                conn.commit()

                # Send verification email (implement this)
                # send_verification_email(email, name, verification_token)

                # Generate JWT for immediate login (optional)
                token_payload = {
                    'user_id': user_id,
                    'email': email,
                    'name': name,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
                }
                token = jwt.encode(token_payload, JWT_SECRET, algorithm='HS256')

                return jsonify({
                    "success": True,
                    "message": "Registration successful! Please check your email to verify your account.",
                    "token": token,
                    "user": {
                        "id": user_id,
                        "email": email,
                        "name": name,
                        "plan": "free",
                        "verified": False
                    }
                })

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"success": False, "error": "Server error during registration"}), 500
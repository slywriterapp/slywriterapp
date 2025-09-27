# Settings sync API endpoints
# Add these to slywriter_server.py

@app.route('/api/settings', methods=['GET'])
@requires_auth
def get_settings():
    """Get user settings from database"""
    user_id = request.user['id']

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT settings
                    FROM user_settings
                    WHERE user_id = %s
                """, (user_id,))

                result = cursor.fetchone()

                if result and result['settings']:
                    return jsonify({
                        "success": True,
                        "settings": result['settings']
                    })
                else:
                    # Return default settings
                    return jsonify({
                        "success": True,
                        "settings": {
                            "theme": "dark",
                            "typing_speed": 60,
                            "humanizer": True,
                            "auto_save": True
                        }
                    })

    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/settings', methods=['POST'])
@requires_auth
def save_settings():
    """Save user settings to database"""
    user_id = request.user['id']
    settings = request.get_json()

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_settings (user_id, settings, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (user_id)
                    DO UPDATE SET
                        settings = EXCLUDED.settings,
                        updated_at = NOW()
                """, (user_id, json.dumps(settings)))

                conn.commit()

                return jsonify({
                    "success": True,
                    "message": "Settings saved"
                })

    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/hotkeys', methods=['GET'])
@requires_auth
def get_hotkeys():
    """Get user hotkey settings"""
    user_id = request.user['id']

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT hotkeys
                    FROM user_settings
                    WHERE user_id = %s
                """, (user_id,))

                result = cursor.fetchone()

                if result and result['hotkeys']:
                    return jsonify({
                        "success": True,
                        "hotkeys": result['hotkeys']
                    })
                else:
                    # Return default hotkeys
                    return jsonify({
                        "success": True,
                        "hotkeys": {
                            "start": "shift+o",
                            "stop": "shift+l",
                            "pause": "shift+p",
                            "overlay": "shift+)",
                            "ai_generation": "shift+^"
                        }
                    })

    except Exception as e:
        logger.error(f"Failed to get hotkeys: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/hotkeys', methods=['POST'])
@requires_auth
def save_hotkeys():
    """Save user hotkey settings"""
    user_id = request.user['id']
    hotkeys = request.get_json()

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_settings (user_id, hotkeys, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (user_id)
                    DO UPDATE SET
                        hotkeys = EXCLUDED.hotkeys,
                        updated_at = NOW()
                """, (user_id, json.dumps(hotkeys)))

                conn.commit()

                return jsonify({
                    "success": True,
                    "message": "Hotkeys saved"
                })

    except Exception as e:
        logger.error(f"Failed to save hotkeys: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
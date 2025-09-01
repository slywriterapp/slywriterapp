# Environment Variables Configuration Guide

## Your Current Environment Variables on Render

### ✅ Required Variables You Have:

1. **OPENAI_API_KEY** ✅
   - Used for: AI text generation, humanization, learning content
   - Location: `slywriter_server.py` line 1495
   - Status: WORKING

2. **DATABASE_URL** ✅ 
   - Used for: PostgreSQL telemetry storage
   - Location: `slywriter_server.py` line 46
   - Status: WORKING - Stores all user telemetry data

3. **ADMIN_PASSWORD** ✅
   - Used for: Admin dashboard authentication
   - Location: `slywriter_server.py` line 589
   - Status: WORKING

4. **AIUNDETECT_API_KEY** ✅
   - Used for: AI text humanization service
   - Location: `slywriter_server.py` line 1645
   - Status: WORKING

5. **SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD** ✅
   - Used for: Email verification and password reset
   - Location: `slywriter_server.py` lines 540-543
   - Status: WORKING if configured

6. **CORS_ORIGINS** ✅
   - Used for: CORS configuration
   - Not currently used in code but can be added

### ⚠️ Missing Variables to Add:

1. **JWT_SECRET_KEY** (or just **JWT_SECRET**)
   - Purpose: Secure user authentication tokens
   - Add this value: Any random string like `your-random-jwt-secret-key-2025`
   - Used at: `slywriter_server.py` line 30

2. **SECRET_KEY**
   - Purpose: Flask session security
   - Add this value: Any random string like `your-random-flask-secret-2025`
   - Used at: `slywriter_server.py` line 29

### Optional Variables:

1. **TELEMETRY_ENABLED**
   - Not currently used, but telemetry is automatically enabled when DATABASE_URL exists
   - Your telemetry IS working with DATABASE_URL

2. **FRONTEND_URL**
   - Default: `http://localhost:3000`
   - Used for email verification links
   - You might want to set this to your actual frontend URL

## How Telemetry Works with Your DATABASE_URL:

When users use the app, the following data is sent to your PostgreSQL database:

1. **Session Data** (`telemetry_sessions` table):
   - User ID
   - Session duration
   - System info
   - Total actions

2. **Events** (`telemetry_events` table):
   - Every user action
   - Feature usage
   - Timestamps

3. **Errors** (`telemetry_errors` table):
   - Any errors that occur
   - Error context
   - Component that failed

4. **Feature Usage** (`telemetry_features` table):
   - Which features are used most
   - Usage counts
   - User preferences

## Telemetry Endpoints:

### User sends telemetry:
```
POST https://slywriterapp.onrender.com/api/beta-telemetry
```

### Admin views telemetry (requires ADMIN_PASSWORD):
```
GET https://slywriterapp.onrender.com/api/admin/telemetry
GET https://slywriterapp.onrender.com/api/admin/telemetry/stats
```

## Quick Test Commands:

### Test telemetry is working:
```bash
curl https://slywriterapp.onrender.com/api/admin/telemetry/health
```

### View telemetry stats (needs admin password):
```bash
curl -H "X-Admin-Password: YOUR_ADMIN_PASSWORD" \
  https://slywriterapp.onrender.com/api/admin/telemetry/stats
```

## Action Items:

1. ✅ Add **JWT_SECRET_KEY** environment variable on Render
2. ✅ Add **SECRET_KEY** environment variable on Render
3. ✅ Verify telemetry is saving to PostgreSQL
4. ✅ Test admin endpoints with your ADMIN_PASSWORD

Your telemetry system is ACTIVE and will collect all usage data in your PostgreSQL database!
# 🚀 SlyWriter Beta Deployment Guide

## ✅ What's Been Updated (FULLY CLOUD-READY)

### 1. **Telemetry System**
- ✅ All telemetry data goes to `https://slywriterapp.onrender.com`
- ✅ PostgreSQL database stores all beta testing data
- ✅ Admin dashboard fetches from cloud
- ✅ No more localhost dependencies for telemetry

### 2. **Database Structure**
Your PostgreSQL database on Render will have these tables:
- `telemetry_events` - All user actions
- `telemetry_sessions` - Session information  
- `telemetry_errors` - Error tracking
- `telemetry_features` - Feature usage stats

### 3. **Security**
- Admin endpoints require password header
- User data is anonymous (no personal info)
- GDPR compliant with data export/delete endpoints

---

## 📋 Steps to Deploy on Render

### Step 1: Upload Server Files
Upload these files to your Render server repository:
1. `telemetry_postgres.py` - PostgreSQL handler
2. `telemetry_endpoints.py` - Copy the endpoints into your existing server file
3. `requirements_render.txt` - Merge with your existing requirements.txt

### Step 2: Update Your Server Code
In your main server file (slywriter_server.py or similar), add:

```python
# At the top
from telemetry_postgres import telemetry_db
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Add all the endpoints from telemetry_endpoints.py
# (Copy everything after the imports)
```

### Step 3: Environment Variables (Already Done ✅)
You've already set these in Render:
- `DATABASE_URL` - PostgreSQL connection
- `ADMIN_PASSWORD` - slywriter-admin-brice
- `TELEMETRY_ENABLED` - true
- `CORS_ORIGINS` - *

### Step 4: Push to GitHub
```bash
git add .
git commit -m "Add cloud telemetry system for beta testing"
git push origin main
```

Render will auto-deploy when you push!

---

## 🖥️ Admin Dashboard Access

### View Telemetry Data:
1. **Local Development**: http://localhost:3000/admin
2. **Production**: https://your-app-url.onrender.com/admin
3. **Password**: slywriter-admin-brice

### API Endpoints:
- `GET /api/admin/telemetry/stats` - Statistics
- `GET /api/admin/telemetry` - Recent entries
- `GET /api/admin/telemetry/export` - Export all data
- `GET /api/admin/telemetry/health` - Check system health

---

## 🧪 Testing Before Beta Launch

### 1. Test Telemetry Upload
Open browser console and run:
```javascript
fetch('https://slywriterapp.onrender.com/api/beta-telemetry', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    userId: 'test-user',
    sessionId: 'test-session',
    systemInfo: {platform: 'test'},
    actions: [],
    errors: [],
    featureUsage: [],
    performanceMetrics: [],
    sessionDuration: 0,
    lastActivity: Date.now(),
    timestamp: new Date().toISOString()
  })
})
```

### 2. Check Database
```bash
# SSH into Render (if you have shell access)
# Or use Render PostgreSQL dashboard
psql $DATABASE_URL
\dt  # List tables
SELECT COUNT(*) FROM telemetry_events;
```

### 3. Test Admin Endpoints
```bash
curl -H "X-Admin-Password: slywriter-admin-brice" \
  https://slywriterapp.onrender.com/api/admin/telemetry/stats
```

---

## 📊 What Beta Testers Will Experience

1. **First Launch**: Beta disclosure screen appears
2. **Automatic**: Telemetry enabled by default
3. **Privacy**: Can opt-out in Settings → Privacy
4. **Transparent**: Shows their anonymous Beta ID
5. **No Impact**: Telemetry runs in background, no performance impact

---

## 🔍 Monitoring During Beta

### Real-time Monitoring:
1. Check Render Metrics tab for API calls
2. View PostgreSQL usage in database dashboard
3. Admin dashboard auto-refreshes every 30 seconds

### Daily Checks:
1. Total users count
2. Error frequency
3. Most used features
4. Average session duration

### Export Data:
- Click "Export All" in admin dashboard
- Downloads complete JSON dataset

---

## 🚨 Troubleshooting

### If Telemetry Not Working:
1. Check Render logs for errors
2. Verify DATABASE_URL is correct
3. Test database connection: `/api/admin/telemetry/health`
4. Check CORS settings

### If Admin Dashboard Can't Connect:
1. Verify password in environment variables
2. Check API endpoints are deployed
3. Look for 401/403 errors in browser console

### Database Issues:
1. Check PostgreSQL is running on Render
2. Verify connection string
3. Check if tables were created (init_database should run automatically)

---

## 🎯 Ready for Beta!

Once deployed and tested:
1. ✅ Telemetry automatically starts collecting
2. ✅ Data flows to PostgreSQL on Render
3. ✅ Admin dashboard shows real-time stats
4. ✅ 20 beta testers can start using immediately

**No localhost, no local files, everything in the cloud!** 🌩️

---

## 📝 Notes for Beta Testers Email

Include this in your beta tester invitation:

```
This beta version includes anonymous telemetry to help improve SlyWriter.
- We track feature usage and errors (no personal data)
- You can opt-out in Settings → Privacy
- Your anonymous ID: [shown on first launch]
- Help us make SlyWriter better!
```
# SlyWriter Backend Deployment Guide

**Version**: Unified Backend v1.0
**Date**: 2025-01-07
**Target**: Render.com / Production Server

---

## 🎯 What's Changed

The merged backend (`main_merged.py`) now includes **ALL** endpoints needed for:
- ✅ Web Application (existing Stripe/AI/Learning features)
- ✅ Desktop Application (license/config/clipboard features)
- ✅ Both platforms using a single unified API

**Total Endpoints**: 64 (36 web + 18 desktop + 10 shared)

---

## 📦 Deployment Package

### Required Files

Copy these files to your deployment directory:

```
slywriter-ui/backend/
├── main_merged.py          ← Rename to main.py for deployment
├── requirements.txt         ← Updated with pyperclip
├── database.py             ← Database models
├── auth.py                 ← Authentication logic
├── .env                    ← Environment variables (create if missing)
└── license_manager.py      ← (Optional) From C:\Typing Project\license_manager.py
```

###Step-by-Step Deployment

#### 1. Prepare Files

```bash
# Navigate to backend directory
cd "C:\Typing Project\slywriter-ui\backend"

# Backup current main.py (IMPORTANT!)
cp main.py main_backup_$(date +%Y%m%d).py

# Replace with merged version
cp main_merged.py main.py

# Copy license manager (if not already there)
cp "C:\Typing Project\license_manager.py" .
```

#### 2. Update Environment Variables

Add these to your `.env` or Render environment variables:

```bash
# Existing variables (keep these as-is)
DATABASE_URL=postgresql://...
STRIPE_API_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
OPENAI_API_KEY=sk-...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
JWT_SECRET=...

# NEW: Admin authentication
ADMIN_PASSWORD=your-super-secure-admin-password-here
```

#### 3. Deploy to Render

**Option A: Via Render Dashboard**
1. Go to your Render service
2. Upload the updated files
3. Add `ADMIN_PASSWORD` to environment variables
4. Click "Manual Deploy"

**Option B: Via Git Push** (if using Git deployment)
```bash
git add .
git commit -m "Unified backend with desktop endpoints"
git push render main
```

#### 4. Verify Deployment

After deployment, test critical endpoints:

**Health Check:**
```bash
curl https://slywriterapp.onrender.com/api/health
# Expected: {"status":"healthy"}
```

**License Verify (Desktop):**
```bash
curl -X POST https://slywriterapp.onrender.com/api/license/verify \
  -H "Content-Type: application/json" \
  -d '{"license_key":"test@test.com","machine_id":"test","device_name":"Test","app_version":"2.4.7"}'
# Expected: JSON response (NOT {"detail":"Not Found"})
```

**Auth Register (Desktop):**
```bash
curl -X POST https://slywriterapp.onrender.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}'
# Expected: JSON response (NOT {"detail":"Not Found"})
```

**Stripe Checkout (Web):**
```bash
curl https://slywriterapp.onrender.com/api/stripe/create-checkout
# Should still work as before
```

---

## 🔧 Configuration Notes

### Database

No database changes needed. The merged backend uses the same database schema.

### Dependencies

The updated `requirements.txt` includes one new optional dependency:
- `pyperclip>=1.8.2` - For clipboard features (gracefully degrades if unavailable)

Render will auto-install this during deployment.

### License Manager

The `license_manager.py` module is **optional**. If not present:
- License endpoints will return errors with helpful messages
- Web/Stripe/AI endpoints continue working normally
- Desktop app will show "license verification unavailable"

To enable full desktop functionality, copy `license_manager.py` to the backend directory before deploying.

---

## 🚀 Rollback Plan

If something goes wrong:

```bash
# Restore from backup
cp main_backup_YYYYMMDD.py main.py

# Redeploy
git add main.py
git commit -m "Rollback to previous version"
git push render main
```

---

## ✅ Post-Deployment Checklist

- [ ] `/api/health` returns healthy status
- [ ] `/api/license/verify` returns JSON (not 404)
- [ ] `/api/auth/register` returns JSON (not 404)
- [ ] `/api/config` (GET) returns JSON (not 404)
- [ ] `/api/stripe/create-checkout` still works (web app)
- [ ] `/api/ai/generate` still works (web app)
- [ ] Desktop app can connect and verify license
- [ ] Website OAuth still works
- [ ] Admin password set in environment variables

---

## 🐛 Troubleshooting

### Issue: "Module not found" errors

**Solution:** Check that all required files are uploaded:
```bash
# Required files checklist
database.py
auth.py
main.py (renamed from main_merged.py)
requirements.txt
```

### Issue: License endpoints return errors

**Solution:** Copy `license_manager.py` to deployment directory
```bash
cp "C:\Typing Project\license_manager.py" slywriter-ui/backend/
```

### Issue: "ADMIN_PASSWORD not configured"

**Solution:** Add to Render environment variables:
```
ADMIN_PASSWORD=your-secure-password
```

### Issue: Clipboard features don't work

**Solution:** This is expected in headless server environment. The endpoints will gracefully return error messages. Desktop app uses local backend instead.

---

## 📊 Endpoint Inventory

### ✅ Web Endpoints (36) - Already Working

- Authentication & Users
- Stripe Payment Processing
- AI Text Generation
- Learning/Lessons
- Telemetry & Analytics
- Usage Tracking
- Referrals

### ✅ Desktop Endpoints (18) - NEWLY ADDED

1. POST `/api/auth/logout`
2. POST `/api/auth/register`
3. POST `/api/auth/google` (desktop version)
4. GET `/api/auth/status`
5. GET `/api/config`
6. POST `/api/config`
7. POST `/api/config/hotkey`
8. POST `/api/profiles/generate-from-wpm`
9. POST `/api/copy-highlighted`
10. POST `/api/copy-highlighted-overlay`
11. POST `/api/typing/update_wpm`
12. POST `/api/typing/pause/{session_id}`
13. POST `/api/typing/resume/{session_id}`
14. POST `/api/typing/stop/{session_id}`
15. GET `/api/usage` (desktop version)
16. POST `/api/license/verify`
17. GET `/api/license/status`
18. GET `/api/license/features`

### ✅ Shared Endpoints (10) - Work for Both

- GET `/api/health`
- POST `/api/typing/start`
- POST `/api/typing/pause`
- POST `/api/typing/stop`
- GET `/api/typing/status`
- GET `/api/profiles`
- POST `/api/profiles/save`
- DELETE `/api/profiles/{name}`
- POST `/api/beta-telemetry`
- GET `/api/admin/telemetry`

---

## 📞 Support

**Issues during deployment?**

1. Check Render logs for errors
2. Verify all environment variables are set
3. Confirm all required files are uploaded
4. Test endpoints using curl commands above
5. Check `BACKEND_DEPLOYMENT_FIX.md` for detailed troubleshooting

**Success indicators:**
- No 404 errors on desktop endpoints
- Desktop app connects successfully
- Website functionality unchanged
- All 64 endpoints return valid responses

---

## 🎉 Success!

Once deployed, you'll have:
- ✅ Single unified backend serving web + desktop
- ✅ 16 previously missing endpoints now available
- ✅ Desktop app can authenticate and verify licenses
- ✅ Website functionality fully preserved
- ✅ No code duplication between platforms

**Next:** Test desktop app connection and verify all features work!

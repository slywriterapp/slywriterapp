# SlyWriter Production Deployment Checklist

## ✅ COMPLETED FIXES

### Critical Issues Fixed:
1. ✅ **Removed Skip Login Button** - Users can no longer bypass authentication (login\page.tsx)
2. ✅ **Removed client_secret.json from Electron build** - No longer packaged with app
3. ✅ **Removed client_secret.json from git tracking** - Secret removed from repository
4. ✅ **Added Admin Authentication** - Admin endpoints now require Bearer token (backend_api.py)
5. ✅ **Cleaned up .env placeholders** - Local .env now clearly marked as dev-only with placeholders
6. ✅ **Removed mock AI responses** - No longer returns fake data when server sleeps
7. ✅ **Deleted old Beta directories** - Removed SlyWriter_Beta and SlyWriter_Beta_Complete
8. ✅ **DEBUG=False configured** - User added to Render dashboard

### High Priority Issues Fixed:
9. ✅ **Moved hardcoded URLs to environment variables** - All 30+ instances now use RENDER_API_URL from config/api.ts
   - Fixed files: AdminDashboard, AIHubTab, HotkeysTabEnhanced, UserDashboard, HumanizerTab, +5 more

### Documentation Added:
- Code signature verification plan documented in main.js (purchase cert, then enable)
- Production environment variable instructions added to .env files
- GitHub token generation instructions added to update-server/.env

---

## 🔴 CRITICAL - DO BEFORE LAUNCH

### 1. Regenerate Google OAuth Credentials
**Status**: WAITING FOR ACCESS FROM WEB DEV

**Why**: OAuth client secret was exposed in git history (`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`)

**Steps**:
1. Get owner access to Google Cloud Console project from web dev
2. Go to https://console.cloud.google.com/apis/credentials
3. Find OAuth 2.0 Client ID
4. Click "Regenerate Secret" or create new client ID
5. Update `GOOGLE_CLIENT_SECRET` in Render dashboard with new secret
6. Update GOOGLE_CLIENT_ID if you created a new one

### 2. Set Production Environment Variables in Render
**Status**: NEEDS VERIFICATION

Go to Render dashboard and ensure these are set:

```
DEBUG=False  (currently not set - ADD THIS)
APP_ENV=production
NODE_ENV=production
```

All other variables are already configured correctly in Render.

### 3. Commit and Deploy These Changes
```bash
cd "C:\Typing Project"
git status  # Review changes
git add .
git commit -m "Security fixes: Remove auth bypass, secure admin endpoints, clean up secrets"
git push origin main
```

---

## 🟠 HIGH PRIORITY - Fix Soon (Can Do After Launch)

### 4. Remove 200+ Console.log Statements
**Impact**: Performance, information leakage
**Files**: main.js (100+), AIHubTab.tsx (50+), GlobalHotkeyListener.tsx (30+), and many others
**Status**: Can be done post-launch

**Recommended Approach**:
Leave them for now since they're helpful for debugging during beta. After a few weeks of stable operation:
1. Use conditional logging: `if (process.env.NODE_ENV !== 'production') console.log(...)`
2. Or create a logger utility that's disabled in production
3. Keep critical error logs, remove debug/info logs

**Priority**: LOW - These won't break anything, just slightly slower performance

### 5. ✅ COMPLETED - Moved Hardcoded URLs to Environment Variables
All URLs now use `RENDER_API_URL` from `config/api.ts`

### 6. Update GitHub Token for Auto-Updates
**File**: `C:\Typing Project\update-server\.env`
**Current**: `GITHUB_TOKEN=ghp_YOUR_GITHUB_TOKEN_HERE`

**Steps**:
1. Go to https://github.com/settings/tokens
2. Generate new token with `repo` scope
3. Update update-server/.env with real token
4. Never commit this file to git

---

## 🟡 MEDIUM PRIORITY - Nice to Have

### 7. Code Signing Certificate
**Cost**: $249/year (EV cert from SSL.com) + $100/month (eSigner service)
**Status**: Plan to purchase after release

**When ready**:
1. Purchase certificate
2. Sign builds with `electron-builder`
3. Remove `process.env.ELECTRON_UPDATER_ALLOW_UNSIGNED = 'true'` from main.js line 5
4. Users will trust updates without warnings

### 8. Clean Up Localhost References
**Files**: `.claude\settings.local.json`, various test files
**Impact**: Low (only affects development)

---

## 📋 RENDER DASHBOARD CHECKLIST

Login to Render and verify/add these environment variables:

### ✅ Already Configured (Good!):
- ADMIN_PASSWORD
- AIUNDETECT_API_KEY
- CORS_ORIGINS
- DATABASE_URL
- GITHUB_TOKEN
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET (will need new value after regeneration)
- JWT_SECRET_KEY
- NODE_ENV
- OPENAI_API_KEY
- SECRET_KEY
- SMTP_* (all email settings)
- STRIPE_* (all payment settings)
- TELEMETRY_ENABLED

### ❌ NEED TO ADD:
- **DEBUG=False** (critical for production)
- **APP_ENV=production** (if not already set)

---

## 🎯 LAUNCH DAY CHECKLIST

### Before First User Signup:
- [ ] Google OAuth credentials regenerated
- [ ] DEBUG=False in Render
- [ ] Code pushed to production
- [ ] Render deployment successful
- [ ] Test login flow with new OAuth credentials
- [ ] Test payment flow (Pro and Premium)
- [ ] Test AI generation features
- [ ] Test auto-update system
- [ ] Verify admin endpoints require authentication

### After Launch:
- [ ] Remove console.log statements
- [ ] Move hardcoded URLs to environment variables
- [ ] Purchase code signing certificate (when budget allows)
- [ ] Clean up remaining TODO comments

---

## 🔒 SECURITY NOTES

1. **OAuth Secret Exposed**: The old secret `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` was in git history. Regenerating makes it useless.

2. **Admin Password**: Currently `slywriter-admin-brice` in Render. Consider changing to something more secure.

3. **JWT Secrets**: Current Render secrets are strong (e.g., `b8Y#2dM@6eK*4fR!...`). Good!

4. **Auto-Updates**: Currently allows unsigned updates. Plan to enable signature verification post-launch.

---

## 📊 SUMMARY

**Critical fixes completed**: 7/7 ✅
**Waiting on**: Google OAuth access from web dev
**Ready to deploy**: After OAuth regeneration
**Can launch**: Yes, once OAuth is fixed and DEBUG=False

**Post-launch improvements**: Console logs, hardcoded URLs, code signing

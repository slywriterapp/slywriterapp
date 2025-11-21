# FOR ALL CLAUDES - COMPLETE SLYWRITER DEPLOYMENT GUIDE

**Last Updated:** 2025-11-21
**Version:** 2.9.2

This guide contains EVERYTHING you need to know about building, deploying, and managing SlyWriter. Read this CAREFULLY before making any changes.

---

## 🚨 CRITICAL: ARCHITECTURE OVERVIEW

### What is SlyWriter?
SlyWriter is an **Electron desktop app** (Windows + Mac) with a **Next.js UI** and **FastAPI Python backend**.

### How It Works:
1. **Electron App**: Installed on user's computer
2. **UI**: Loads from `https://slywriter-ui.onrender.com` (production) or `localhost:3000` (dev)
3. **Local Backend**: Runs `backend_desktop.py` on `localhost:8000` inside the Electron app
4. **Cloud API**: Separate FastAPI backend at `https://slywriterapp.onrender.com` for auth/telemetry

### ⚠️ COMMON MISTAKE #1: File Locations
**DO NOT EDIT FILES IN THESE LOCATIONS:**
- `C:\Typing Project\slywriter-electron\dist\` - Built files only
- `C:\Typing Project\slywriter-electron\Resources\` - Old location, not used
- `C:\Typing Project\slywriter-ui\backend\` - Cloud API (different from desktop backend!)
- `C:\Typing Project\render_deployment\` - Old deployment folder (NOT USED ANYMORE)

**EDIT FILES HERE:**
- `C:\Typing Project\*.py` - Desktop Python backend files
- `C:\Typing Project\slywriter-ui\app\` - Next.js UI components
- `C:\Typing Project\slywriter-electron\` - Electron app configuration

---

## 📁 PROJECT STRUCTURE

```
C:\Typing Project\
├── backend_desktop.py          ← Local FastAPI backend (runs in Electron)
├── utils.py                    ← Utilities with OPTIONAL tkinter imports
├── sly_config.py              ← Config with OPTIONAL tkinter imports
├── typing_engine.py           ← Core typing automation
├── premium_typing.py          ← Premium features
├── config.py                  ← App constants
├── auth.py                    ← Authentication
├── (50+ other .py files)      ← All copied into Electron Resources during build
│
├── slywriter-electron/        ← ELECTRON APP
│   ├── main.js               ← Electron main process
│   ├── setup-python.js       ← Python environment setup
│   ├── package.json          ← Build config (COPY FILES FROM PARENT DIR)
│   └── dist/                 ← Build output (DO NOT EDIT)
│
├── slywriter-ui/             ← NEXT.JS UI (HOSTED ON RENDER)
│   ├── app/                  ← Next.js 15 app directory
│   │   ├── components/       ← React components
│   │   │   └── OnboardingFlow.tsx  ← Mac permission screen
│   │   └── page.tsx         ← Main page
│   ├── backend/             ← CLOUD API (separate from desktop!)
│   │   └── main.py          ← FastAPI for auth/telemetry
│   └── package.json         ← Next.js build config
│
├── signed-dmg/              ← Notarized Mac DMGs
└── CONTEXT_FOR_NEXT_CLAUDE.md  ← Previous session notes
```

---

## 🚀 HOW TO RELEASE A NEW VERSION

### Step 1: Update Version Number

**Edit:** `C:\Typing Project\slywriter-electron\package.json`

```json
{
  "version": "2.9.3",  ← Change this
}
```

### Step 2: Commit Your Changes

```bash
cd "C:\Typing Project"
git add .
git commit -m "Release v2.9.3 - Your changes here"
git push
```

### Step 3: Create Git Tag

```bash
git tag -a v2.9.3 -m "Release v2.9.3"
git push origin v2.9.3
```

### Step 4: Build Windows Version

```bash
cd "C:\Typing Project\slywriter-electron"
npm run dist:nsis
```

**Output:** `dist\SlyWriter-Setup-2.9.3.exe`

### Step 5: Build Mac Version (Two Options)

#### Option A: GitHub Actions (RECOMMENDED - Auto-signs and notarizes)

```bash
cd "C:\Typing Project"
gh workflow run build-mac.yml --ref v2.9.3
gh run watch  # Wait for completion
gh run download <run-id> --name SlyWriter-Mac-DMG --dir signed-dmg
```

#### Option B: AWS Mac Instance (Manual build)

See "AWS MAC INSTANCE ACCESS" section below.

### Step 6: Create GitHub Release

```bash
cd "C:\Typing Project"

gh release create v2.9.3 \
  --title "SlyWriter v2.9.3 - Your Title" \
  --notes "Release notes here"
```

### Step 7: Upload Builds

```bash
# Upload Windows installer
cd "C:\Typing Project\slywriter-electron\dist"
gh release upload v2.9.3 SlyWriter-Setup-2.9.3.exe

# Upload Mac DMG (notarized)
cd "C:\Typing Project\signed-dmg"
gh release upload v2.9.3 SlyWriter-2.9.3.dmg
```

### ✅ Verify Release

```bash
gh release view v2.9.3
```

Should show:
- `SlyWriter-Setup-2.9.3.exe` (Windows)
- `SlyWriter-2.9.3.dmg` (Mac, signed & notarized)
- `latest.yml` (auto-update metadata)

---

## 🍎 AWS MAC INSTANCE ACCESS

### Instance Details
- **Instance Name:** slyporter
- **Instance ID:** i-0c5e3a99a92573d24
- **Type:** mac1.metal (macOS 14.7.8 Sonoma)
- **Region:** us-east-2
- **Public IP:** 3.137.139.130
- **SSH Key:** `C:\Users\brice\Downloads\key1.pem`
- **User:** ec2-user

### Connect via SSH

```bash
ssh -i "C:\Users\brice\Downloads\key1.pem" ec2-user@3.137.139.130
```

### Build Mac DMG on AWS Mac

```bash
# 1. SSH into Mac
ssh -i "C:\Users\brice\Downloads\key1.pem" ec2-user@3.137.139.130

# 2. Clone/update repo
cd ~/mac-build
git pull origin main

# 3. Install dependencies (first time only)
cd slywriter-electron
npm install

# 4. Build DMG (unsigned)
npm run dist:mac

# 5. DMG location
ls -lh dist/SlyWriter-*.dmg
```

### Download DMG from Mac

```bash
# From Windows
scp -i "C:\Users\brice\Downloads\key1.pem" \
  ec2-user@3.137.139.130:~/mac-build/slywriter-electron/dist/SlyWriter-2.9.3.dmg \
  "C:\Typing Project\slywriter-electron\dist\"
```

### Mac Notarization (Automated)

**ALWAYS use GitHub Actions for notarization** - it has the signing certificate and Apple credentials stored in secrets.

Manually building on AWS Mac produces **UNSIGNED** DMGs which will show "App is damaged" warnings.

---

## ☁️ RENDER DEPLOYMENT

### Two Separate Services

#### 1. slywriter-ui (Frontend - Next.js)
- **URL:** https://slywriter-ui.onrender.com
- **Region:** Oregon (US West)
- **Root Directory:** `slywriter-ui`
- **Build:** `npm install && npm run build`
- **Start:** `npm start`
- **Purpose:** Hosts the UI that Electron apps load
- **Auto-Deploy:** Enabled on `main` branch commits

#### 2. slywriterapp (Backend - FastAPI)
- **URL:** https://slywriterapp.onrender.com
- **Region:** Oregon (US West)
- **Root Directory:** `slywriter-ui/backend`
- **Build:** `pip install -r requirements.txt`
- **Start:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Purpose:** Auth, telemetry, user management API
- **Auto-Deploy:** Enabled on `main` branch commits

### ⚠️ IMPORTANT: Which Backend is Which?

**Desktop Backend** (runs locally in Electron):
- File: `C:\Typing Project\backend_desktop.py`
- Port: `localhost:8000`
- Purpose: Typing automation, hotkeys, local features
- Users: Each user runs their own instance

**Cloud Backend** (runs on Render):
- File: `C:\Typing Project\slywriter-ui\backend\main.py`
- URL: `https://slywriterapp.onrender.com`
- Purpose: Authentication, user management, telemetry
- Users: Shared service for all users

### Manual Deployment

```bash
# Deploy frontend
cd "C:\Typing Project\slywriter-ui"
git push origin main  # Auto-deploys

# Deploy backend
cd "C:\Typing Project\slywriter-ui\backend"
git push origin main  # Auto-deploys

# Or force deploy via Render CLI
"C:\Users\brice\Downloads\cli_2.4.1_windows_amd64\cli_v2.4.1.exe" \
  deploys create srv-d3bj9iili9vc73cqfri0 --confirm --wait  # Frontend

"C:\Users\brice\Downloads\cli_2.4.1_windows_amd64\cli_v2.4.1.exe" \
  deploys create srv-d26gc60gjchc73aq7dsg --confirm --wait  # Backend
```

### Check Deployment Status

```bash
# Via Render dashboard
https://dashboard.render.com

# Via CLI
"C:\Users\brice\Downloads\cli_2.4.1_windows_amd64\cli_v2.4.1.exe" services list
```

---

## 🐛 CRITICAL BUG FIXES TO REMEMBER

### 1. Tkinter Import Errors

**Problem:** Backend fails with `ModuleNotFoundError: No module named 'tkinter'` in Electron

**Solution:** Make tkinter imports OPTIONAL with dummy classes

**Files to check:**
- `backend_desktop.py`
- `utils.py`
- `sly_config.py`

**Example:**
```python
# Optional tkinter import
try:
    import tkinter as tk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    # Dummy classes
    class tk:
        class Label:
            def __init__(self, *args, **kwargs): pass
            def pack(self, *args, **kwargs): pass
```

### 2. Mac Permission Flow

**Problem:** Permission requests happen during installation (annoying)

**Solution:** Request permissions during onboarding (after login)

**Files:**
- `backend_desktop.py` - Permission endpoints (`/api/test-typing-permission`, `/api/check-typing-permission`)
- `slywriter-ui/app/components/OnboardingFlow.tsx` - Mac permission screen

### 3. Installation Progress

**Problem:** "Installing dependencies" shows for minutes with no feedback

**Solution:** Package-by-package progress indicators

**File:** `slywriter-electron/setup-python.js`

```javascript
for (let i = 0; i < packages.length; i++) {
  const progress = 80 + Math.floor((i / packages.length) * 15)
  if (onProgress) onProgress(`Installing ${i+1}/${packages.length}...`, progress)
  // ... install package
}
```

---

## 🔐 MAC CODE SIGNING & NOTARIZATION

### GitHub Secrets (Already Configured)

```
APPLE_ID                    - Apple developer email
APPLE_ID_PASSWORD          - App-specific password
APPLE_TEAM_ID              - Team ID (55S897P97X)
MACOS_CERTIFICATE          - P12 certificate (base64)
MACOS_CERTIFICATE_PASSWORD - P12 password
KEYCHAIN_PASSWORD          - Keychain password
```

### Automatic Notarization Workflow

**File:** `.github/workflows/build-mac.yml`

**Triggers:**
- On tag push: `git push origin v2.9.3`
- Manual: `gh workflow run build-mac.yml --ref v2.9.3`

**What it does:**
1. Checks out code
2. Imports signing certificate into macOS keychain
3. Builds app with `npm run dist:mac`
4. electron-builder automatically:
   - Signs app with Developer ID
   - Submits to Apple for notarization
   - Staples notarization ticket to DMG
5. Uploads DMG as artifact

### Download Notarized DMG

```bash
# List recent runs
gh run list --workflow=build-mac.yml --limit 5

# Download DMG
gh run download <run-id> --name SlyWriter-Mac-DMG --dir signed-dmg
```

---

## 🚨 COMMON MISTAKES TO AVOID

### ❌ Mistake 1: Editing Files in Wrong Location

**WRONG:**
```bash
# These are build outputs, NOT source files!
Edit "C:\Typing Project\slywriter-electron\dist\win-unpacked\resources\backend_desktop.py"
Edit "C:\Typing Project\slywriter-electron\Resources\utils.py"
```

**CORRECT:**
```bash
# Edit source files in project root
Edit "C:\Typing Project\backend_desktop.py"
Edit "C:\Typing Project\utils.py"

# Then rebuild
cd "C:\Typing Project\slywriter-electron"
npm run dist:nsis  # For Windows
npm run dist:mac   # For Mac
```

### ❌ Mistake 2: Confusing Desktop vs Cloud Backend

**Desktop Backend** (local):
- `C:\Typing Project\backend_desktop.py`
- Runs in Electron
- Port 8000 (localhost only)

**Cloud Backend** (Render):
- `C:\Typing Project\slywriter-ui\backend\main.py`
- Runs on Render
- https://slywriterapp.onrender.com

**If you need to fix typing automation** → Edit `backend_desktop.py`
**If you need to fix auth/users** → Edit `slywriter-ui/backend/main.py`

### ❌ Mistake 3: Pushing to Wrong Render Service

**Frontend changes** (UI, components, pages):
- Root directory: `slywriter-ui`
- Auto-deploys to: `slywriter-ui` service

**Backend API changes** (auth, telemetry):
- Root directory: `slywriter-ui/backend`
- Auto-deploys to: `slywriterapp` service

Render watches the `root directory` setting - changes outside that directory won't trigger deploys!

### ❌ Mistake 4: Forgetting to Update Version

Before releasing:
```bash
# 1. Update version in package.json
Edit "C:\Typing Project\slywriter-electron\package.json"
# Change: "version": "2.9.3"

# 2. Commit changes
git add .
git commit -m "Release v2.9.3"

# 3. Create tag
git tag -a v2.9.3 -m "Release v2.9.3"
git push origin main
git push origin v2.9.3
```

### ❌ Mistake 5: Using Unsigned Mac DMG

**WRONG:**
```bash
# Building on AWS Mac without GitHub Actions
ssh ec2-user@3.137.139.130
cd ~/mac-build/slywriter-electron
npm run dist:mac
# ❌ This produces UNSIGNED DMG!
```

**CORRECT:**
```bash
# Use GitHub Actions for automatic signing + notarization
gh workflow run build-mac.yml --ref v2.9.3
gh run watch
gh run download <run-id> --name SlyWriter-Mac-DMG --dir signed-dmg
# ✅ This produces SIGNED & NOTARIZED DMG!
```

### ❌ Mistake 6: Editing Old Deployment Files

**DO NOT EDIT:**
- `C:\Typing Project\render_deployment\` - Old folder, not used anymore
- `C:\Typing Project\slywriter_server.py` - Old server file

**EDIT INSTEAD:**
- `C:\Typing Project\slywriter-ui\backend\main.py` - Current cloud backend

---

## 📦 ELECTRON BUILD PROCESS

### How Electron Build Works

1. `package.json` defines `extraFiles` section
2. During build, electron-builder copies files from `C:\Typing Project\*.py` into app resources
3. On app start, Electron runs `setup-python.js` to install Python + packages
4. Then starts `backend_desktop.py` on localhost:8000
5. UI loads from Render and connects to local backend

### Key Build Files

**main.js** - Electron main process
- Creates BrowserWindow
- Loads UI from `https://slywriter-ui.onrender.com` (production) or `localhost:3000` (dev)
- Starts Python backend via `setup-python.js`

**setup-python.js** - Python environment setup
- Downloads Python embedded (Windows) or python-build-standalone (Mac)
- Installs pip
- Installs required packages (fastapi, uvicorn, pyautogui, etc.)
- Shows progress to user

**package.json** - Build configuration
- Lists all Python files to copy into app
- Defines build targets (nsis for Windows, dmg for Mac)
- Notarization settings for Mac

---

## 🧪 TESTING RELEASES

### Test Windows Build Locally

```bash
cd "C:\Typing Project\slywriter-electron"
npm run dist:nsis

# Install and test
dist\SlyWriter-Setup-2.9.3.exe
```

### Test Mac Build on AWS

```bash
# SSH to Mac
ssh -i "C:\Users\brice\Downloads\key1.pem" ec2-user@3.137.139.130

# Build
cd ~/mac-build/slywriter-electron
npm run dist:mac

# Test backend starts without errors
cd dist/mac
open SlyWriter.app
# Check Console.app for errors
```

### Verify Fixes Work

**Tkinter fix:**
```bash
# On Mac
python3 backend_desktop.py
# Should start without "ModuleNotFoundError: No module named 'tkinter'"
```

**Permission endpoints:**
```bash
# Test endpoints
curl http://localhost:8000/api/check-typing-permission
curl -X POST http://localhost:8000/api/test-typing-permission
# Should return platform: "mac" and trigger permission popup
```

---

## 🔍 DEBUGGING TIPS

### Backend Won't Start

1. Check if Python is installed:
```bash
# Windows
where python
python --version

# Mac
which python3
python3 --version
```

2. Check for import errors:
```bash
python backend_desktop.py
# Look for ModuleNotFoundError
```

3. Check if port 8000 is in use:
```bash
# Windows
netstat -ano | findstr :8000

# Mac
lsof -i :8000
```

### Build Failures

1. Check Node.js version:
```bash
node --version  # Should be 18+
npm --version
```

2. Clear cache and rebuild:
```bash
rm -rf node_modules
npm install
npm run dist:nsis  # or dist:mac
```

3. Check build logs in:
- `C:\Typing Project\slywriter-electron\dist\builder-debug.yml`

### Render Deployment Issues

1. Check deployment logs:
```bash
# Via dashboard
https://dashboard.render.com/web/<service-id>/logs

# Via CLI
"C:\Users\brice\Downloads\cli_2.4.1_windows_amd64\cli_v2.4.1.exe" logs <service-id>
```

2. Verify root directory setting:
- Frontend: `slywriter-ui`
- Backend: `slywriter-ui/backend`

3. Check if files are in correct location:
```bash
# Frontend files should be in
C:\Typing Project\slywriter-ui\app\
C:\Typing Project\slywriter-ui\package.json

# Backend files should be in
C:\Typing Project\slywriter-ui\backend\main.py
C:\Typing Project\slywriter-ui\backend\requirements.txt
```

---

## 📊 MONITORING & ANALYTICS

### Check User Count

```bash
# Production users on v2.9.2
# See plan_data.json and users.json for user data
cat "C:\Typing Project\plan_data.json"
cat "C:\Typing Project\users.json"
```

### Check Telemetry

- Database: PostgreSQL on Render (slywriter-telemetry)
- API: https://slywriterapp.onrender.com/api/telemetry

### Monitor Errors

1. Render logs (backend errors)
2. Electron app logs (desktop errors)
3. GitHub Issues (user reports)

---

## 🛠️ USEFUL COMMANDS

### Git

```bash
# Create release branch
git checkout -b release/v2.9.3
git push origin release/v2.9.3

# Tag release
git tag -a v2.9.3 -m "Release v2.9.3"
git push origin v2.9.3

# Delete tag (if mistake)
git tag -d v2.9.3
git push origin :refs/tags/v2.9.3
```

### GitHub CLI

```bash
# List releases
gh release list

# View release
gh release view v2.9.3

# Delete release
gh release delete v2.9.3 --yes

# Upload asset
gh release upload v2.9.3 SlyWriter-Setup-2.9.3.exe

# Delete asset
gh release delete-asset v2.9.3 SlyWriter-2.9.3.dmg --yes

# List workflow runs
gh run list --workflow=build-mac.yml

# Watch workflow
gh run watch <run-id>

# Download artifacts
gh run download <run-id>
```

### Render CLI

```bash
# List services
"C:\Users\brice\Downloads\cli_2.4.1_windows_amd64\cli_v2.4.1.exe" services list

# Deploy service
"C:\Users\brice\Downloads\cli_2.4.1_windows_amd64\cli_v2.4.1.exe" deploys create <service-id> --confirm --wait

# View logs
"C:\Users\brice\Downloads\cli_2.4.1_windows_amd64\cli_v2.4.1.exe" logs <service-id>
```

### npm

```bash
# Install dependencies
npm install

# Clean build
rm -rf node_modules dist
npm install
npm run dist:nsis

# Dev mode (Electron)
npm run dev
```

---

## 📝 RELEASE CHECKLIST

Before releasing a new version, complete this checklist:

### Pre-Release
- [ ] All changes committed and pushed
- [ ] Version updated in `slywriter-electron/package.json`
- [ ] Tested on Windows (build + install)
- [ ] Tested on Mac (build + install)
- [ ] Backend starts without errors
- [ ] UI loads correctly
- [ ] Critical features work (typing, hotkeys, permissions)

### Build
- [ ] Windows build created (`npm run dist:nsis`)
- [ ] Mac build created via GitHub Actions (signed + notarized)
- [ ] Both builds tested locally

### Release
- [ ] Git tag created and pushed
- [ ] GitHub release created
- [ ] Windows .exe uploaded
- [ ] Mac .dmg uploaded (notarized)
- [ ] Release notes written
- [ ] Update CONTEXT_FOR_NEXT_CLAUDE.md with any issues

### Post-Release
- [ ] Verify downloads work
- [ ] Test auto-update mechanism
- [ ] Monitor for user issues
- [ ] Update documentation if needed

---

## 🆘 EMERGENCY CONTACTS & RESOURCES

### Credentials Locations
- **GitHub Secrets:** Repository Settings → Secrets and variables → Actions
- **Render Dashboard:** https://dashboard.render.com
- **AWS Console:** EC2 → Instances → slyporter (i-0c5e3a99a92573d24)
- **Apple Developer:** https://developer.apple.com (Team ID: 55S897P97X)

### Important URLs
- **GitHub Repo:** https://github.com/slywriterapp/slywriterapp
- **Frontend (Render):** https://slywriter-ui.onrender.com
- **Backend API (Render):** https://slywriterapp.onrender.com
- **Releases:** https://github.com/slywriterapp/slywriterapp/releases

### Key Files to Reference
- `CONTEXT_FOR_NEXT_CLAUDE.md` - Previous session notes
- `CODE_SIGNING_ANALYSIS.md` - Code signing info
- `MAC_PORT_REQUIREMENTS.md` - Mac-specific requirements
- `.github/workflows/build-mac.yml` - Mac build workflow

---

## 💡 FINAL TIPS

1. **ALWAYS read CONTEXT_FOR_NEXT_CLAUDE.md first** - It contains notes from previous Claude sessions

2. **NEVER edit files in build output directories** - Only edit source files in project root

3. **Test locally before releasing** - Build and install on both Windows and Mac

4. **Use GitHub Actions for Mac builds** - Automatic signing and notarization

5. **Keep credentials secure** - Never commit API keys, passwords, or certificates

6. **Update version numbers** - package.json, git tags, release notes

7. **Document your changes** - Update CONTEXT_FOR_NEXT_CLAUDE.md for next Claude

8. **When in doubt, ask** - Better to clarify than break production for 30+ users

---

## 📞 NEED HELP?

If you're stuck:
1. Read this guide thoroughly
2. Check CONTEXT_FOR_NEXT_CLAUDE.md
3. Look at previous git commits for examples
4. Check GitHub Actions logs for build errors
5. Review Render deployment logs
6. Ask the user for clarification

**Remember:** 30+ users depend on SlyWriter working correctly. Take your time, test thoroughly, and don't rush releases.

---

**End of Guide** - Last updated: 2025-11-21 by Claude (v2.9.2 release session)

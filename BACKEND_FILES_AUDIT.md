# Backend Files Audit - SlyWriter Project

**Date**: October 9, 2025
**Purpose**: Identify which backend files are used and which can be safely removed/renamed

---

## 🔍 KEY FINDING: TWO SEPARATE BACKENDS

### 1. **Desktop App Backend** (Electron)
- **File**: `C:\Typing Project\backend_api.py` (ROOT directory)
- **Used by**: Electron desktop app
- **Configured in**: `slywriter-electron/main.js` (lines 131-132)
- **How it starts**: Electron spawns Python process running this file
- **Status**: ✅ **ACTIVELY USED**

### 2. **Web App Backend** (Render Cloud)
- **File**: `C:\Typing Project\slywriter-ui\backend\main.py`
- **Used by**: Web app at slywriter-ui.onrender.com
- **Configured in**: Render.com deployment settings
  - Root Directory: `slywriter-ui/backend`
  - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Status**: ✅ **ACTIVELY USED**

---

## ⚠️ THE PROBLEM

**I've been editing the WRONG file!**
- Made WPM changes to: `backend_api.py` (desktop backend)
- But user is testing on: Web app (which uses `main.py`)
- **Result**: Changes never deployed to web app!

---

## 📋 All Backend Files in Repository

### Root Directory Backend Files (`C:\Typing Project\`)

| File | Purpose | Used By | Status |
|------|---------|---------|--------|
| **backend_api.py** | Desktop typing backend | Electron app | ✅ ACTIVE |
| gui_main.py | Desktop app entry point | Electron app | ✅ ACTIVE |
| sly_app.py | Main desktop UI | Electron app | ✅ ACTIVE |
| typing_engine.py | Typing automation core | Desktop app | ✅ ACTIVE |
| typing_logic.py | Text processing | Desktop app | ✅ ACTIVE |
| typing_ui.py | Desktop UI components | Desktop app | ✅ ACTIVE |
| premium_typing.py | AI filler features | Desktop app | ✅ ACTIVE |
| auth.py | Authentication | Desktop app | ✅ ACTIVE |
| config.py | Config constants | Desktop app | ✅ ACTIVE |
| utils.py | Utilities | Desktop app | ✅ ACTIVE |
| sly_config.py | Profile management | Desktop app | ✅ ACTIVE |
| tab_*.py | Desktop UI tabs | Desktop app | ✅ ACTIVE |
| modern_*.py | Modern UI components | Desktop app | ✅ ACTIVE |
| websocket_typing.py | WebSocket support | Desktop app | ✅ ACTIVE |
| settings_sync.py | Settings sync | Desktop app | ✅ ACTIVE |
| telemetry_*.py | Telemetry tracking | Desktop app | ✅ ACTIVE |
| grammarly_simulator.py | Grammarly-style corrections | Desktop app | ✅ ACTIVE |
| license_manager.py | License verification | Desktop app | ✅ ACTIVE |

### Test Files (Root Directory)

| File | Purpose | Status |
|------|---------|--------|
| test_*.py | Various test scripts | 🧪 TEST FILES |
| comprehensive_test_suite.py | Test suite | 🧪 TEST FILES |
| exhaustive_test.py | Tests | 🧪 TEST FILES |
| final_200wpm_test.py | WPM tests | 🧪 TEST FILES |
| verify_200wpm.py | Verification | 🧪 TEST FILES |

**Note**: Test files can be kept or moved to a /tests folder

### Utility/Setup Scripts (Root Directory)

| File | Purpose | Status |
|------|---------|--------|
| create_*.py | Graphics/asset creation | 🛠️ UTILITY |
| deploy_to_render_complete.py | Deployment script | 🛠️ UTILITY |
| run_auth_server.py | Auth server runner | 🛠️ UTILITY |
| set_pro.py | Pro account setter | 🛠️ UTILITY |
| update_api_urls.py | API URL updater | 🛠️ UTILITY |

**Note**: Utility scripts can be kept or moved to /scripts folder

### Web Backend Files (`C:\Typing Project\slywriter-ui\backend\`)

| File | Purpose | Used By | Status |
|------|---------|---------|--------|
| **main.py** (77KB) | Web app backend | Render deployment | ✅ ACTIVE |
| auth.py | Web authentication | main.py | ✅ ACTIVE |
| database.py | Database operations | main.py | ✅ ACTIVE |
| license_manager.py | License verification | main.py | ✅ ACTIVE |
| ai_integration.py | AI features | main.py | ✅ ACTIVE |
| advanced_humanization.py | Text humanization | main.py | ✅ ACTIVE |
| startup.py | Startup scripts | Deployment | ✅ ACTIVE |
| logging_config.py | Logging setup | main.py | ✅ ACTIVE |
| wpm_calculator.py | WPM calculations | main.py | ✅ ACTIVE (?) |
| wpm_calculator_v2.py | WPM calculations v2 | main.py | ⚠️ MIGHT BE OLD VERSION |
| fix_typos.py | Typo fixing | main.py | ✅ ACTIVE (?) |
| typo_correction_enhanced.py | Enhanced typo fix | main.py | ⚠️ MIGHT BE OLD VERSION |
| voice_transcription.py | Voice features | main.py | ✅ ACTIVE (?) |
| migrate_add_profile_picture.py | Database migration | One-time use | ⏭️ MIGRATION SCRIPT |

**Note**: Files marked with (?) need import check in main.py to confirm usage

---

## 🔧 SOLUTION TO WPM BUG

### What Needs To Happen:

**Desktop App (Electron)**:
1. ✅ Already has WPM fix in `backend_api.py`
2. ✅ Debug logging already added
3. ✅ Should work correctly

**Web App (Render)**:
1. ❌ Need to apply WPM fix to `slywriter-ui/backend/main.py`
2. ❌ Need to add debug logging to `main.py`
3. ❌ Need to trigger Render redeploy

---

## 📝 RECOMMENDATIONS

### Option 1: Keep Both Backends (Current State)
**Pros**:
- Desktop and web have different requirements
- No breaking changes
- Clear separation

**Cons**:
- Have to maintain two backends
- Bug fixes must be applied twice
- Confusing (as evidenced by this bug!)

### Option 2: Unify Backends
**Pros**:
- Single source of truth
- Fix bugs once
- Less confusion

**Cons**:
- Major refactoring required
- Might break desktop or web functionality
- Risky

### Option 3: Rename for Clarity (RECOMMENDED)
**Immediate action**:
1. Rename `backend_api.py` → `backend_desktop.py` (make it obvious)
2. Keep `slywriter-ui/backend/main.py` as is (web backend)
3. Update Electron's `main.js` to use new filename
4. Apply WPM fix to **BOTH** backends

**Pros**:
- Immediately clear which is which
- No functionality broken
- Easy to maintain both

**Cons**:
- Need to update Electron config
- Need to rebuild desktop app

---

## 🎯 IMMEDIATE ACTION NEEDED

### To Fix WPM Bug on Web App:

1. **Apply WPM fix to `slywriter-ui/backend/main.py`**
   - Add debug logging
   - Fix WPM state handling
   - Fix profile selection logic

2. **Trigger Render Redeploy**
   - Push changes to GitHub
   - Render will auto-deploy

3. **Test on web app**
   - User tests at slywriter-ui.onrender.com
   - Should finally see WPM: 250 instead of 70

---

## ❓ QUESTIONS FOR USER

1. **Do you want to rename files for clarity?**
   - `backend_api.py` → `backend_desktop.py`
   - Would require rebuilding desktop app

2. **Should we consolidate backends in the future?**
   - Or keep them separate?

3. **What to do with test files?**
   - Keep in root?
   - Move to /tests folder?
   - Delete old ones?

4. **What to do with utility scripts?**
   - Keep in root?
   - Move to /scripts folder?

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

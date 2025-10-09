# SlyWriter Version 2.5.2 - WPM Debug & Custom Speed Update

**Release Date**: October 9, 2025

---

## 🔧 Bug Fixes & Improvements

### WPM Profile Debug Logging
- **Added comprehensive debug logging for WPM profile selection** (`TypingTabWithWPM.tsx:873-879`)
  - Shows selected profile name in console
  - Displays calculated WPM value before sending to backend
  - Logs full request data including custom_wpm parameter
  - Helps diagnose WPM discrepancies between selected profiles and actual typing speed

**Debug Output Example**:
```
========== TYPING START DEBUG ==========
[TypingTab] Selected Profile: Lightning
[TypingTab] Profile Default WPM: 250
[TypingTab] Actual WPM (will be sent): 250
[TypingTab] Custom WPM parameter: 250
[TypingTab] Request Data: {...custom_wpm: 250...}
========================================
```

### Custom Profile Enhancement
- **Increased Custom profile WPM limit: 200 → 500 WPM**
  - Allows ultra-fast typing speeds up to 500 WPM
  - Updated both Ctrl+Up hotkey and UI button limits
  - Changed profile label to show "Up to 500 WPM" instead of "Calibrate First"
  - Backend updated to support higher WPM values

**Impact**: Users can now calibrate custom typing speeds much faster than before, with support for professional/competitive typing speeds.

---

## 📋 Previous Changes (Completed in 2.5.1)

### Profile Switching Debug Logging
- Added comprehensive debug logging to profile switching
- Logs which profile is being loaded (built-in vs custom)
- Shows preset values before settings update
- Displays settings values after update for verification

---

## 🎯 Known Issues Being Investigated

### WPM Profile Application
**Issue**: Some users report that changing profiles doesn't change the actual typing speed or WPM displayed in overlay.

**Debug Tools Added in 2.5.2**:
- Console now shows exactly what profile is selected
- Logs show WPM value being calculated
- Request data is logged with custom_wpm parameter
- Backend logs show received WPM value

**Diagnostic Steps**:
1. Open desktop app with console visible
2. Select a profile (e.g., Lightning - 250 WPM)
3. Paste text and click "Start Typing"
4. Check console output for `========== TYPING START DEBUG ==========`
5. Verify the "Actual WPM (will be sent)" matches expected profile WPM
6. Check if typing speed matches expected WPM

**Expected WPM Values**:
- **Slow**: ~40 WPM
- **Medium**: ~70 WPM (default)
- **Fast**: ~100 WPM
- **Lightning**: ~250 WPM ⚡
- **Custom**: Up to 500 WPM (user calibrated)

---

## 📝 Files Modified

1. **slywriter/__init__.py** - Version bumped to 2.5.2
2. **slywriter-electron/package.json** - Version bumped to 2.5.2
3. **slywriter-ui/app/components/TypingTabWithWPM.tsx** - Added debug logging, increased Custom WPM limit to 500
4. **backend_api.py** - Updated Custom profile description

---

## 🚀 Deployment

This release includes:
- WPM profile debugging improvements for desktop app
- Custom profile speed limit increase (200 → 500 WPM)
- Maintained all UI enhancements from 2.5.0
- Maintained all API tracking fixes from 2.5.0
- Maintained profile switching debug logging from 2.5.1

**Auto-deploy**: Changes will be deployed to Render backend automatically on git push.

**Desktop App**: Users will need to download version 2.5.2 manually (auto-update coming soon).

---

## 🔧 Technical Details

### WPM Calculation Flow
1. User selects profile from dropdown
2. Frontend calculates WPM using `getProfileWpm()`
3. **[NEW]** Console logs show calculated WPM value
4. Request sent to backend with `custom_wpm` parameter
5. **[NEW]** Backend logs show received WPM value
6. Backend calculates delays from WPM
7. Typing starts with calculated delays
8. WebSocket sends WPM to frontend for overlay display

### Debug Output Locations
- **Frontend Debug**: `TypingTabWithWPM.tsx:873-879, 898-899`
- **Backend Debug**: `backend_api.py:257, 269, 271, 275`

### Custom WPM Limits
- **Previous**: 20-200 WPM
- **New**: 20-500 WPM
- **Changes**: Lines 794, 1457 in TypingTabWithWPM.tsx

---

## 📞 Support

If you continue experiencing WPM issues after 2.5.2:
1. Check console output when selecting profiles and starting typing
2. Look for the debug section starting with `========== TYPING START DEBUG ==========`
3. Take screenshot of debug messages
4. Report issue with console output at: https://github.com/anthropics/slywriter/issues

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

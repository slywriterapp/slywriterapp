# SlyWriter Version 2.5.1 - Profile Debug Update

**Release Date**: October 9, 2025

---

## 🐛 Bug Fixes

### Profile Switching Debug Logging
- **Added comprehensive debug logging to profile switching** (`sly_config.py:187-214`)
  - Logs which profile is being loaded (built-in vs custom)
  - Shows preset values before settings update (min_delay, max_delay)
  - Displays settings values after update for verification
  - Helps diagnose issues where profile delays aren't being applied correctly

**Impact**: Users experiencing WPM discrepancies between selected profiles and actual typing speed can now see detailed console output to identify if profiles are loading correctly.

---

## 📋 Previous Changes (Completed in 2.5.0)

### UI Enhancements
- ✅ **Logo**: Updated to transparent purple logo (`for_topleft_logo.png`)
- ✅ **Title Bar**: Black title bar using Windows DWM API (Windows 10/11)
- ✅ **Scrollbars**: Discord-style minimal scrollbars (thin, gray, rounded, no arrows)

### API Tracking Verified
- ✅ Word tracking: Working correctly
- ✅ AI generation tracking: Working correctly
- ✅ Humanizer tracking: Working correctly
- ✅ AI filler: FREE (not tracked) - Fixed
- ✅ Referral system: Fixed endpoint
- ✅ Learn tab: FREE (not tracked)

---

## 🔍 Known Issues Being Investigated

### WPM Profile Application
**Issue**: Some users report that changing profiles (Default, Speed-Type, Ultra-Slow) doesn't change the actual typing speed or WPM displayed in overlay.

**Current Status**: Debug logging added in 2.5.1 to track profile loading behavior.

**Expected Values**:
- **Default**: ~125-133 WPM (min_delay: 0.07s, max_delay: 0.11s)
- **Speed-Type**: ~400 WPM (min_delay: 0.01s, max_delay: 0.05s)
- **Ultra-Slow**: ~44-51 WPM (min_delay: 0.15s, max_delay: 0.40s)

**Diagnostic Steps**:
1. Open desktop app with console visible
2. Switch between profiles using dropdown
3. Check console output for `[PROFILE]` messages
4. Verify min_delay and max_delay values match expected profile settings
5. Check if WPM overlay updates accordingly

---

## 📝 Files Modified

1. **slywriter/__init__.py** - Version bumped to 2.5.1
2. **sly_config.py** - Added profile switching debug logging

---

## 🚀 Deployment

This release includes:
- Profile debugging improvements for desktop app
- Maintained all UI enhancements from 2.5.0
- Maintained all API tracking fixes from 2.5.0

**Auto-deploy**: Changes will be deployed to Render backend automatically on git push.

**Desktop App**: Users will need to download version 2.5.1 manually (auto-update coming soon).

---

## 🔧 Technical Details

### Profile Loading Flow
1. User selects profile from dropdown
2. `on_profile_change()` is called
3. Profile preset values loaded (built-in or custom)
4. Settings updated with preset values
5. Config saved to disk
6. UI updated via `update_from_config()`

### Debug Output Example
```
[PROFILE] Loading built-in profile: Speed-Type
[PROFILE] Preset values: min_delay=0.01, max_delay=0.05
[PROFILE] After update - settings: min_delay=0.01, max_delay=0.05
```

---

## 📞 Support

If you continue experiencing WPM issues after 2.5.1:
1. Check console output when switching profiles
2. Take screenshot of debug messages
3. Report issue with console output at: https://github.com/anthropics/slywriter/issues

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
